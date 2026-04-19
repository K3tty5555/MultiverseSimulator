"""平行宇宙推演引擎 - A2A 多 Agent SSE 流"""

import json
import queue
import threading
import time
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import Generator, List, Optional

from ..models.universe import UniverseRepository
from ..utils.llm_client import LLMClient
from .agent_factory import detect_new_agents, generate_agent_profile

logger = logging.getLogger('lifeplanner.universe')

MAX_THREAD_CONTEXT = 8     # 带入 prompt 的最近 N 轮上下文
MAX_AGENTS_PER_TURN = 5   # 每轮最多响应的 NPC 数量
MEMORY_COMPRESS_THRESHOLD = 1500  # agent memory 超过此字数时触发压缩


def _build_narrator_messages(universe: dict, thread: list,
                              protagonist_action: str, locale: str) -> list:
    """构建世界叙事者的 prompt。"""
    perspective = universe.get('perspective', 'god')
    protagonist_name = universe['protagonist_name']
    protagonist_role = universe.get('protagonist_role') or ''

    # 选取最近 MAX_THREAD_CONTEXT 轮作为上下文
    recent = thread[-MAX_THREAD_CONTEXT:] if len(thread) > MAX_THREAD_CONTEXT else thread

    history_lines = []
    for node in recent:
        if node.get('protagonist_action'):
            history_lines.append(f"[行动] {node['protagonist_action']}")
        if node.get('narrator_content'):
            # 只取前 300 字避免 prompt 过长
            history_lines.append(f"[世界] {node['narrator_content'][:300]}")

    history_text = '\n'.join(history_lines) if history_lines else '（宇宙刚刚开启）'

    if perspective == 'first_person':
        system_content = (
            '你是这个平行宇宙的意识本体，以第二人称（"你..."）呈现主角感受到的现实反馈。'
            '叙述沉浸式、感官化，让主角感受到世界对其行动的即时回应。'
            '输出 120-200 字的叙事片段，不使用标题或小节分隔。'
        )
        action_prompt = (
            f'主角\u300c{protagonist_name}\u300d({protagonist_role}) 刚刚：{protagonist_action}\n\n'
            '描述主角接下来感受到的世界回应（第二人称）：'
        )
    else:  # god
        system_content = (
            "你是全知叙事者，以第三人称、客观且富有戏剧感的笔触描述平行宇宙中发生的事。"
            "叙述有因果逻辑，展现主角行动对周围世界的即时影响。"
            "输出 120-200 字的叙事片段，不使用标题或小节分隔。"
        )
        action_prompt = (
            f'主角\u300c{protagonist_name}\u300d({protagonist_role}) 刚刚：{protagonist_action}\n\n'
            '叙述这个行动对世界的直接影响与后果：'
        )

    if locale and locale.startswith('en'):
        system_content += " Reply in English."

    return [
        {"role": "system", "content": (
            f"{system_content}\n\n"
            f"宇宙背景：{universe['premise'][:600]}"
        )},
        {"role": "user", "content": (
            f"历史进程（最近 {len(recent)} 轮）：\n{history_text}\n\n"
            f"{action_prompt}"
        )}
    ]


def _build_npc_messages(agent: dict, universe: dict, thread: list,
                        protagonist_action: str, narrator_content: str) -> list:
    """构建单个 NPC 的反应 prompt。"""
    memory = agent.get('memory_summary') or ''
    stance_label = {'ally': '盟友/支持者', 'neutral': '中立', 'adversary': '对立/对手'}.get(
        agent.get('stance', 'neutral'), '中立'
    )

    # 最近 3 轮上下文
    recent = thread[-3:] if len(thread) > 3 else thread
    context_lines = []
    for node in recent:
        if node.get('protagonist_action'):
            context_lines.append(f"主角行动：{node['protagonist_action']}")
        if node.get('narrator_content'):
            context_lines.append(f"世界反应：{node['narrator_content'][:200]}")
    context_text = '\n'.join(context_lines) if context_lines else '（初始状态）'

    return [
        {
            "role": "system",
            "content": (
                f"你是角色「{agent['name']}」，扮演该角色对主角行动作出真实反应。\n"
                f"身份：{agent.get('role') or '未知'}\n"
                f"性格：{agent.get('persona') or '普通人'}\n"
                f"对主角立场：{stance_label}\n"
                f"宇宙背景：{universe['premise'][:300]}"
            )
        },
        {
            "role": "user",
            "content": (
                f"近期记忆摘要：{memory[:400] if memory else '无'}\n\n"
                f"最近进展：\n{context_text}\n\n"
                f"主角刚刚：{protagonist_action}\n"
                f"世界反应：{narrator_content[:300]}\n\n"
                f"以第一人称写出「{agent['name']}」此刻的反应（40-80字，内心想法或直接行动）："
            )
        }
    ]


