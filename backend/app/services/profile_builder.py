"""个人档案构建服务"""

import threading
import logging
from ..models.task import TaskManager, TaskStatus
from ..models.profile import ProfileRepository
from ..utils.llm_client import LLMClient
from ..utils.claude_reader import get_claude_summary, count_sessions
from ..utils.locale import get_language_instruction, set_locale

logger = logging.getLogger('lifeplanner.profile')


def auto_import_claude(task_id: str, locale: str = 'zh'):
    """后台任务：从 ~/.claude/ 导入数据"""
    tm = TaskManager()
    set_locale(locale)
    tm.update_task(task_id, status=TaskStatus.PROCESSING, progress=10, message="正在读取 Claude 历史...")

    try:
        summary_text = get_claude_summary()
        session_count = count_sessions()

        if summary_text:
            ProfileRepository.add_file(
                filename='claude_history.txt',
                file_type='txt',
                source='claude_auto',
                content=summary_text[:50000]
            )
            tm.complete_task(task_id, {
                'files': ProfileRepository.get_all_files(),
                'sessions_found': session_count
            })
        else:
            tm.complete_task(task_id, {'files': [], 'sessions_found': 0})
    except Exception as e:
        logger.exception(f"Claude 历史导入失败 [task={task_id}]: {e}")
        tm.fail_task(task_id, f"导入失败：{str(e)[:200]}")


def synthesize_profile(task_id: str, locale: str = 'zh'):
    """后台任务：LLM 合成档案摘要"""
    tm = TaskManager()
    set_locale(locale)
    tm.update_task(task_id, status=TaskStatus.PROCESSING, progress=20, message="正在分析档案数据...")

    try:
        profile = ProfileRepository.get()
        if not profile:
            tm.fail_task(task_id, "档案不存在")
            return

        files = profile.get('files', [])
        structured = profile.get('structured', {})

        parts = []
        if structured:
            parts.append(f"基本信息：{structured}")
        for f in files[:10]:
            if f.get('content'):
                parts.append(f"[{f['filename']}]\n{f['content'][:3000]}")

        if not parts:
            tm.fail_task(task_id, "没有足够的数据合成摘要，请先填写基本信息或上传文件")
            return

        combined = '\n\n'.join(parts)
        lang_instruction = get_language_instruction()

        tm.update_task(task_id, progress=50, message="正在生成人物画像摘要...")

        llm = LLMClient(timeout=120)
        response = llm.chat(
            messages=[
                {
                    "role": "system",
                    "content": f"""你是一个专业的人生规划师助手。根据用户提供的个人信息，
生成一段 400-600 字的第三人称人物画像摘要，用于后续的决策推演分析。
摘要应涵盖：基本背景、职业现状、家庭情况、个性特征、价值观倾向、常见关注点和决策偏好。
{lang_instruction}"""
                },
                {
                    "role": "user",
                    "content": f"请根据以下信息生成人物画像摘要：\n\n{combined[:8000]}"
                }
            ],
            temperature=0.5,
            max_tokens=1000
        )

        ProfileRepository.update_summary(response)
        tm.complete_task(task_id, {'summary': response})
    except Exception as e:
        logger.exception(f"档案合成失败 [task={task_id}]: {e}")
        tm.fail_task(task_id, f"合成失败：{str(e)[:200]}")


def start_auto_import(locale: str = 'zh') -> str:
    tm = TaskManager()
    task_id = tm.create_task('claude_import')
    thread = threading.Thread(
        target=auto_import_claude,
        args=(task_id, locale),
        daemon=False,
        name=f"import-{task_id[:8]}"
    )
    thread.start()
    return task_id


def start_synthesis(locale: str = 'zh') -> str:
    tm = TaskManager()
    task_id = tm.create_task('profile_synthesis')
    thread = threading.Thread(
        target=synthesize_profile,
        args=(task_id, locale),
        daemon=False,
        name=f"synth-{task_id[:8]}"
    )
    thread.start()
    return task_id
