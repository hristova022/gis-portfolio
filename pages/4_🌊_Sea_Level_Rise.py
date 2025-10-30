"""
Sea Level Rise Simulator - Long Beach, California
Interactive coastal flooding analysis under different sea level rise scenarios
"""

import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.element import Template, MacroElement
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Sea Level Rise Simulator", page_icon="🌊", layout="wide")

# Simple styling - matches your other pages
# No custom styling - use default Streamlit metrics

# Helper functions
def _load_geojson(pathlike):
    with open(pathlike, 'r', encoding='utf-8') as f:
        return json.load(f)

def _bounds_from_geojson(gj):
    def _walk(geom):
        t = geom.get('type')
        if t == 'Point':
            yield geom['coordinates']
        elif t in ('MultiPoint','LineString'):
            for c in geom['coordinates']: yield c
        elif t in ('MultiLineString','Polygon'):
            for ring in geom['coordinates']:
                for c in ring: yield c
        elif t == 'MultiPolygon':
            for poly in geom['coordinates']:
                for ring in poly:
                    for c in ring: yield c
    xs, ys = [], []
    for feat in gj.get('features', []):
        if not feat.get('geometry'): continue
        for x, y in _walk(feat['geometry']):
            xs.append(x); ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else [-118.2, 33.7, -118.08, 33.85]

# Load data
@st.cache_data
def load_data():
    base = Path('data/sea_level_rise/processed')
    data = {}
    with open(base / 'flood_scenarios.json', 'r', encoding='utf-8') as f:
        data['scenarios'] = json.load(f)
    data['impacts'] = pd.read_csv(base / 'property_impact.csv')
    data['boundary'] = _load_geojson(base / 'long_beach_boundary.geojson')
    data['infrastructure'] = _load_geojson(base / 'infrastructure_all.geojson')
    
    data['flood_zones'] = {}
    for scenario in data['scenarios'].keys():
        p_simple = base / f'flood_zone_{scenario}_simple.geojson'
        p_full = base / f'flood_zone_{scenario}.geojson'
        if p_simple.exists():
            data['flood_zones'][scenario] = _load_geojson(p_simple)
        elif p_full.exists():
            data['flood_zones'][scenario] = _load_geojson(p_full)
    return data

with st.spinner("Loading sea level rise data..."):
    data = load_data()

# Simple header
st.title("🌊 Sea Level Rise Impact Simulator")
st.subheader("Long Beach, California")

st.markdown("""
This tool shows which parts of Long Beach could flood as sea levels rise. Use the sidebar 
to explore different scenarios and see which homes, businesses, and infrastructure are at risk.
""")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.markdown("## 🌊 Select Scenario")
    
    scenario_labels = {
        '1ft_2030': '1 foot by 2030',
        '3ft_2050': '3 feet by 2050',
        '5ft_2070': '5 feet by 2070',
        '7ft_2100': '7 feet by 2100'
    }
    
    selected_label = st.selectbox("Choose sea level rise:", list(scenario_labels.values()))
    selected_scenario = [k for k, v in scenario_labels.items() if v == selected_label][0]
    scenario_data = data['scenarios'][selected_scenario]
    
    st.markdown("---")
    st.markdown("### 📊 Details")
    st.metric("Sea Level Rise", f"{scenario_data['rise_ft']} ft")
    st.metric("Year", scenario_data['year'])
    st.metric("Flooded Area", f"{scenario_data['area_km2']:.2f} km²")
    
    st.markdown("---")
    st.markdown("### 🗺️ Map Layers")
    show_flood = st.checkbox("Show flood zones", value=True)
    show_infra = st.checkbox("Show infrastructure", value=True)

# Impact metrics
impact_row = data['impacts'][data['impacts']['scenario'] == selected_scenario].iloc[0]

st.markdown("### 📊 Impact Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🌊 Flooded Area", f"{impact_row['flooded_area_km2']:.1f} km²")
    st.caption(f"{impact_row['flooded_area_km2']/130.8*100:.1f}% of city")