def _detect_branch(universe: dict, thread: list, narrator_content: str,
                   protagonist_action: str) -> dict:
    """基于当前世界状态，为主角生成 2-3 个推荐的下一步行动。

    每回合必定返回建议（不再用 is_branch 门控），让玩家始终有参考方向。

    三层上下文：
      L0 宇宙前提（~80 tokens）
      L1 当前实体状态摘要（有数据时）或最近 4 回历史（降级）
      L2 最近 2 回原文 + 本回叙事（最鲜活的上下文）
    """
    try:
        # L0：宇宙前提
        l0 = universe['premise'][:400]

        # L1：优先使用结构化实体状态，无数据时降级到 thread 历史
        entity_states = UniverseRepository.get_entity_states(universe['id'])
        if entity_states:
            def _stance_label(score: float, stance: str) -> str:
                if stance == 'unknown':
                    return ''
                if score > 0.3:
                    return '  [对主角友善]'
                if score < -0.3:
                    return '  [对主角敌对]'
                return '  [对主角中立]'

            l1_lines = [
                f"- {e['entity_name']}（{e['category']}）：{e['summary']}"
                + _stance_label(e['stance_score'], e['stance'])
                for e in entity_states
            ]
            l1 = "当前世界实体状态：\n" + "\n".join(l1_lines)
        else:
            # 早期回合尚无实体状态，降级使用历史文本
            recent_fb = thread[-4:] if len(thread) > 4 else thread
            fb_lines = []
            for node in recent_fb:
                if node.get('protagonist_action'):
                    fb_lines.append(f"[行动] {node['protagonist_action'][:100]}")
                if node.get('narrator_content'):
                    fb_lines.append(f"[世界] {node['narrator_content'][:200]}")
            l1 = "历史经过：\n" + ('\n'.join(fb_lines) or '（初始状态）')

        # L2：最近 2 回原文 + 本回叙事
        recent2 = thread[-2:] if len(thread) >= 2 else thread
        l2_lines = []
        for node in recent2:
            if node.get('protagonist_action'):
                l2_lines.append(f"[行动] {node['protagonist_action'][:150]}")
            if node.get('narrator_content'):
                l2_lines.append(f"[世界] {node['narrator_content'][:300]}")
        l2_lines.append(f"[本回行动] {protagonist_action}")
        l2_lines.append(f"[本回世界] {narrator_content[:400]}")
        l2 = "近期经过：\n" + "\n".join(l2_lines)

        protagonist_name = universe.get('protagonist_name', '主角')

        llm = LLMClient(timeout=30)
        msgs = [
            {
                "role": "system",
                "content": (
                    f"你是叙事顾问。根据当前世界状态，为主角「{protagonist_name}」"
                    "生成 2-3 个合理的下一步行动建议。"
                    "建议必须与已发生的事件和当前实体状态完全一致，"
                    "不得出现与既成事实矛盾的内容。"
                    "每个建议应风格各异（如：进攻/防守/外交/观望），给玩家真正不同的选择。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"宇宙背景：{l0}\n\n"
                    f"{l1}\n\n"
                    f"{l2}\n\n"
                    f"请为主角「{protagonist_name}」生成 2-3 个下一步行动建议。\n"
                    "返回 JSON（必须包含 options，不要 is_branch 字段）：\n"
                    '{"prompt": "接下来如何行动？（15字内）", '
                    '"options": [{"label": "选项标签（8字内）", "description": "具体行动描述（25字内）"}]}'
                )
            }
        ]
        result = llm.chat_json(msgs, temperature=0.4, max_tokens=400)
        # 兼容旧格式：强制 is_branch=True，保证前端始终展示
        if isinstance(result, dict) and result.get('options'):
            result['is_branch'] = True
        else:
            result = {'is_branch': False}
        return result
    except Exception as e:
        logger.warning(f"行动建议生成失败（已忽略）: {e}")
        return {'is_branch': False}


