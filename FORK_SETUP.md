# Safe Fork Workflow Guide

## Current Situation

You have three repositories that are currently pointing directly to upstream:
- `espresso-profile-schema` → `MeticulousHome/espresso-profile-schema`
- `pyMeticulous` → `MeticulousHome/pyMeticulous`
- `python-sdk` → `modelcontextprotocol/python-sdk`

**Problem**: If you push with `git push`, you could accidentally push to upstream repositories!

## Solution: Safe Fork Setup

### Option 1: Use the Setup Script (Recommended)

Run the provided script to automatically configure all repos:

```bash
./setup_safe_forks.sh
```

This will:
1. Rename `origin` → `upstream` for each repo
2. Set push URL to `no_push_configured` (pushes will fail)
3. Allow you to add your fork as `origin` later

### Option 2: Manual Setup

For each repository, run:

```bash
cd REPO_NAME

# 1. Rename origin to upstream
git remote rename origin upstream

# 2. Prevent accidental pushes to upstream
git remote set-url --push upstream "no_push_configured"

# 3. Add your fork as origin (if you have one)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git remote set-url --push origin https://github.com/YOUR_USERNAME/REPO_NAME.git
```

### Workflow After Setup

**Fetching updates from upstream:**
```bash
git fetch upstream
git merge upstream/main  # or upstream/master
```

**Pushing to your fork:**
```bash
git push origin main  # or origin master
```

**Creating PRs:**
- Push to your fork (`origin`)
- Create PR from your fork to upstream on GitHub
- Never push directly to `upstream`

## Setup Your Own Repository (meticulous-mcp)

Your `meticulous-mcp` directory is not a git repository yet. Initialize it:

```bash
cd meticulous-mcp
git init
git add .
git commit -m "Initial commit"
git branch -M main

# Add your GitHub repo as origin
git remote add origin https://github.com/YOUR_USERNAME/meticulous-mcp.git
git push -u origin main
```

## Git Configuration Protection

You can also add these safety checks to your global git config:

```bash
# Prevent pushes to protected remotes
git config --global push.default simple
git config --global init.defaultBranch main

# Set up push protection (optional: uses a pre-push hook)
git config --global core.hooksPath ~/.git-hooks
```

## Verify Setup

Check remotes:
```bash
git remote -v
```

Should show:
- `upstream` → upstream repo (fetch only, push blocked)
- `origin` → your fork (fetch + push)

## Troubleshooting

**If you accidentally try to push to upstream:**
```bash
# Error will be: "fatal: remote 'upstream' does not support push"
# This is EXPECTED and PROTECTS you!
```

**To allow upstream push temporarily (not recommended):**
```bash
git remote set-url --push upstream REAL_UPSTREAM_URL
```

**To restore protection:**
```bash
git remote set-url --push upstream "no_push_configured"
```

