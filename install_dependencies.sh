#!/bin/bash

echo "🔧 Installing WeChat Crawler Dependencies"

# Activate virtual environment
if [ -f ".venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source .venv/bin/activate
else
    echo "❌ Virtual environment not found. Creating new one..."
    python3 -m venv .venv
    source .venv/bin/activate
fi

# Install Python dependencies
echo "📥 Installing Python packages..."
pip install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Install Playwright system dependencies
echo "🔧 Installing Playwright system dependencies..."
playwright install-deps

echo "✅ Installation complete!"
echo ""
echo "To activate the environment manually:"
echo "source .venv/bin/activate"
echo ""
echo "To test the installation:"
echo "python main.py stats"