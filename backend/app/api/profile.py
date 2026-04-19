"""Profile API Blueprint"""

import os
import uuid
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from ..models.profile import ProfileRepository
from ..models.task import TaskManager
from ..services.profile_builder import start_auto_import, start_synthesis
from ..utils.file_parser import extract_text
from ..config import Config
from ..utils.locale import get_locale

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

_MAGIC_BYTES = {
    b'%PDF': 'pdf',
}

def _check_file_type(file) -> str:
    """用文件头验证实际类型，返回 ext 或 None"""
    header = file.read(8)
    file.seek(0)
    for magic, ftype in _MAGIC_BYTES.items():
        if header.startswith(magic):
            return ftype
    # txt / md 无固定 magic，允许通过
    return 'text'

profile_bp = Blueprint('profile', __name__)


@profile_bp.route('', methods=['GET'])
def get_profile():
    profile = ProfileRepository.get()
    if not profile:
        return jsonify({'profile': None}), 200
    return jsonify({'profile': profile})


@profile_bp.route('', methods=['POST'])
def save_profile():
    data = request.get_json() or {}
    profile = ProfileRepository.upsert(
        display_name=data.get('name'),
        age=data.get('age'),
        structured=data.get('structured', {})
    )
    return jsonify({'profile': profile})


@profile_bp.route('', methods=['PUT'])
def update_profile():
    data = request.get_json() or {}
    profile = ProfileRepository.upsert(
        display_name=data.get('name'),
        age=data.get('age'),
        structured=data.get('structured', {})
    )
    return jsonify({'profile': profile})


@profile_bp.route('/auto-import', methods=['POST'])
def auto_import():
    locale = get_locale()
    task_id = start_auto_import(locale)
    return jsonify({'task_id': task_id})


@profile_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id):
    tm = TaskManager()
    task = tm.get_task(task_id)
    if not task:
        return jsonify({'error': '任务不存在'}), 404
    return jsonify({'task': task.to_dict()})


@profile_bp.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': '没有文件'}), 400

    uploaded = []
    files = request.files.getlist('files')
    for file in files:
        if not file.filename:
            continue
        ext = os.path.splitext(file.filename)[1].lower().lstrip('.')
        if ext not in Config.ALLOWED_EXTENSIONS:
            continue

        # 文件大小检查
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_FILE_SIZE:
            continue

        # PDF 用 magic bytes 验证，其他文本文件直接通过
        if ext == 'pdf' and _check_file_type(file) != 'pdf':
            continue

        # 安全文件名：先 secure_filename，再加 UUID 前缀避免重名覆盖
        safe_name = secure_filename(file.filename) or 'upload'
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        save_path = os.path.join(Config.UPLOAD_FOLDER, unique_name)
        file.save(save_path)
        content = extract_text(save_path)

        record = ProfileRepository.add_file(
            filename=safe_name,
            file_type=ext,
            source='upload',
            content=content
        )
        uploaded.append(record)

    return jsonify({'files': ProfileRepository.get_all_files()})


@profile_bp.route('/files/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    ProfileRepository.delete_file(file_id)
    return jsonify({'success': True})


@profile_bp.route('/synthesize', methods=['POST'])
def synthesize():
    locale = get_locale()
    task_id = start_synthesis(locale)
    return jsonify({'task_id': task_id})


@profile_bp.route('/versions', methods=['GET'])
def get_versions():
    """获取档案版本列表（最近 5 个）"""
    versions = ProfileRepository.get_versions()
    return jsonify({'versions': versions}), 200


@profile_bp.route('/versions/<int:version_id>', methods=['GET'])
def get_version(version_id):
    """获取某版本的完整数据"""
    from ..utils.safe_json import safe_json_loads
    version = ProfileRepository.get_version(version_id)
    if not version:
        return jsonify({'error': '版本不存在'}), 404
    if version.get('structured'):
        version['structured'] = safe_json_loads(version['structured'], {}, 'profile_version')
    return jsonify({'version': version}), 200
