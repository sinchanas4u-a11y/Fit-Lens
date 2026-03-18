# .gitignore Files Guide

## Overview

I've created comprehensive .gitignore files for the project to prevent unnecessary files from being tracked in Git.

## Files Created

### 1. Root `.gitignore`
**Location:** Project root

**Purpose:** Covers the entire project

**Ignores:**
- Python files (`__pycache__`, `*.pyc`, etc.)
- Node.js files (`node_modules/`, etc.)
- Virtual environments (`venv/`, `venv311/`, etc.)
- Build outputs (`dist/`, `build/`)
- IDE files (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Environment variables (`.env`, `.env.local`)
- Logs (`*.log`)
- Temporary files (`*.tmp`, `*.temp`)
- Output directories (`output/`, `uploads/`)
- Model weights (optional - commented out)

### 2. Backend `.gitignore`
**Location:** `backend/.gitignore`

**Purpose:** Python/Flask specific ignores

**Ignores:**
- Python bytecode and cache
- Virtual environments
- Flask instance files
- Testing artifacts
- Database files
- Model files (optional)
- Output directories
- YOLOv8 cache

### 3. Frontend Vite `.gitignore`
**Location:** `frontend-vite/.gitignore`

**Purpose:** Vite/React specific ignores

**Ignores:**
- `node_modules/`
- Build outputs (`dist/`, `build/`)
- Environment files
- Editor configs
- Logs
- Cache files
- Vite specific files

### 4. Frontend CRA `.gitignore`
**Location:** `frontend/.gitignore`

**Purpose:** Create React App specific ignores

**Ignores:**
- `node_modules/`
- Build outputs
- Environment files
- Testing coverage
- Logs

## What Gets Tracked

### ✅ Should be tracked:
- Source code (`.py`, `.js`, `.jsx`, `.css`)
- Configuration files (`package.json`, `requirements.txt`, `vite.config.js`)
- Documentation (`.md` files)
- Batch scripts (`.bat` files)
- Static assets (images, icons)
- README files

### ❌ Should NOT be tracked:
- Dependencies (`node_modules/`, `venv/`)
- Build outputs (`dist/`, `build/`)
- Environment variables (`.env`)
- IDE settings (`.vscode/`, `.idea/`)
- OS files (`.DS_Store`, `Thumbs.db`)
- Logs (`*.log`)
- Cache files
- Temporary files
- User-specific files

## Model Files

By default, model weight files are tracked. If you want to ignore them (recommended for large models):

**Uncomment these lines in root `.gitignore`:**
```gitignore
# *.pt
# *.pth
# *.h5
# *.pkl
# *.onnx
```

Remove the `#` to activate:
```gitignore
*.pt
*.pth
*.h5
*.pkl
*.onnx
```

## Environment Variables

### Never commit:
- `.env`
- `.env.local`
- `.env.development.local`
- `.env.production.local`

### Instead, create:
- `.env.example` (template with dummy values)

**Example `.env.example`:**
```
# Backend
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Frontend
VITE_API_URL=http://localhost:5000
```

## Checking What's Ignored

### See ignored files:
```bash
git status --ignored
```

### Check if a file is ignored:
```bash
git check-ignore -v filename
```

### List all ignored files:
```bash
git ls-files --others --ignored --exclude-standard
```

## Common Issues

### Issue 1: File already tracked

If a file is already tracked by Git, adding it to `.gitignore` won't remove it.

**Solution:**
```bash
# Remove from Git but keep locally
git rm --cached filename

# Or for a directory
git rm -r --cached directory/

# Then commit
git commit -m "Remove tracked files that should be ignored"
```

### Issue 2: node_modules still showing

**Solution:**
```bash
# Remove from Git
git rm -r --cached node_modules/

# Commit
git commit -m "Remove node_modules from tracking"
```

### Issue 3: .env file committed

**Solution:**
```bash
# Remove from Git
git rm --cached .env

# Commit
git commit -m "Remove .env from tracking"

# Make sure .env is in .gitignore
echo ".env" >> .gitignore
```

## Best Practices

### 1. Check before committing
```bash
git status
```

### 2. Review what will be committed
```bash
git diff --cached
```

### 3. Use .gitignore early
Add `.gitignore` before making your first commit.

### 4. Keep it updated
Add new patterns as needed.

### 5. Use global .gitignore
For personal preferences (OS files, editor configs):

```bash
# Create global gitignore
git config --global core.excludesfile ~/.gitignore_global

# Add your preferences
echo ".DS_Store" >> ~/.gitignore_global
echo ".vscode/" >> ~/.gitignore_global
```

## Project-Specific Patterns

### Python/Backend
```gitignore
# Virtual environment
venv311/

# Output
output/

# YOLOv8 models
yolov8*.pt
runs/
```

### Frontend
```gitignore
# Dependencies
node_modules/

# Build
dist/
build/

# Environment
.env.local
```

## Cleaning Up

### Remove all ignored files (careful!):
```bash
# Dry run (see what would be deleted)
git clean -ndX

# Actually delete
git clean -fdX
```

### Remove untracked files:
```bash
# Dry run
git clean -nd

# Actually delete
git clean -fd
```

## Verification

After setting up .gitignore:

1. **Check status:**
   ```bash
   git status
   ```

2. **Should NOT see:**
   - `node_modules/`
   - `venv/` or `venv311/`
   - `__pycache__/`
   - `.env`
   - `dist/` or `build/`
   - `.DS_Store`

3. **Should see:**
   - Source files (`.py`, `.js`, `.jsx`)
   - Config files (`package.json`, `requirements.txt`)
   - Documentation (`.md`)

## Summary

✅ `.gitignore` files created for:
- Root directory (covers everything)
- Backend (Python/Flask specific)
- Frontend Vite (Vite/React specific)
- Frontend CRA (Create React App specific)

✅ Ignores:
- Dependencies
- Build outputs
- Environment variables
- IDE files
- OS files
- Logs and cache
- Temporary files

✅ Tracks:
- Source code
- Configuration
- Documentation
- Scripts

Your repository is now clean and ready for Git! 🎉

## Quick Commands

```bash
# Initialize Git (if not already)
git init

# Add all files (respecting .gitignore)
git add .

# Check what will be committed
git status

# Commit
git commit -m "Initial commit with proper .gitignore"

# Add remote (if needed)
git remote add origin <your-repo-url>

# Push
git push -u origin main
```
