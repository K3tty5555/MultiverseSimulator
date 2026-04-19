"""Persona API Blueprint（只读）

角色管理 UI 已从前端删除，personas 表现在只作为内置历史角色（诸葛亮/曹操等）
和 world_checkpoints 的数据源。本文件只保留读取端点，供兜底及未来功能使用。
写入（create/update/delete/assist）已废弃——新角色通过「新建宇宙」流程产生，
主角直接存在 parallel_universes.protagonist_name/role/bio。
"""

from flask import Blueprint, jsonify
from ..models.persona import PersonaRepository
from ..models.universe import UniverseRepository

persona_bp = Blueprint('persona', __name__)


@persona_bp.route('', methods=['GET'])
def list_personas():
    return jsonify({'personas': PersonaRepository.list_all()})


@persona_bp.route('/<int:persona_id>', methods=['GET'])
def get_persona(persona_id):
    persona = PersonaRepository.get(persona_id)
    if not persona:
        return jsonify({'error': '角色不存在'}), 404
    return jsonify({'persona': persona})


@persona_bp.route('/<int:persona_id>/universes', methods=['GET'])
def get_persona_universes(persona_id):
    """返回关联到该角色的活跃宇宙列表。"""
    persona = PersonaRepository.get(persona_id)
    if not persona:
        return jsonify({'error': '角色不存在'}), 404
    universes = UniverseRepository.list_by_persona(persona_id)
    return jsonify({'universes': universes})
