# 🚀 Quick Publishing Guide

## Single Source of Truth

Version is maintained **once** in `pyproject.toml`, tag prefix is documented in a comment:

```toml
# LangSwarm (root pyproject.toml)
[tool.poetry]
version = "0.0.54.dev46"  # ← Update this
# Tag format: langswarm-v{version}  # ← Tag prefix documented here

# AgentMem (agentmem/pyproject.toml)
[project]
version = "0.1.0"  # ← Update this
# Tag format: agentmem-v{version}  # ← Tag prefix documented here
```

## 📝 Publishing Workflow

### 1. Update Version

```bash
# LangSwarm
poetry version 0.0.55
# Updates pyproject.toml → version = "0.0.55"

# AgentMem
cd agentmem
# Edit pyproject.toml manually: version = "0.1.1"
```

### 2. Commit Changes

```bash
git add pyproject.toml  # or agentmem/pyproject.toml
git commit -m "Bump to v0.0.55"
git push
```

### 3. Publish (Auto-Tags!)

```bash
# Use the helper script - it reads version and creates tag automatically!
./scripts/publish.sh langswarm
# OR
./scripts/publish.sh agentmem
```

The script:
- ✅ Reads version from `pyproject.toml`
- ✅ Creates tag with correct prefix (`langswarm-v` or `agentmem-v`)
- ✅ Pushes tag
- ✅ Triggers GitHub Actions
- ✅ Publishes to PyPI automatically

## 🎯 Example

```bash
# 1. Bump version
poetry version 0.0.55

# 2. Commit
git commit -am "Bump to v0.0.55"
git push

# 3. Publish (one command!)
./scripts/publish.sh langswarm

# Script output:
# 📦 Package:  langswarm
# 🔢 Version:  0.0.55
# 🏷️  Tag:     langswarm-v0.0.55  ← Auto-generated from pyproject.toml!
# ✅ Tag created and pushed
# 🚀 GitHub Actions publishing...
```

## 📦 Publish Both Packages

```bash
# 1. Publish AgentMem first (if it has changes)
./scripts/publish.sh agentmem

# 2. Wait for it to appear on PyPI (~2-5 min)

# 3. Publish LangSwarm
./scripts/publish.sh langswarm
```

## ✅ Benefits

- **Single source**: Only update version in `pyproject.toml`
- **No duplication**: Tag prefix in comment for reference
- **No mistakes**: Script ensures tag matches version
- **Simple**: One command to publish
- **Safe**: Warns if tag already exists

## 🔍 Manual Tags (Alternative)

If you prefer to create tags manually:

```bash
# LangSwarm
VERSION=$(poetry version -s)
git tag langswarm-v$VERSION
git push origin langswarm-v$VERSION

# AgentMem
VERSION=$(grep -m 1 '^version = ' agentmem/pyproject.toml | cut -d'"' -f2)
git tag agentmem-v$VERSION
git push origin agentmem-v$VERSION
```

## 📊 Check Status

After tagging:
- **GitHub Actions**: https://github.com/aekdahl/langswarm/actions
- **PyPI LangSwarm**: https://pypi.org/project/langswarm/
- **PyPI AgentMem**: https://pypi.org/project/agentmem/

---

**Quick Reference**:
```bash
./scripts/publish.sh langswarm   # Publish LangSwarm
./scripts/publish.sh agentmem    # Publish AgentMem
```

