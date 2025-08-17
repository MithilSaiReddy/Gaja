#!/bin/bash
set -e

APP_NAME="C2C_AE_Renderer"
SCRIPT="ae.py"

echo "🚀 Starting build for $APP_NAME"

# 1. Check for Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found. Please install Python3 first."
    exit 1
fi

# 2. Create venv
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# 3. Upgrade pip & install pyinstaller
pip install --upgrade pip
pip install pyinstaller

# 4. Clean old builds
rm -rf build dist

# 5. Run PyInstaller
echo "🔨 Building executable..."
pyinstaller --onefile --windowed --name "$APP_NAME" "$SCRIPT"

# 6. Copy config.json
cp config.json dist/

# 7. Deactivate venv
deactivate

echo "✅ Build complete!"
echo "Output: dist/$APP_NAME (binary) and dist/$APP_NAME.app (macOS bundle)"
