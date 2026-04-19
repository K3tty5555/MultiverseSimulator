"""AI 辅助生成：
- assist_persona:             全局人物库 (name → bio/era_year/avatar_emoji)
- assist_agent:               宇宙内 NPC (name + universe context → role/bio/persona/mbti)
- generate_universe_scaffold: 新建宇宙时 (type + keywords → title/premise/era_label/world_label)
- assist_protagonist:         新建宇宙主角 (name + premise + era_label → role/bio)
- generate_canonical_events:  角色史实年表 (name + type + world_label → [{year,title,description}])
所有函数带 retry（2 次），捕获 JSON 解析 / 网络超时。
"""

import json
import logging
from typing import Dict
from ..utils.llm_client import LLMClient

logger = logging.getLogger('lifeplanner.ai_assist')


def assist_persona(name: str) -> Dict:
    """
    根据人物名称用 LLM 自动生成 bio / era_year / avatar_emoji。
    同步调用，约 2s。
    """
    llm = LLMClient()
    result = llm.chat_json(
        messages=[
            {
                "role": "system",
                "content": (
                    "你是一位历史知识专家，帮助用户快速创建历史人物角色卡。"
                    "根据人物名字，生成简洁准确的简介、标志年份和代表性 emoji。"
                    "简介要聚焦于其决策思维方式、所处历史背景和主要成就，150-300 字。"
                    "era_year 选择该人物最具代表性的年份（整数）。"
                    "avatar_emoji 选一个最能代表该人物的 emoji（单个字符）。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"请为历史人物「{name}」生成角色卡信息。\n"
                    "返回格式（JSON）：\n"
                    '{"bio": "简介内容", "avatar_emoji": "🎯", "era_year": 1955}'
                )
            }
        ],
        temperature=0.3,
        max_tokens=512
    )
    return result


def _call_assist_agent_llm(name: str, premise: str, protagonist: str) -> Dict:
    """单次 LLM 调用（无 retry），供 assist_agent 外层包装重试。"""
    llm = LLMClient()
    clipped_premise = (premise or '').strip()[:300] or '（无背景）'
    clipped_protagonist = (protagonist or '').strip()[:40] or '（未指定主角）'
    return llm.chat_json(
        messages=[
            {
                "role": "system",
                "content": (
                    "你是叙事 NPC 档案师，为给定宇宙设计 NPC 的性格档案。"
                    "档案要聚焦 NPC 的身份、性格特质、与主角相关的背景故事，"
                    "不要判断 NPC 对主角的立场（这由用户决定）。"
                    "严格返回 JSON，字段齐全；不确定的 mbti 可返回空字符串。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"宇宙背景：{clipped_premise}\n"
                    f"主角：{clipped_protagonist}\n"
                    f"NPC 姓名：{name}\n\n"
                    "请生成该 NPC 的档案。返回格式（JSON）：\n"
                    '{"role": "身份职位，10-30字",'
                    ' "bio": "背景简介，聚焦性格与决策动机，100-200字",'
                    ' "persona": "5-10 个性格形容词，空格分隔",'
                    ' "mbti": "MBTI 类型如 INTJ，不确定则空字符串"}'
                )
            }
        ],
        temperature=0.4,
        max_tokens=600
    )


_UNIVERSE_TYPE_LABEL = {
    'historical': '历史',
    'fictional':  '虚构',
}


def generate_universe_scaffold(universe_type: str, keywords: str) -> Dict:
    """新建宇宙时根据类型 + 关键词，LLM 生成 {title, premise, era_label, world_label}。
    - era_label 仅历史类型填（"汉末三国 · 208 AD"）
    - world_label 是 IP / 题材名（"三国" / "红楼梦" / "王者荣耀" / "赛博朋克"）
    """
    label = _UNIVERSE_TYPE_LABEL.get(universe_type, '历史')
    kw = (keywords or '').strip()[:200] or '（未提供关键词）'

    def _call():
        llm = LLMClient()
        return llm.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是平行宇宙构造师，根据类型和关键词，生成宇宙骨架。"
                        "- title：宇宙名称，富有画面感的短标题，10-30字。"
                        "- premise：世界观背景，100-300字，为主角推演提供舞台。"
                        "- era_label：时期标签，仅历史类型填（例：'汉末三国 · 208 AD'）；虚构类型返回空字符串。"
                        "- world_label：简短的 IP / 题材名（2-8 字），如 '三国' / '红楼梦' / '王者荣耀' / '赛博朋克 2077' / '哈利波特'。"
                        "严格返回 JSON，不要 markdown 包裹。"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"类型：{label}\n"
                        f"关键词：{kw}\n\n"
                        "返回格式（JSON）：\n"
                        '{"title": "...", "premise": "...", "era_label": "...", "world_label": "..."}'
                    )
                }
            ],
            temperature=0.7,
            max_tokens=700
        )

    last_err = None
    for attempt in range(2):
        try:
            result = _call()
            return {
                'title':       str(result.get('title', ''))[:200],
                'premise':     str(result.get('premise', ''))[:2000],
                'era_label':   str(result.get('era_label', ''))[:100],
                'world_label': str(result.get('world_label', ''))[:40],
            }
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            logger.warning("scaffold JSON 解析失败 (attempt=%d): %s", attempt + 1, e)
        except Exception as e:
            last_err = e
            logger.warning("scaffold LLM 调用失败 (attempt=%d): %s", attempt + 1, e)
    raise last_err if last_err else RuntimeError('scaffold 生成失败')