with col2:
    st.metric("🏠 Homes at Risk", f"{int(impact_row['properties_at_risk']):,}")
    st.caption(f"{impact_row['properties_at_risk']/171632*100:.1f}% of all homes")

with col3:
    st.metric("👥 People Affected", f"{int(impact_row['population_at_risk']):,}")
    st.caption(f"{impact_row['population_at_risk']/466742*100:.1f}% of residents")

with col4:
    st.metric("💰 Property Value", f"${impact_row['economic_impact_millions']:.0f}M")
    st.caption("Total value at risk")

st.markdown("---")

# Map
st.markdown("### 🗺️ Flood Risk Map")

# Dynamic info message based on scenario
color_names = {
    '1ft_2030': 'Blue',
    '3ft_2050': 'Orange',
    '5ft_2070': 'Red',
    '7ft_2100': 'Dark red'
}
color_name = color_names.get(selected_scenario, 'Blue')

st.info(f"**How to read:** {color_name} areas show land at or below +{scenario_data['rise_ft']} ft sea level by {scenario_data['year']}. Click markers for details.")

bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

# City boundary
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#1e3a8a',
        'weight': 2,
        'dashArray': '5,5'
    }
).add_to(m)

# Flood zones - thin lines like before
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
            'fillOpacity': 0.35
        },
        smooth_factor=1.2,
        tooltip=folium.GeoJsonTooltip(
            fields=['rise_ft', 'year'],
            aliases=['Sea Level Rise:', 'Expected By:'],
            style='background-color: white; color: black; font-size: 14px; padding: 8px; border-radius: 5px;'
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
    
    for feat in data['infrastructure'].get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if geom and geom.get('type') == 'Point':
            lon, lat = geom['coordinates'][:2]
            icon_name, color = icon_map.get(props.get('type', ''), ('circle', 'gray'))
            
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{props.get('name', '')}</b><br>{props.get('type', '')}<br>Elevation: {props.get('elevation_ft', 0)} ft",
                tooltip=props.get('name', ''),
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

# Simple legend
_legend_html = f"""
{{% macro html() %}}
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
            background: white; border: 2px solid #333; border-radius: 8px;
            padding: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.3); 
            font-family: Arial; font-size: 13px; color: #000;">
  <div style="font-weight:bold; margin-bottom:8px; color:#000;">Map Legend</div>
  <div style="display:flex; align-items:center; gap:8px; margin:4px 0;">
    <span style="display:inline-block; width:16px; height:16px; 
                 background:{colors.get(selected_scenario, '#3b82f6')}; 
                 opacity:0.35; border:1px solid #333;"></span>
    <span style="color:#000;">Flood zone</span>
  </div>
  <div style="display:flex; align-items:center; gap:8px; margin:4px 0;">
    <span style="display:inline-block; width:16px; height:2px; 
                 background:#1e3a8a; border:1px dashed #1e3a8a;"></span>
    <span style="color:#000;">City boundary</span>
  </div>
</div>
{{% endmacro %}}
"""

_legend_macro = MacroElement()
_legend_macro._template = Template(_legend_html)
m.get_root().add_child(_legend_macro)

st_folium(m, width=1400, height=600, returned_objects=[])

st.markdown("---")

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "📖 About", 
    "🔬 Methodology",
    "📊 Compare", 
    "💡 Actions"
])

