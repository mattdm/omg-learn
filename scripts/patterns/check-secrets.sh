#!/bin/bash
# check-secrets.sh - Example pattern check script
# Checks staged files for potential secrets
# Returns non-zero if secrets detected

# Check git diff for common secret patterns
if git diff --cached | grep -qE "(API_KEY|SECRET|PASSWORD|TOKEN|private_key|aws_access)" 2>/dev/null; then
    # Secrets potentially detected
    exit 1
fi

# No secrets detected
exit 0
