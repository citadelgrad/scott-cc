#!/bin/bash
# PostToolUse hook: encode JSON tool responses to TOON format
# TOON is a compact alternative to JSON that saves context tokens.
#
# For MCP tools: replaces tool output via updatedMCPToolOutput
# For built-in tools: adds compact TOON as additionalContext

TOON=$(command -v toon 2>/dev/null)
MIN_JSON_LENGTH=200  # skip small responses — not worth encoding

INPUT=$(cat)

TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')
TOOL_RESPONSE=$(echo "$INPUT" | jq -c '.tool_response // empty')
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty')

# Bail if no response
[ -z "$TOOL_RESPONSE" ] && exit 0

# Warn once per session if toon is not installed
if [ -z "$TOON" ] || [ ! -x "$TOON" ]; then
  SENTINEL_DIR="/tmp/.scott-cc-hooks"
  mkdir -p "$SENTINEL_DIR"
  WARNED="$SENTINEL_DIR/toon-warned-${SESSION_ID:-unknown}"
  if [ ! -f "$WARNED" ]; then
    touch "$WARNED"
    # Clean up stale sentinels older than 24h
    find "$SENTINEL_DIR" -name "toon-warned-*" -mtime +1 -delete 2>/dev/null
    jq -n '{
      "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "[scott-cc] TOON hook: `toon` binary not found. Install it to enable compact tool response encoding and save context tokens. See: https://github.com/citadelgrad/toon"
      }
    }'
  fi
  exit 0
fi

# Skip if response is too short to benefit from encoding
RESP_LEN=${#TOOL_RESPONSE}
[ "$RESP_LEN" -lt "$MIN_JSON_LENGTH" ] && exit 0

# Check if tool_response is a JSON object or array (not a bare string/number)
if ! echo "$TOOL_RESPONSE" | jq -e 'type == "object" or type == "array"' > /dev/null 2>&1; then
  exit 0
fi

# Encode to TOON
TOON_OUTPUT=$(echo "$TOOL_RESPONSE" | "$TOON" --encode 2>/dev/null)
[ $? -ne 0 ] || [ -z "$TOON_OUTPUT" ] && exit 0

# Check TOON is actually shorter (with some margin)
TOON_LEN=${#TOON_OUTPUT}
if [ "$TOON_LEN" -ge "$RESP_LEN" ]; then
  exit 0
fi

# Determine if this is an MCP tool (mcp__ prefix)
if [[ "$TOOL_NAME" == mcp__* ]]; then
  # MCP tools: replace the output entirely
  jq -n --arg toon "$TOON_OUTPUT" '{
    "hookSpecificOutput": {
      "hookEventName": "PostToolUse",
      "updatedMCPToolOutput": $toon
    }
  }'
else
  # Built-in tools: add TOON as additional context
  jq -n --arg toon "$TOON_OUTPUT" '{
    "hookSpecificOutput": {
      "hookEventName": "PostToolUse",
      "additionalContext": ("(TOON-encoded response, compact format)\n" + $toon)
    }
  }'
fi
