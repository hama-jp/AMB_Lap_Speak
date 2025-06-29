# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Python client for AMB (Amsterdam Micro Broadcasting) P3 timing decoders, used in RC car racing timing systems. It connects to AMB hardware via TCP socket, decodes transponder timing data, stores race information in MySQL, and provides Japanese voice announcements for race events.

## Key Features Added
- **Japanese Voice Announcements**: Multi-engine TTS system (gTTS, pyttsx3, espeak)
- **Real-time Race Commentary**: Automatic lap announcements and position updates
- **All Cars Time Announcement**: Periodic and manual reading of all car positions
- **Web Voice Control**: Browser-based controls for voice settings and manual announcements

## Common Development Commands

### Development Setup
```bash
# Quick setup using provided script
chmod +x setup.sh
./setup.sh

# Manual setup
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# Database setup with Docker (requires Docker Desktop)
docker run -d --name mysql-amb -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=karts -e MYSQL_USER=kart -e MYSQL_PASSWORD=karts -p 3307:3306 mysql:5.7
sleep 30 && cat schema | docker exec -i mysql-amb mysql -u kart -pkarts karts
```

### Code Quality
```bash
# Lint code (configured for 140 char line length)
flake8
```

### Running the Application
```bash
# Main timing client (connects to AMB decoder)
python amb_client.py

# Race heat management
python amb_laps.py

# Send messages to decoder
python amb_send.py

# Test with mock data
python test_server.py

# Web application for live lap timing display
python web_app.py
# Access at http://localhost:5000
```

### Voice System Testing
```bash
# Test voice announcer independently
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True, engine='auto')
print(f'Engine type: {announcer.engine_type}')
announcer.test_voice()
"

# Test individual lap announcement
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True)
announcer.announce_lap_time(5, 3, 65.234, is_best=True)
"

# Test all cars announcement
python -c "
from AmbP3.voice_announcer import LapTimeMonitor, VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True)
monitor = LapTimeMonitor(announcer)
mock_data = [
    {'car_number': 1, 'lap_count': 5, 'best_lap_time': '1:02.123'},
    {'car_number': 2, 'lap_count': 4, 'best_lap_time': '1:05.456'}
]
monitor._announce_all_times(mock_data)
"
```

### Docker Deployment
```bash
# Build container
docker build -t ambp3client .

# Container uses Python 3.7 Alpine with MariaDB dependencies
```

## Architecture

### Core Components
- **amb_client.py**: Main application entry point, connects to AMB decoder and processes timing data
- **AmbP3/decoder.py**: TCP socket communication with P3 hardware, protocol decoding
- **AmbP3/records.py**: P3 protocol message format definitions and data structures
- **AmbP3/write.py**: MySQL database operations for race data persistence
- **AmbP3/time_server.py** & **AmbP3/time_client.py**: Time synchronization with decoder RTC
- **amb_laps.py**: Race heat management and lap validation logic
- **web_app.py**: Flask web application providing live timing dashboard and voice control
- **AmbP3/voice_announcer.py**: Multi-engine TTS system for Japanese race announcements
- **templates/index.html**: Responsive web interface with real-time updates and voice controls

### Configuration
- **conf.yaml**: Main configuration file containing:
  - Decoder connection (default: 192.168.1.21:5403)
  - MySQL database settings (default: localhost:3307)
  - Logging paths and feature flags

### Database Schema
Core tables: `passes` (raw transponder readings), `laps` (validated lap times), `heats` (race sessions), `cars` (transponder mappings), `settings` (runtime config)

### Data Flow
1. TCP connection to AMB P3 decoder hardware
2. Continuous reading of P3 protocol messages
3. CRC validation and protocol decoding
4. Time synchronization and transponder event processing
5. Lap validation and race heat management
6. MySQL persistence with comprehensive logging
7. Web dashboard serves real-time data via Flask API
8. Voice announcements triggered on lap completion and position changes
9. Periodic all-cars time announcements (30-second intervals)

## Testing
- **test_server.py**: Mock AMB decoder for testing
- **test_server/**: Contains sample AMB data files for development
- **decode_one.py**: Single message decoder utility for debugging

## Development Notes
- Uses Python 3.7+ with mysql-connector for database operations
- P3 protocol implementation with CRC16 validation
- Designed for production karting timing applications with focus on practice sessions
- RC car timing requires precise time synchronization between client and decoder
- Web interface uses in-memory data store for high-performance real-time updates
- Voice announcements are per-ponder configurable through web interface
- flake8 configuration uses 140 character line length (tox.ini)
- Docker setup requires Docker Desktop on WSL/Windows environments
- Web application requires numpy for data processing
- espeak-ng dependency may fail on some systems (voice system defaults to gTTS)