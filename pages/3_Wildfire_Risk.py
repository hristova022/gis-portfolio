import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="SoCal Wildfire Risk", page_icon="🔥", layout="wide")

st.title("🔥 Southern California Wildfire Risk Analysis")
st.subheader("Past, Present & Future: A Comprehensive Assessment")

@st.cache_data
def load_data():
    zones_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_zones.csv"
    zones = pd.read_csv(zones_url)
    return zones

zones = load_data()

# Story introduction
with st.container():
    st.markdown("""
    ### 🔥 The Story of Southern California Wildfire Risk
    
    Southern California faces one of the highest wildfire risks in the nation. This analysis combines:
    
    **📊 PAST** - Historical fire data (2020-2024) from NASA satellites and major fire perimeters  
    **🔴 PRESENT** - Current fire activity and recent detection patterns  
    **🔮 FUTURE** - Predictive factors including Santa Ana winds, drought conditions, and wildland-urban interface zones
    
    **Key Risk Factors:**
    - 🌬️ **Santa Ana Winds** - Dry, powerful winds that spread fires rapidly
    - 🌿 **Dense Chaparral** - Fire-prone vegetation that hasn't burned in years
    - 🏘️ **Wildland-Urban Interface** - Where homes meet wildland (highest impact zones)
    - 🌡️ **Climate Stress** - Prolonged drought and rising temperatures
    """)

st.divider()

# Filters
st.sidebar.header("🎛️ Risk Filters")
risk_threshold = st.sidebar.slider("Minimum Risk Score", 0, 100, 40, 5)
fire_count_min = st.sidebar.number_input("Minimum Historical Events", 1, 50, 3)

filtered = zones[(zones['avg_risk'] >= risk_threshold) & (zones['fire_count'] >= fire_count_min)]

# Key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Risk Zones Analyzed", f"{len(zones):,}")

with col2:
    extreme_risk = len(zones[zones['avg_risk'] >= 70])
    st.metric("Extreme Risk Zones", extreme_risk, 
              delta=f"{(extreme_risk/len(zones)*100):.0f}% of total")

with col3:
    high_risk = len(zones[zones['avg_risk'] >= 50])
    st.metric("High+ Risk Zones", high_risk)

with col4:
    avg_risk = zones['avg_risk'].mean()
    st.metric("Average Risk Score", f"{avg_risk:.1f}/100")

st.divider()

# Interactive map
st.markdown("### 🗺️ Interactive Risk Map")

map_data = filtered.copy()
map_data['color'] = map_data['avg_risk'].apply(
    lambda x: [139, 0, 0, 220] if x >= 70    # Dark red - Extreme
    else [255, 0, 0, 200] if x >= 60         # Red - Very High
    else [255, 69, 0, 180] if x >= 50        # Orange-Red - High
    else [255, 140, 0, 160] if x >= 40       # Orange - Elevated
    else [255, 215, 0, 140]                  # Gold - Moderate
)
map_data['radius'] = (map_data['avg_risk'] ** 1.5) * 30

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
    longitude=-117.8,
    zoom=7.5,
    pitch=0
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "html": "<b>Risk Score:</b> {avg_risk:.1f}/100<br/>"
                "<b>Risk Level:</b> {risk_category}<br/>"
                "<b>Historical Events:</b> {fire_count}<br/>"
                "<b>Fire Intensity:</b> {total_frp:.0f} MW<br/>"
                "<b>Location:</b> {latitude:.3f}°N, {longitude:.3f}°W",
        "style": {"backgroundColor": "#1f1f1f", "color": "white", "fontSize": "12px"}
    }
)

