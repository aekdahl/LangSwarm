#!/bin/bash
# Publish LangSwarm or AgentMem - reads version from pyproject.toml
# Creates and pushes tag automatically with correct prefix

set -e

PACKAGE=$1

if [ -z "$PACKAGE" ]; then
    echo "Usage: $0 [langswarm|agentmem]"
    echo ""
    echo "Examples:"
    echo "  $0 langswarm   # Publish langswarm"
    echo "  $0 agentmem    # Publish agentmem"
    exit 1
fi

case $PACKAGE in
    langswarm)
        # Get version from root pyproject.toml
        VERSION=$(grep -m 1 '^version = ' pyproject.toml | cut -d'"' -f2)
        TAG="langswarm-v${VERSION}"
        FILE="pyproject.toml"
        ;;
    
    agentmem)
        # Get version from agentmem/pyproject.toml
        VERSION=$(grep -m 1 '^version = ' agentmem/pyproject.toml | cut -d'"' -f2)
        TAG="agentmem-v${VERSION}"
        FILE="agentmem/pyproject.toml"
        ;;
    
    *)
        echo "❌ Unknown package: $PACKAGE"
        echo "   Must be 'langswarm' or 'agentmem'"
        exit 1
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📦 Package:  $PACKAGE"
echo "🔢 Version:  $VERSION"
echo "🏷️  Tag:     $TAG"
echo "📄 Source:   $FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "⚠️  Warning: Tag $TAG already exists!"
    echo ""
    read -p "Delete and recreate? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git tag -d "$TAG"
        git push origin ":refs/tags/$TAG" 2>/dev/null || true
        echo "✅ Deleted old tag"
    else
        echo "❌ Cancelled"
        exit 1
    fi
fi

# Create and push tag
echo "Creating tag..."
git tag "$TAG"

echo "Pushing tag to origin..."
git push origin "$TAG"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Tag created and pushed: $TAG"
echo ""
echo "🚀 GitHub Actions will now:"
echo "   1. Build the package"
echo "   2. Publish to PyPI"
echo "   3. Available as: pip install $PACKAGE==$VERSION"
echo ""
echo "📊 Monitor progress:"
echo "   https://github.com/aekdahl/langswarm/actions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

