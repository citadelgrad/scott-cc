#!/bin/bash
# Ghostty tab indicator for Claude Code Stop events
# Sends BEL to trigger 🔔 in tab title + dock bounce
# Sends OSC 9 desktop notification with brief summary of work done
# Skips if stop_hook_active (prevents double-bell when another hook blocks)

INPUT=$(cat)

ACTIVE=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('stop_hook_active', False))" 2>/dev/null)
if [ "$ACTIVE" = "True" ]; then
  exit 0
fi

# BEL for tab indicator + dock bounce
printf '\a' > /dev/tty 2>/dev/null

# Extract a brief summary from the last assistant message in the transcript
SUMMARY=$(echo "$INPUT" | python3 -c "
import json, sys, re

input_data = json.load(sys.stdin)
transcript_path = input_data.get('transcript_path', '')
if not transcript_path:
    print('Claude finished')
    sys.exit(0)

# Read last assistant message from JSONL transcript
last_text = ''
with open(transcript_path, 'r') as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        if entry.get('type') == 'assistant':
            # Extract text content from message blocks
            msg = entry.get('message', {})
            parts = []
            for block in msg.get('content', []):
                if isinstance(block, dict) and block.get('type') == 'text':
                    parts.append(block['text'])
                elif isinstance(block, str):
                    parts.append(block)
            if parts:
                last_text = ' '.join(parts)

if not last_text:
    print('Claude finished')
    sys.exit(0)

# Clean up: collapse whitespace, strip markdown artifacts
text = re.sub(r'\s+', ' ', last_text).strip()
text = re.sub(r'[#*\`\[\]]', '', text).strip()

# Take first ~10 words
words = text.split()[:10]
summary = ' '.join(words)
if len(text.split()) > 10:
    summary += '...'

print(summary)
" 2>/dev/null)

SUMMARY="${SUMMARY:-Claude finished}"

# OSC 9 desktop notification with summary
printf '\033]9;%s\a' "$SUMMARY" > /dev/tty 2>/dev/null