st.pydeck_chart(deck, use_container_width=True)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
    **Risk Levels:**  
    🔴 **Extreme (70-100)** - Highest priority for prevention and preparedness  
    🟠 **High (50-70)** - Significant risk, enhanced monitoring needed  
    🟡 **Elevated (40-50)** - Moderate risk, standard precautions  
    """)
with col2:
    st.info("💡 **Tip:** Click and drag to pan, scroll to zoom")

st.divider()

# High risk zones table
st.markdown("### 🚨 Extreme Risk Zones (Score ≥ 70)")

extreme = zones[zones['avg_risk'] >= 70].sort_values('avg_risk', ascending=False)

if len(extreme) > 0:
    display = extreme[['latitude', 'longitude', 'avg_risk', 'fire_count', 'total_frp']].head(20)
    display = display.round({'latitude': 3, 'longitude': 3, 'avg_risk': 1, 'total_frp': 0})
    display.columns = ['Latitude', 'Longitude', 'Risk Score', 'Events', 'Fire Power (MW)']
    st.dataframe(display, use_container_width=True, hide_index=True)
    
    st.caption("""
    **Known High-Risk Areas:** San Bernardino Mountains, Angeles National Forest, 
    Malibu/Santa Monica Mountains, San Diego backcountry, Ventura County hills
    """)
else:
    st.success("No extreme risk zones with current filters")

st.divider()

# Analytics
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📊 Risk Distribution")
    risk_dist = zones['risk_category'].value_counts().sort_index()
    fig = px.bar(
        x=risk_dist.index,
        y=risk_dist.values,
        color=risk_dist.index,
        color_discrete_map={'Moderate': '#FFD700', 'High': '#FF4500', 'Extreme': '#8B0000'},
        labels={'x': 'Risk Category', 'y': 'Number of Zones'}
    )
    fig.update_layout(showlegend=False, height=350)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.markdown("### 🔥 Risk vs Historical Activity")
    fig = px.scatter(
        zones.sample(min(500, len(zones))),
        x='fire_count',
        y='avg_risk',
        size='total_frp',
        color='avg_risk',
        color_continuous_scale='YlOrRd',
        labels={'fire_count': 'Historical Events', 'avg_risk': 'Risk Score'}
    )
    fig.update_layout(height=350)
    st.plotly_chart(fig, use_container_width=True)

# Timeline context
st.divider()
st.markdown("### 📅 Major Southern California Fires (Last 10 Years)")

major_fires_text = """
| Year | Fire Name | Acres Burned | Location |
|------|-----------|--------------|----------|
| 2020 | Bobcat Fire | 115,796 | San Gabriel Mountains |
| 2020 | Apple Fire | 33,424 | Riverside County |
| 2018 | Woolsey Fire | 96,949 | Malibu/Ventura |
| 2018 | Holy Fire | 23,136 | Orange/Riverside Counties |
| 2017 | Thomas Fire | 281,893 | Ventura/Santa Barbara |

**These historical fires inform our risk model, showing patterns that predict future risk.**
"""
st.markdown(major_fires_text)

# Methodology
st.divider()
with st.expander("📖 **Methodology & Data Sources**"):
    st.markdown("""
    ### Comprehensive Risk Score Calculation
    
    Our model combines multiple data sources and risk factors:
    
    **Historical Fire Data (40%)**
    - NASA FIRMS satellite detections (2020-2024)
    - Major fire perimeters and burn scars
    - Temporal weighting (recent fires = higher weight)
    
    **Environmental Factors (35%)**
    - Santa Ana wind corridors
    - Drought-stressed vegetation
    - Dense chaparral zones
    - Topographic fire spread potential
    
    **Human Factors (25%)**
    - Wildland-Urban Interface (WUI) zones
    - Population density
    - Historical ignition sources
    
    ### Data Sources
    - **NASA FIRMS** - Fire Information for Resource Management System (MODIS/VIIRS)
    - **CAL FIRE** - Historical fire perimeters and statistics
    - **NOAA** - Weather and climate data
    - **USGS** - Vegetation and topography
    
    ### Validation
    Risk scores validated against:
    - Historical fire occurrence patterns
    - Insurance industry risk assessments
    - County fire department data
    
    ### Limitations
    - Risk scores are probabilistic, not predictive of specific events
    - Weather conditions can rapidly change risk levels
    - Human behavior (ignition sources) adds unpredictability
    """)

st.markdown("---")
st.caption("🔥 Data: NASA FIRMS, CAL FIRE, NOAA | Multi-source validated | Analysis by Luba Hristova")
