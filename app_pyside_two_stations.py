import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QFrame, QGridLayout,
                             QScrollArea, QFileDialog, QMessageBox)
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QFont, QPalette, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime
from temperature_station import TemperatureStation


class TemperatureChart(FigureCanvas):
    """Custom matplotlib widget for temperature charts"""
    
    def __init__(self, station_name):
        self.figure = Figure(figsize=(6, 4), dpi=100)
        super().__init__(self.figure)
        self.station_name = station_name
        self.ax = self.figure.add_subplot(111)
        self.setup_chart()
        
    def setup_chart(self):
        """Initialize the chart appearance"""
        self.ax.set_title(f'{self.station_name} Temperature Trend', fontsize=11, fontweight='bold')
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
            
            # Set fixed y-axis limits
            self.ax.set_ylim(-20, 40)
                
            # Add legend below the "Time" x-axis label
            self.ax.legend(bbox_to_anchor=(0.5, -0.35), loc='upper center', ncol=2)
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
        layout.setSpacing(10)
        
        # Station container
        self.setStyleSheet("""
            StationWidget {
                border: 2px solid #ddd;
                border-radius: 8px;
                background-color: white;
                margin: 5px;
            }
        """)
        
        # Station title
        station_title = QLabel(f"🔬 {self.station.name}")
        station_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        station_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        station_title.setStyleSheet("color: #333333; margin: 5px;")
        layout.addWidget(station_title)
        
        # Control buttons
        button_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶️ Start")
        self.stop_btn = QPushButton("⏹️ Stop")
        
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
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
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: bold;
                font-size: 11px;
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
        
        # Compact status and temperature display
        compact_info_layout = QHBoxLayout()
        compact_info_layout.setSpacing(10)
        
        # Status indicator
        self.status_indicator = QLabel("🔴 Inactive")
        self.status_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_indicator.setFont(QFont("Arial", 9, QFont.Weight.Bold))
        self.status_indicator.setFixedWidth(70)
        compact_info_layout.addWidget(self.status_indicator)
        
        # Current temperature display
        self.temp_value = QLabel("No data")
        self.temp_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_value.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        compact_info_layout.addWidget(self.temp_value)
        
        # Temperature status
        self.temp_status = QLabel("")
        self.temp_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.temp_status.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        compact_info_layout.addWidget(self.temp_status)
        
        layout.addLayout(compact_info_layout)
        
        # Readings count and export
        info_layout = QHBoxLayout()
        
        self.readings_label = QLabel("Readings: 0")
        self.readings_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.readings_label.setFont(QFont("Arial", 9))
        self.readings_label.setStyleSheet("color: #666666;")
        info_layout.addWidget(self.readings_label)
        
        self.export_btn = QPushButton("💾 CSV")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-weight: bold;
                font-size: 10px;
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
        info_layout.addWidget(self.export_btn)
        
        layout.addLayout(info_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Temperature chart (larger)
        self.chart = TemperatureChart(self.station.name)
        self.chart.setMinimumHeight(250)  # Minimum height for two-station layout
        layout.addWidget(self.chart, 1)  # Give chart stretch factor of 1
        
        self.setLayout(layout)
        
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
            self.status_indicator.setText("🟢 Active")
            self.status_indicator.setStyleSheet("color: green;")
        else:
            self.status_indicator.setText("🔴 Inactive")
            self.status_indicator.setStyleSheet("color: red;")
        
        # Update temperature display
        if status['current_temperature'] is not None:
            temp = status['current_temperature']
            self.temp_value.setText(f"{temp}°C")
            
            # Color-coded temperature status
            threshold = status['threshold_temp']
            if temp > threshold:
                self.temp_status.setText(f"⚠️ Abnormal")
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
        self.readings_label.setText(f"Readings: {status['readings_count']}")
        
        # Enable/disable export button
        self.export_btn.setEnabled(status['readings_count'] > 0)
        
        # Update chart
        history = self.station.get_temperature_history()
        self.chart.update_chart(history, status['threshold_temp'])


class TemperatureDetectionApp(QMainWindow):
    """Main application window for two-station monitoring"""
    
    def __init__(self):
        super().__init__()
        # Create two stations
        self.stations = [
            TemperatureStation(1, "Station Alpha"),
            TemperatureStation(2, "Station Beta")
        ]
        self.station_widgets = []
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Setup the main UI"""
        self.setWindowTitle("🌡️ Temperature Detection System - Two Stations")
        self.setGeometry(100, 100, 1200, 700)
        
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
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("🌡️ Temperature Detection System")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #333; margin: 10px;")
        layout.addWidget(title)
        
        # Stations layout (horizontal)
        stations_layout = QHBoxLayout()
        stations_layout.setSpacing(15)
        
        # Create station widgets
        for station in self.stations:
            station_widget = StationWidget(station)
            self.station_widgets.append(station_widget)
            stations_layout.addWidget(station_widget)
            
            # Add vertical separator between stations
            if len(self.station_widgets) == 1:  # Add separator after first station
                separator = QFrame()
                separator.setFrameShape(QFrame.Shape.VLine)
                separator.setFrameShadow(QFrame.Shadow.Sunken)
                separator.setStyleSheet("color: #404040; margin: 10px 0px;")
                stations_layout.addWidget(separator)
        
        layout.addLayout(stations_layout)
        
        # Combined statistics at bottom
        stats_layout = QHBoxLayout()
        
        # Station Alpha stats
        alpha_stats_layout = QHBoxLayout()
        alpha_stats_layout.setSpacing(5)
        self.alpha_avg_label = QLabel("Average\n--°C")
        self.alpha_min_label = QLabel("Minimum\n--°C")
        self.alpha_max_label = QLabel("Maximum\n--°C")
        
        for label in [self.alpha_avg_label, self.alpha_min_label, self.alpha_max_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("""
                QLabel {
                    border: 1px solid #4CAF50;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #f1f8e9;
                    color: #333333;
                    margin: 3px;
                    min-width: 80px;
                }
            """)
            alpha_stats_layout.addWidget(label, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Alpha label
        alpha_label = QLabel("Station Alpha")
        alpha_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        alpha_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        alpha_label.setStyleSheet("color: #4CAF50; margin: 5px;")
        
        alpha_container = QVBoxLayout()
        alpha_container.addWidget(alpha_label)
        alpha_container.addLayout(alpha_stats_layout)
        
        stats_layout.addLayout(alpha_container)
        
        # Spacer
        stats_layout.addStretch()
        
        # Station Beta stats
        beta_stats_layout = QHBoxLayout()
        beta_stats_layout.setSpacing(5)
        self.beta_avg_label = QLabel("Average\n--°C")
        self.beta_min_label = QLabel("Minimum\n--°C")
        self.beta_max_label = QLabel("Maximum\n--°C")
        
        for label in [self.beta_avg_label, self.beta_min_label, self.beta_max_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 10))
            label.setStyleSheet("""
                QLabel {
                    border: 1px solid #2196F3;
                    padding: 8px;
                    border-radius: 4px;
                    background-color: #e3f2fd;
                    color: #333333;
                    margin: 3px;
                    min-width: 80px;
                }
            """)
            beta_stats_layout.addWidget(label, 1, Qt.AlignmentFlag.AlignCenter)
        
        # Beta label
        beta_label = QLabel("Station Beta")
        beta_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        beta_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        beta_label.setStyleSheet("color: #2196F3; margin: 5px;")
        
        beta_container = QVBoxLayout()
        beta_container.addWidget(beta_label)
        beta_container.addLayout(beta_stats_layout)
        
        stats_layout.addLayout(beta_container)
        
        layout.addLayout(stats_layout)
        
        # Footer
        footer = QLabel("Two Station Temperature Monitoring System")
        footer.setFont(QFont("Arial", 10))
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #888; margin-top: 10px;")
        layout.addWidget(footer)
        
    def setup_timer(self):
        """Setup the timer for auto-refresh"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_all_displays)
        self.timer.start(1000)  # Update every 1 second
        
    def update_all_displays(self):
        """Update all station displays and statistics"""
        # Update individual station widgets
        for widget in self.station_widgets:
            widget.update_display()
        
        # Update statistics for Station Alpha
        alpha_history = self.stations[0].get_temperature_history()
        if alpha_history and len(alpha_history) > 0:
            temperatures = [reading['temperature'] for reading in alpha_history]
            avg_temp = sum(temperatures) / len(temperatures)
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            
            self.alpha_avg_label.setText(f"Average\n{avg_temp:.1f}°C")
            self.alpha_min_label.setText(f"Minimum\n{min_temp:.1f}°C")
            self.alpha_max_label.setText(f"Maximum\n{max_temp:.1f}°C")
        else:
            self.alpha_avg_label.setText("Average\n--°C")
            self.alpha_min_label.setText("Minimum\n--°C")
            self.alpha_max_label.setText("Maximum\n--°C")
        
        # Update statistics for Station Beta
        beta_history = self.stations[1].get_temperature_history()
        if beta_history and len(beta_history) > 0:
            temperatures = [reading['temperature'] for reading in beta_history]
            avg_temp = sum(temperatures) / len(temperatures)
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            
            self.beta_avg_label.setText(f"Average\n{avg_temp:.1f}°C")
            self.beta_min_label.setText(f"Minimum\n{min_temp:.1f}°C")
            self.beta_max_label.setText(f"Maximum\n{max_temp:.1f}°C")
        else:
            self.beta_avg_label.setText("Average\n--°C")
            self.beta_min_label.setText("Minimum\n--°C")
            self.beta_max_label.setText("Maximum\n--°C")
    
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
    app.setApplicationName("Temperature Detection System - Two Stations")
    app.setApplicationVersion("1.0")
    
    # Create and show main window
    window = TemperatureDetectionApp()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 