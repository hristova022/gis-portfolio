"""
Sea Level Rise Simulator - Long Beach, California
Interactive coastal flooding analysis under different sea level rise scenarios
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Sea Level Rise Simulator", page_icon="🌊", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        padding: 1rem 0;
    }
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    data = {}
    base_path = 'data/sea_level_rise/processed'
    
    data['scenarios'] = json.load(open(f'{base_path}/flood_scenarios.json'))
    data['impacts'] = pd.read_csv(f'{base_path}/property_impact.csv')
    data['infrastructure'] = gpd.read_file(f'{base_path}/infrastructure_all.geojson')
    data['boundary'] = gpd.read_file(f'{base_path}/long_beach_boundary.geojson')
    
    data['flood_zones'] = {}
    for scenario in data['scenarios'].keys():
        try:
            data['flood_zones'][scenario] = gpd.read_file(f'{base_path}/flood_zone_{scenario}.geojson')
        except:
            pass
    
    return data

with st.spinner("Loading sea level rise data..."):
    data = load_data()

# Header
st.markdown('<p class="main-header">🌊 Sea Level Rise Impact Simulator</p>', unsafe_allow_html=True)
st.markdown("### Long Beach, California - Coastal Flooding Analysis")

st.markdown("""
This interactive tool visualizes potential impacts of sea level rise on Long Beach using **USGS elevation data** 
and **NOAA projections**. Explore different scenarios from 2030 to 2100.
""")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Seal_of_Long_Beach%2C_California.svg/200px-Seal_of_Long_Beach%2C_California.svg.png", width=100)
    st.title("🌊 Scenario Selector")
    
    scenario_labels = {
        '1ft_2030': '1ft by 2030 (High Probability)',
        '3ft_2050': '3ft by 2050 (Medium Probability)',
        '5ft_2070': '5ft by 2070 (Low Probability)',
        '7ft_2100': '7ft by 2100 (Very Low Probability)'
    }
    
    selected_label = st.selectbox("Select Scenario", list(scenario_labels.values()))
    selected_scenario = [k for k, v in scenario_labels.items() if v == selected_label][0]
    
    scenario_data = data['scenarios'][selected_scenario]
    
    st.markdown("### 📊 Scenario Details")
    st.metric("Sea Level Rise", f"{scenario_data['rise_ft']} ft ({scenario_data['rise_m']:.2f} m)")
    st.metric("Projected Year", scenario_data['year'])
    st.metric("Area Affected", f"{scenario_data['area_km2']:.2f} km²")
    
    st.markdown("---")
    
    st.markdown("### 🗺️ Map Layers")
    show_flood = st.checkbox("Show Flood Zone", value=True)
    show_infra = st.checkbox("Show Infrastructure", value=True)
    
    st.markdown("---")
    
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        **Data Sources:**
        - USGS 3DEP elevation data
        - NOAA sea level projections
        - US Census demographics
        
        **Methodology:**
        Simple bathtub model identifying areas below projected sea levels
        
        **Created by:** Hristova022  
        **GitHub:** [gis-portfolio](https://github.com/hristova022/gis-portfolio)
        """)

# Key Metrics
impact_row = data['impacts'][data['impacts']['scenario'] == selected_scenario].iloc[0]

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌊 Area Flooded", f"{impact_row['flooded_area_km2']:.1f} km²", 
              f"{impact_row['flooded_area_km2']/130.8*100:.1f}% of Long Beach")

with col2:
    st.metric("🏠 Properties at Risk", f"{impact_row['properties_at_risk']:,}",
              f"{impact_row['properties_at_risk']/171632*100:.1f}% of total")

with col3:
    st.metric("👥 Population at Risk", f"{impact_row['population_at_risk']:,}",
              f"{impact_row['population_at_risk']/466742*100:.1f}% of total")

with col4:
    st.metric("💰 Economic Impact", f"${impact_row['economic_impact_millions']:.0f}M",
              "Property value at risk")

st.markdown("---")

# Interactive Map
st.markdown("### 🗺️ Interactive Flood Map")

bounds = data['boundary'].total_bounds
center = [(bounds[1] + bounds[3])/2, (bounds[0] + bounds[2])/2]

m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')

# Boundary
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#1e3a8a',
        'weight': 2
    }
).add_to(m)

