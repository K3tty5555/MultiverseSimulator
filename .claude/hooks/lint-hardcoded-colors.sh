#!/bin/bash
# Hook: 编辑 .vue/.css 文件后检查硬编码颜色
# 所有颜色必须通过 design.css Token 引用
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.vue && "$FILE_PATH" != *.css ]] && exit 0
[[ "$FILE_PATH" == *"design.css" ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

# 匹配 6 位十六进制颜色（最常见的硬编码格式）
# 排除注释行和 SVG fill/stroke 中的 none/currentColor
MATCHES=$(grep -nE '#[0-9a-fA-F]{6}\b' "$FILE_PATH" 2>/dev/null \
  | grep -v '^\s*//' \
  | grep -v '^\s*\*' \
  | grep -v '<!--')

if [ -n "$MATCHES" ]; then
  echo "检测到硬编码颜色值，请使用 design.css 中的 CSS 变量替代：" >&2
  echo "$MATCHES" >&2
  exit 2
fi

exit 0
