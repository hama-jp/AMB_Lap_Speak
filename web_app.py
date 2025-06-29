#!/usr/bin/env python
from flask import Flask, render_template, jsonify, request
import mysql.connector
from datetime import datetime
import time
import threading
import numpy as np
import os
from AmbP3.voice_announcer import VoiceAnnouncer

# --- Initialization ---
app = Flask(__name__)
voice_announcer = VoiceAnnouncer(enabled=True, engine='auto')

# --- Database Configuration ---
DB_CONFIG = {
    'user': 'kart',
    'password': 'karts',
    'host': os.getenv('MYSQL_HOST', '127.0.0.1'),
    'port': 3306, # Docker uses the default port
    'database': 'karts'
}

def get_db_connection():
    """Establishes a new database connection."""
    return mysql.connector.connect(**DB_CONFIG)

# --- In-Memory Data Store ---
# These global variables will hold the entire state of the application.
all_laps_sorted = []  # A list of the most recent lap from each ponder, sorted by time.
ponder_data = {}      # A dictionary holding detailed statistics and history for each ponder.
data_lock = threading.Lock() # A lock to ensure thread-safe access to the data.
last_processed_rtc_time = 0 # The timestamp of the last processed record to avoid redundant work.


# --- Data Processing Logic ---
def calculate_stats(laps):
    """Calculates standard deviation and moving average for a list of lap times."""
    if not laps:
        return None, None
    
    std_dev = np.std(laps) if len(laps) > 1 else 0.0
    
    # Use all available laps for average if fewer than 10
    num_laps_for_avg = min(len(laps), 10)
    moving_avg = np.mean(laps[-num_laps_for_avg:])
        
    return std_dev, moving_avg

def update_data_from_db():
    """
    This function runs in a background thread.
    It periodically fetches ONLY NEW passes from the database and updates the in-memory store.
    """
    global last_processed_rtc_time
    print("Starting background data updater...")
    
    while True:
        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            # Fetch only records newer than the last one we processed.
            cursor.execute(
                "SELECT p.transponder_id, p.rtc_time, c.car_number, c.name "
                "FROM passes p LEFT JOIN cars c ON p.transponder_id = c.transponder_id "
                "WHERE p.rtc_time > %s ORDER BY p.rtc_time ASC",
                (last_processed_rtc_time,)
            )
            new_passes = cursor.fetchall()
            conn.close()

            if new_passes:
                with data_lock:
                    # The last pass in the fetched list is the most recent one.
                    last_processed_rtc_time = new_passes[-1]['rtc_time']

                    for p_pass in new_passes:
                        ponder_id = p_pass['transponder_id']
                        rtc_time = p_pass['rtc_time']

                        # Initialize a data structure for a ponder if it's the first time we see it.
                        if ponder_id not in ponder_data:
                            ponder_data[ponder_id] = {
                                'transponder_id': ponder_id,
                                'car_number': p_pass['car_number'] or 'Unknown',
                                'last_pass_time': None,
                                'laps': [],
                                'lap_history': [],
                                'best_lap': float('inf'),
                                'latest_lap': None,
                                'moving_avg_10': None,
                                'std_dev': None,
                                'voice_enabled': False, # Voice is off by default for all ponders.
                                'nickname': '' # Nickname for voice announcements
                            }
                        
                        pd = ponder_data[ponder_id]

                        # A lap is the time between two consecutive passes.
                        if pd['last_pass_time'] is not None:
                            lap_time = (rtc_time - pd['last_pass_time']) / 1000000.0
                            
                            # Filter out unrealistic lap times (e.g., pit stops, errors).
                            if 10.0 < lap_time < 300.0:
                                timestamp = datetime.fromtimestamp(rtc_time / 1000000.0)
                                
                                # Update the ponder's data with the new lap.
                                pd['laps'].append(lap_time)
                                std_dev, moving_avg = calculate_stats(pd['laps'])
                                pd['std_dev'] = std_dev
                                pd['moving_avg_10'] = moving_avg
                                pd['best_lap'] = min(pd['best_lap'], lap_time)
                                pd['latest_lap'] = lap_time

                                new_lap_record = {
                                    'lap_number': len(pd['laps']),
                                    'lap_time': lap_time,
                                    'timestamp': timestamp,
                                    'ponder_id': ponder_id,
                                    'car_number': pd['car_number']
                                }
                                pd['lap_history'].append(new_lap_record)

                                # Remove the old "latest lap" for this ponder from our sorted list.
                                global all_laps_sorted
                                all_laps_sorted = [l for l in all_laps_sorted if l['ponder_id'] != ponder_id]
                                # Add the new lap to the very top of the list.
                                all_laps_sorted.insert(0, new_lap_record)

                                # Announce the lap time if voice is enabled for this ponder.
                                if pd['voice_enabled']:
                                    # Use nickname if available, otherwise use car_number
                                    identifier = pd['nickname'] if pd['nickname'] else pd['car_number']
                                    # Format time in Japanese style: 12.24 -> "12秒24" (じゅうにびょう にーよん)
                                    seconds = int(lap_time)
                                    hundredths = int((lap_time - seconds) * 100)
                                    if hundredths > 0:
                                        announcement = f"{identifier}、{seconds}秒{hundredths:02d}"
                                    else:
                                        announcement = f"{identifier}、{seconds}秒"
                                    voice_announcer.announce(announcement)

                        # Update the last pass time to the current one for the next calculation.
                        pd['last_pass_time'] = rtc_time

        except Exception as e:
            print(f"Error in background thread: {e}")
        
        time.sleep(1) # Wait for 1 second before checking for new data again.

