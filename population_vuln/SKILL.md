name: population-vuln
allowed-tools: Bash(python3 *)
description: Trigger when user asks about population vulnerability, demographics, seniors, overcrowding or INSEE data.
run: python3 ${CLAUDE_SKILL_DIR}/main.py --args "$ARGUMENTS"
