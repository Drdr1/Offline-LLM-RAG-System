#!/bin/bash

# Offline LLM System - Installation Script (Open WebUI Version)
# Run this on the target Ubuntu 24.04 system

set -e

echo "======================================"
echo "Offline LLM System - Installation"
echo "Open WebUI Version"
echo "======================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "Installing from: $SCRIPT_DIR"
echo ""

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    dpkg -i $SCRIPT_DIR/system-packages/*.deb || apt-get install -f -y
    systemctl start docker
    systemctl enable docker
    echo "✓ Docker installed"
else
    echo "✓ Docker already installed"
fi

# Add current user to docker group
CURRENT_USER=${SUDO_USER:-$USER}
usermod -aG docker $CURRENT_USER
echo "✓ Added $CURRENT_USER to docker group"

# Load Docker images
echo ""
echo "Loading Docker images..."
docker load -i $SCRIPT_DIR/docker-images/ollama.tar
docker load -i $SCRIPT_DIR/docker-images/open-webui.tar
echo "✓ Docker images loaded"

# Create installation directory
INSTALL_DIR="/opt/offline-llm"
echo ""
echo "Creating installation directory at $INSTALL_DIR..."
mkdir -p $INSTALL_DIR
cp $SCRIPT_DIR/docker-compose.yml $INSTALL_DIR/

# Copy Ollama models
echo ""
echo "Installing Ollama models..."
OLLAMA_DIR="/var/lib/ollama"
mkdir -p $OLLAMA_DIR
cp -r $SCRIPT_DIR/ollama-models/* $OLLAMA_DIR/
echo "✓ Ollama models installed"

# Create systemd service
echo ""
echo "Creating systemd service..."
cat > /etc/systemd/system/offline-llm.service << EOF
[Unit]
Description=Offline LLM RAG System with Open WebUI
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/docker-compose up -d
ExecStop=/usr/bin/docker-compose down
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable offline-llm.service
echo "✓ Systemd service created"

# Start the system
echo ""
echo "Starting Offline LLM system..."
cd $INSTALL_DIR
docker-compose up -d

echo ""
echo "Waiting for services to start..."
sleep 15

# Check if Ollama model is available
echo ""
echo "Verifying Ollama model..."
docker exec ollama ollama list

echo ""
echo "======================================"
echo "✓ Installation Complete!"
echo "======================================"
echo ""
echo "The system is now running!"
echo ""
echo "Access Open WebUI at: http://localhost:8080"
echo ""
echo "First time setup:"
echo "  1. Open http://localhost:8080 in your browser"
echo "  2. Create an account (first user becomes admin)"
echo "  3. Start chatting with LLaMA 3!"
echo "  4. Upload documents via the '+' button for RAG"
echo ""
echo "Useful commands:"
echo "  Start:   sudo systemctl start offline-llm"
echo "  Stop:    sudo systemctl stop offline-llm"
echo "  Status:  sudo docker-compose -f $INSTALL_DIR/docker-compose.yml ps"
echo "  Logs:    sudo docker-compose -f $INSTALL_DIR/docker-compose.yml logs -f"
echo ""
echo "Note: You may need to log out and back in for Docker"
echo "      group permissions to take effect."
echo ""
