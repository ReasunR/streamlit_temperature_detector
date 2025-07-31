import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout,
                             QScrollArea, QFileDialog, QMessageBox)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime
from temperature_station import TemperatureStation


class TemperatureChart(FigureCanvas):
    """Custom matplotlib widget for temperature charts"""
    
    def __init__(self, station_name):
        self.figure = Figure(figsize=(6, 4), dpi=80)
        super().__init__(self.figure)
        self.station_name = station_name
        self.ax = self.figure.add_subplot(111)
        self.setup_chart()
        
    def setup_chart(self):
        """Initialize the chart appearance"""
        self.ax.set_title(f'{self.station_name} Temperature Trend', fontsize=12, fontweight='bold')
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Temperature (°C)')
        self.ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        
    def update_chart(self, history, threshold_temp):
        """Update the chart with new data"""
        self.ax.clear()
        self.setup_chart()
        
        if history and len(history) > 0:
            # Prepare data
            times = [reading['timestamp'] for reading in history]
            temperatures = [reading['temperature'] for reading in history]
            
            # Plot temperature line
            self.ax.plot(times, temperatures, 'b-', linewidth=2, label='Temperature')
            
            # Add threshold line
            if times:
                self.ax.axhline(y=threshold_temp, color='red', linestyle='--', 
                               label=f'Threshold: {threshold_temp}°C')
            
            # Format x-axis for time display
            self.ax.tick_params(axis='x', rotation=45)
            
            # Set y-axis limits with some padding
            if temperatures:
                min_temp = min(temperatures)
                max_temp = max(temperatures)
                padding = (max_temp - min_temp) * 0.1 if max_temp != min_temp else 1
                self.ax.set_ylim(min_temp - padding, max_temp + padding)
        else:
            # Show empty chart with message
            self.ax.text(0.5, 0.5, 'No data available\nStart station to see trends', 
                        transform=self.ax.transAxes, ha='center', va='center',
                        fontsize=12, alpha=0.6)
            
        self.figure.tight_layout()
        self.draw()


