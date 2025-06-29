# AMB Lap Speak - RC Practice Lap Timer

**An AMB P3 Decoder-compatible RC car lap timer, specialized for personal practice sessions, with Japanese voice announcements.**

This system is designed to help individual drivers improve their skills by providing detailed, real-time lap data and performance statistics.

[🇯🇵 日本語版README](README_ja.md) | [🇺🇸 English Version](README.md)

## 🎯 Key Features

- 🚗 **Practice-Focused Dashboard**: Displays the most recent lap from any car at the top of the screen.
- 📈 **In-Depth Statistics**: For each car, view the best lap, 10-lap moving average, and standard deviation to gauge consistency.
- 📊 **Visual Lap History**: Click on any ponder to see a detailed lap history page with a chart visualizing lap time progression.
- 🗣️ **Per-Ponder Voice Announcements**: Toggle Japanese voice announcements for individual cars, so you only hear the times you care about.
- 🏷️ **Custom Nicknames**: Set custom nicknames for voice announcements to easily identify multiple cars during practice sessions.
- 🇯🇵 **Japanese Interface**: Fully localized Japanese web interface with natural time formatting for voice announcements.
- ⏱️ **Real-time Data**: Connects to AMB P3 decoders to capture transponder passes instantly.
- 🗄️ **Persistent Data**: Uses a MySQL database to store all lap data for later analysis.
- 🚀 **High-Performance Backend**: An in-memory data store provides a highly responsive web interface that updates every second.
- 📱 **Responsive Design**: A clean, mobile-friendly interface for easy viewing at the track.

## 🖥️ Web Interface

### Main Dashboard
The main view is designed for at-a-glance information.
- The table is sorted by the most recent pass, so the car that just crossed the line is always at the top.
- Key performance indicators are visible for every car:
  - **Ponder**: The transponder ID. Click to view the detailed history page.
  - **Nickname**: Custom name for voice announcements (shows "-" if not set).
  - **Best Lap**: The single fastest lap since the server started.
  - **Avg (10 Laps)**: A moving average of the last 10 laps.
  - **Std Dev**: The standard deviation of lap times, indicating consistency.
  - **Latest Lap**: The most recently completed lap time.
  - **Last Pass**: The timestamp of the last time the car crossed the start/finish line.
  - **Announce**: A checkbox to enable or disable voice announcements for that specific car.

### Lap History Page
- Accessible by clicking a ponder number on the main dashboard.
- **Nickname Setting**: Input field to set a custom name for voice announcements.
- **Performance Summary**: Shows total laps, best lap, and the 10-lap average.
- **Lap Time Chart**: A line graph that visually represents every lap time, making it easy to spot trends and inconsistencies.
- **Full Lap Data**: A table listing every lap number, its time, and the time of day it was set.

## 🎤 Voice Announcements
- Voice announcements can be enabled or disabled for each car individually using the checkbox on the main dashboard.
- Set custom nicknames for each car in the lap history page for easier identification during multi-car sessions.
- When enabled, the system will announce the nickname (or transponder ID if no nickname is set) and lap time in Japanese format.
- **Examples**: 
  - With nickname: "１番、65秒24" (pronounced: "ichiban, rokujūgo-byō ni-yon")
  - Without nickname: "4000822、65秒24" (pronounced: "yonhyaku-man happyaku nijūni, rokujūgo-byō ni-yon")
- Time format uses Japanese-style pronunciation where "65.24" becomes "65秒24" for clearer digit recognition.

## 📋 System Requirements

- **Python**: 3.7 or higher
- **Database**: MySQL 5.7+ or Docker
- **Hardware**: AMB P3 Decoder with network connectivity
- **Browser**: Modern web browser
- **Audio Output**: Speakers or headphones

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/hama-jp/AMB_Lap_Speak.git
cd AMB_Lap_Speak
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
uv pip install -r requirements.txt
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

You can map transponder IDs to car numbers for easier identification.

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
    (1, 4000822, 'My Car 1'),
    (2, 4000823, 'My Car 2'),
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

## 🏗️ System Architecture

```
AMB P3 Decoder (Hardware)
    ↓ TCP Socket (Port 5403)
amb_client.py (Data Collection)
    ↓ Protocol Decoding
MySQL Database (Data Storage)
    ↓ Web API (on startup & for new laps)
web_app.py (Flask Web Server with In-Memory Store)
    ↓ HTTP (Port 5000)
Web Browser (Live Display via polling)
    ↓ Audio Output
Voice Announcer (triggered by new laps in backend)
```

### File Structure

```
AMB_Lap_Speak/
├── AmbP3/                 # Core timing system package
│   ├── ...
│   └── voice_announcer.py # Voice announcement system
├── templates/            # Web interface templates
│   ├── index.html       # Main dashboard
│   └── laps.html        # Lap history detail page
├── amb_client.py        # Main timing client
├── web_app.py          # Flask web application
├── conf.yaml           # Configuration file
├── schema              # MySQL database schema
├── requirements.txt    # Python dependencies
├── setup.sh           # Automated setup script
├── README.md          # English README (this file)
└── README_ja.md       # Japanese README
```

## 📚 API Reference

- `GET /`: Serves the main dashboard page.
- `GET /laps/<transponder_id>`: Serves the detailed lap history page for a specific ponder.
- `GET /api/all_laps`: Returns a JSON list of the latest lap data for all active cars, sorted by the most recent pass. Used by the main dashboard.
- `GET /api/laps/<transponder_id>`: Returns a JSON object with the complete history and statistics for a single car. Used by the lap history page.
- `POST /api/voice_toggle/<transponder_id>`: Toggles the voice announcement setting for a specific car.
- `POST /api/nickname/<transponder_id>`: Updates the custom nickname for voice announcements for a specific car.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
