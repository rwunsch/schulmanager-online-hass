# Docker Guide für Schulmanager Online Integration

## Überblick

Diese Anleitung erklärt, wie du Docker für die Entwicklung und das Testen der Schulmanager Online Home Assistant Integration verwendest.

## Docker Setup

### Aktuelle Konfiguration

Das Projekt verwendet eine Docker Compose Konfiguration für Home Assistant:

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

### Wichtige Pfade

- **Custom Components**: `../custom_components` → `/config/custom_components`
- **HA Config**: `./ha-config` → `/config`
- **Web Interface**: `http://localhost:8123`

## Docker Befehle

### 1. Container starten

```bash
# Aus dem test-scripts Verzeichnis
cd test-scripts
docker compose up -d

# Oder mit explizitem DOCKER_HOST (falls nötig)
export DOCKER_HOST="unix:///var/run/docker.sock"
docker compose up -d
```

### 2. Container neu starten

```bash
# Schneller Neustart (behält Image)
export DOCKER_HOST="unix:///var/run/docker.sock"
docker restart schulmanager-ha-test

# Oder mit docker compose
cd test-scripts
docker compose restart
```

### 3. Container stoppen

```bash
# Container stoppen
docker stop schulmanager-ha-test

# Oder mit docker compose
cd test-scripts
docker compose down
```

### 4. Container neu bauen (bei Image-Updates)

```bash
cd test-scripts

# Image neu laden
docker compose pull

# Container neu erstellen
docker compose up -d --force-recreate
```

### 5. Logs anzeigen

```bash
# Aktuelle Logs
export DOCKER_HOST="unix:///var/run/docker.sock"
docker logs schulmanager-ha-test

# Live Logs verfolgen
docker logs -f schulmanager-ha-test

# Nur die letzten 50 Zeilen
docker logs schulmanager-ha-test --tail 50

# Logs nach Schulmanager filtern
docker logs schulmanager-ha-test | grep -i schulmanager
```

## Entwicklungsworkflow

### 1. Code-Änderungen

Wenn du Änderungen an der Integration machst:

1. **Python-Dateien** (`.py`): Home Assistant lädt diese automatisch neu
2. **JavaScript-Dateien** (Custom Card): Benötigt Browser-Refresh
3. **Konfigurationsdateien**: Benötigt HA-Neustart

### 2. Integration neu laden

```bash
# Nur die Integration neu laden (schnell)
# Über HA UI: Einstellungen → Geräte & Dienste → Schulmanager Online → Neu laden

# Oder kompletter HA-Neustart
export DOCKER_HOST="unix:///var/run/docker.sock"
docker restart schulmanager-ha-test
```

### 3. Custom Card Updates

Nach Änderungen an der Custom Card:

1. Container neu starten (kopiert die Card neu)
2. Browser-Cache leeren (`Ctrl+F5`)
3. Lovelace-Dashboard neu laden

## Debugging

### 1. Container-Status prüfen

```bash
# Container-Status
docker ps | grep schulmanager

# Container-Details
docker inspect schulmanager-ha-test
```

### 2. In Container einsteigen

```bash
# Shell im Container
docker exec -it schulmanager-ha-test /bin/bash

# Dateien im Container prüfen
docker exec schulmanager-ha-test ls -la /config/custom_components/schulmanager_online/
```

### 3. Logs analysieren

```bash
# Fehler finden
docker logs schulmanager-ha-test 2>&1 | grep -i error

# Schulmanager-spezifische Logs
docker logs schulmanager-ha-test 2>&1 | grep -i schulmanager

# API-Aufrufe verfolgen
docker logs schulmanager-ha-test 2>&1 | grep -E "(API|400|401|500)"
```

### 4. Custom Card Debug

```bash
# Prüfen ob Card kopiert wurde
docker exec schulmanager-ha-test ls -la /config/www/schulmanager-schedule-card.js

# Card-Registrierung in Logs
docker logs schulmanager-ha-test 2>&1 | grep -i "custom cards"
```

## Häufige Probleme

### 1. "Custom element doesn't exist"

**Problem**: Custom Card wird nicht gefunden

**Lösung**:
```bash
# Container neu starten (kopiert Card neu)
docker restart schulmanager-ha-test

# Browser-Cache leeren
# Dann: Ctrl+F5 im Browser
```

### 2. "Permission denied" Fehler

**Problem**: Docker Socket Berechtigung

**Lösung**:
```bash
# Docker Socket Berechtigung prüfen
ls -la /var/run/docker.sock

# User zur docker Gruppe hinzufügen
sudo usermod -aG docker $USER

# Neu anmelden oder:
newgrp docker
```

### 3. Port 8123 bereits belegt

**Problem**: Port-Konflikt

**Lösung**:
```bash
# Prüfen was Port 8123 verwendet
sudo netstat -tlnp | grep :8123

# Anderen Port verwenden (docker-compose.yml ändern)
ports:
  - "8124:8123"  # Statt 8123:8123
```

### 4. Integration lädt nicht

**Problem**: Python-Fehler in der Integration

**Lösung**:
```bash
# Syntax-Fehler finden
docker logs schulmanager-ha-test 2>&1 | grep -i "syntaxerror\|importerror"

# Integration-spezifische Fehler
docker logs schulmanager-ha-test 2>&1 | grep "schulmanager_online"
```

## Performance-Tipps

### 1. Volumes optimieren

```yaml
# Nur notwendige Dateien mounten
volumes:
  - ../custom_components/schulmanager_online:/config/custom_components/schulmanager_online
  - ./ha-config/configuration.yaml:/config/configuration.yaml
```

### 2. Image-Updates

```bash
# Regelmäßig Image aktualisieren
docker compose pull
docker compose up -d --force-recreate
```

### 3. Log-Rotation

```bash
# Logs begrenzen (docker-compose.yml)
services:
  homeassistant:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Produktions-Deployment

### 1. HACS Installation

Für die Produktion sollte die Integration über HACS installiert werden:

1. HACS in Home Assistant installieren
2. Custom Repository hinzufügen: `https://github.com/wunsch/schulmanager-online-hass`
3. Integration über HACS installieren

### 2. Manuelle Installation

```bash
# In Home Assistant config Verzeichnis
cd /config/custom_components/
git clone https://github.com/wunsch/schulmanager-online-hass.git schulmanager_online
```

### 3. Backup

```bash
# Konfiguration sichern
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

### 2. Log-Monitoring

```bash
# Kontinuierliches Monitoring
watch -n 5 'docker logs schulmanager-ha-test --tail 10'

# Fehler-Alerts
docker logs -f schulmanager-ha-test | grep -i error
```

## Nützliche Aliases

Füge diese zu deiner `~/.bashrc` hinzu:

```bash
# Schulmanager Docker Aliases
alias ha-logs='export DOCKER_HOST="unix:///var/run/docker.sock" && docker logs schulmanager-ha-test'
alias ha-restart='export DOCKER_HOST="unix:///var/run/docker.sock" && docker restart schulmanager-ha-test'
alias ha-shell='docker exec -it schulmanager-ha-test /bin/bash'
alias ha-status='docker ps | grep schulmanager'

# Mit Parametern
function ha-grep() {
    docker logs schulmanager-ha-test 2>&1 | grep -i "$1"
}
```

Verwendung:
```bash
ha-logs --tail 20
ha-restart
ha-grep "schulmanager"
ha-status
```
