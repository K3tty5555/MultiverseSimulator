#!/bin/bash
# Hook: 编辑 .py 文件后检查 json.loads 直接调用
# 所有 JSON 解析必须通过 safe_json_loads() 包装
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.py ]] && exit 0
[[ "$FILE_PATH" == *"safe_json.py" ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

# 查找直接使用 json.loads 的行（排除 safe_json_loads 和注释）
MATCHES=$(grep -nE '\bjson\.loads\(' "$FILE_PATH" 2>/dev/null \
  | grep -v 'safe_json_loads' \
  | grep -v '^\s*#')

if [ -n "$MATCHES" ]; then
  echo "检测到直接使用 json.loads()，请改用 safe_json_loads()：" >&2
  echo "$MATCHES" >&2
  echo "引入方式：from app.utils.safe_json import safe_json_loads" >&2
  exit 2
fi

exit 0
