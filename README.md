# AMB RC Timer - Real-time RC Car Timing System

**AMB P3 Decoder Compatible RC Car Timing System with Japanese Voice Announcements**

A professional timing system that displays lap times in real-time and announces race status in natural Japanese voice synthesis.

[🇯🇵 日本語版README](README_ja.md) | [🇺🇸 English Version](README.md)

## 🎯 Key Features

- 🏁 **Real-time Lap Timing**: Connect to AMB P3 decoders and track transponder passes
- 📊 **Live Web Dashboard**: Real-time display of lap times for up to 16 RC cars
- 🗣️ **Japanese Voice Announcements**: Natural Japanese race commentary using Google TTS
- 🗄️ **MySQL Database**: Persistent storage of all timing data
- ⏱️ **Automatic Lap Calculation**: Intelligent filtering of valid laps only
- 🔄 **Auto-refresh Interface**: Web dashboard updates every 2 seconds
- 📱 **Responsive Design**: Mobile-friendly interface for trackside use
- 🏆 **Race Management**: Automatic tracking of best laps, lap counts, and driver positions

## 🎤 Voice Announcement Features

### Individual Lap Announcements (Default: Simple Mode)
- **Lap Completion**: "1:05.234" (time only)
- **Best Lap Update**: "59.789秒、ベストラップ！" (Best lap!)
- **New Record**: "新記録！59.789秒" (New record!)

### Detailed Mode (Optional Settings)
- **Lap Completion**: "3ラップ、1:05.234" (with lap number)
- **With Car Number**: "カー5、3ラップ、1:05.234" (with car number)

### All Cars Time Announcement (Default: Disabled)
- **Automatic Announcement**: Optional 30-second interval announcements of all car positions
- **Manual Announcement**: Trigger anytime via web interface button
- **Example**: "現在の順位、1位、5ラップ、ベスト59.8秒、2位、4ラップ、ベスト1分2.1秒..."

### Supported TTS Engines
- **Google TTS (Recommended)**: Highest quality Japanese voice synthesis
- **pyttsx3**: Offline voice synthesis
- **espeak**: Backup voice engine

## 📋 System Requirements

- **Python**: 3.7 or higher
- **Database**: MySQL 5.7+ or Docker
- **Hardware**: AMB P3 Decoder with network connectivity
- **Browser**: Modern web browser
- **Audio Output**: Speakers or headphones

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/hama-jp/AMB_RC_Timer.git
cd AMB_RC_Timer
```

### 2. Automatic Setup (Recommended)

```bash
# Run setup script
chmod +x setup.sh
./setup.sh
```

### 3. Manual Setup

#### Python Environment Setup

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
uv pip install PyYAML>=6.0
grep -v "PyYAML" requirements.txt | uv pip install -r /dev/stdin

# Install web interface packages
uv pip install flask

# Install voice announcement packages
uv pip install gtts pygame
```

#### MySQL Database Setup

**Using Docker (Recommended):**

```bash
# Start MySQL container
docker run -d --name mysql-amb \
  -e MYSQL_ROOT_PASSWORD=root \
  -e MYSQL_DATABASE=karts \
  -e MYSQL_USER=kart \
  -e MYSQL_PASSWORD=karts \
  -p 3307:3306 \
  mysql:5.7

# Wait for MySQL to start (30 seconds)
sleep 30

# Load database schema
cat schema | docker exec -i mysql-amb mysql -u kart -pkarts karts
```

### 4. AMB Decoder Configuration

Configure your AMB decoder settings in `conf.yaml`:

```yaml
---
ip: '192.168.1.21'    # Your AMB decoder IP address
port: 5403            # AMB decoder port (usually 5403)
file: "/tmp/out.log"
debug_file: "/tmp/amb_raw.log"
mysql_backend: True
mysql_host: '127.0.0.1'
mysql_port: 3307      # 3306 for local MySQL
mysql_db: 'karts'
mysql_user: 'kart'
mysql_password: 'karts'
```

### 5. RC Car Information Registration (Optional)

```bash
# Activate virtual environment
source .venv/bin/activate

# Add RC car data
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
cursor = conn.cursor()

# RC car information (car_number, transponder_id, driver_name)
cars = [
    (1, 4000822, 'Driver A'),
    (2, 4000823, 'Driver B'),
    (3, 4000824, 'Driver C'),
    # Add more as needed
]

for car_number, transponder_id, name in cars:
    cursor.execute('INSERT IGNORE INTO cars (car_number, transponder_id, name) VALUES (%s, %s, %s)', 
                   (car_number, transponder_id, name))

conn.commit()
conn.close()
print('RC car data added successfully')
"
```

## 🏃‍♂️ Running the System

### 1. Start AMB Client (Data Collection)

```bash
source .venv/bin/activate
python amb_client.py
```

### 2. Start Web Interface

In a new terminal:

```bash
source .venv/bin/activate
python web_app.py
```

**Web Interface Access**: http://localhost:5000

## 🖥️ Web Interface Features

### Live Timing Display
- **Position**: Current standing based on lap count and best lap time
- **Car Number**: Car number configured in database
- **Driver Name**: Driver name configured in database
- **Status**: Racing (completed laps) or On Track (recent activity)
- **Lap Count**: Total completed laps
- **Last Lap Time**: Most recent lap time
- **Best Lap Time**: Fastest lap time (highlighted in green)
- **Last Activity**: Time of most recent transponder pass

### Recent Passes Display
- Real-time feed of transponder detections
- Shows transponder ID, signal strength, and timestamp
- Auto-scrolls to show latest activity

