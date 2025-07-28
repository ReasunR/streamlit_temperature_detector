import threading
import time
import random
from typing import Dict, List
from datetime import datetime


class TemperatureStation:
    """
    Represents a temperature detection station that can run independently.
    Each station has its own thread and can be started/stopped independently.
    """
    
    def __init__(self, station_id: int, name: str, threshold_temp: float = 26.0):
        self.station_id = station_id
        self.name = name
        self.threshold_temp = threshold_temp
        self.is_running = False
        self.thread = None
        self.current_temperature = None
        self.temperature_history = []
        self.lock = threading.Lock()
        
    def start_detection(self):
        """Start the temperature detection for this station."""
        if not self.is_running:
            # Clear previous data when starting fresh
            with self.lock:
                self.temperature_history.clear()
                self.current_temperature = None
            
            self.is_running = True
            self.thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.thread.start()
            
    def stop_detection(self):
        """Stop the temperature detection for this station."""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _detection_loop(self):
        """
        Main detection loop that runs in a separate thread.
        Simulates temperature detection using random values.
        """
        while self.is_running:
            # Simulate temperature detection (20-30°C range with some variation)
            base_temp = 25.0
            temperature = base_temp + random.uniform(-5.0, 5.0)
            
            with self.lock:
                self.current_temperature = round(temperature, 2)
                timestamp = datetime.now()
                
                # Keep only last 100 readings to prevent memory issues
                self.temperature_history.append({
                    'timestamp': timestamp,
                    'temperature': self.current_temperature
                })
                if len(self.temperature_history) > 100:
                    self.temperature_history.pop(0)
            
            # Wait for 1 second before next reading
            time.sleep(1)
            
    def get_current_temperature(self):
        """Get the current temperature reading."""
        with self.lock:
            return self.current_temperature
            
    def get_temperature_history(self):
        """Get the temperature history for this station."""
        with self.lock:
            return self.temperature_history.copy()
            
    def get_status(self):
        """Get the current status of the station."""
        current_temp = self.get_current_temperature()
        return {
            'station_id': self.station_id,
            'name': self.name,
            'is_running': self.is_running,
            'current_temperature': current_temp,
            'readings_count': len(self.temperature_history),
            'threshold_temp': self.threshold_temp,
            'is_abnormal': current_temp is not None and current_temp > self.threshold_temp
        }
    
    def export_to_csv(self):
        """Export temperature history to CSV format."""
        import io
        import csv
        from datetime import datetime
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'Temperature_Celsius', 'Station_Name', 'Station_ID'])
        
        # Write data
        with self.lock:
            for reading in self.temperature_history:
                writer.writerow([
                    reading['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                    reading['temperature'],
                    self.name,
                    self.station_id
                ])
        
        return output.getvalue() 