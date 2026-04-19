#!/bin/bash
# Hook: 编辑含 EventSource 的 .vue 文件后检查是否有清理逻辑
# 防止 SSE 连接泄漏
INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

[[ -z "$FILE_PATH" ]] && exit 0
[[ "$FILE_PATH" != *.vue ]] && exit 0
[[ ! -f "$FILE_PATH" ]] && exit 0

# 检查文件是否使用了原生 EventSource（非 composable 封装）
if grep -q 'new EventSource' "$FILE_PATH" 2>/dev/null; then
  # 检查是否有 onBeforeUnmount 清理
  if ! grep -q 'onBeforeUnmount' "$FILE_PATH" 2>/dev/null; then
    echo "文件使用了 EventSource 但未发现 onBeforeUnmount 清理逻辑。" >&2
    echo "请使用 useEventStream composable，或在 onBeforeUnmount 中手动关闭连接。" >&2
    exit 2
  fi
fi

exit 0