### 🎛️ Voice Control
- **Voice Enable/Disable**: Toggle voice announcements on/off
- **Volume Adjustment**: 0-100% volume control
- **Speaking Rate**: 50-300 WPM speed adjustment
- **Announcement Style**:
  - **Include Car Numbers**: Off (default) / On
  - **Include Lap Numbers**: Off (default) / On
  - **Periodic All Times**: Off (default) / On (30-second intervals)
- **Voice Test**: "音声テスト。RCカータイマーシステムが正常に動作しています。"
- **Announce All Times**: Manual announcement of all current car times
- **Race Reset**: Reset race state

### Auto-refresh
- Updates every 2 seconds
- Live status indicator shows connection health
- Displays up to 16 RC cars simultaneously

## 🗄️ Database Schema

The system uses 5 main tables:

- **passes**: Raw transponder readings from AMB decoder
- **laps**: Validated lap times within race sessions
- **heats**: Race session management
- **cars**: Transponder to RC car/driver mapping
- **settings**: Runtime configuration storage

## 🔧 Troubleshooting

### AMB Decoder Connection Issues

```bash
# Test direct connection to decoder
python -c "
from AmbP3.decoder import Connection
conn = Connection('192.168.1.21', 5403)  # Adjust IP address
conn.connect()
print('Connection successful!')
conn.close()
"
```

### MySQL Connection Issues

```bash
# Test database connection
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
print('Database connection successful!')
conn.close()
"
```

### Voice Output Issues

```bash
# Test voice engine
python -c "
from AmbP3.voice_announcer import VoiceAnnouncer
announcer = VoiceAnnouncer(enabled=True, engine='auto')
print(f'Voice engine in use: {announcer.engine_type}')
announcer.test_voice()
"
```

### System Status Check

```bash
# Check recent timing data
tail -f /tmp/out.log

# Check database activity
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM passes')
print(f'Total passes: {cursor.fetchone()[0]}')
conn.close()
"
```

## 🏗️ System Architecture

```
AMB P3 Decoder (Hardware)
    ↓ TCP Socket (Port 5403)
amb_client.py (Data Collection)
    ↓ Protocol Decoding
MySQL Database (Data Storage)
    ↓ Web API
web_app.py (Flask Web Server)
    ↓ HTTP (Port 5000)
Web Browser (Live Display)
    ↓ Audio Output
Google TTS / pygame (Voice Announcements)
```

## 🧪 Development & Testing

### Code Quality Check

```bash
# Run linter
flake8
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
announcer.announce_lap_time(5, 3, 65.234, is_best=True, simple_mode=True)
"
```

### File Structure

```
AMB_RC_Timer/
├── AmbP3/                 # Core timing system package
│   ├── config.py         # Configuration management
│   ├── decoder.py        # AMB P3 protocol handling
│   ├── records.py        # Protocol message definitions
│   ├── write.py          # Database operations
│   ├── voice_announcer.py # Voice announcement system
│   └── ...
├── templates/            # Web interface templates
│   └── index.html       # Main dashboard
├── amb_client.py        # Main timing client
├── web_app.py          # Flask web application
├── conf.yaml           # Configuration file
├── schema              # MySQL database schema
├── requirements.txt    # Python dependencies
├── setup.sh           # Automated setup script
├── CLAUDE.md          # Development guidelines
├── README.md          # English README (this file)
└── README_ja.md       # Japanese README
```

## 📚 API Reference

### Main Endpoints

- `GET /` - Main dashboard
- `GET /api/lap_times` - Current lap times (JSON)
- `GET /api/recent_passes` - Recent transponder passes (JSON)

### Voice Control API

- `GET /api/voice/settings` - Get voice settings
- `POST /api/voice/settings` - Update voice settings
- `POST /api/voice/test` - Test voice announcement
- `POST /api/voice/announce` - Manual voice announcement
- `POST /api/voice/announce_all` - Announce all car times
- `GET/POST /api/voice/announcement_settings` - Announcement style settings

### Race Management API

- `POST /api/race/reset` - Reset race state

## 🎯 Usage Examples

### Basic Usage Flow

1. **Set up AMB decoder and network configuration**
2. **Setup and start the system**
3. **Access dashboard via web browser**
4. **Adjust voice settings as needed**
5. **Start racing and monitor in real-time**

### Voice Setting Use Cases

- **Practice Sessions**: Simple mode (time only)
- **Qualifying & Finals**: Detailed mode (with lap/car numbers)
- **Endurance Races**: Enable periodic all-cars announcements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔗 Related Projects

- [AMB Web](https://github.com/vmindru/ambweb) - Alternative web interface
- [AMB Docker](https://github.com/br0ziliy/amb-docker) - Docker deployment

## 📞 Support

For issues and questions:

1. Check the troubleshooting section above
2. Review logs in `/tmp/out.log` and `/tmp/amb_raw.log`
3. Open an issue on GitHub with detailed error information

## 📈 Roadmap

- [ ] Export functionality (CSV, PDF)
- [ ] Multiple race session management
- [ ] Custom voice messages
- [ ] Mobile app version
- [ ] Cloud sync capabilities

## 🙏 Acknowledgments

This project uses the following technologies and libraries:

- **AMB (Amsterdam Micro Broadcasting)** - P3 timing decoders
- **Google Text-to-Speech** - High-quality Japanese voice synthesis
- **Flask** - Web application framework
- **MySQL** - Database management system
- **pygame** - Audio playback library

---

**Happy RC Racing! 🏎️🎌**

*A professional timing system with Japanese voice announcements, built for RC car racing in Japan*