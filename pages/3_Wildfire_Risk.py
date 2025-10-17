import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Wildfire Risk Analysis", page_icon="🔥", layout="wide")

st.title("🔥 Southern California Wildfire Risk Analysis")
st.subheader("Real-time satellite detection and predictive risk modeling")

@st.cache_data
def load_data():
    zones_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_zones.csv"
    points_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_points.csv"
    
    zones = pd.read_csv(zones_url)
    points = pd.read_csv(points_url)
    return zones, points

zones, points = load_data()

st.markdown("""
### 🛰️ About This Analysis

Using **NASA FIRMS** (Fire Information for Resource Management System) satellite data to:
- Track active wildfire detections in real-time (MODIS satellite)
- Calculate risk scores based on fire intensity and frequency
- Identify high-risk zones for emergency response planning

**Data Updates:** Every 3 hours from NASA satellites
""")

st.divider()

# Sidebar filters
st.sidebar.header("🎛️ Filters")

risk_threshold = st.sidebar.slider(
    "Minimum Risk Score",
    min_value=0,
    max_value=100,
    value=30,
    step=5,
    help="Show only zones with risk score above this threshold"
)

fire_count_min = st.sidebar.number_input(
    "Minimum Fire Detections",
    min_value=1,
    max_value=50,
    value=1,
    help="Filter zones by number of fire detections"
)

# Filter data
filtered_zones = zones[
    (zones['avg_risk'] >= risk_threshold) &
    (zones['fire_count'] >= fire_count_min)
]

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Active Fire Zones", len(filtered_zones))

with col2:
    high_risk = len(filtered_zones[filtered_zones['avg_risk'] > 70])
    st.metric("High Risk Zones", high_risk, 
              delta=f"{(high_risk/len(filtered_zones)*100):.1f}%" if len(filtered_zones) > 0 else "0%")

with col3:
    total_fires = filtered_zones['fire_count'].sum()
    st.metric("Total Detections", int(total_fires))

with col4:
    avg_risk = filtered_zones['avg_risk'].mean() if len(filtered_zones) > 0 else 0
    st.metric("Average Risk Score", f"{avg_risk:.1f}")

st.divider()

# Map
st.markdown("### 🗺️ Fire Risk Map")

map_data = filtered_zones.copy()
map_data['color'] = map_data['avg_risk'].apply(
    lambda x: [255, 0, 0, 200] if x > 70 
    else [255, 165, 0, 160] if x > 40 
    else [255, 255, 0, 140]
)
map_data['radius'] = map_data['fire_count'] * 800

layer = pdk.Layer(
    'ScatterplotLayer',
    data=map_data,
    get_position='[longitude, latitude]',
    get_color='color',
    get_radius='radius',
    pickable=True,
    auto_highlight=True
)

view_state = pdk.ViewState(
    latitude=34.0,
    longitude=-118.0,
    zoom=7,
    pitch=0
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>Risk Score:</b> {avg_risk:.1f}<br/>"
                "<b>Fire Count:</b> {fire_count}<br/>"
                "<b>Avg Brightness:</b> {avg_brightness:.0f}K<br/>"
                "<b>Total Power:</b> {total_frp:.0f} MW",
        "style": {"backgroundColor": "steelblue", "color": "white"}
    }
)

st.pydeck_chart(deck)

col1, col2 = st.columns(2)

with col1:
    st.markdown("**Legend:**")
    st.markdown("🔴 High Risk (70+) | 🟠 Medium Risk (40-70) | 🟡 Low Risk (<40)")
    st.caption("Circle size = number of fire detections in zone")

with col2:
    st.info("💡 **Tip:** Hover over circles for detailed zone information")

st.divider()

# High risk table
st.markdown("### 🚨 High Risk Zones (Risk Score > 60)")

high_risk_zones = filtered_zones[filtered_zones['avg_risk'] > 60].sort_values('avg_risk', ascending=False)

if len(high_risk_zones) > 0:
    display = high_risk_zones[['latitude', 'longitude', 'avg_risk', 'fire_count', 'total_frp']].head(15)
    display['avg_risk'] = display['avg_risk'].round(1)
    display['latitude'] = display['latitude'].round(3)
    display['longitude'] = display['longitude'].round(3)
    display['total_frp'] = display['total_frp'].round(0)
    display.columns = ['Latitude', 'Longitude', 'Risk Score', 'Detections', 'Fire Power (MW)']
    
    st.dataframe(display, use_container_width=True, hide_index=True)
else:
    st.info("✅ No high-risk zones detected with current filters")

st.divider()

# Charts
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Risk Distribution")
    
    risk_bins = pd.cut(filtered_zones['avg_risk'], 
                       bins=[0, 30, 60, 100],
                       labels=['Low (0-30)', 'Medium (30-60)', 'High (60+)'])
    risk_dist = risk_bins.value_counts()
    
    fig = px.bar(
        x=risk_dist.index,
        y=risk_dist.values,
        labels={'x': 'Risk Level', 'y': 'Number of Zones'},
        color=risk_dist.index,
        color_discrete_map={
            'Low (0-30)': '#FFFF00',
            'Medium (30-60)': '#FFA500',
            'High (60+)': '#FF0000'
        }
    )
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🔥 Fire Intensity Analysis")
    
    fig = px.scatter(
        filtered_zones,
        x='fire_count',
        y='avg_risk',
        size='total_frp',
        color='avg_risk',
        color_continuous_scale='YlOrRd',
        labels={
            'fire_count': 'Number of Detections',
            'avg_risk': 'Risk Score',
            'total_frp': 'Fire Power (MW)'
        },
        hover_data=['avg_brightness']
    )
    st.plotly_chart(fig, use_container_width=True)

st.divider()

with st.expander("📖 **Methodology & Data Sources**"):
    st.markdown("""
    ### Risk Score Calculation
    
    Our risk model combines three key factors from NASA satellite data:
    
    1. **Fire Brightness (40%)** - Temperature of detected hotspots
    2. **Fire Radiative Power (40%)** - Intensity/energy output of fires  
    3. **Detection Confidence (20%)** - Satellite confidence level
    
    Zones are created using a 0.5-degree grid overlay, with risk scores averaged across all detections.
    
    ### Data Sources
    - **NASA FIRMS** - Fire Information for Resource Management System
    - **MODIS Satellite** - Moderate Resolution Imaging Spectroradiometer
    - Updates every 3 hours with near-real-time fire detection
    
    ### Limitations
    - Satellite detection can be affected by cloud cover
    - Small fires may not be detected
    - Risk scores are relative, not absolute predictions
    """)

st.markdown("---")
st.caption("🛰️ Data: NASA FIRMS (MODIS) | Updated every 3 hours | Analysis by Luba Hristova")
