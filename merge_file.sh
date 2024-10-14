#!/bin/bash

# Function to pull all remote branches to local
pull_all_branches() {
  echo "Fetching all remote branches..."
  git fetch --all
  for REMOTE_BRANCH in $(git branch -r | grep -v '\->' | grep 'origin/' | sed 's/origin\///'); do
    if ! git show-ref --verify --quiet refs/heads/$REMOTE_BRANCH; then
      echo "Creating local branch '$REMOTE_BRANCH' from 'origin/$REMOTE_BRANCH'"
      git checkout -b $REMOTE_BRANCH origin/$REMOTE_BRANCH
    else
      echo "Pulling latest changes for '$REMOTE_BRANCH'"
      git checkout $REMOTE_BRANCH
      git pull origin $REMOTE_BRANCH
    fi
  done
  git checkout $CURRENT_BRANCH
}

# Get the current branch
CURRENT_BRANCH=$(git branch --show-current)

# Ensure we are on a valid branch
if [ -z "$CURRENT_BRANCH" ]; then
  echo "Error: Not on a valid branch."
  exit 1
fi

# Call the function to pull all branches
pull_all_branches

# Push current branch to origin to ensure all changes are up to date
if [ -n "$(git status --porcelain)" ]; then
  echo "Pushing changes in current branch '$CURRENT_BRANCH' to origin"
  git push origin $CURRENT_BRANCH
fi

# Check if the filename argument is provided
if [ -z "$1" ]; then
  echo "Usage: $0 <filename>"
  exit 1
fi

FILENAME=$1

# Fetch all branches and sort them
BRANCHES=$(git branch --list --format='%(refname:short)' | sort)

# Add new files if they are not already tracked
if [ -n "$(git ls-files --others --exclude-standard $FILENAME)" ]; then
  echo "Adding new file '$FILENAME' to tracking"
  git add "$FILENAME"
fi

# Commit any uncommitted changes for the specified file
if [ -n "$(git status --porcelain $FILENAME)" ]; then
  echo "Committing changes in '$FILENAME' on branch '$CURRENT_BRANCH'"
  git add "$FILENAME"
  git commit -m "Updated $FILENAME"
fi

# Get the latest commit for the specified file
FILE_COMMIT=$(git log -n 1 --pretty=format:"%H" -- "$FILENAME")

# Find branches greater than the current one and cherry-pick the commit
MERGE_BRANCHES=false
for BRANCH in $BRANCHES; do
  if [ "$BRANCH" == "$CURRENT_BRANCH" ]; then
    MERGE_BRANCHES=true
    continue
  fi

  if [ "$MERGE_BRANCHES" = true ]; then
    echo "Checking if '$FILENAME' exists in branch '$BRANCH'"
    git checkout $BRANCH
    if ! git ls-files --error-unmatch "$FILENAME" > /dev/null 2>&1; then
      echo "File '$FILENAME' does not exist in branch '$BRANCH'. Adding the file with current changes."
      git checkout $CURRENT_BRANCH -- "$FILENAME"
      git add "$FILENAME"
      git commit -m "Added '$FILENAME' to branch '$BRANCH'"
    fi

    # Check if there are any differences before cherry-picking
    if git diff --quiet $CURRENT_BRANCH..$BRANCH -- "$FILENAME"; then
      echo "No changes detected for '$FILENAME' in branch '$BRANCH'. Skipping cherry-pick."
      continue
    fi

    echo "Cherry-picking changes in '$FILENAME' from commit '$FILE_COMMIT' to branch '$BRANCH'"
    git cherry-pick $FILE_COMMIT
    if [ $? -eq 0 ]; then
      echo "Pushing changes to 'origin/$BRANCH'"
      git push origin $BRANCH
    elif git status | grep -q "The previous cherry-pick is now empty"; then
      echo "No changes to apply. Skipping cherry-pick for branch '$BRANCH'."
      git cherry-pick --skip
    else
      echo "Conflict detected during cherry-pick. Manual resolution is required."
      echo "Please resolve the conflict, then run 'git cherry-pick --continue' or 'git cherry-pick --abort' to proceed."
      exit 1
    fi
    CURRENT_BRANCH=$BRANCH
  fi
done

# Finally, cherry-pick to the main branch
echo "Pulling latest changes from 'origin/main'"
git checkout main
git pull origin main

if ! git ls-files --error-unmatch "$FILENAME" > /dev/null 2>&1; then
  echo "File '$FILENAME' does not exist in 'main' branch. Adding the file with current changes."
  git checkout $CURRENT_BRANCH -- "$FILENAME"
  git add "$FILENAME"
  git commit -m "Added '$FILENAME' to 'main' branch"
fi

# Check if there are any differences before cherry-picking
if git diff --quiet $CURRENT_BRANCH..main -- "$FILENAME"; then
  echo "No changes detected for '$FILENAME' in 'main' branch. Skipping cherry-pick."
else
  echo "Cherry-picking changes in '$FILENAME' to 'main' branch"
  git cherry-pick $FILE_COMMIT
  if [ $? -eq 0 ]; then
    echo "Pushing changes to 'origin/main'"
    git push origin main
  elif git status | grep -q "The previous cherry-pick is now empty"; then
    echo "No changes to apply. Skipping cherry-pick for 'main' branch."
    git cherry-pick --skip
  else
    echo "Conflict detected during cherry-pick. Manual resolution is required."
    echo "Please resolve the conflict, then run 'git cherry-pick --continue' or 'git cherry-pick --abort' to proceed."
    exit 1
  fi
fi

echo "Pushing any remaining changes to 'origin/main'"
git push origin main

echo "Merge completed successfully!"
