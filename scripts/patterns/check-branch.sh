#!/bin/bash
# check-branch.sh - Example pattern check script
# Returns non-zero if committing to main/master branch

CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)

if [[ "$CURRENT_BRANCH" == "main" ]] || [[ "$CURRENT_BRANCH" == "master" ]]; then
    # Return non-zero to indicate pattern matched (bad)
    exit 1
fi

# Return 0 to indicate pattern did not match (OK to proceed)
exit 0