def initialize_data():
    """
    Pre-populates the in-memory data store on application startup.
    This function performs one large read to build the initial state.
    """
    global last_processed_rtc_time
    print("Initializing data from database...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT p.transponder_id, p.rtc_time, c.car_number, c.name "
            "FROM passes p LEFT JOIN cars c ON p.transponder_id = c.transponder_id "
            "ORDER BY p.rtc_time ASC"
        )
        all_passes = cursor.fetchall()
        conn.close()

        if not all_passes:
            print("No historical pass data found in the database.")
            return

        with data_lock:
            last_processed_rtc_time = all_passes[-1]['rtc_time']
            
            # Group all passes by their transponder ID first.
            passes_by_ponder = {}
            for p_pass in all_passes:
                ponder_id = p_pass['transponder_id']
                if ponder_id not in passes_by_ponder:
                    passes_by_ponder[ponder_id] = []
                passes_by_ponder[ponder_id].append(p_pass)

            # Process the history for each ponder.
            for ponder_id, passes in passes_by_ponder.items():
                if ponder_id not in ponder_data:
                     ponder_data[ponder_id] = {
                        'transponder_id': ponder_id, 'car_number': passes[0]['car_number'] or 'Unknown',
                        'last_pass_time': None, 'laps': [], 'lap_history': [], 'best_lap': float('inf'),
                        'latest_lap': None, 'moving_avg_10': None, 'std_dev': None, 'voice_enabled': False,
                        'nickname': ''
                    }
                pd = ponder_data[ponder_id]

                # Calculate all historical laps.
                for i in range(1, len(passes)):
                    lap_time = (passes[i]['rtc_time'] - passes[i-1]['rtc_time']) / 1000000.0
                    if 10.0 < lap_time < 300.0:
                        pd['laps'].append(lap_time)
                        pd['lap_history'].append({
                            'lap_number': len(pd['laps']), 'lap_time': lap_time,
                            'timestamp': datetime.fromtimestamp(passes[i]['rtc_time'] / 1000000.0),
                            'ponder_id': ponder_id, 'car_number': pd['car_number']
                        })
                
                # After processing all laps, calculate the final statistics.
                if pd['laps']:
                    std_dev, moving_avg = calculate_stats(pd['laps'])
                    pd['std_dev'] = std_dev
                    pd['moving_avg_10'] = moving_avg
                    pd['best_lap'] = min(pd['laps'])
                    pd['latest_lap'] = pd['laps'][-1]
                    
                    # Add its most recent lap to the global sorted list.
                    all_laps_sorted.append(pd['lap_history'][-1])

        # Finally, sort the list of latest laps by timestamp to ensure the newest is first.
        with data_lock:
            all_laps_sorted.sort(key=lambda x: x['timestamp'], reverse=True)
        print(f"Initialization complete. Loaded {len(all_laps_sorted)} final laps.")

    except Exception as e:
        print(f"Error during data initialization: {e}")


