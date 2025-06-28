#!/usr/bin/env python
from flask import Flask, render_template, jsonify, request
import mysql.connector
from datetime import datetime
import time
import threading
from AmbP3.voice_announcer import VoiceAnnouncer, LapTimeMonitor

app = Flask(__name__)

# Initialize voice announcer with auto-detection of best engine
voice_announcer = VoiceAnnouncer(enabled=True, engine='auto')
lap_monitor = LapTimeMonitor(voice_announcer)

# Database configuration from conf.yaml
DB_CONFIG = {
    'user': 'kart',
    'password': 'karts',
    'host': '127.0.0.1',
    'port': 3307,
    'database': 'karts'
}

def get_db_connection():
    """Get MySQL database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def get_recent_passes(limit=50):
    """Get recent transponder passes"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
    SELECT 
        p.transponder_id,
        p.rtc_time,
        p.strength,
        p.decoder_id,
        c.car_number,
        c.name
    FROM passes p
    LEFT JOIN cars c ON p.transponder_id = c.transponder_id
    ORDER BY p.rtc_time DESC
    LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    
    passes = []
    for row in results:
        # Convert RTC time (microseconds) to readable format
        rtc_time_seconds = row[1] / 1000000
        timestamp = datetime.fromtimestamp(rtc_time_seconds)
        
        passes.append({
            'transponder_id': row[0],
            'time': timestamp.strftime('%H:%M:%S.%f')[:-3],  # Show milliseconds
            'raw_time': row[1],
            'strength': row[2],
            'decoder_id': row[3],
            'car_number': row[4] if row[4] else 'Unknown',
            'driver_name': row[5] if row[5] else 'Unknown'
        })
    
    conn.close()
    return passes

def calculate_lap_times():
    """Calculate lap times for each transponder"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get passes grouped by transponder, ordered by time
    query = """
    SELECT 
        p.transponder_id,
        p.rtc_time,
        c.car_number,
        c.name,
        p.strength
    FROM passes p
    LEFT JOIN cars c ON p.transponder_id = c.transponder_id
    ORDER BY p.transponder_id, p.rtc_time
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Group by transponder and calculate lap times
    transponder_data = {}
    for row in results:
        transponder_id = row[0]
        rtc_time = row[1]
        car_number = row[2] if row[2] else 'Unknown'
        driver_name = row[3] if row[3] else 'Unknown'
        strength = row[4]
        
        if transponder_id not in transponder_data:
            transponder_data[transponder_id] = {
                'car_number': car_number,
                'driver_name': driver_name,
                'passes': [],
                'laps': [],
                'best_lap': None,
                'last_lap': None,
                'lap_count': 0
            }
        
        transponder_data[transponder_id]['passes'].append({
            'time': rtc_time,
            'strength': strength
        })
    
    # Calculate lap times
    for transponder_id, data in transponder_data.items():
        passes = data['passes']
        if len(passes) > 1:
            for i in range(1, len(passes)):
                lap_time = (passes[i]['time'] - passes[i-1]['time']) / 1000000  # Convert to seconds
                
                # Filter reasonable lap times (between 10 seconds and 5 minutes)
                if 10 <= lap_time <= 300:
                    lap_data = {
                        'lap_number': len(data['laps']) + 1,
                        'time': lap_time,
                        'formatted_time': format_lap_time(lap_time),
                        'timestamp': datetime.fromtimestamp(passes[i]['time'] / 1000000)
                    }
                    
                    data['laps'].append(lap_data)
                    data['last_lap'] = lap_data
                    data['lap_count'] = len(data['laps'])
                    
                    # Update best lap
                    if data['best_lap'] is None or lap_time < data['best_lap']['time']:
                        data['best_lap'] = lap_data
    
    conn.close()
    return transponder_data

