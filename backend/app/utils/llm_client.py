"""LLM 客户端 - 支持普通调用和 SSE 流式输出"""

import json
import re
import time
import logging
from typing import Optional, Dict, Any, List, Generator
from openai import OpenAI

logger = logging.getLogger('lifeplanner.llm')

from ..config import Config


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

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url, timeout=timeout)

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
            "max_tokens": max_tokens,
            "stream": True,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        chunks: List[str] = []
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if delta:
                chunks.append(delta)
        content = ''.join(chunks)

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
        # 提取第一个 {...} 块（防止模型多说了废话）
        match = re.search(r'\{[\s\S]*\}', cleaned)
        if match:
            cleaned = match.group(0)
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            raise ValueError(f"LLM 返回的 JSON 格式无效: {cleaned}")

    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096
    ) -> Generator[str, None, None]:
        """流式输出，生成 delta 文本块，自动跳过 <think> 思维链内容。"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        in_think = False
        buf = ''
        for chunk in response:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta.content
            if not delta:
                continue
            buf += delta
            # 逐步扫描缓冲区，过滤 <think>...</think>
            while buf:
                if in_think:
                    end = buf.find('</think>')
                    if end == -1:
                        buf = ''  # 思维链还没结束，继续积累
                        break
                    buf = buf[end + len('</think>'):]
                    in_think = False
                else:
                    start = buf.find('<think>')
                    if start == -1:
                        yield buf
                        buf = ''
                        break
                    if start > 0:
                        yield buf[:start]
                    buf = buf[start + len('<think>'):]
                    in_think = True
