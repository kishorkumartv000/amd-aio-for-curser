#!/bin/bash
# Development startup script for Project-Siesta

set -e

echo "🚀 Starting Project-Siesta Development Environment"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from sample..."
    cp sample.env .env
    echo "📝 Please edit .env file with your configuration before running the bot."
    exit 1
fi

# Make scripts executable
echo "🔧 Setting up permissions..."
chmod +x downloader/*.sh

# Run tests
echo "🧪 Running tests..."
python test_bot.py

if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    echo "🤖 Starting bot..."
    python -m bot
else
    echo "❌ Tests failed. Please fix issues before starting the bot."
    exit 1
fi