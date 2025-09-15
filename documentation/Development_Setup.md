# Development Environment - Setup Guide

## 🎯 Overview

This guide describes the complete setup of a development environment for the Schulmanager Online integration, including Docker setup, test scripts, and debugging tools.

## 🐳 Docker Development Environment

### Prerequisites

```bash
# Install Docker (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose
sudo usermod -aG docker $USER

# Start Docker service
sudo systemctl start docker
sudo systemctl enable docker

# WSL2-specific (if used)
export DOCKER_HOST="unix:///var/run/docker.sock"
```

### Home Assistant Test Container

```yaml
# test-scripts/docker-compose-fixed.yml
version: '3.8'
services:
  homeassistant:
    container_name: schulmanager-ha-test
    image: ghcr.io/home-assistant/home-assistant:stable
    volumes:
      - ./ha-config:/config
      - /etc/localtime:/etc/localtime:ro
      - ../custom_components:/config/custom_components  # Mount integration
    restart: unless-stopped
    privileged: true
    ports:
      - 8123:8123
    environment:
      - TZ=Europe/Berlin
```

### Container Management

```bash
# Start container
cd test-scripts
docker compose -f docker-compose-fixed.yml up -d

# Follow logs
docker logs -f schulmanager-ha-test

# Stop container
docker compose -f docker-compose-fixed.yml down

# Restart container (after code changes)
docker restart schulmanager-ha-test
```

### Home Assistant Configuration

```yaml
# test-scripts/ha-config/configuration.yaml
homeassistant:
  name: Schulmanager Test
  latitude: 52.520008
  longitude: 13.404954
  elevation: 34
  unit_system: metric
  time_zone: Europe/Berlin
  country: DE
  currency: EUR
  internal_url: "http://localhost:8123"
  external_url: "http://ha-test.local"
  
  # Allow loading custom integrations
  allowlist_external_dirs:
    - /config/custom_components

# Enable default_config to get basic Home Assistant functionality
default_config:

# Configure recorder using SQLite (simpler than PostgreSQL)
recorder:
  db_url: sqlite:////config/home-assistant_v2.db

# Debug logging for development
logger:
  default: info
  logs:
    custom_components.schulmanager_online: debug
    custom_components.schulmanager_online.api: debug
    custom_components.schulmanager_online.coordinator: debug

# Custom Card Resources
lovelace:
  resources:
    - url: /hacsfiles/schulmanager_online/schulmanager-schedule-card.js
      type: module
```

## 🧪 Test Scripts Setup

### Python Virtual Environment

```bash
# Create virtual environment
cd test-scripts
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Requirements

```txt
# test-scripts/requirements.txt
aiohttp>=3.8.0
python-dateutil>=2.8.0
asyncio-mqtt>=0.11.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
jsbeautifier>=1.14.0
```

### Makefile for Simple Commands

```makefile
# test-scripts/Makefile
.PHONY: help setup test docker-up docker-down clean

help:
	@echo "Available commands:"
	@echo "  setup      - Setup virtual environment and install dependencies"
	@echo "  test       - Run API tests"
	@echo "  docker-up  - Start Home Assistant test container"
	@echo "  docker-down- Stop Home Assistant test container"
	@echo "  clean      - Clean up temporary files"

setup:
	python3 -m venv venv
	./venv/bin/pip install -r requirements.txt
	@echo "✅ Setup complete. Activate with: source venv/bin/activate"

test: venv
	./venv/bin/python test_corrected_hash.py

test-standalone: venv
	./venv/bin/python standalone_api_test.py

test-complete: venv
	./venv/bin/python test_api_complete.py

docker-up:
	export DOCKER_HOST="unix:///var/run/docker.sock" && \
	docker compose -f docker-compose-fixed.yml up -d
	@echo "✅ Home Assistant started at http://localhost:8123"

docker-down:
	export DOCKER_HOST="unix:///var/run/docker.sock" && \
	docker compose -f docker-compose-fixed.yml down

docker-logs:
	export DOCKER_HOST="unix:///var/run/docker.sock" && \
	docker logs -f schulmanager-ha-test

docker-restart:
	export DOCKER_HOST="unix:///var/run/docker.sock" && \
	docker restart schulmanager-ha-test

clean:
	rm -rf venv
	rm -rf __pycache__
	rm -rf .pytest_cache
	find . -name "*.pyc" -delete

venv:
	@if [ ! -d "venv" ]; then make setup; fi
```

## 🔧 Development Tools

### API Test Scripts

#### 1. Basic API Test

```python
# test-scripts/test_corrected_hash.py
import asyncio
import aiohttp
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from custom_components.schulmanager_online.api import SchulmanagerAPI, SchulmanagerAPIError

