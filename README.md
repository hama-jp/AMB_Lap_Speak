# AMB Lap Speak - Real-time Kart Racing Timing System

A Python-based timing system for AMB (Amsterdam Micro Broadcasting) P3 decoders with a live web interface for real-time lap timing display.

## Features

- 🏁 **Real-time Lap Timing**: Connect to AMB P3 decoders and track transponder passes
- 📊 **Live Web Dashboard**: Real-time web interface displaying current lap times for up to 16 karts
- 🗄️ **MySQL Database**: Persistent storage of all timing data (passes, laps, heats, kart mappings)
- ⏱️ **Automatic Lap Calculation**: Intelligent lap time calculation with filtering for valid laps
- 🔄 **Auto-refresh Interface**: Web dashboard updates every 2 seconds
- 📱 **Responsive Design**: Mobile-friendly interface for trackside use
- 🏆 **Race Management**: Track best lap times, lap counts, and driver positions

## System Requirements

- Python 3.7+
- MySQL 5.7+ or Docker
- AMB P3 Decoder with network connectivity
- Modern web browser

## Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/hama-jp/AMB_Lap_Speak.git
cd AMB_Lap_Speak
```

### 2. Setup Virtual Environment

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

# Install Flask for web interface
uv pip install flask
```

### 3. Setup MySQL Database

#### Option A: Using Docker (Recommended)

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

#### Option B: Using Local MySQL

```bash
# Install MySQL server (Ubuntu/Debian)
sudo apt update && sudo apt install mysql-server

# Create database and user
mysql -u root -p << EOF
CREATE DATABASE karts;
CREATE USER 'kart'@'localhost' IDENTIFIED BY 'karts';
GRANT ALL PRIVILEGES ON karts.* TO 'kart'@'localhost';
FLUSH PRIVILEGES;
EOF

# Load schema
mysql -u kart -pkarts karts < schema

# Update conf.yaml to use local MySQL
sed -i 's/mysql_port: 3307/mysql_port: 3306/' conf.yaml
```

### 4. Configure AMB Decoder

Edit `conf.yaml` with your AMB decoder settings:

```yaml
---
ip: '192.168.1.21'    # Your AMB decoder IP
port: 5403            # AMB decoder port (default 5403)
file: "/tmp/out.log"
debug_file: "/tmp/amb_raw.log"
mysql_backend: True
mysql_host: '127.0.0.1'
mysql_port: 3307      # 3306 for local MySQL
mysql_db: 'karts'
mysql_user: 'kart'
mysql_password: 'karts'
```

### 5. Add Kart Information (Optional)

Add your kart and driver mappings to the database:

```bash
# Activate virtual environment
source .venv/bin/activate

# Add kart data
python -c "
from AmbP3.write import open_mysql_connection
conn = open_mysql_connection(user='kart', db='karts', password='karts', host='127.0.0.1', port=3307)
cursor = conn.cursor()

# Add your karts (kart_number, transponder_id, driver_name)
karts = [
    (1, 4000822, 'Driver A'),
    (2, 4000823, 'Driver B'),
    (3, 4000824, 'Driver C'),
    # Add more karts as needed
]

for kart_number, transponder_id, name in karts:
    cursor.execute('INSERT IGNORE INTO karts (kart_number, transponder_id, name) VALUES (%s, %s, %s)', 
                   (kart_number, transponder_id, name))

conn.commit()
conn.close()
print('Kart data added successfully')
"
```

## Running the System

### 1. Start AMB Client (Data Collection)

```bash
source .venv/bin/activate
python amb_client.py
```

This will:
- Connect to your AMB decoder
- Start receiving transponder data
- Store passes and calculate lap times in MySQL
- Display raw protocol data and any errors

### 2. Start Web Interface

In a new terminal:

```bash
source .venv/bin/activate
python web_app.py
```

Access the web interface at: **http://localhost:5000**

## Web Interface Features

### Live Timing Display
- **Position**: Current standing based on lap count and best lap time
- **Car Number**: Configured car number from database
- **Driver Name**: Driver name from database
- **Status**: Racing (completed laps) or On Track (recent activity)
- **Lap Count**: Total completed laps
- **Last Lap Time**: Most recent lap time
- **Best Lap Time**: Fastest lap time (highlighted in green)
- **Last Activity**: Time of most recent transponder pass

### Recent Passes
- Real-time feed of transponder detections
- Shows transponder ID, signal strength, and timestamp
- Automatically scrolls to show latest activity

### Auto-refresh
- Updates every 2 seconds
- Live status indicator shows connection health
- Displays up to 16 karts simultaneously

## Database Schema

The system uses 5 main tables:

- **passes**: Raw transponder readings from AMB decoder
- **laps**: Validated lap times within race sessions
- **heats**: Race session management
- **karts**: Transponder to kart/driver mapping
- **settings**: Runtime configuration storage

## Troubleshooting

### AMB Decoder Connection Issues

```bash
# Test direct connection to decoder
python -c "
from AmbP3.decoder import Connection
conn = Connection('192.168.1.21', 5403)  # Use your IP
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

### Check System Status

```bash
# View recent timing data
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

## Architecture

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
```

## Development

### Code Quality

```bash
# Run linter
flake8
```

### File Structure

```
AMB_Lap_Speak/
├── AmbP3/                 # Core timing system package
│   ├── config.py         # Configuration management
│   ├── decoder.py        # AMB P3 protocol handling
│   ├── records.py        # Protocol message definitions
│   ├── write.py          # Database operations
│   └── ...
├── templates/            # Web interface templates
│   └── index.html       # Main dashboard
├── amb_client.py        # Main timing client
├── web_app.py          # Flask web application
├── conf.yaml           # Configuration file
├── schema              # MySQL database schema
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Related Projects

- [AMB Web](https://github.com/vmindru/ambweb) - Alternative web interface
- [AMB Docker](https://github.com/br0ziliy/amb-docker) - Docker deployment

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in `/tmp/out.log` and `/tmp/amb_raw.log`
3. Open an issue on GitHub with detailed error information

---

**Happy RC Racing! 🏎️**