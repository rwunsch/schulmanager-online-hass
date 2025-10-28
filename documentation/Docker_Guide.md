# Docker Guide for Schulmanager Online Integration

## Overview

This guide explains how to use Docker for developing and testing the Schulmanager Online Home Assistant integration.

## Docker Setup

### Current Configuration

The project uses a Docker Compose configuration for Home Assistant:

```yaml
# test-scripts/docker-compose.yml
version: '3.8'
services:
  homeassistant:
    container_name: schulmanager-ha-test
    image: homeassistant/home-assistant:latest
    volumes:
      - ../custom_components:/config/custom_components
      - ./ha-config:/config
    ports:
      - "8123:8123"
    environment:
      - TZ=Europe/Berlin
    restart: unless-stopped
```

### Important Paths

- **Custom Components**: `../custom_components` → `/config/custom_components`
- **HA Config**: `./ha-config` → `/config`
- **Web Interface**: `http://localhost:8123`

## Docker Commands

### 1. Start Container

```bash
# From the test-scripts directory
cd test-scripts
docker compose up -d

# Or with explicit DOCKER_HOST (if needed)
export DOCKER_HOST="unix:///var/run/docker.sock"
docker compose up -d
```

### 2. Restart Container

```bash
# Quick restart (keeps image)
export DOCKER_HOST="unix:///var/run/docker.sock"
docker restart schulmanager-ha-test

# Or with docker compose
cd test-scripts
docker compose restart
```

### 3. Stop Container

```bash
# Stop container
docker stop schulmanager-ha-test

# Or with docker compose
cd test-scripts
docker compose down
```

### 4. Rebuild Container (for image updates)

```bash
cd test-scripts

# Pull new image
docker compose pull

# Recreate container
docker compose up -d --force-recreate
```

### 5. View Logs

```bash
# Current logs
export DOCKER_HOST="unix:///var/run/docker.sock"
docker logs schulmanager-ha-test

# Follow live logs
docker logs -f schulmanager-ha-test

# Only last 50 lines
docker logs schulmanager-ha-test --tail 50

# Filter logs for Schulmanager
docker logs schulmanager-ha-test | grep -i schulmanager
```

## Development Workflow

### 1. Code Changes

When making changes to the integration:

1. **Python files** (`.py`): Home Assistant automatically reloads these
2. **JavaScript files** (Custom Card): Requires browser refresh
3. **Configuration files**: Requires HA restart

### 2. Reload Integration

```bash
# Only reload integration (fast)
# Via HA UI: Settings → Devices & Services → Schulmanager Online → Reload

# Or complete HA restart
export DOCKER_HOST="unix:///var/run/docker.sock"
docker restart schulmanager-ha-test
```

### 3. Custom Card Updates

After changes to the custom card:

1. Restart container (copies card again)
2. Clear browser cache (`Ctrl+F5`)
3. Reload Lovelace dashboard

## Debugging

### 1. Check Container Status

```bash
# Container status
docker ps | grep schulmanager

# Container details
docker inspect schulmanager-ha-test
```

### 2. Enter Container

```bash
# Shell in container
docker exec -it schulmanager-ha-test /bin/bash

# Check files in container
docker exec schulmanager-ha-test ls -la /config/custom_components/schulmanager_online/
```

### 3. Analyze Logs

```bash
# Find errors
docker logs schulmanager-ha-test 2>&1 | grep -i error

# Schulmanager-specific logs
docker logs schulmanager-ha-test 2>&1 | grep -i schulmanager

# Track API calls
docker logs schulmanager-ha-test 2>&1 | grep -E "(API|400|401|500)"
```

### 4. Custom Card Debug

```bash
# Check if card was copied
docker exec schulmanager-ha-test ls -la /config/www/schulmanager-schedule-card.js

# Card registration in logs
docker logs schulmanager-ha-test 2>&1 | grep -i "custom cards"
```

## Common Problems

### 1. "Custom element doesn't exist"

**Problem**: Custom card not found

**Solution**:
```bash
# Restart container (copies card again)
docker restart schulmanager-ha-test

# Clear browser cache
# Then: Ctrl+F5 in browser
```

### 2. "Permission denied" errors

**Problem**: Docker socket permission

**Solution**:
```bash
# Check docker socket permission
ls -la /var/run/docker.sock

# Add user to docker group
sudo usermod -aG docker $USER

# Re-login or:
newgrp docker
```

### 3. Port 8123 already in use

**Problem**: Port conflict

**Solution**:
```bash
# Check what's using port 8123
sudo netstat -tlnp | grep :8123

# Use different port (change docker-compose.yml)
ports:
  - "8124:8123"  # Instead of 8123:8123
```

### 4. Integration doesn't load

**Problem**: Python errors in integration

**Solution**:
```bash
# Find syntax errors
docker logs schulmanager-ha-test 2>&1 | grep -i "syntaxerror\|importerror"

# Integration-specific errors
docker logs schulmanager-ha-test 2>&1 | grep "schulmanager_online"
```

## Performance Tips

### 1. Optimize Volumes

```yaml
# Only mount necessary files
volumes:
  - ../custom_components/schulmanager_online:/config/custom_components/schulmanager_online
  - ./ha-config/configuration.yaml:/config/configuration.yaml
```

### 2. Image Updates

```bash
# Regularly update image
docker compose pull
docker compose up -d --force-recreate
```

### 3. Log Rotation

```bash
# Limit logs (docker-compose.yml)
services:
  homeassistant:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Production Deployment

### 1. HACS Installation

For production, the integration should be installed via HACS:

1. Install HACS in Home Assistant
2. Add custom repository: `https://github.com/rwunsch/schulmanager-online-hass`
3. Install integration through HACS

### 2. Manual Installation

```bash
# In Home Assistant config directory
cd /config/custom_components/
git clone https://github.com/rwunsch/schulmanager-online-hass.git schulmanager_online
```

### 3. Backup

```bash
# Backup configuration
docker exec schulmanager-ha-test tar -czf /config/backup.tar.gz /config/custom_components/schulmanager_online/
docker cp schulmanager-ha-test:/config/backup.tar.gz ./backup.tar.gz
```

## Monitoring

### 1. Health Checks

```yaml
# docker-compose.yml
services:
  homeassistant:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 2. Log Monitoring

```bash
# Continuous monitoring
watch -n 5 'docker logs schulmanager-ha-test --tail 10'

# Error alerts
docker logs -f schulmanager-ha-test | grep -i error
```

## Useful Aliases

Add these to your `~/.bashrc`:

```bash
# Schulmanager Docker Aliases
alias ha-logs='export DOCKER_HOST="unix:///var/run/docker.sock" && docker logs schulmanager-ha-test'
alias ha-restart='export DOCKER_HOST="unix:///var/run/docker.sock" && docker restart schulmanager-ha-test'
alias ha-shell='docker exec -it schulmanager-ha-test /bin/bash'
alias ha-status='docker ps | grep schulmanager'

# With parameters
function ha-grep() {
    docker logs schulmanager-ha-test 2>&1 | grep -i "$1"
}
```

Usage:
```bash
ha-logs --tail 20
ha-restart
ha-grep "schulmanager"
ha-status
```
