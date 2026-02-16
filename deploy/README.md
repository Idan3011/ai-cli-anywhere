# Deployment

## systemd (Linux server / Oracle Cloud VM)

```bash
# 1. Copy the service file (replace 'youruser' with your Linux username)
sudo cp deploy/ai-cli-anywhere.service /etc/systemd/system/ai-cli-anywhere@youruser.service

# 2. Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable ai-cli-anywhere@youruser
sudo systemctl start  ai-cli-anywhere@youruser

# 3. Check status and logs
sudo systemctl status ai-cli-anywhere@youruser
journalctl -u ai-cli-anywhere@youruser -f
```

The `%i` template means you can run the bot as any user without editing the file.

## Docker Compose

```bash
# 1. Make sure .env is filled in
cp .env.example .env && nano .env

# 2. Build and start
docker compose up -d

# 3. Logs
docker compose logs -f
```

> **Note:** Claude CLI and Cursor inside Docker require additional setup to authenticate.
> For most users, running natively (systemd) is simpler.
