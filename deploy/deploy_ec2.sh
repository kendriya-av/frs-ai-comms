#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Deploy FRS AI Comms to an EC2 instance (Amazon Linux 2023)
#
# Run this script ON the EC2 instance after SSH-ing in.
# The instance needs:
#   - IAM role with Comprehend + Bedrock permissions
#   - Python 3.11+
#   - Port 8050 open in security group (or use nginx reverse proxy)
#
# Usage (on EC2):
#   curl -O https://raw.githubusercontent.com/.../deploy_ec2.sh
#   chmod +x deploy_ec2.sh && ./deploy_ec2.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

APP_DIR="/opt/frs-ai-comms"
SERVICE_NAME="frs-ai-comms"
REPO_URL="${REPO_URL:-}"   # set this to your git repo URL if using git

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FRS AI Comms — EC2 Deployment"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Install system dependencies ───────────────────────────────────────────────
echo "▶ Installing system dependencies..."
sudo dnf update -y
sudo dnf install -y python3.11 python3.11-pip git nginx

# ── Set up app directory ──────────────────────────────────────────────────────
echo "▶ Setting up app directory..."
sudo mkdir -p "$APP_DIR"
sudo chown ec2-user:ec2-user "$APP_DIR"

# Copy app files (assumes you've uploaded them via scp or git clone)
if [ -n "$REPO_URL" ]; then
    git clone "$REPO_URL" "$APP_DIR" || git -C "$APP_DIR" pull
else
    echo "  No REPO_URL set — copy files manually to $APP_DIR"
fi

cd "$APP_DIR/frs_ai_comms"

# ── Python virtual environment ────────────────────────────────────────────────
echo "▶ Setting up Python environment..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# ── Environment file ──────────────────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ⚠ Edit $APP_DIR/frs_ai_comms/.env with your values before starting"
fi

# ── systemd service ───────────────────────────────────────────────────────────
echo "▶ Creating systemd service..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=FRS AI Communications System
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=${APP_DIR}/frs_ai_comms
EnvironmentFile=${APP_DIR}/frs_ai_comms/.env
ExecStart=${APP_DIR}/frs_ai_comms/venv/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl start "$SERVICE_NAME"
echo "  ✓ Service started"

# ── nginx reverse proxy (serves on port 80) ───────────────────────────────────
echo "▶ Configuring nginx..."
sudo tee /etc/nginx/conf.d/frs-ai-comms.conf > /dev/null <<'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass         http://127.0.0.1:8050;
        proxy_http_version 1.1;
        proxy_set_header   Upgrade $http_upgrade;
        proxy_set_header   Connection "upgrade";
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_read_timeout 300s;
    }
}
EOF

sudo systemctl enable nginx
sudo systemctl restart nginx
echo "  ✓ nginx configured"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Deployment complete!"
echo "  App running at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "  Useful commands:"
echo "    sudo systemctl status $SERVICE_NAME   # check status"
echo "    sudo journalctl -u $SERVICE_NAME -f   # tail logs"
echo "    sudo systemctl restart $SERVICE_NAME  # restart"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
