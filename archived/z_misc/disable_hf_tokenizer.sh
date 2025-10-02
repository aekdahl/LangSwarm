#!/bin/bash
# Disable HuggingFace Tokenizer Loading
# =====================================
# 
# This script sets the environment variable to disable HuggingFace tokenizer loading,
# which prevents rate limiting issues when HuggingFace Hub is experiencing high traffic.

echo "🚫 Disabling HuggingFace tokenizer loading..."
export LANGSWARM_DISABLE_HF_TOKENIZER=true

echo "✅ Environment variable set:"
echo "   LANGSWARM_DISABLE_HF_TOKENIZER=$LANGSWARM_DISABLE_HF_TOKENIZER"
echo ""
echo "🔄 LangSwarm will now use tiktoken fallback for all tokenization"
echo "💡 To make this permanent, add the following to your shell profile:"
echo "   echo 'export LANGSWARM_DISABLE_HF_TOKENIZER=true' >> ~/.bashrc"
echo "   # or for zsh:"
echo "   echo 'export LANGSWARM_DISABLE_HF_TOKENIZER=true' >> ~/.zshrc"
echo ""
echo "🎯 Run your LangSwarm application now to avoid HuggingFace rate limits!"
