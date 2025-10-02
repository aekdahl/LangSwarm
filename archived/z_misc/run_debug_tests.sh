#!/bin/bash
# Quick script to set API key and run LangSwarm debug tests

echo "🎯 LangSwarm Debug Test Runner"
echo "============================="

# Check if API key is already set
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✅ OPENAI_API_KEY is already set"
    echo "   Key ends with: ...${OPENAI_API_KEY: -8}"
else
    echo "❌ OPENAI_API_KEY is not set"
    echo ""
    echo "🔑 Please enter your OpenAI API key:"
    echo "   (Find it at: https://platform.openai.com/api-keys)"
    read -s -p "API Key: " OPENAI_API_KEY
    echo ""
    
    if [ -z "$OPENAI_API_KEY" ]; then
        echo "❌ No API key provided. Exiting."
        exit 1
    fi
    
    export OPENAI_API_KEY
    echo "✅ API key set for this session"
fi

echo ""
echo "🧪 Choose test to run:"
echo "1. Run Case 1 only (Simple Agent)"
echo "2. Run all basic cases (1, 2, 3)"
echo "3. Analyze existing trace files"
echo "4. Show detailed trace view"

read -p "Choice (1-4): " choice

case $choice in
    1)
        echo "🚀 Running Case 1: Simple Agent"
        python -m langswarm.core.debug.cli run-case-1
        ;;
    2)
        echo "🚀 Running all basic test cases"
        python -m langswarm.core.debug.cli run-all-basic
        ;;
    3)
        echo "📊 Analyzing trace files..."
        for file in debug_traces/*.jsonl; do
            if [ -f "$file" ]; then
                echo "Analyzing: $file"
                python -m langswarm.core.debug.cli analyze "$file"
                echo ""
            fi
        done
        ;;
    4)
        echo "📋 Available trace files:"
        ls -la debug_traces/*.jsonl 2>/dev/null || echo "No trace files found"
        echo ""
        read -p "Enter trace file name: " tracefile
        if [ -f "$tracefile" ]; then
            python -m langswarm.core.debug.cli detail "$tracefile"
        else
            echo "❌ File not found: $tracefile"
        fi
        ;;
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "🎉 Test completed!"
echo "💡 Your API key is set for this terminal session."
echo "💡 Run this script again anytime: ./run_debug_tests.sh"
