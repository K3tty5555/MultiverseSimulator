"""读取 ~/.claude/ 目录中的对话记录和记忆文件"""

import os
import json
from typing import List, Dict
from ..config import Config


def read_claude_memory() -> List[Dict]:
    """读取 ~/.claude/projects/ 下的记忆文件"""
    memory_dir = os.path.join(Config.CLAUDE_HOME, 'projects')
    if not os.path.exists(memory_dir):
        return []

    entries = []
    project_dirs = sorted(os.listdir(memory_dir), reverse=True)[:50]

    for project in project_dirs:
        project_path = os.path.join(memory_dir, project)
        if not os.path.isdir(project_path):
            continue
        jsonl_files = [f for f in os.listdir(project_path) if f.endswith('.jsonl')]
        for jf in jsonl_files[:3]:
            filepath = os.path.join(project_path, jf)
            entries.extend(_parse_jsonl(filepath, max_entries=20))

    return entries


def _parse_jsonl(filepath: str, max_entries: int = 20) -> List[Dict]:
    results = []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Read from end for most recent messages
        for line in reversed(lines):
            if len(results) >= max_entries:
                break
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get('type') == 'user':
                    content = _extract_text_content(entry.get('message', {}).get('content', ''))
                    if content and len(content) > 20:
                        results.append({'role': 'user', 'content': content[:500]})
            except (json.JSONDecodeError, KeyError):
                continue
    except Exception:
        pass
    return results


def _extract_text_content(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                parts.append(item.get('text', ''))
        return ' '.join(parts)
    return ''


def read_claude_memory_files() -> str:
    """读取 ~/.claude/projects/ 下的 MEMORY.md 和记忆文件"""
    memory_path = os.path.join(Config.CLAUDE_HOME, 'MEMORY.md')
    result = []

    if os.path.exists(memory_path):
        try:
            with open(memory_path, 'r', encoding='utf-8') as f:
                result.append(f"[Claude 记忆索引]\n{f.read()[:2000]}")
        except Exception:
            pass

    # Also scan project-level memory
    projects_dir = os.path.join(Config.CLAUDE_HOME, 'projects')
    if os.path.exists(projects_dir):
        for project in os.listdir(projects_dir)[:10]:
            project_memory = os.path.join(projects_dir, project, 'memory')
            if os.path.isdir(project_memory):
                for mf in os.listdir(project_memory)[:5]:
                    if mf.endswith('.md'):
                        try:
                            with open(os.path.join(project_memory, mf), 'r', encoding='utf-8') as f:
                                result.append(f.read()[:1000])
                        except Exception:
                            pass

    return '\n\n'.join(result)


def get_claude_summary() -> str:
    """合并 Claude 历史摘要，用于 profile 上下文"""
    memory_text = read_claude_memory_files()
    conversation_entries = read_claude_memory()

    parts = []
    if memory_text:
        parts.append(f"=== Claude 记忆文件 ===\n{memory_text[:3000]}")

    if conversation_entries:
        samples = conversation_entries[:30]
        conv_text = '\n'.join([f"- {e['content']}" for e in samples])
        parts.append(f"=== Claude 对话样本 ===\n{conv_text}")

    return '\n\n'.join(parts)


def count_sessions() -> int:
    """统计可导入的对话数量"""
    memory_dir = os.path.join(Config.CLAUDE_HOME, 'projects')
    if not os.path.exists(memory_dir):
        return 0
    count = 0
    for project in os.listdir(memory_dir):
        project_path = os.path.join(memory_dir, project)
        if os.path.isdir(project_path):
            count += len([f for f in os.listdir(project_path) if f.endswith('.jsonl')])
    return count
