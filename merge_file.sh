#!/bin/bash

# Function to pull all remote branches to local
pull_all_branches() {
  echo "Fetching all remote branches..."
  git fetch --all
  for REMOTE_BRANCH in $(git branch -r | grep -v '\->'); do
    LOCAL_BRANCH=$(echo $REMOTE_BRANCH | sed 's/origin\///')
    if ! git show-ref --verify --quiet refs/heads/$LOCAL_BRANCH; then
      echo "Creating local branch '$LOCAL_BRANCH' from '$REMOTE_BRANCH'"
      git checkout -b $LOCAL_BRANCH $REMOTE_BRANCH
    else
      echo "Pulling latest changes for '$LOCAL_BRANCH'"
      git checkout $LOCAL_BRANCH
      git pull origin $LOCAL_BRANCH
    fi
  done
  git checkout $CURRENT_BRANCH
}

# Call the function to pull all branches
pull_all_branches

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

# Commit any uncommitted changes for the specified file
if [ -n "$(git status --porcelain $FILENAME)" ]; then
  echo "Committing changes in '$FILENAME' on branch '$CURRENT_BRANCH'"
  git add "$FILENAME"
  git commit -m "Updated $FILENAME"
fi

# Get the latest commit for the specified file
FILE_COMMIT=$(git log -n 1 --pretty=format:"%H" -- "$FILENAME")

# Find branches greater than the current one
MERGE_BRANCHES=false
for BRANCH in $BRANCHES; do
  if [ "$BRANCH" == "$CURRENT_BRANCH" ]; then
    MERGE_BRANCHES=true
    continue
  fi

  if [ "$MERGE_BRANCHES" = true ]; then
    echo "Cherry-picking changes in '$FILENAME' from commit '$FILE_COMMIT' to branch '$BRANCH'"
    git checkout $BRANCH
    git cherry-pick $FILE_COMMIT
    if [ $? -ne 0 ]; then
      if git status | grep -q "The previous cherry-pick is now empty"; then
        echo "No changes to apply. Skipping cherry-pick for branch '$BRANCH'. Otherwise, please use 'git cherry-pick --skip' if the merge makes no sense."
        git cherry-pick --skip
      else
        echo "Error: Cherry-pick failed for branch '$BRANCH'. Aborting."
        git cherry-pick --abort
        exit 1
      fi
    fi
        echo "Pushing changes to 'origin/$BRANCH'"
    git push origin $BRANCH
    CURRENT_BRANCH=$BRANCH
  fi
done

# Finally, cherry-pick to the main branch
echo "Pulling latest changes from 'origin/main'"
git checkout main
git pull origin main

echo "Cherry-picking changes in '$FILENAME' to 'main' branch"
git cherry-pick $FILE_COMMIT
if [ $? -ne 0 ]; then
  if git status | grep -q "The previous cherry-pick is now empty"; then
    echo "No changes to apply. Skipping cherry-pick for 'main' branch. Otherwise, please use 'git cherry-pick --skip' if the merge makes no sense."
    git cherry-pick --skip
  else
    echo "Error: Cherry-pick failed for 'main' branch. Aborting."
    git cherry-pick --abort
    exit 1
  fi
fi

echo "Pushing changes to 'origin/main'"
git push origin main

echo "Merge completed successfully!"