def _extract_entity_states(universe_id: int, narrator_content: str,
                            protagonist_action: str, turn_number: int,
                            protagonist_name: str) -> list:
    """从本回叙事中提取实体状态变化，异步持久化到 DB。

    只提取本回明确发生改变的实体，不重复未变化内容。
    失败时仅记录警告，不影响主流程。
    """
    try:
        llm = LLMClient(timeout=45)
        msgs = [
            {
                "role": "system",
                "content": (
                    "你是世界状态分析师。从叙事片段中提取角色/势力/地点的状态变化。"
                    "只提取本回明确发生改变的实体，不推测，不重复未变化的内容。"
                    "每条摘要用一句话（20-40字），准确描述变化后的新状态。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"主角：{protagonist_name}\n"
                    f"本回行动：{protagonist_action[:300]}\n"
                    f"本回叙事：{narrator_content[:800]}\n\n"
                    "提取实体状态变化，返回 JSON 数组（无变化则返回空数组 []）：\n"
                    '[{"entity": "曹操", "category": "person", '
                    '"summary": "被生擒，押于柴桑水寨，命运未卜", '
                    '"stance": "opposing", "stance_score": -0.9}]\n'
                    "category 只能是：person / faction / location / situation\n"
                    "stance 只能是：supportive / opposing / neutral / unknown\n"
                    "stance_score：-1.0（强烈敌对）到 +1.0（强烈友善），相对于主角"
                )
            }
        ]
        result = llm.chat_json(msgs, temperature=0.2, max_tokens=500)
        # 兼容模型返回 {"changes": [...]} 或直接返回数组
        changes = result if isinstance(result, list) else result.get('changes', [])
        if not isinstance(changes, list):
            return []

        for c in changes:
            if not isinstance(c, dict):
                continue
            entity = c.get('entity') or c.get('name') or ''
            summary = c.get('summary') or c.get('state') or ''
            if not entity or not summary:
                continue
            name = str(entity)[:50]
            category = c.get('category', 'person')
            if category not in ('person', 'faction', 'location', 'situation'):
                category = 'person'
            summary = str(summary)[:200]
            stance = c.get('stance', 'unknown')
            if stance not in ('supportive', 'opposing', 'neutral', 'unknown'):
                stance = 'unknown'
            try:
                score = float(c.get('stance_score', 0.0))
                score = max(-1.0, min(1.0, score))
            except (TypeError, ValueError):
                score = 0.0

            UniverseRepository.upsert_entity_state(
                universe_id, name, category, summary, stance, score, turn_number
            )
            UniverseRepository.add_entity_history(
                universe_id, name, category, summary, stance, score, turn_number
            )

        logger.info(f"实体状态提取完成 universe={universe_id} turn={turn_number} changes={len(changes)}")
        return changes
    except Exception as e:
        logger.warning(f"实体状态提取失败（已忽略）: {e}")
        return []


def _compress_agent_memory(agent: dict, new_reaction: str) -> str:
    """将新反应追加到 memory_summary，若超阈值则压缩。"""
    current = agent.get('memory_summary') or ''
    updated = (current + '\n' + new_reaction).strip() if current else new_reaction

    if len(updated) <= MEMORY_COMPRESS_THRESHOLD:
        return updated

    # 触发压缩
    try:
        llm = LLMClient(timeout=30)
        msgs = [
            {"role": "system", "content": "你是记忆压缩器。将以下角色记忆摘要压缩到300字以内，保留关键事件和立场变化。"},
            {"role": "user", "content": updated}
        ]
        return llm.chat(msgs, temperature=0.2, max_tokens=400)
    except Exception:
        # 压缩失败时截断
        return updated[-MEMORY_COMPRESS_THRESHOLD:]


