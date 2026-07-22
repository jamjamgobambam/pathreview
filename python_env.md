## python env setup
python3 -m venv venv
source venv/bin/activate
deactivate

## check env
git ls-files .env
git rm --cached .env

## git ignore

# Virtual environments
.venv/
venv/
ENV/
env/
.env
.env.local
.env.*.local

# Python cache files
__pycache__/
*.pyc
*.py[cod]
*$py.class
*.so
*.egg-info/
dist/
build/
.eggs/
.venv/
venv/
*.egg

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Node
node_modules/
frontend/node_modules/
frontend/dist/

# Docker
*.log

# OS
.DS_Store
Thumbs.db

# Test / Coverage
htmlcov/
.coverage
.coverage.*
.pytest_cache/
.mypy_cache/

# Build artifacts
*.pyc