class StationWidget(QWidget):
    """Widget representing a single temperature station"""
    
    def __init__(self, station):
        super().__init__()
        self.station = station
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the UI for this station"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        
        # Station title
        title = QLabel(f"🔬 {self.station.name}")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Start")
        self.stop_btn = QPushButton("⏹️ Stop")
        
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        self.start_btn.clicked.connect(self.start_station)
        self.stop_btn.clicked.connect(self.stop_station)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        layout.addLayout(button_layout)
        
        # Status indicator
        self.status_label = QLabel("🔴 Inactive")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.status_label)
        
        # Current temperature display
        self.temp_label = QLabel("Current Temperature")
        self.temp_label.setAlignment(Qt.AlignCenter)
        self.temp_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.temp_label)
        
        self.temp_value = QLabel("No data")
        self.temp_value.setAlignment(Qt.AlignCenter)
        self.temp_value.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(self.temp_value)
        
        # Temperature status
        self.temp_status = QLabel("")
        self.temp_status.setAlignment(Qt.AlignCenter)
        self.temp_status.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self.temp_status)
        
        # Readings count
        self.readings_label = QLabel("Total readings: 0")
        self.readings_label.setAlignment(Qt.AlignCenter)
        self.readings_label.setFont(QFont("Arial", 9))
        layout.addWidget(self.readings_label)
        
        # CSV Export button
        self.export_btn = QPushButton("💾 Save CSV")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.export_btn.clicked.connect(self.export_csv)
        self.export_btn.setEnabled(False)
        layout.addWidget(self.export_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)
        
        # Chart section
        chart_label = QLabel("📈 Temperature History")
        chart_label.setAlignment(Qt.AlignCenter)
        chart_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(chart_label)
        
        # Temperature chart
        self.chart = TemperatureChart(self.station.name)
        layout.addWidget(self.chart)
        
        # Statistics
        stats_layout = QHBoxLayout()
        self.avg_label = QLabel("Avg\n--°C")
        self.min_label = QLabel("Min\n--°C")
        self.max_label = QLabel("Max\n--°C")
        
        for label in [self.avg_label, self.min_label, self.max_label]:
            label.setAlignment(Qt.AlignCenter)
            label.setFont(QFont("Arial", 9))
            label.setStyleSheet("""
                QLabel {
                    border: 1px solid #ddd;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #f9f9f9;
                }
            """)
            stats_layout.addWidget(label)
        
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            StationWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }
        """)
        
    def start_station(self):
        """Start the temperature station"""
        self.station.start_detection()
        
    def stop_station(self):
        """Stop the temperature station"""
        self.station.stop_detection()
        
    def export_csv(self):
        """Export temperature data to CSV"""
        if self.station.get_status()['readings_count'] > 0:
            filename = f"{self.station.name.replace(' ', '_')}_temperature_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save Temperature Data", 
                filename, 
                "CSV Files (*.csv)"
            )
            
            if file_path:
                try:
                    csv_data = self.station.export_to_csv()
                    with open(file_path, 'w') as f:
                        f.write(csv_data)
                    QMessageBox.information(self, "Success", f"Data exported to {file_path}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to export data: {str(e)}")
        
    def update_display(self):
        """Update the display with current station data"""
        status = self.station.get_status()
        
        # Update status indicator
        if status['is_running']:
            self.status_label.setText("🟢 Active")
            self.status_label.setStyleSheet("color: green;")
        else:
            self.status_label.setText("🔴 Inactive")
            self.status_label.setStyleSheet("color: red;")
        
        # Update temperature display
        if status['current_temperature'] is not None:
            temp = status['current_temperature']
            self.temp_value.setText(f"{temp}°C")
            
            # Color-coded temperature status
            threshold = status['threshold_temp']
            if temp > threshold:
                self.temp_status.setText(f"⚠️ Abnormal (>{threshold}°C)")
                self.temp_status.setStyleSheet("color: red;")
                self.temp_value.setStyleSheet("color: red;")
            elif temp < 20:
                self.temp_status.setText("❄️ Cold")
                self.temp_status.setStyleSheet("color: blue;")
                self.temp_value.setStyleSheet("color: blue;")
            else:
                self.temp_status.setText("✅ Normal")
                self.temp_status.setStyleSheet("color: green;")
                self.temp_value.setStyleSheet("color: green;")
        else:
            self.temp_value.setText("No data")
            self.temp_value.setStyleSheet("color: gray;")
            self.temp_status.setText("")
        
        # Update readings count
        self.readings_label.setText(f"Total readings: {status['readings_count']}")
        
        # Enable/disable export button
        self.export_btn.setEnabled(status['readings_count'] > 0)
        
        # Update chart
        history = self.station.get_temperature_history()
        self.chart.update_chart(history, status['threshold_temp'])
        
        # Update statistics
        if history and len(history) > 0:
            temperatures = [reading['temperature'] for reading in history]
            avg_temp = sum(temperatures) / len(temperatures)
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            
            self.avg_label.setText(f"Avg\n{avg_temp:.1f}°C")
            self.min_label.setText(f"Min\n{min_temp:.1f}°C")
            self.max_label.setText(f"Max\n{max_temp:.1f}°C")
        else:
            self.avg_label.setText("Avg\n--°C")
            self.min_label.setText("Min\n--°C")
            self.max_label.setText("Max\n--°C")


class TemperatureDetectionApp(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.stations = [
            TemperatureStation(1, "Station Alpha"),
            TemperatureStation(2, "Station Beta"),
            TemperatureStation(3, "Station Gamma")
        ]
        self.station_widgets = []
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("🌡️ Temperature Detection System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
        """)
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout(main_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("🌡️ Temperature Detection System")
        title.setFont(QFont("Arial", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; margin: 20px;")
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("📊 Real-time Temperature Monitoring")
        subtitle.setFont(QFont("Arial", 16))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Stations layout
        stations_layout = QHBoxLayout()
        stations_layout.setSpacing(20)
        
        # Create station widgets
        for station in self.stations:
            station_widget = StationWidget(station)
            self.station_widgets.append(station_widget)
            
            # Add vertical separators between stations
            if len(self.station_widgets) > 1:
                separator = QFrame()
                separator.setFrameShape(QFrame.VLine)
                separator.setFrameShadow(QFrame.Sunken)
                separator.setStyleSheet("color: #404040;")
                stations_layout.addWidget(separator)
            
            stations_layout.addWidget(station_widget)
        
        layout.addLayout(stations_layout)
        
        # Footer
        footer = QLabel("Temperature Detection System | Real-time monitoring with independent station control")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignCenter)
        footer.setStyleSheet("color: #888; margin-top: 20px;")
        layout.addWidget(footer)
        
    def setup_timer(self):
        """Setup the timer for auto-refresh"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_displays)
        self.timer.start(1000)  # Update every 1 second
        
    def update_all_displays(self):
        """Update all station displays"""
        for widget in self.station_widgets:
            widget.update_display()
    
    def closeEvent(self, event):
        """Handle application closing"""
        # Stop all stations
        for station in self.stations:
            station.stop_detection()
        event.accept()


def main():
    """Main function to run the application"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Temperature Detection System")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = TemperatureDetectionApp()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main() 