with tab1:
    st.markdown("## 📖 Understanding Sea Level Rise")
    
    st.markdown("""
    ### What This Tool Shows
    
    This tool shows which parts of Long Beach are at or below different future sea levels. 
    As oceans rise due to climate change, low-lying areas could flood during high tides and storms.
    
    ### Why Long Beach?
    
    Long Beach sits right on the coast with many neighborhoods close to sea level. Rising seas could affect:
    - Homes and businesses
    - The Port of Long Beach (2nd busiest in America)
    - Long Beach Airport
    - Hospitals and emergency services
    
    ### How to Use This Tool
    
    1. Choose a scenario in the sidebar (different years and sea level rises)
    2. Look at the blue areas on the map - these are flood zones
    3. Click on markers to see if buildings are at risk
    4. Compare scenarios to see how risk grows over time
    
    ### What It Doesn't Include
    
    This is a simplified "bathtub" model that doesn't account for:
    - Storm surge
    - Existing flood walls
    - Drainage systems
    - Wave action
    
    Use this as a starting point to identify areas that need detailed study.
    """)

with tab2:
    st.markdown("## 🔬 Methodology")
    
    st.markdown("""
    ### How This Was Made
    
    **Step 1: Get Elevation Data**
    - Source: USGS 3DEP (Digital Elevation Model)
    - Shows height of every point above sea level
    - Resolution: 1 meter
    
    **Step 2: Define Scenarios**
    - Based on NOAA sea level rise projections
    - 4 scenarios: 1ft (2030), 3ft (2050), 5ft (2070), 7ft (2100)
    
    **Step 3: Find Flood Zones**
    - Simple formula: If ground ≤ sea level, it floods
    - Mark all areas at or below each threshold
    - Clip to Long Beach city boundary
    
    **Step 4: Calculate Impacts**
    - Use U.S. Census data for population and housing
    - Estimate properties affected by flooded area percentage
    - Calculate economic impact using median home values
    
    ### Data Sources
    
    - **Elevation:** USGS 3DEP
    - **Sea Level:** NOAA projections
    - **Demographics:** U.S. Census 2020
    - **Boundary:** OpenStreetMap
    
    ### Calculations
    
    **Properties at risk** = (Flooded area / Total area) × Total homes × 1.5
    
    **Population at risk** = Properties × 2.72 (avg household size)
    
    **Economic impact** = Properties × $600,000 (median home value)
    
    ### Limitations
    
    - Bathtub model (no barriers or drainage)
    - No storm surge modeling
    - Simplified property distribution
    - Static snapshots (not year-by-year)
    """)

with tab3:
    st.markdown("### 📊 Compare All Scenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='year',
            y='properties_at_risk',
            title='Homes at Risk by Year',
            labels={'properties_at_risk': 'Homes', 'year': 'Year'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='year',
            y='economic_impact_millions',
            title='Property Value at Risk ($M)',
            labels={'economic_impact_millions': 'Value ($M)', 'year': 'Year'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### Data Table")
    
    comparison_df = data['impacts'][['year', 'rise_ft', 'flooded_area_km2', 
                                      'properties_at_risk', 'population_at_risk', 
                                      'economic_impact_millions']].copy()
    
    comparison_df.columns = ['Year', 'Rise (ft)', 'Area (km²)', 
                            'Homes', 'People', 'Value ($M)']
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)
    
    # Download
    csv = data['impacts'].to_csv(index=False)
    st.download_button("📥 Download Data", csv, "slr_analysis.csv", "text/csv")

with tab4:
    st.markdown("### 💡 What Can Be Done?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Short-Term (0-5 years)**
        - Install flood monitoring
        - Update building codes
        - Community education
        - Emergency planning
        
        **Mid-Term (5-15 years)**
        - Build sea walls
        - Upgrade infrastructure
        - Relocate critical facilities
        - Improve drainage
        """)
    
    with col2:
        st.markdown("""
        **Long-Term (15+ years)**
        - Complete coastal defenses
        - Create resilient zones
        - Managed retreat
        - Regional coordination
        
        **What You Can Do**
        - Know your flood risk
        - Get flood insurance
        - Prepare emergency kit
        - Support climate action
        """)

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b;'>
    <p><strong>Sea Level Rise Simulator</strong> | Long Beach, California</p>
    <p>Data: USGS, NOAA, U.S. Census | Created by Hristova022</p>
</div>
""", unsafe_allow_html=True)