def format_lap_time(seconds):
    """Format lap time as MM:SS.mmm"""
    minutes = int(seconds // 60)
    remaining_seconds = seconds % 60
    return f"{minutes}:{remaining_seconds:06.3f}"

@app.route('/')
def index():
    """Main page showing live lap times"""
    return render_template('index.html')

@app.route('/api/lap_times')
def api_lap_times():
    """API endpoint for current lap times (max 16 karts)"""
    try:
        lap_data = calculate_lap_times()
        
        # Convert to list and include karts with recent activity (even if no completed laps)
        results = []
        for transponder_id, data in lap_data.items():
            # Show karts that have completed laps OR have recent activity (within last 5 minutes)
            last_pass_time = None
            if data['passes']:
                last_pass_time = data['passes'][-1]['time']
                time_since_last = (time.time() * 1000000 - last_pass_time) / 1000000  # seconds
                
            show_kart = (data['lap_count'] > 0 or 
                        (last_pass_time and time_since_last < 300))  # 5 minutes
            
            if show_kart:
                results.append({
                    'transponder_id': transponder_id,
                    'car_number': data['car_number'],
                    'driver_name': data['driver_name'],
                    'lap_count': data['lap_count'],
                    'last_lap_time': data['last_lap']['formatted_time'] if data['last_lap'] else '-',
                    'best_lap_time': data['best_lap']['formatted_time'] if data['best_lap'] else '-',
                    'last_activity': data['last_lap']['timestamp'].strftime('%H:%M:%S') if data['last_lap'] else 
                                   (datetime.fromtimestamp(last_pass_time / 1000000).strftime('%H:%M:%S') if last_pass_time else '-'),
                    'status': 'Racing' if data['lap_count'] > 0 else 'On Track'
                })
        
        # Sort by lap count (desc), then by best lap time (asc), then by recent activity
        results.sort(key=lambda x: (
            -x['lap_count'],  # More laps first
            999999 if x['best_lap_time'] == '-' else float(x['best_lap_time'].replace(':', '')) if ':' in str(x['best_lap_time']) else 999999,  # Best lap time
            x['last_activity'] if x['last_activity'] != '-' else '00:00:00'
        ), reverse=True)
        
        # Limit to 16 cars maximum
        results = results[:16]
        
        # Update lap monitor for voice announcements
        lap_monitor.update_lap_data(results)
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent_passes')
def api_recent_passes():
    """API endpoint for recent transponder passes"""
    try:
        passes = get_recent_passes(20)
        return jsonify(passes)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/settings', methods=['GET', 'POST'])
def api_voice_settings():
    """API endpoint for voice settings"""
    if request.method == 'GET':
        # Get current settings with fallback values
        volume = 0.9
        rate = 150
        
        if voice_announcer.engine and hasattr(voice_announcer.engine, 'getProperty'):
            try:
                volume = voice_announcer.engine.getProperty('volume')
                rate = voice_announcer.engine.getProperty('rate')
            except:
                pass
        
        return jsonify({
            'enabled': voice_announcer.enabled,
            'volume': volume,
            'rate': rate,
            'engine_type': voice_announcer.engine_type
        })
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if 'enabled' in data:
                voice_announcer.set_enabled(data['enabled'])
            
            if 'volume' in data:
                voice_announcer.set_volume(data['volume'])
            
            if 'rate' in data:
                voice_announcer.set_rate(data['rate'])
            
            return jsonify({'status': 'success'})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

@app.route('/api/voice/test', methods=['POST'])
def api_voice_test():
    """Test voice announcement"""
    try:
        voice_announcer.test_voice()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/announce', methods=['POST'])
def api_voice_announce():
    """Manual voice announcement"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if text:
            voice_announcer.announce(text)
            return jsonify({'status': 'success'})
        else:
            return jsonify({'error': 'No text provided'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/race/reset', methods=['POST'])
def api_race_reset():
    """Reset race state"""
    try:
        lap_monitor.reset_race()
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/announce_all', methods=['POST'])
def api_announce_all_times():
    """Announce all cars' current times"""
    try:
        # Get current lap data
        lap_data = calculate_lap_times()
        
        # Convert to list format expected by lap monitor
        results = []
        for transponder_id, data in lap_data.items():
            if data['lap_count'] > 0:  # Only include cars with completed laps
                results.append({
                    'transponder_id': transponder_id,
                    'car_number': data['car_number'],
                    'lap_count': data['lap_count'],
                    'best_lap_time': data['best_lap']['formatted_time'] if data['best_lap'] else '-'
                })
        
        # Sort by lap count and best time (same as main API)
        results.sort(key=lambda x: (
            -x['lap_count'],
            999999 if x['best_lap_time'] == '-' else float(x['best_lap_time'].replace(':', '')) if ':' in str(x['best_lap_time']) else 999999
        ), reverse=True)
        
        # Trigger announcement
        lap_monitor._announce_all_times(results)
        
        return jsonify({'status': 'success', 'cars_announced': len(results)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/voice/announcement_settings', methods=['GET', 'POST'])
def api_announcement_settings():
    """API endpoint for voice announcement settings"""
    if request.method == 'GET':
        settings = lap_monitor.get_announcement_settings()
        return jsonify(settings)
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            announce_car_numbers = data.get('announce_car_numbers', False)
            announce_lap_numbers = data.get('announce_lap_numbers', False)
            announce_all_times_enabled = data.get('announce_all_times_enabled', False)
            
            lap_monitor.set_announcement_mode(
                announce_car_numbers=announce_car_numbers,
                announce_lap_numbers=announce_lap_numbers,
                announce_all_times_enabled=announce_all_times_enabled
            )
            
            return jsonify({'status': 'success'})
        
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)