# Flood zone
if show_flood and selected_scenario in data['flood_zones']:
    colors = {
        '1ft_2030': '#3b82f6',
        '3ft_2050': '#f59e0b',
        '5ft_2070': '#ef4444',
        '7ft_2100': '#991b1b'
    }
    
    folium.GeoJson(
        data['flood_zones'][selected_scenario],
        style_function=lambda x: {
            'fillColor': colors.get(selected_scenario, '#3b82f6'),
            'color': colors.get(selected_scenario, '#3b82f6'),
            'weight': 1,
            'fillOpacity': 0.4
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['scenario', 'rise_ft', 'year'],
            aliases=['Scenario:', 'Rise (ft):', 'Year:']
        )
    ).add_to(m)

# Infrastructure
if show_infra:
    icon_map = {
        'Hospital': ('plus', 'red'),
        'Airport': ('plane', 'blue'),
        'Port': ('ship', 'darkblue'),
        'Attraction': ('star', 'purple'),
        'Historic Ship': ('anchor', 'darkred')
    }
    
    for _, facility in data['infrastructure'].iterrows():
        icon_name, color = icon_map.get(facility['type'], ('circle', 'gray'))
        
        folium.Marker(
            location=[facility.geometry.y, facility.geometry.x],
            popup=f"<b>{facility['name']}</b><br>{facility['type']}<br>Elevation: {facility['elevation_ft']}ft",
            tooltip=facility['name'],
            icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
        ).add_to(m)

st_folium(m, width=1400, height=600)

st.markdown("---")

# Analysis Tabs
tab1, tab2, tab3 = st.tabs(["📊 Scenario Comparison", "📈 Temporal Analysis", "💡 Key Insights"])

with tab1:
    st.markdown("### Compare All Scenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='scenario',
            y='properties_at_risk',
            title='Properties at Risk',
            color='year',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='scenario',
            y='economic_impact_millions',
            title='Economic Impact ($M)',
            color='year',
            color_continuous_scale='Reds'
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.dataframe(data['impacts'], use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### Impact Progression Over Time")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=data['impacts']['year'],
        y=data['impacts']['properties_at_risk'],
        name='Properties at Risk',
        line=dict(color='#3b82f6', width=3),
        mode='lines+markers'
    ))
    fig.update_layout(title='Properties at Risk Over Time', height=400)
    st.plotly_chart(fig, use_container_width=True)
    
    fig2 = px.area(
        data['impacts'],
        x='year',
        y='economic_impact_millions',
        title='Economic Impact Progression',
        color_discrete_sequence=['#991b1b']
    )
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### 💡 Key Findings")
    
    worst_case = data['impacts'].sort_values('properties_at_risk', ascending=False).iloc[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🌊 Coastal Vulnerability")
        st.markdown(f"""
        - **Immediate Risk (2030):** {data['impacts'].iloc[0]['properties_at_risk']:,} properties
        - **Long-term Risk (2100):** {worst_case['properties_at_risk']:,} properties
        - **Total Economic Exposure:** ${worst_case['economic_impact_millions']:.0f}M
        - **Population Affected:** Up to {worst_case['population_at_risk']:,} residents
        """)
    
    with col2:
        st.markdown("#### 🎯 Recommended Actions")
        st.markdown("""
        **Immediate (0-5 years):**
        - Enhance flood monitoring systems
        - Update building codes
        - Begin infrastructure hardening
        
        **Medium-term (5-15 years):**
        - Construct coastal barriers
        - Upgrade stormwater systems
        - Relocate critical facilities
        
        **Long-term (15+ years):**
        - Complete defense systems
        - Establish resilient zones
        """)
    
    st.markdown("---")
    
    st.markdown("#### 📥 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = data['impacts'].to_csv(index=False)
        st.download_button(
            "📊 Download Impact Analysis (CSV)",
            csv,
            "impact_analysis.csv",
            "text/csv"
        )
    
    with col2:
        summary = json.dumps(data['scenarios'], indent=2)
        st.download_button(
            "📋 Download Scenario Summary (JSON)",
            summary,
            "scenarios.json",
            "application/json"
        )

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b;">
    <p><strong>Sea Level Rise Simulator</strong> | GIS Portfolio Project</p>
    <p>Data: USGS 3DEP, NOAA, US Census | Created by Hristova022</p>
</div>
""", unsafe_allow_html=True)