def stream_turn(
    universe_id: int,
    parent_node_id: Optional[int],
    protagonist_action: str,
    locale: str = 'zh'
) -> Generator[str, None, None]:
    """SSE 生成器：处理平行宇宙推演一轮。

    事件协议：
    - agent_created: 新 NPC 档案生成
    - narrator_chunk: 叙事者流式文本片段
    - narrator_done: 叙事者完整文本
    - agent_reaction: 单个 NPC 的反应
    - branch_prompt: AI 检测到分叉点
    - node_done: 节点已持久化
    - error: 不可恢复错误
    """
    # 立即 flush HTTP headers
    yield ': turn-start\n\n'

    # ── 1. 加载宇宙与线程上下文 ──────────────────────────────────────────
    universe = UniverseRepository.get(universe_id)
    if not universe:
        yield f'data: {json.dumps({"type": "error", "message": "宇宙不存在"}, ensure_ascii=False)}\n\n'
        return

    agents = universe.get('agents', [])
    known_names = {a['name'] for a in agents}

    thread = []
    if parent_node_id:
        thread = UniverseRepository.get_thread(parent_node_id)

    # ── 2. 叙事者：先流式输出（不阻塞等待 NPC 检测）────────────────────────
    narrator_messages = _build_narrator_messages(universe, thread, protagonist_action, locale)
    llm_narrator = LLMClient(timeout=300)
    narrator_content = ''
    try:
        for chunk in llm_narrator.stream(narrator_messages, temperature=0.8, max_tokens=600):
            narrator_content += chunk
            yield f'data: {json.dumps({"type": "narrator_chunk", "chunk": chunk}, ensure_ascii=False)}\n\n'
        yield f'data: {json.dumps({"type": "narrator_done", "content": narrator_content}, ensure_ascii=False)}\n\n'
    except Exception as e:
        logger.exception(f"叙事者生成失败: {e}")
        yield f'data: {json.dumps({"type": "error", "message": "叙事生成失败，请重试"}, ensure_ascii=False)}\n\n'
        return

    # ── 3. 检测并生成新 NPC（叙事完成后，基于完整上下文更准确）───────────────
    detection_text = protagonist_action + '\n' + narrator_content[:600]
    try:
        new_names = detect_new_agents(detection_text, known_names)
        for name in new_names:
            try:
                agent = generate_agent_profile(
                    universe_id, name,
                    universe['premise'],
                    universe['protagonist_name'],
                    detection_text[:500]
                )
                known_names.add(name)
                agents.append(agent)
                yield f'data: {json.dumps({"type": "agent_created", "agent": agent}, ensure_ascii=False)}\n\n'
            except Exception as e:
                logger.warning(f"NPC生成失败 [{name}]: {e}")
    except Exception as e:
        logger.warning(f"NPC检测失败（已忽略）: {e}")

    # ── 4. NPC 并行反应 ────────────────────────────────────────────────────
    active_agents = agents[:MAX_AGENTS_PER_TURN]
    agent_reactions_list = []

    if active_agents:
        reaction_queue: queue.Queue = queue.Queue()

        def npc_worker(agent: dict):
            try:
                msgs = _build_npc_messages(agent, universe, thread,
                                           protagonist_action, narrator_content)
                llm_npc = LLMClient(timeout=60)
                reaction = llm_npc.chat(msgs, temperature=0.7, max_tokens=300)
                reaction_queue.put(('ok', agent, reaction))
            except Exception as e:
                logger.warning(f"NPC反应失败 [{agent.get('name')}]: {e}")
                reaction_queue.put(('error', agent, str(e)))

        executor = ThreadPoolExecutor(
            max_workers=len(active_agents),
            thread_name_prefix=f'npc-{universe_id}'
        )
        for ag in active_agents:
            executor.submit(npc_worker, ag)
        executor.shutdown(wait=False)

        received_npc = 0
        npc_deadline = time.monotonic() + 30
        while received_npc < len(active_agents):
            remaining = npc_deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                status, agent, reaction = reaction_queue.get(timeout=min(15.0, remaining))
                received_npc += 1
                if status == 'ok':
                    reaction_data = {
                        'agent_id': agent['id'],
                        'name': agent['name'],
                        'reaction': reaction
                    }
                    agent_reactions_list.append(reaction_data)
                    yield f'data: {json.dumps({"type": "agent_reaction", **reaction_data}, ensure_ascii=False)}\n\n'
            except queue.Empty:
                yield ': heartbeat\n\n'

    # ── 5. 分叉检测 ────────────────────────────────────────────────────────
    branch_result = {'is_branch': False}
    try:
        branch_result = _detect_branch(universe, thread, narrator_content, protagonist_action)
        if branch_result.get('is_branch'):
            yield f'data: {json.dumps({"type": "branch_prompt", "prompt": branch_result.get("prompt"), "options": branch_result.get("options", [])}, ensure_ascii=False)}\n\n'
    except Exception as e:
        logger.warning(f"分叉检测失败（已忽略）: {e}")

    # ── 6. 持久化节点（turn_number 由 DB 原子计算，避免并发竞态）─────────────
    try:
        node = UniverseRepository.create_node(
            universe_id=universe_id,
            parent_id=parent_node_id,
            perspective=universe.get('perspective', 'god'),
            protagonist_action=protagonist_action,
            narrator_content=narrator_content,
            agent_reactions=json.dumps(agent_reactions_list, ensure_ascii=False),
            branch_prompt=branch_result.get('prompt') if branch_result.get('is_branch') else None,
            branch_options=json.dumps(branch_result.get('options', []), ensure_ascii=False) if branch_result.get('is_branch') else None,
        )
        UniverseRepository.touch(universe_id)
        yield f'data: {json.dumps({"type": "node_done", "node_id": node["id"], "turn_number": node["turn_number"], "branch": branch_result.get("is_branch", False)}, ensure_ascii=False)}\n\n'
    except Exception as e:
        logger.exception(f"节点保存失败: {e}")
        yield f'data: {json.dumps({"type": "error", "message": "节点保存失败，推演内容已生成但未记录"}, ensure_ascii=False)}\n\n'
        return

    # ── 7. 后台更新 Agent 记忆（best-effort）─────────────────────────────
    if agent_reactions_list:
        def update_memories():
            for reaction_data in agent_reactions_list:
                agent_obj = next(
                    (a for a in active_agents if a['id'] == reaction_data['agent_id']), None
                )
                if not agent_obj:
                    continue
                try:
                    new_summary = _compress_agent_memory(agent_obj, reaction_data['reaction'])
                    UniverseRepository.update_agent_memory(
                        agent_obj['id'], new_summary, node['id']
                    )
                except Exception as e:
                    logger.warning(f"Agent记忆更新失败 [{agent_obj.get('name')}]: {e}")

        mem_thread = threading.Thread(target=update_memories, daemon=False,
                                      name=f'mem-{universe_id}-{node["id"]}')
        mem_thread.start()

    # ── 8. 后台提取实体世界状态（与 Phase 7 并行，best-effort）────────────
    # 提前捕获变量，避免 closure 引用被后续修改
    _uid   = universe_id
    _nt    = narrator_content
    _pa    = protagonist_action
    _tn    = node.get('turn_number', 0)
    _pname = universe.get('protagonist_name', '')

    def _run_entity_extraction():
        _extract_entity_states(_uid, _nt, _pa, _tn, _pname)

    threading.Thread(
        target=_run_entity_extraction, daemon=True,
        name=f'entity-{_uid}-{_tn}'
    ).start()