# --- Flask API Endpoints ---
@app.route('/')
def index():
    """Serves the main dashboard page."""
    return render_template('index.html')

@app.route('/laps/<int:transponder_id>')
def lap_details(transponder_id):
    """Serves the detail page for a single ponder."""
    return render_template('laps.html', transponder_id=transponder_id)

@app.route('/api/all_laps')
def api_all_laps():
    """API endpoint for the main page. Returns the sorted list of latest laps with all stats."""
    response_data = []
    with data_lock:
        for lap_record in all_laps_sorted:
            ponder_id = lap_record['ponder_id']
            pd = ponder_data.get(ponder_id)
            if pd:
                response_data.append({
                    'ponder_id': ponder_id,
                    'car_number': pd['car_number'],
                    'latest_lap_time': f"{pd['latest_lap']:.3f}" if pd['latest_lap'] is not None else '-',
                    'best_lap_time': f"{pd['best_lap']:.3f}" if pd['best_lap'] != float('inf') else '-',
                    'moving_avg_10': f"{pd['moving_avg_10']:.3f}" if pd['moving_avg_10'] is not None else '-',
                    'std_dev': f"{pd['std_dev']:.3f}" if pd['std_dev'] is not None else '-',
                    'timestamp': lap_record['timestamp'].strftime('%H:%M:%S'),
                    'voice_enabled': pd['voice_enabled'],
                    'nickname': pd['nickname']
                })
    return jsonify(response_data)

@app.route('/api/laps/<int:transponder_id>')
def api_lap_details(transponder_id):
    """API endpoint for the detail page. Returns all historical data for a single ponder."""
    with data_lock:
        data = ponder_data.get(transponder_id)
        if data:
            # Create a copy to avoid sending the raw 'laps' list, which can be large.
            response = {k: v for k, v in data.items() if k != 'laps'}
            return jsonify(response)
        else:
            return jsonify({'error': 'Transponder not found'}), 404

@app.route('/api/voice_toggle/<int:transponder_id>', methods=['POST'])
def api_voice_toggle(transponder_id):
    """API endpoint to toggle voice announcements for a specific ponder."""
    with data_lock:
        if transponder_id in ponder_data:
            data = request.get_json()
            new_state = data.get('enabled', False)
            ponder_data[transponder_id]['voice_enabled'] = new_state
            print(f"Set voice for ponder {transponder_id} to {new_state}")
            return jsonify({'status': 'success', 'new_state': new_state})
        else:
            return jsonify({'error': 'Transponder not found'}), 404

@app.route('/api/nickname/<int:transponder_id>', methods=['POST'])
def api_nickname_update(transponder_id):
    """API endpoint to update the nickname for a specific ponder."""
    with data_lock:
        if transponder_id in ponder_data:
            data = request.get_json()
            new_nickname = data.get('nickname', '')
            ponder_data[transponder_id]['nickname'] = new_nickname
            print(f"Set nickname for ponder {transponder_id} to '{new_nickname}'")
            return jsonify({'status': 'success', 'nickname': new_nickname})
        else:
            return jsonify({'error': 'Transponder not found'}), 404

# --- Main Execution ---
if __name__ == '__main__':
    initialize_data()
    # Start the background thread to fetch data continuously.
    # 'daemon=True' ensures the thread exits when the main app does.
    update_thread = threading.Thread(target=update_data_from_db, daemon=True)
    update_thread.start()
    # 'use_reloader=False' is important when running background threads with Flask's dev server.
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
