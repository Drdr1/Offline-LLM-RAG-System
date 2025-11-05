#!/bin/bash

# Offline LLM System Setup Script (Open WebUI Version)
# This script prepares all necessary files for USB installation

set -e

echo "======================================"
echo "Offline LLM System - Setup Script"
echo "Open WebUI Version"
echo "======================================"
echo ""

# Create directory structure
echo "Creating directory structure..."
mkdir -p usb-package/{docker-images,ollama-models,system-packages}

# Pull and export Ollama image
echo ""
echo "Pulling Ollama image..."
docker pull ollama/ollama:latest
echo "Exporting Ollama image..."
docker save ollama/ollama:latest -o usb-package/docker-images/ollama.tar
echo "✓ Ollama image exported"

# Pull and export Open WebUI image
echo ""
echo "Pulling Open WebUI image..."
docker pull ghcr.io/open-webui/open-webui:main
echo "Exporting Open WebUI image..."
docker save ghcr.io/open-webui/open-webui:main -o usb-package/docker-images/open-webui.tar
echo "✓ Open WebUI image exported"

# Download Ollama model
echo ""
echo "Downloading LLaMA model (this will take several GB and time)..."
docker run --rm -v $(pwd)/usb-package/ollama-models:/root/.ollama ollama/ollama:latest \
    ollama pull llama3:latest
echo "✓ LLaMA model downloaded"

# Download system packages
echo ""
echo "Downloading system packages..."
cd usb-package/system-packages
apt-get download docker.io docker-compose 2>/dev/null || echo "Note: Run with sudo if package download fails"
cd ../..
echo "✓ System packages downloaded"

# Copy project files
echo ""
echo "Copying project files..."
cp docker-compose.yml usb-package/
cp install.sh usb-package/
chmod +x usb-package/install.sh
echo "✓ Project files copied"

# Create README
cat > usb-package/README.txt << 'EOF'
OFFLINE LLM SYSTEM - USB PACKAGE (Open WebUI)
==============================================

This package contains everything needed to install and run
the offline LLM RAG system with Open WebUI on Ubuntu 24.04.

Contents:
- docker-images/     : Pre-built Docker images (Ollama + Open WebUI)
- ollama-models/     : Pre-downloaded LLaMA model
- system-packages/   : Ubuntu packages for Docker
- docker-compose.yml : Docker orchestration config
- install.sh         : Installation script

Features:
- Professional ChatGPT-like interface
- Built-in document upload and RAG
- Chat history and conversations
- User management
- Dark/light themes

Installation:
1. Boot Ubuntu 24.04
2. Copy this entire folder to the system
3. Run: sudo ./install.sh
4. Access at: http://localhost:8080

First time:
- Create an account (first user is admin)
- Upload documents via the interface
- Chat with your documents!

For detailed instructions, see INSTALLATION.md
EOF

echo ""
echo "======================================"
echo "✓ Setup complete!"
echo "======================================"
echo ""
echo "USB package created at: ./usb-package/"
echo "Total size:"
du -sh usb-package/
echo ""
echo "Contents:"
echo "  - Ollama image + LLaMA 3 model"
echo "  - Open WebUI image (professional UI)"
echo "  - System packages"
echo "  - Configuration files"
echo ""
echo "Next steps:"
echo "1. Copy the 'usb-package' folder to your USB drive"
echo "2. Boot the target system with Ubuntu 24.04"
echo "3. Run the install.sh script from the USB"
echo "4. Access Open WebUI at http://localhost:8080"
echo ""
