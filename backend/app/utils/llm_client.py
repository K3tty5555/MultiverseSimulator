"""LLM 客户端 - 支持普通调用和 SSE 流式输出"""

import re
import time
import logging
from typing import Optional, Dict, Any, List, Generator
from openai import OpenAI
from .safe_json import safe_json_loads

logger = logging.getLogger('lifeplanner.llm')

from ..config import Config

# 推理模型关键字（model name 含其一即视为推理模型，自动放大 token / timeout 预算）
# 业务调用方只需按"正文真正需要的"传 max_tokens；推理模型下自动留出思维链预算。
REASONING_MODEL_KEYWORDS = (
    'k2.6', 'kimi-thinking',
    'o1', 'o3',
    'r1', 'reasoner', 'deepseek-reasoner',
    'qwq', 'thinking', 'reasoning',
)
# 推理模型 token 放大倍率与上限（避免超 API 限制）
REASONING_TOKEN_MULTIPLIER = 4
REASONING_TOKEN_CAP = 8192
# 推理模型 timeout 放大倍率与下限（思维链可能耗时 60-120s）
REASONING_TIMEOUT_MULTIPLIER = 3
REASONING_TIMEOUT_FLOOR = 180


def _is_reasoning_model(name: Optional[str]) -> bool:
    if not name:
        return False
    n = name.lower()
    return any(kw in n for kw in REASONING_MODEL_KEYWORDS)


class LLMClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: int = 30
    ):
        # 懒加载，避免循环依赖
        from ..models.settings import SettingsRepository
        cfg = SettingsRepository.get_llm_config()
        self.api_key = api_key or cfg['api_key']
        self.base_url = base_url or cfg['base_url']
        self.model = model or cfg['model']

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.is_reasoning = _is_reasoning_model(self.model)
        if self.is_reasoning:
            timeout = max(timeout * REASONING_TIMEOUT_MULTIPLIER, REASONING_TIMEOUT_FLOOR)

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

    def _scale_tokens(self, max_tokens: int) -> int:
        """推理模型下放大 max_tokens 给思维链留预算，并 clip 到 API 上限。"""
        if not self.is_reasoning:
            return max_tokens
        return min(max_tokens * REASONING_TOKEN_MULTIPLIER, REASONING_TOKEN_CAP)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None
    ) -> str:
        """流式收集完整回复，避免推理模型长时间思考导致 ReadTimeout。"""
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": self._scale_tokens(max_tokens),
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        content_chunks: List[str] = []
        reasoning_chunks: List[str] = []
        for chunk in response:
            if not chunk.choices:
                continue
            c = chunk.choices[0].delta.content
            r = getattr(chunk.choices[0].delta, 'reasoning_content', None)
            if c:
                content_chunks.append(c)
            if r:
                reasoning_chunks.append(r)

        has_content = bool(content_chunks)
        has_reasoning = bool(reasoning_chunks)
        logger.debug("chat() content_len=%d reasoning_len=%d",
                     sum(len(c) for c in content_chunks),
                     sum(len(r) for r in reasoning_chunks))
        if not has_content and has_reasoning:
            # 模型仅通过 reasoning_content 输出（如部分 Kimi/DeepSeek 配置）
            content = ''.join(reasoning_chunks)
        else:
            content = ''.join(content_chunks)

        # 剥离 <think>...</think> 思维链（闭合、未闭合开始标签、孤立结束标签三种情况）
        content = re.sub(r'<think>[\s\S]*?</think>', '', content)
        content = re.sub(r'<think>[\s\S]*$', '', content)
        content = re.sub(r'</think>', '', content)          # 清除孤立的结束标签
        return content.strip()

    def chat_with_retry(
        self,
        messages: List[Dict[str, str]],
        max_retries: int = 2,
        **kwargs
    ) -> Optional[str]:
        """带指数退避重试的 chat 调用，失败时返回 None（调用方负责降级处理）。"""
        for attempt in range(max_retries + 1):
            try:
                return self.chat(messages, **kwargs)
            except Exception as e:
                if attempt == max_retries:
                    logger.error("LLM chat 已重试 %d 次仍失败: %s", max_retries, e)
                    return None
                wait = 2 ** attempt
                logger.warning("LLM chat 重试 %d/%d，等待 %ds: %s", attempt + 1, max_retries, wait, e)
                time.sleep(wait)
        return None  # 不可达，但 mypy 需要

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        # 在最后一条 user 消息末尾注入 JSON 提示，兼容所有模型
        patched = list(messages)
        for i in reversed(range(len(patched))):
            if patched[i]['role'] == 'user':
                patched[i] = dict(patched[i])
                patched[i]['content'] += '\n\n请以 JSON 格式返回结果。'
                break

        response = self.chat(
            messages=patched,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        cleaned = response.strip()
        # 去掉 markdown 代码块包裹
        cleaned = re.sub(r'^```(?:json)?\s*\n?', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\n?```\s*$', '', cleaned).strip()
        # 提取第一个 {...} 块（防止模型多说废话；贪婪匹配可正确处理嵌套数组）
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            cleaned = match.group(0)
        result = safe_json_loads(cleaned)
        if result is None:
            raise ValueError(f"LLM 返回的 JSON 格式无效: {cleaned}")
        return result

    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Generator[tuple, None, None]:
        """流式输出，yield (is_thinking: bool, chunk: str) 元组。

        - is_thinking=True：思维链内容（reasoning_content 或 <think> 块）
        - is_thinking=False：正式正文内容

        调用方可选择丢弃思维链或单独展示。
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=self._scale_tokens(max_tokens),
            stream=True
        )
        in_think = False
        buf = ''
        for chunk in response:
            if not chunk.choices:
                continue
            # reasoning_content = 原生思维链字段（Kimi K2 / DeepSeek R1 等）
            reasoning = getattr(chunk.choices[0].delta, 'reasoning_content', None)
            content = chunk.choices[0].delta.content

            if reasoning:
                yield (True, reasoning)
                continue

            if not content:
                continue

            buf += content
            # 扫描缓冲区，区分 <think>...</think> 包裹的思维链与正文
            while buf:
                if in_think:
                    end = buf.find('</think>')
                    if end == -1:
                        yield (True, buf)
                        buf = ''
                        break
                    yield (True, buf[:end])
                    buf = buf[end + len('</think>'):]
                    in_think = False
                else:
                    start = buf.find('<think>')
                    if start == -1:
                        yield (False, buf)
                        buf = ''
                        break
                    if start > 0:
                        yield (False, buf[:start])
                    buf = buf[start + len('<think>'):]
                    in_think = True
