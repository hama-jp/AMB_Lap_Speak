#!/usr/bin/env python
"""
Voice announcer module for RC car lap timing
Provides text-to-speech functionality for lap time announcements
Supports multiple TTS engines: pyttsx3, gTTS, and espeak
"""

import threading
import queue
import time
import os
import tempfile
from datetime import datetime
from .logs import Logg

# Import TTS engines with fallbacks
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    from gtts import gTTS
    import pygame
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

logger = Logg.create_logger('voice_announcer')

class VoiceAnnouncer:
    """Handles voice announcements for lap timing events"""
    
    def __init__(self, enabled=True, engine='auto'):
        self.enabled = enabled
        self.engine_type = engine  # 'auto', 'pyttsx3', 'gtts', 'espeak'
        self.engine = None
        self.announcement_queue = queue.Queue()
        self.worker_thread = None
        self.running = False
        self.pygame_initialized = False
        
        if self.enabled:
            self._initialize_engine()
            self._start_worker()
    
    def _initialize_engine(self):
        """Initialize the text-to-speech engine"""
        if self.engine_type == 'auto':
            # Try engines in order of preference for Japanese
            if GTTS_AVAILABLE:
                self.engine_type = 'gtts'
            elif PYTTSX3_AVAILABLE:
                self.engine_type = 'pyttsx3'
            else:
                self.engine_type = 'espeak'
        
        try:
            if self.engine_type == 'gtts' and GTTS_AVAILABLE:
                self._initialize_gtts()
            elif self.engine_type == 'pyttsx3' and PYTTSX3_AVAILABLE:
                self._initialize_pyttsx3()
            elif self.engine_type == 'espeak':
                self._initialize_espeak()
            else:
                logger.warning("No TTS engine available, running in log-only mode")
                self.engine = None
                
        except Exception as e:
            logger.error(f"TTS engine initialization failed (running in log-only mode): {e}")
            self.engine = None
    
    def _initialize_gtts(self):
        """Initialize Google TTS engine (best for Japanese)"""
        try:
            # Initialize pygame for audio playback
            pygame.mixer.init()
            self.pygame_initialized = True
            self.engine = 'gtts'
            logger.info("Using Google TTS engine (gTTS) for Japanese speech")
        except Exception as e:
            logger.error(f"Failed to initialize gTTS/pygame: {e}")
            raise
    
    def _initialize_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        self.engine = pyttsx3.init()
        
        # Configure voice settings
        self.engine.setProperty('rate', 150)    # Speaking rate (words per minute)
        self.engine.setProperty('volume', 0.9)  # Volume level (0.0 to 1.0)
        
        # Try to set a Japanese voice if available
        voices = self.engine.getProperty('voices')
        if voices:
            for voice in voices:
                if 'japan' in voice.name.lower() or 'ja' in voice.id.lower():
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Using Japanese voice: {voice.name}")
                    break
            else:
                logger.info("Using default voice (Japanese voice not found)")
        else:
            logger.warning("No voices available in pyttsx3")
        
        logger.info("Using pyttsx3 TTS engine")
    
    def _initialize_espeak(self):
        """Initialize espeak as fallback"""
        # Test if espeak is available
        result = os.system('espeak --version >/dev/null 2>&1')
        if result != 0:
            logger.warning("espeak not available, installing...")
            os.system('sudo apt-get update && sudo apt-get install -y espeak espeak-data')
        
        self.engine = 'espeak'
        logger.info("Using espeak TTS engine")
    
    def _start_worker(self):
        """Start the background worker thread for announcements"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Voice announcer worker thread started")
    
    def _worker(self):
        """Background worker that processes announcement queue"""
        while self.running:
            try:
                # Get announcement from queue (blocking with timeout)
                announcement = self.announcement_queue.get(timeout=1.0)
                
                if announcement is None:  # Shutdown signal
                    break
                
                # Speak the announcement
                logger.info(f"🔊 VOICE: {announcement}")
                if self.engine:
                    self._speak_text(announcement)
                else:
                    logger.info("(Voice engine not available - announcement logged only)")
                
                self.announcement_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in voice announcer worker: {e}")
    
    def _speak_text(self, text):
        """Speak text using the configured engine"""
        try:
            if self.engine == 'gtts':
                self._speak_gtts(text)
            elif hasattr(self.engine, 'say'):  # pyttsx3
                self.engine.say(text)
                self.engine.runAndWait()
            elif self.engine == 'espeak':
                self._speak_espeak(text)
            else:
                logger.warning(f"Unknown engine type: {self.engine}")
        except Exception as e:
            logger.error(f"Error speaking text '{text}': {e}")
    
    def _speak_gtts(self, text):
        """Speak text using Google TTS"""
        try:
            # Create TTS object
            tts = gTTS(text=text, lang='ja', slow=False)
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
                tts.save(tmp_file.name)
                
                # Play audio file
                pygame.mixer.music.load(tmp_file.name)
                pygame.mixer.music.play()
                
                # Wait for playback to complete
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
                
                # Clean up
                os.unlink(tmp_file.name)
                
        except Exception as e:
            logger.error(f"Error with gTTS speech: {e}")
            # Fallback to espeak if gTTS fails
            self._speak_espeak(text)
    
    def _speak_espeak(self, text):
        """Speak text using espeak"""
        try:
            # Use espeak with Japanese phonemes if possible
            # Escape quotes in text
            safe_text = text.replace('"', '\"')
            cmd = f'espeak -v ja "{safe_text}"'
            os.system(cmd)
        except Exception as e:
            logger.error(f"Error with espeak speech: {e}")
    
    def announce(self, text):
        """Add an announcement to the queue"""
        if not self.enabled:
            return
        
        try:
            # Add to queue (non-blocking)
            self.announcement_queue.put_nowait(text)
            logger.debug(f"Queued announcement: {text}")
        except queue.Full:
            logger.warning("Announcement queue is full, skipping announcement")
    
    def announce_lap_time(self, car_number, lap_number, lap_time_seconds, is_best=False, simple_mode=True):
        """Announce a lap time completion"""
        try:
            # Format lap time
            minutes = int(lap_time_seconds // 60)
            seconds = lap_time_seconds % 60
            
            if minutes > 0:
                time_text = f"{minutes}分{seconds:.3f}秒"
            else:
                time_text = f"{seconds:.3f}秒"
            
            # Create announcement text based on mode
            if simple_mode:
                # Simple mode: only announce time and best lap indicator
                if is_best:
                    announcement = f"{time_text}、ベストラップ！"
                else:
                    announcement = time_text
            else:
                # Detailed mode: include lap number
                if is_best:
                    announcement = f"{lap_number}ラップ、{time_text}、ベストラップ！"
                else:
                    announcement = f"{lap_number}ラップ、{time_text}"
            
            self.announce(announcement)
            
        except Exception as e:
            logger.error(f"Error creating lap time announcement: {e}")
    
    def announce_race_start(self):
        """Announce race start"""
        self.announce("レース開始！")
    
    def announce_race_finish(self):
        """Announce race finish"""
        self.announce("レース終了！")
    
    def announce_best_lap(self, car_number, lap_time_seconds):
        """Announce new best lap"""
        try:
            minutes = int(lap_time_seconds // 60)
            seconds = lap_time_seconds % 60
            
            if minutes > 0:
                time_text = f"{minutes}分{seconds:.3f}秒"
            else:
                time_text = f"{seconds:.3f}秒"
            
            announcement = f"新記録！{time_text}"
            self.announce(announcement)
            
        except Exception as e:
            logger.error(f"Error creating best lap announcement: {e}")
    
    def announce_position_change(self, car_number, new_position):
        """Announce position change"""
        position_text = ["", "1位", "2位", "3位", "4位", "5位", "6位", "7位", "8位"]
        
        if 1 <= new_position <= 8:
            announcement = f"{position_text[new_position]}に上がりました！"
            self.announce(announcement)
    
    def set_enabled(self, enabled):
        """Enable or disable voice announcements"""
        self.enabled = enabled
        if enabled and self.engine is None:
            self._initialize_engine()
            if not self.running:
                self._start_worker()
        logger.info(f"Voice announcer {'enabled' if enabled else 'disabled'}")
    
    def set_volume(self, volume):
        """Set voice volume (0.0 to 1.0)"""
        if self.engine and hasattr(self.engine, 'setProperty'):
            self.engine.setProperty('volume', max(0.0, min(1.0, volume)))
            logger.info(f"Voice volume set to {volume}")
        elif self.engine == 'gtts' and self.pygame_initialized:
            # For gTTS/pygame, adjust system volume
            pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
            logger.info(f"Voice volume set to {volume} (pygame)")
        else:
            logger.info(f"Volume control not available for engine type: {self.engine_type}")
    
    def set_rate(self, rate):
        """Set speaking rate (words per minute)"""
        if self.engine and hasattr(self.engine, 'setProperty'):
            self.engine.setProperty('rate', max(50, min(300, rate)))
            logger.info(f"Voice rate set to {rate} WPM")
        else:
            logger.info(f"Rate control not available for engine type: {self.engine_type}")
    
    def test_voice(self):
        """Test voice announcement"""
        self.announce("音声テスト。RCカータイマーシステムが正常に動作しています。")
    
    def shutdown(self):
        """Shutdown the voice announcer"""
        logger.info("Shutting down voice announcer")
        self.running = False
        
        if self.worker_thread and self.worker_thread.is_alive():
            # Send shutdown signal
            self.announcement_queue.put(None)
            self.worker_thread.join(timeout=5.0)
        
        if self.engine:
            try:
                if hasattr(self.engine, 'stop'):
                    self.engine.stop()
                elif self.pygame_initialized:
                    pygame.mixer.quit()
            except:
                pass


class LapTimeMonitor:
    """Monitors lap times and triggers voice announcements"""
    
    def __init__(self, announcer, min_lap_time=10.0, max_lap_time=300.0):
        self.announcer = announcer
        self.min_lap_time = min_lap_time  # Minimum valid lap time (seconds)
        self.max_lap_time = max_lap_time  # Maximum valid lap time (seconds)
        
        # Track previous state for each car
        self.car_states = {}
        self.race_started = False
        self.last_all_times_announcement = 0  # Track when we last announced all times
        self.all_times_interval = 30  # Announce all times every 30 seconds
        
        # Voice announcement settings (defaults to simple mode)
        self.announce_car_numbers = False  # Default: don't announce car numbers
        self.announce_lap_numbers = False  # Default: don't announce lap numbers  
        self.announce_all_times_enabled = False  # Default: disable periodic all-times announcements
        
        logger.info(f"Lap time monitor initialized (min: {min_lap_time}s, max: {max_lap_time}s)")
    
    def update_lap_data(self, lap_data):
        """Update with new lap data and trigger announcements"""
        try:
            # Check if this is the start of a race
            if not self.race_started and lap_data:
                self.race_started = True
                self.announcer.announce_race_start()
            
            for car_info in lap_data:
                car_number = car_info.get('car_number', 'Unknown')
                transponder_id = car_info.get('transponder_id')
                
                if car_number == 'Unknown' or not transponder_id:
                    continue
                
                # Get current state
                lap_count = car_info.get('lap_count', 0)
                last_lap_time = car_info.get('last_lap_time', '-')
                best_lap_time = car_info.get('best_lap_time', '-')
                
                # Get previous state
                prev_state = self.car_states.get(transponder_id, {})
                prev_lap_count = prev_state.get('lap_count', 0)
                prev_best_lap = prev_state.get('best_lap_time', '-')
                
                # Check for new lap completion
                if lap_count > prev_lap_count and last_lap_time != '-':
                    try:
                        # Parse lap time
                        lap_time_seconds = self._parse_lap_time(last_lap_time)
                        
                        if self.min_lap_time <= lap_time_seconds <= self.max_lap_time:
                            # Check if this is a new best lap
                            is_best = (best_lap_time != '-' and 
                                      prev_best_lap != best_lap_time and 
                                      best_lap_time == last_lap_time)
                            
                            # Announce the lap (using simple mode by default)
                            self.announcer.announce_lap_time(
                                car_number, lap_count, lap_time_seconds, is_best, simple_mode=True
                            )
                            
                            logger.info(f"Car {car_number} completed lap {lap_count}: {lap_time_seconds:.3f}s")
                        
                    except ValueError as e:
                        logger.warning(f"Could not parse lap time '{last_lap_time}': {e}")
                
                # Update state
                self.car_states[transponder_id] = {
                    'car_number': car_number,
                    'lap_count': lap_count,
                    'last_lap_time': last_lap_time,
                    'best_lap_time': best_lap_time
                }
            
            # Check if it's time to announce all cars' times (only if enabled)
            current_time = time.time()
            if (self.announce_all_times_enabled and 
                current_time - self.last_all_times_announcement > self.all_times_interval and 
                len(lap_data) > 0 and self.race_started):
                self._announce_all_times(lap_data)
                self.last_all_times_announcement = current_time
                
        except Exception as e:
            logger.error(f"Error in lap time monitor update: {e}")
    
    def _announce_all_times(self, lap_data):
        """Announce all cars' current times"""
        try:
            # Filter cars that have completed at least one lap and sort by position
            active_cars = [car for car in lap_data if car.get('lap_count', 0) > 0]
            
            if not active_cars:
                return
            
            # Sort by lap count (desc) then by best lap time (asc)
            active_cars.sort(key=lambda x: (
                -x.get('lap_count', 0),
                999999 if x.get('best_lap_time', '-') == '-' else self._parse_lap_time_safe(x.get('best_lap_time', '-'))
            ))
            
            # Create announcement for all cars
            announcements = []
            for i, car in enumerate(active_cars[:8]):  # Announce top 8 cars
                position = i + 1
                lap_count = car.get('lap_count', 0)
                best_lap = car.get('best_lap_time', '-')
                
                if best_lap != '-':
                    # Format the time nicely for speech
                    try:
                        lap_seconds = self._parse_lap_time(best_lap)
                        minutes = int(lap_seconds // 60)
                        seconds = lap_seconds % 60
                        
                        if minutes > 0:
                            time_text = f"{minutes}分{seconds:.1f}秒"
                        else:
                            time_text = f"{seconds:.1f}秒"
                        
                        announcements.append(f"{position}位、{lap_count}ラップ、ベスト{time_text}")
                    except:
                        announcements.append(f"{position}位、{lap_count}ラップ")
                else:
                    announcements.append(f"{position}位、{lap_count}ラップ")
            
            if announcements:
                full_announcement = "現在の順位、" + "、".join(announcements)
                self.announcer.announce(full_announcement)
                logger.info(f"Announced all times: {len(announcements)} cars")
                
        except Exception as e:
            logger.error(f"Error announcing all times: {e}")
    
    def _parse_lap_time_safe(self, lap_time_str):
        """Safely parse lap time string, return high number if invalid"""
        try:
            return self._parse_lap_time(lap_time_str)
        except:
            return 999999
    
    def _parse_lap_time(self, lap_time_str):
        """Parse lap time string to seconds (format: 'M:SS.mmm')"""
        if lap_time_str == '-':
            raise ValueError("Invalid lap time")
        
        parts = lap_time_str.split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            return float(lap_time_str)
    
    def reset_race(self):
        """Reset race state"""
        self.car_states.clear()
        self.race_started = False
        self.last_all_times_announcement = 0  # Reset timer
        logger.info("Race state reset")
    
    def set_announcement_mode(self, announce_car_numbers=False, announce_lap_numbers=False, 
                             announce_all_times_enabled=False):
        """Set voice announcement preferences"""
        self.announce_car_numbers = announce_car_numbers
        self.announce_lap_numbers = announce_lap_numbers
        self.announce_all_times_enabled = announce_all_times_enabled
        
        mode_desc = []
        if announce_car_numbers:
            mode_desc.append("car numbers")
        if announce_lap_numbers:
            mode_desc.append("lap numbers")
        if announce_all_times_enabled:
            mode_desc.append("periodic all-times")
        
        if mode_desc:
            logger.info(f"Voice announcement mode updated: {', '.join(mode_desc)} enabled")
        else:
            logger.info("Voice announcement mode: simple (time only)")
    
    def get_announcement_settings(self):
        """Get current announcement settings"""
        return {
            'announce_car_numbers': self.announce_car_numbers,
            'announce_lap_numbers': self.announce_lap_numbers,
            'announce_all_times_enabled': self.announce_all_times_enabled,
            'all_times_interval': self.all_times_interval
        }