def assist_protagonist(name: str, premise: str, era_label: str = '') -> Dict:
    """为新建宇宙的主角生成 {role, bio}。与 assist_agent 的区别：
    - 没有 protagonist 上下文（本函数输出的就是主角自己）
    - 不返回 stance（主角无立场概念）
    """
    clipped_premise = (premise or '').strip()[:400] or '（无背景）'
    clipped_era = (era_label or '').strip()[:60]
    era_line = f"时期：{clipped_era}\n" if clipped_era else ''

    def _call():
        llm = LLMClient()
        return llm.chat_json(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "你是叙事主角档案师，根据宇宙背景和主角姓名，生成主角的身份和背景简介。"
                        "聚焦主角的独特处境、决策动机、性格基调，帮助后续剧情推演。"
                        "严格返回 JSON，不要 markdown 包裹。"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"宇宙背景：{clipped_premise}\n"
                        f"{era_line}"
                        f"主角姓名：{name}\n\n"
                        "返回格式（JSON）：\n"
                        '{"role": "身份/职位，10-30字", "bio": "背景简介，100-200字"}'
                    )
                }
            ],
            temperature=0.4,
            max_tokens=500
        )

    last_err = None
    for attempt in range(2):
        try:
            result = _call()
            return {
                'role': str(result.get('role', ''))[:100],
                'bio':  str(result.get('bio', ''))[:500],
            }
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            logger.warning("assist_protagonist JSON 失败 (attempt=%d): %s", attempt + 1, e)
        except Exception as e:
            last_err = e
            logger.warning("assist_protagonist LLM 失败 (attempt=%d): %s", attempt + 1, e)
    raise last_err if last_err else RuntimeError('主角生成失败')


def generate_canonical_events(name: str, universe_type: str,
                              world_label: str = '') -> list:
    """为指定角色生成 5-8 个史实/原著关键节点。
    返回 [{year: int|null, title: str, description: str, sort_order: int}]。
    - historical：真实史实节点，year 为 AD 整数（公元前用负数）
    - fictional：原著情节节点，year 可为 null（用 sort_order 排序）
    """
    label = _UNIVERSE_TYPE_LABEL.get(universe_type, '历史')
    world = (world_label or '').strip()[:60]

    def _call():
        llm = LLMClient(timeout=90)
        system = (
            "你是角色档案师，提炼指定角色在真实历史或文学原著中的关键节点。"
            "要求："
            "- 生成 5-8 个，聚焦对角色命运有重大影响的事件；"
            "- historical 类型：title 是事件名（如「官渡之战」），year 为整数 AD（公元前负数）；"
            "- fictional 类型：title 是原著章节或情节（如「黛玉初入贾府」），year 可为 null；"
            "- description 100-200 字，概括事件经过与对角色的意义；"
            "- sort_order 从 1 递增，按时间先后；"
            "- 如果你不熟悉此角色或无可考证史实，events 返回空数组。"
            "严格返回 JSON，不要 markdown 包裹。"
        )
        world_line = f"世界 / 题材：{world}\n" if world else ""
        user = (
            f"角色：{name}\n"
            f"类型：{label}\n"
            f"{world_line}"
            "返回格式（JSON）：\n"
            '{"events": [{"year": 200, "title": "...", "description": "...", "sort_order": 1}]}'
        )
        return llm.chat_json(
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            temperature=0.5,
            max_tokens=1500
        )

    last_err = None
    for attempt in range(2):
        try:
            result = _call()
            raw = result.get('events') or []
            events = []
            for idx, e in enumerate(raw):
                if not isinstance(e, dict):
                    continue
                title = str(e.get('title') or '').strip()
                if not title:
                    continue
                year = e.get('year')
                if year is not None:
                    try:
                        year = int(year)
                    except (ValueError, TypeError):
                        year = None
                events.append({
                    'year': year,
                    'title': title[:200],
                    'description': str(e.get('description') or '')[:1000],
                    'sort_order': int(e.get('sort_order') or (idx + 1)),
                })
            return events
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            logger.warning("canonical JSON 失败 (attempt=%d): %s", attempt + 1, e)
        except Exception as e:
            last_err = e
            logger.warning("canonical LLM 失败 (attempt=%d): %s", attempt + 1, e)
    raise last_err if last_err else RuntimeError('canonical 生成失败')


def assist_agent(name: str, premise: str, protagonist: str) -> Dict:
    """
    根据宇宙背景 + 主角 + NPC 姓名，LLM 生成 NPC 档案。
    最多重试 2 次（首次 + 1 次）以覆盖 JSON 解析失败 / 偶发网络抖动。
    返回 {role, bio, persona, mbti, stance='neutral'}；stance 不由 LLM 判定。
    """
    last_err = None
    for attempt in range(2):
        try:
            result = _call_assist_agent_llm(name, premise, protagonist)
            return {
                'role':    str(result.get('role', ''))[:100],
                'bio':     str(result.get('bio', ''))[:500],
                'persona': str(result.get('persona', ''))[:200],
                'mbti':    str(result.get('mbti', ''))[:10],
                # 立场由用户手动选，后端一律返回 neutral
                'stance':  'neutral',
            }
        except (json.JSONDecodeError, ValueError) as e:
            last_err = e
            logger.warning("assist_agent JSON 解析失败 (attempt=%d): %s", attempt + 1, e)
            continue
        except Exception as e:
            # 网络/超时等其他错误也重试一次
            last_err = e
            logger.warning("assist_agent LLM 调用失败 (attempt=%d): %s", attempt + 1, e)
            continue
    raise last_err if last_err else RuntimeError('assist_agent 失败')
