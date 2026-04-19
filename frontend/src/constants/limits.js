/**
 * 前后端共享的长度常量。
 * 后端 backend/app/api/universe.py 的 MAX_NAME_LEN=50，保持一致。
 * 后续如需动态拉取，可改为 /api/config/limits 端点。
 */
export const MAX_NAME_LEN = 50
export const MAX_BIO_LEN = 500
export const MAX_ROLE_LEN = 100
export const MAX_PERSONA_LEN = 200
export const MAX_MBTI_LEN = 10
