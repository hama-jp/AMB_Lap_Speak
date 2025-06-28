# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview
This is a Python client for AMB (Amsterdam Micro Broadcasting) P3 timing decoders, used in motorsport/karting timing systems. It connects to AMB hardware via TCP socket, decodes transponder timing data, and stores race information in MySQL.

## Common Development Commands

### Development Setup
```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies (note: PyYAML 5.4 has issues with Python 3.11+)
uv pip install PyYAML>=6.0
grep -v "PyYAML" requirements.txt | uv pip install -r /dev/stdin
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

### Configuration
- **conf.yaml**: Main configuration file containing:
  - Decoder connection (default: 127.0.0.1:12000)
  - MySQL database settings (default: localhost:3307)
  - Logging paths and feature flags

### Database Schema
Core tables: `passes` (raw transponder readings), `laps` (validated lap times), `heats` (race sessions), `karts` (transponder mappings), `settings` (runtime config)

### Data Flow
1. TCP connection to AMB P3 decoder hardware
2. Continuous reading of P3 protocol messages
3. CRC validation and protocol decoding
4. Time synchronization and transponder event processing
5. Lap validation and race heat management
6. MySQL persistence with comprehensive logging

## Testing
- **test_server.py**: Mock AMB decoder for testing
- **test_server/**: Contains sample AMB data files for development
- **decode_one.py**: Single message decoder utility for debugging

## Development Notes
- Uses Python 3.7 with mysql-connector for database operations
- P3 protocol implementation with CRC16 validation
- Designed for production karting timing applications
- Race timing requires precise time synchronization between client and decoder