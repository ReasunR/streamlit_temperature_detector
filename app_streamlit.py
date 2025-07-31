import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import time
from temperature_station import TemperatureStation

# Configure the Streamlit page
st.set_page_config(
    page_title="Temperature Detection System",
    page_icon="🌡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state for stations
if 'stations' not in st.session_state:
    st.session_state.stations = [
        TemperatureStation(1, "Station Alpha"),
        TemperatureStation(2, "Station Beta"),
        TemperatureStation(3, "Station Gamma")
    ]

# Main title
st.title("🌡️ Temperature Detection System")
st.markdown("---")



# Main content area
st.header("📊 Real-time Temperature Monitoring")

# Create columns with separators
col1, sep1, col2, sep2, col3 = st.columns([3, 0.1, 3, 0.1, 3])

# Add vertical separators
with sep1:
    st.markdown('<div style="border-left: 3px solid #404040; height: 1200px; margin-left: 50%;"></div>', unsafe_allow_html=True)

with sep2:
    st.markdown('<div style="border-left: 3px solid #404040; height: 1200px; margin-left: 50%;"></div>', unsafe_allow_html=True)

columns = [col1, col2, col3]

# Display each station's data with integrated controls
for idx, station in enumerate(st.session_state.stations):
    with columns[idx]:
        st.subheader(f"🔬 {station.name}")
        
        # Control buttons row
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button(f"▶️ Start", key=f"start_{station.station_id}"):
                station.start_detection()
                
        with btn_col2:
            if st.button(f"⏹️ Stop", key=f"stop_{station.station_id}"):
                station.stop_detection()
        
        # Get status for display
        status = station.get_status()
        
        # Status indicator
        if status['is_running']:
            st.success("🟢 Active")
        else:
            st.error("🔴 Inactive")
        
        # Current temperature display
        if status['current_temperature'] is not None:
            # Create a gauge-like metric display
            st.metric(
                label="Current Temperature",
                value=f"{status['current_temperature']}°C",
                delta=None
            )
            
            # Color-coded temperature indicator with threshold
            temp = status['current_temperature']
            threshold = status['threshold_temp']
            
            if temp > threshold:
                st.error(f"⚠️ Abnormal (>{threshold}°C)")
            elif temp < 20:
                st.info("❄️ Cold")
            else:
                st.success("✅ Normal")
        else:
            st.metric("Current Temperature", "No data")
        
        # Readings count
        st.caption(f"Total readings: {status['readings_count']}")
        
        # CSV Export button
        if status['readings_count'] > 0:
            csv_data = station.export_to_csv()
            from datetime import datetime
            filename = f"{station.name.replace(' ', '_')}_temperature_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            st.download_button(
                label="💾 Save CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                key=f"download_{station.station_id}",
                help=f"Download temperature data for {station.name}",
                use_container_width=True
            )
        else:
            st.info("📝 No data to export")
        
        # Temperature chart section - moved into each column
        st.markdown("---")
        st.markdown("**📈 Temperature History**")
        
        # Get history for this specific station
        history = station.get_temperature_history()
        
        if history and len(history) > 0:
            # Create DataFrame for this station only
            station_data = []
            for reading in history:
                station_data.append({
                    'Time': reading['timestamp'],
                    'Temperature': reading['temperature']
                })
            
            df_station = pd.DataFrame(station_data)
            
            # Create individual chart for this station
            fig = px.line(
                df_station,
                x='Time',
                y='Temperature',
                title=f'{station.name} Temperature Trend',
                labels={'Temperature': 'Temperature (°C)'},
                height=300
            )
            
            # Add threshold line
            threshold = station.threshold_temp
            fig.add_hline(
                y=threshold, 
                line_dash="dash", 
                line_color="red",
                annotation_text=f"Threshold: {threshold}°C",
                annotation_position="bottom right"
            )
            
            # Customize the chart appearance
            fig.update_traces(line_color='#1f77b4', line_width=2)
            fig.update_layout(
                xaxis_title="Time",
                yaxis_title="°C",
                title_font_size=14,
                showlegend=False,
                margin=dict(l=20, r=20, t=40, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Summary statistics for this station
            if len(df_station) > 0:
                avg_temp = df_station['Temperature'].mean()
                min_temp = df_station['Temperature'].min()
                max_temp = df_station['Temperature'].max()
                
                # Display stats in a compact format
                stat_col1, stat_col2, stat_col3 = st.columns(3)
                with stat_col1:
                    st.metric("Avg", f"{avg_temp:.1f}°C")
                with stat_col2:
                    st.metric("Min", f"{min_temp:.1f}°C")
                with stat_col3:
                    st.metric("Max", f"{max_temp:.1f}°C")
        else:
            # Show simple message when no data - no chart
            st.info("📊 No data available")
            st.markdown("Start this station to see temperature trends")

# Auto-refresh the page every 2 seconds
time.sleep(1)
st.rerun()

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
        <p>Temperature Detection System | Real-time monitoring with independent station control</p>
    </div>
    """, 
    unsafe_allow_html=True
) 
