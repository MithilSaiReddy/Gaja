#!/bin/bash
set -e

APP_NAME="C2C_AE_Renderer"

echo "🗑 Uninstalling $APP_NAME ..."

# macOS app bundle
if [ -d "/Applications/$APP_NAME.app" ]; then
    echo "Removing /Applications/$APP_NAME.app"
    rm -rf "/Applications/$APP_NAME.app"
fi

# Config file (if user wants)
if [ -f "/Applications/config.json" ]; then
    echo "Removing config.json"
    rm -f "/Applications/config.json"
fi

# Clean PyInstaller dist leftovers
if [ -d "dist" ]; then
    echo "Removing dist folder"
    rm -rf dist
fi

if [ -d "build" ]; then
    echo "Removing build folder"
    rm -rf build
fi

if [ -d "venv" ]; then
    echo "Removing venv"
    rm -rf venv
fi

echo "✅ $APP_NAME uninstalled successfully!"