async def test_api():
    """Test the Schulmanager API with corrected hash implementation."""
    
    # Test credentials
    email = "<schulmanager-login>"
    password = "<schulmanager-password>"
    
    async with aiohttp.ClientSession() as session:
        api = SchulmanagerAPI(email, password, session)
        
        try:
            print("🔐 Testing authentication...")
            await api.authenticate()
            print(f"✅ Authentication successful! Token: {api.token[:20]}...")
            
            print("\n👥 Testing student data...")
            students = await api.get_students()
            print(f"✅ Found {len(students)} students:")
            
            for student in students:
                print(f"   - {student['firstname']} {student['lastname']} (ID: {student['id']})")
            
            print("\n📅 Testing schedule data...")
            if students:
                student_id = students[0]['id']
                from datetime import date, timedelta
                
                start_date = date.today()
                end_date = start_date + timedelta(days=7)
                
                schedule = await api.get_schedule(student_id, start_date, end_date)
                print(f"✅ Retrieved schedule with {len(schedule)} entries")
                
                if schedule:
                    print("   Sample lesson:")
                    lesson = schedule[0]
                    print(f"   - Date: {lesson.get('date')}")
                    print(f"   - Subject: {lesson.get('lesson', {}).get('subject')}")
                    print(f"   - Teacher: {lesson.get('lesson', {}).get('teacher')}")
                    print(f"   - Room: {lesson.get('lesson', {}).get('room')}")
            
            print("\n🎉 All tests passed!")
            
        except SchulmanagerAPIError as e:
            print(f"❌ API Error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_api())
    sys.exit(0 if success else 1)
```

#### 2. Integration Test

```python
# test-scripts/test_ha_integration.py
import asyncio
import aiohttp
import json
from datetime import datetime

HA_URL = "http://localhost:8123"
HA_API_URL = f"{HA_URL}/api/"

async def test_ha_integration():
    """Test Home Assistant integration."""
    
    print("🏠 Testing Home Assistant Integration...")
    
    async with aiohttp.ClientSession() as session:
        
        # Test HA API access
        try:
            async with session.get(HA_API_URL) as response:
                if response.status == 401:
                    print("✅ Home Assistant API accessible (authentication required)")
                else:
                    print(f"⚠️  Unexpected status: {response.status}")
        except Exception as e:
            print(f"❌ Cannot connect to Home Assistant: {e}")
            return False
        
        # Test states endpoint (without auth - will return 401 but confirms API works)
        try:
            async with session.get(f"{HA_API_URL}states") as response:
                if response.status == 401:
                    print("✅ States endpoint accessible")
                else:
                    print(f"⚠️  States endpoint status: {response.status}")
        except Exception as e:
            print(f"❌ States endpoint error: {e}")
        
        print("\n📊 Integration Status:")
        print("   - Home Assistant: Running")
        print("   - API: Accessible")
        print("   - Custom Integration: Check via UI")
        
        return True

if __name__ == "__main__":
    asyncio.run(test_ha_integration())
```

### JavaScript Debugging

#### Browser Console Tests

```javascript
// Browser Console (F12) - Test custom card
console.log("Testing Custom Card...");

// Check if card is registered
const cardElement = customElements.get('schulmanager-schedule-card');
console.log("Card registered:", !!cardElement);

// Test card creation
if (cardElement) {
    const card = new cardElement();
    card.setConfig({
        entity: 'sensor.name_of_child_current_lesson',
        view: 'weekly_matrix'
    });
    console.log("Card created successfully");
}

// Check available entities
const entities = Object.keys(window.hass.states).filter(id => 
    id.includes('schulmanager')
);
console.log("Schulmanager entities:", entities);
```

#### Card Development Server

```html
<!-- test-scripts/test-card.html -->
<!DOCTYPE html>
<html>
<head>
    <title>Schulmanager Card Test</title>
    <script type="module" src="../custom_components/schulmanager_online/www/schulmanager-schedule-card.js"></script>
</head>
<body>
    <h1>Schulmanager Schedule Card Test</h1>
    
    <schulmanager-schedule-card id="test-card"></schulmanager-schedule-card>
    
    <script>
        // Mock Home Assistant object
        window.hass = {
            states: {
                'sensor.name_of_child_current_lesson': {
                    state: 'Mathematics',
                    attributes: {
                        subject: 'Mathematics',
                        teacher: 'Mr. Schmidt',
                        room: 'R204',
                        start_time: '09:45',
                        end_time: '10:30'
                    }
                }
            }
        };
        
        // Configure card
        const card = document.getElementById('test-card');
        card.hass = window.hass;
        card.setConfig({
            entity: 'sensor.name_of_child_current_lesson',
            view: 'compact'
        });
    </script>
</body>
</html>
```

## 🔍 Debugging Strategies

### Home Assistant Debugging

```bash
# Follow live logs
docker logs -f schulmanager-ha-test | grep -i schulmanager

# Specific component logs
docker logs schulmanager-ha-test 2>&1 | grep "custom_components.schulmanager_online"

# Container shell for debugging
docker exec -it schulmanager-ha-test /bin/bash
```

### Python Debugging

```python
# Debug mode in test scripts
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Breakpoints for debugging
import pdb; pdb.set_trace()

# Or with ipdb (better alternative)
import ipdb; ipdb.set_trace()
```

### API Request Debugging

```python
# Log HTTP traffic
import aiohttp
import aiohttp_debugtoolbar

# Session with debug toolbar
session = aiohttp.ClientSession(
    trace_configs=[aiohttp.TraceConfig()]
)

# Log request/response
async def log_request(session, trace_config_ctx, params):
    print(f"Request: {params.method} {params.url}")
    print(f"Headers: {params.headers}")

async def log_response(session, trace_config_ctx, params):
    print(f"Response: {params.response.status}")
    print(f"Headers: {params.response.headers}")

trace_config = aiohttp.TraceConfig()
trace_config.on_request_start.append(log_request)
trace_config.on_request_end.append(log_response)
```

## 🧪 Testing Framework

### Pytest Setup

```python
# test-scripts/conftest.py
import pytest
import asyncio
import aiohttp
from unittest.mock import AsyncMock

@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def http_session():
    """Create HTTP session for tests."""
    session = aiohttp.ClientSession()
    yield session
    await session.close()

@pytest.fixture
def mock_api_response():
    """Mock API response data."""
    return {
        "jwt": "mock_token",
        "user": {
            "associatedParents": [
                {
                    "student": {
                        "id": 123456,
                        "firstname": "Test",
                        "lastname": "Student"
                    }
                }
            ]
        }
    }
```

### Unit Tests

```python
# test-scripts/test_api_unit.py
import pytest
from unittest.mock import AsyncMock, patch
from custom_components.schulmanager_online.api import SchulmanagerAPI

class TestSchulmanagerAPI:
    
    @pytest.mark.asyncio
    async def test_hash_generation(self, http_session):
        """Test hash generation."""
        api = SchulmanagerAPI("test@example.com", "password", http_session)
        
        hash_result = api._generate_salted_hash("password", "salt")
        
        assert len(hash_result) == 1024
        assert isinstance(hash_result, str)
        assert hash_result.isalnum()  # Only hex characters
    
    @pytest.mark.asyncio
    async def test_authentication_success(self, http_session, mock_api_response):
        """Test successful authentication."""
        api = SchulmanagerAPI("test@example.com", "password", http_session)
        
        with patch.object(api, '_get_salt', return_value='test_salt'), \
             patch.object(api, '_login') as mock_login:
            
            await api.authenticate()
            mock_login.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_students_parent_account(self, http_session, mock_api_response):
        """Test student extraction from parent account."""
        api = SchulmanagerAPI("test@example.com", "password", http_session)
        api.user_data = mock_api_response["user"]
        
        students = await api.get_students()
        
        assert len(students) == 1
        assert students[0]["firstname"] == "Test"
        assert students[0]["lastname"] == "Student"
```

### Integration Tests

```python
# test-scripts/test_integration.py
import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from custom_components.schulmanager_online import async_setup_entry

@pytest.mark.asyncio
async def test_integration_setup(hass: HomeAssistant):
    """Test integration setup."""
    
    # Mock config entry
    config_entry = ConfigEntry(
        version=1,
        domain="schulmanager_online",
        title="Test",
        data={
            "email": "test@example.com",
            "password": "password"
        },
        entry_id="test_entry"
    )
    
    # Test setup
    result = await async_setup_entry(hass, config_entry)
    assert result is True
    
    # Check if coordinator is created
    assert "schulmanager_online" in hass.data
    assert config_entry.entry_id in hass.data["schulmanager_online"]
```

## 📊 Performance Monitoring

### Profiling

```python
# Performance profiling
import cProfile
import pstats

def profile_api_call():
    """Profile API call performance."""
    
    async def run_test():
        # Your API test code here
        pass
    
    # Profile the execution
    profiler = cProfile.Profile()
    profiler.enable()
    
    asyncio.run(run_test())
    
    profiler.disable()
    
    # Analyze results
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 functions
```

### Memory Monitoring

```python
# Memory usage monitoring
import tracemalloc
import asyncio

async def monitor_memory():
    """Monitor memory usage during API calls."""
    
    tracemalloc.start()
    
    # Your code here
    await api.authenticate()
    
    current, peak = tracemalloc.get_traced_memory()
    print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
    print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
    
    tracemalloc.stop()
```

## 🔄 CI/CD Pipeline

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Test Integration

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        cd test-scripts
        pip install -r requirements.txt
    
    - name: Run unit tests
      run: |
        cd test-scripts
        python -m pytest test_api_unit.py -v
    
    - name: Run integration tests
      env:
        SCHULMANAGER_EMAIL: ${{ secrets.SCHULMANAGER_EMAIL }}
        SCHULMANAGER_PASSWORD: ${{ secrets.SCHULMANAGER_PASSWORD }}
      run: |
        cd test-scripts
        python test_corrected_hash.py
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11
  
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203]
  
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: [--profile=black]
```

## 📚 Further Documentation

- [API Implementation](API_Implementation.md) - API details
- [Integration Architecture](Integration_Architecture.md) - Architecture
- [Troubleshooting Guide](Troubleshooting_Guide.md) - Problem solutions
- [Test Scripts Guide](Test_Scripts_Guide.md) - Test documentation