def generate_perspective_alt(universe_id: int, node_ids: List[int],
                              new_perspective: str) -> Generator[str, None, None]:
    """为历史节点生成新视角的回溯叙事（SSE 流）。"""
    yield ': retro-start\n\n'

    universe = UniverseRepository.get(universe_id)
    if not universe:
        yield f'data: {json.dumps({"type": "error", "message": "宇宙不存在"}, ensure_ascii=False)}\n\n'
        return

    for node_id in node_ids[:3]:  # 最多回溯3个节点
        node = UniverseRepository.get_node(node_id)
        if not node or not node.get('narrator_content'):
            continue

        try:
            llm = LLMClient(timeout=60)
            protagonist_name = universe['protagonist_name']
            original = node['narrator_content']
            action = node.get('protagonist_action') or ''

            action_context = f"（场景：{action[:100]}）\n\n" if action else ""
            if new_perspective == 'first_person':
                prompt = (
                    f'将以下第三人称叙事改写为第二人称沉浸视角（"你..."），'
                    f'保持内容相同但更具代入感（60-150字）：\n\n{action_context}{original[:600]}'
                )
            else:
                prompt = (
                    f"将以下第二人称叙事改写为第三人称全知叙事，"
                    f"主角为「{protagonist_name}」（60-150字）：\n\n{action_context}{original[:600]}"
                )

            msgs = [
                {"role": "system", "content": "你是专业叙事改写者，保持情节不变，只改写视角。"},
                {"role": "user", "content": prompt}
            ]
            alt_content = llm.chat(msgs, temperature=0.5, max_tokens=300)
            UniverseRepository.update_node_alt(node_id, alt_content)
            yield f'data: {json.dumps({"type": "retro_done", "node_id": node_id, "alt_content": alt_content}, ensure_ascii=False)}\n\n'
        except Exception as e:
            logger.warning(f"回溯叙事生成失败 node={node_id}: {e}")

    yield f'data: {json.dumps({"type": "done"}, ensure_ascii=False)}\n\n'
