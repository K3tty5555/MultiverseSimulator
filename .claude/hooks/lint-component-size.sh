#!/bin/bash
# Hook: 编辑 .vue 文件后检查组件体积
# 超过 400 行的组件应考虑拆分
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.vue ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

LINE_COUNT=$(wc -l < "$FILE_PATH" 2>/dev/null | tr -d ' ')

if [ "$LINE_COUNT" -gt 400 ]; then
  echo "组件已达 ${LINE_COUNT} 行（超过 400 行警戒线），建议拆分为子组件。" >&2
  exit 2
fi

exit 0
