#!/bin/bash
# Install LangSwarm in sibling project for testing

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  LangSwarm Local Installation Helper${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get the sibling project directory
if [ -z "$1" ]; then
    echo "Usage: $0 <sibling-project-name> [mode]"
    echo ""
    echo "Modes:"
    echo "  editable  - Install in editable mode (default, best for development)"
    echo "  regular   - Regular installation"
    echo "  wheel     - Build wheel and install (closest to PyPI)"
    echo ""
    echo "Examples:"
    echo "  $0 MyProject"
    echo "  $0 MyProject editable"
    echo "  $0 MyProject wheel"
    exit 1
fi

PROJECT_NAME=$1
MODE=${2:-editable}
LANGSWARM_DIR="/Users/alexanderekdahl/Docker/LangSwarm"
SIBLING_DIR="/Users/alexanderekdahl/Docker/$PROJECT_NAME"

# Check if sibling project exists
if [ ! -d "$SIBLING_DIR" ]; then
    echo "❌ Error: Project directory not found: $SIBLING_DIR"
    exit 1
fi

echo "📦 LangSwarm: $LANGSWARM_DIR"
echo "🎯 Target Project: $SIBLING_DIR"
echo "🔧 Mode: $MODE"
echo ""

# Check for virtual environment
if [ -d "$SIBLING_DIR/venv" ]; then
    VENV="$SIBLING_DIR/venv/bin/activate"
    echo "✅ Found venv at $SIBLING_DIR/venv"
elif [ -d "$SIBLING_DIR/.venv" ]; then
    VENV="$SIBLING_DIR/.venv/bin/activate"
    echo "✅ Found venv at $SIBLING_DIR/.venv"
elif [ -d "$SIBLING_DIR/env" ]; then
    VENV="$SIBLING_DIR/env/bin/activate"
    echo "✅ Found venv at $SIBLING_DIR/env"
else
    echo "⚠️  Warning: No virtual environment found in $SIBLING_DIR"
    echo "   Looking for: venv/, .venv/, or env/"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    VENV=""
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Perform installation
case $MODE in
    editable)
        echo "🔧 Installing in EDITABLE mode..."
        echo "   (Changes to LangSwarm will be immediately reflected)"
        echo ""
        if [ -n "$VENV" ]; then
            source "$VENV"
        fi
        pip uninstall -y langswarm 2>/dev/null || true
        pip install -e "$LANGSWARM_DIR"
        ;;
    
    regular)
        echo "📦 Installing in REGULAR mode..."
        echo "   (Fixed snapshot, reinstall after changes)"
        echo ""
        if [ -n "$VENV" ]; then
            source "$VENV"
        fi
        pip uninstall -y langswarm 2>/dev/null || true
        pip install "$LANGSWARM_DIR"
        ;;
    
    wheel)
        echo "🏗️  Building wheel and installing..."
        echo "   (Closest to PyPI experience)"
        echo ""
        cd "$LANGSWARM_DIR"
        python -m build
        WHEEL=$(ls -t dist/*.whl | head -1)
        echo "   Built: $WHEEL"
        echo ""
        if [ -n "$VENV" ]; then
            source "$VENV"
        fi
        pip uninstall -y langswarm 2>/dev/null || true
        pip install "$WHEEL"
        ;;
    
    *)
        echo "❌ Unknown mode: $MODE"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Installation complete!"
echo ""
echo "Test it:"
echo "  cd $SIBLING_DIR"
if [ -n "$VENV" ]; then
    echo "  source ${VENV##*/}"
fi
echo "  python -c 'import langswarm; print(langswarm.__version__)'"
echo "  python -c 'from langswarm.core.planning import Coordinator; print(\"✅ V2 works!\")'"
echo "  python -c 'from langswarm.v1.core.config import LangSwarmConfigLoader; print(\"✅ V1 works!\")'"
echo ""

