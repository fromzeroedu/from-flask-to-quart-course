#!/bin/bash

# Check if the filename argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

FILENAME=$1

# Fetch all branches and sort them
BRANCHES=$(git branch --list --format='%(refname:short)' | sort)

# Get the current branch
CURRENT_BRANCH=$(git branch --show-current)

# Ensure we are on a valid branch
if [ -z "$CURRENT_BRANCH" ]; then
  echo "Error: Not on a valid branch."
  exit 1
fi

# Find branches greater than the current one
MERGE_BRANCHES=false
for BRANCH in $BRANCHES; do
  if [ "$BRANCH" == "$CURRENT_BRANCH" ]; then
    MERGE_BRANCHES=true
    continue
  fi

  if [ "$MERGE_BRANCHES" = true ]; then
    echo "Merging changes in '$FILENAME' from '$CURRENT_BRANCH' to '$BRANCH'"
    git checkout $BRANCH
    git merge $CURRENT_BRANCH --no-commit --no-ff -- "$FILENAME"
    if [ $? -ne 0 ]; then
      echo "Error: Merge failed for branch '$BRANCH'"
      exit 1
    fi
    git commit -m "Merged changes in '$FILENAME' from '$CURRENT_BRANCH'"
    CURRENT_BRANCH=$BRANCH
  fi
done

# Finally, merge to the main branch
echo "Merging changes in '$FILENAME' to 'main' branch"
git checkout main
git merge $CURRENT_BRANCH --no-commit --no-ff -- "$FILENAME"
if [ $? -ne 0 ]; then
  echo "Error: Merge failed for 'main' branch"
  exit 1
fi
git commit -m "Merged changes in '$FILENAME' from '$CURRENT_BRANCH'"

echo "Merge completed successfully!"
