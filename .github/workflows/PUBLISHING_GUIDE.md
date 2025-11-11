# 🚀 Publishing Guide for LangSwarm & AgentMem

This repository contains **two packages** that can be published independently to PyPI:
- **AgentMem**: Memory system for AI agents
- **LangSwarm**: Multi-agent orchestration framework

## 📦 Package Publishing Workflows

### 1. AgentMem Publishing
**Workflow**: `.github/workflows/publish_agentmem.yml`  
**Trigger**: Tags matching `agentmem-v*.*.*`

```bash
# Tag format
agentmem-v0.1.0
agentmem-v0.1.1
agentmem-v0.2.0
```

### 2. LangSwarm Publishing
**Workflow**: `.github/workflows/publish_langswarm.yml`  
**Trigger**: Tags matching `langswarm-v*.*.*`

```bash
# Tag format
langswarm-v0.0.54.dev46
langswarm-v0.1.0
langswarm-v1.0.0
```

## 🎯 Publishing Scenarios

### Scenario 1: Publish AgentMem Only

```bash
cd agentmem

# 1. Update version in pyproject.toml
# version = "0.1.0"  → "0.1.1"

# 2. Commit changes
git add pyproject.toml
git commit -m "Bump agentmem to v0.1.1"
git push

# 3. Create and push tag
git tag agentmem-v0.1.1
git push origin agentmem-v0.1.1

# ✅ Workflow triggers automatically!
```

### Scenario 2: Publish LangSwarm Only

```bash
# 1. Update version in pyproject.toml
poetry version 0.0.55

# 2. Commit changes
git add pyproject.toml
git commit -m "Bump langswarm to v0.0.55"
git push

# 3. Create and push tag
git tag langswarm-v0.0.55
git push origin langswarm-v0.0.55

# ✅ Workflow triggers automatically!
```

### Scenario 3: Publish Both (AgentMem First, Then LangSwarm)

**Important**: Always publish AgentMem first if LangSwarm depends on a new AgentMem version!

```bash
# Step 1: Publish AgentMem
cd agentmem
# Update version, commit, tag, push (as in Scenario 1)
git tag agentmem-v0.2.0
git push origin agentmem-v0.2.0

# Step 2: Wait for AgentMem to be published (~2-5 minutes)
# Check: https://pypi.org/project/agentmem/

# Step 3: Update LangSwarm dependency
cd ..
# Edit pyproject.toml: agentmem = "^0.2.0"
poetry version 0.1.0
git add pyproject.toml
git commit -m "Update agentmem dep to v0.2.0, bump to v0.1.0"
git push

# Step 4: Publish LangSwarm
git tag langswarm-v0.1.0
git push origin langswarm-v0.1.0

# ✅ Both packages published!
```

## ✅ Pre-Publishing Checklist

### For AgentMem
- [ ] Version updated in `agentmem/pyproject.toml`
- [ ] Tests passing
- [ ] README updated
- [ ] CHANGELOG updated
- [ ] Tag matches version (e.g., `agentmem-v0.1.0`)

### For LangSwarm
- [ ] Version updated in `pyproject.toml` (use `poetry version X.Y.Z`)
- [ ] AgentMem dependency is NOT a local path (must be `agentmem = "^0.1.0"`)
- [ ] Tests passing
- [ ] README updated
- [ ] Release notes created in `docs/releases/`
- [ ] Tag matches version (e.g., `langswarm-v0.0.54.dev46`)

## 🔍 Version Verification

Both workflows **verify** that the tag matches the version in `pyproject.toml`:

```bash
# AgentMem
Tag:         agentmem-v0.1.0
pyproject:   version = "0.1.0"
✅ Match!

# LangSwarm
Tag:         langswarm-v0.0.55
pyproject:   version = "0.0.55"
✅ Match!
```

If they don't match, the workflow **fails** with a clear error message.

## 🚨 Common Issues

### Issue 1: Local Path Dependency

**Error**: `Can't have direct dependency: agentmem@ file:///...`

**Fix**: Update `pyproject.toml` line 16:
```toml
# ❌ Wrong (local path)
agentmem = {path = "./agentmem", develop = true}

# ✅ Correct (PyPI version)
agentmem = "^0.1.0"
```

### Issue 2: Version Mismatch

**Error**: `Version mismatch! Tag: v0.1.0, pyproject: 0.0.55`

**Fix**: 
```bash
# Update version
poetry version 0.1.0

# Recreate tag
git tag -d langswarm-v0.1.0
git push origin :refs/tags/langswarm-v0.1.0
git tag langswarm-v0.1.0
git push origin langswarm-v0.1.0
```

### Issue 3: Package Already Exists

**Error**: `File already exists`

**Fix**: You can't overwrite existing PyPI versions. Bump the version:
```bash
poetry version patch  # 0.0.54 → 0.0.55
```

## 📊 Workflow Status

Check workflow runs:
- **AgentMem**: https://github.com/aekdahl/langswarm/actions/workflows/publish_agentmem.yml
- **LangSwarm**: https://github.com/aekdahl/langswarm/actions/workflows/publish_langswarm.yml

## 🔐 Required Secrets

Both workflows need:
- `PYPI_API_TOKEN` - PyPI API token with upload permissions

Set in: **Settings** → **Secrets and variables** → **Actions** → **Repository secrets**

## 📝 Quick Reference

```bash
# Publish AgentMem
git tag agentmem-v0.1.0 && git push origin agentmem-v0.1.0

# Publish LangSwarm
git tag langswarm-v0.0.55 && git push origin langswarm-v0.0.55

# List tags
git tag -l 'agentmem-v*'
git tag -l 'langswarm-v*'

# Delete tag (if mistake)
git tag -d agentmem-v0.1.0
git push origin :refs/tags/agentmem-v0.1.0
```

## 🎉 Success!

After successful publishing:

**AgentMem**: https://pypi.org/project/agentmem/  
**LangSwarm**: https://pypi.org/project/langswarm/

Users can install:
```bash
pip install agentmem
pip install langswarm  # Automatically installs agentmem
```

---

**Last Updated**: 2025-11-11  
**LangSwarm Version**: v0.0.54.dev46  
**AgentMem Version**: v0.1.0

