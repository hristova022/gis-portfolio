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

st.markdown("""
<style>
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
    }
    .highlight-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .method-box {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

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

# Title
st.title("🌊 Sea Level Rise Impact Simulator")
st.subheader("Long Beach, California")

# Eye-catching summary at top
st.markdown("""
<div class='highlight-box'>
    <h2 style='margin:0 0 1rem 0;'>⚠️ What You Need to Know</h2>
    <p style='font-size:1.1rem;margin:0.5rem 0;'>
        By 2100, up to <b>{:,} homes</b> in Long Beach could be in flood risk zones, 
        affecting <b>{:,} residents</b> and threatening <b>${:.0f} million</b> in property value.
    </p>
    <p style='font-size:1rem;margin:1rem 0 0 0;opacity:0.9;'>
        This tool shows which neighborhoods are most vulnerable so we can protect them before it's too late.
    </p>
</div>
""".format(
    int(data['impacts'].iloc[-1]['properties_at_risk']),
    int(data['impacts'].iloc[-1]['population_at_risk']),
    data['impacts'].iloc[-1]['economic_impact_millions']
), unsafe_allow_html=True)

st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Seal_of_Long_Beach%2C_California.svg/200px-Seal_of_Long_Beach%2C_California.svg.png", width=100)
    st.title("🌊 Select Scenario")
    
    scenario_labels = {
        '1ft_2030': '1 foot by 2030',
        '3ft_2050': '3 feet by 2050',
        '5ft_2070': '5 feet by 2070',
        '7ft_2100': '7 feet by 2100'
    }
    
    selected_label = st.selectbox("Choose sea level rise:", list(scenario_labels.values()))
    selected_scenario = [k for k, v in scenario_labels.items() if v == selected_label][0]
    scenario_data = data['scenarios'][selected_scenario]
    
    st.markdown("### 📊 Scenario Details")
    st.metric("Sea Level Rise", f"{scenario_data['rise_ft']} ft ({scenario_data['rise_m']:.2f} m)")
    st.metric("Year", scenario_data['year'])
    st.metric("Flooded Area", f"{scenario_data['area_km2']:.2f} km²")
    st.caption(f"{scenario_data['area_km2']/130.8*100:.1f}% of city area")
    
    st.markdown("---")
    
    st.markdown("### 🗺️ Map Controls")
    show_flood = st.checkbox("Show flood zones", value=True)
    show_infra = st.checkbox("Show facilities", value=True)
    
    # Map style
    st.markdown("### 🎨 Map Style")
    map_style = st.radio("Base map:", ["Light", "Satellite"], index=0)

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

# Map with better visualization
st.markdown("### 🗺️ Interactive Map: Where Would Water Reach?")

st.info("**How to read:** Colored areas show land at or below the selected sea level. Darker colors = higher risk scenarios. Click buildings to see if they're safe.")

bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

# Choose tile based on selection
if map_style == "Satellite":
    tiles = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    attr = "Esri"
else:
    tiles = 'CartoDB positron'
    attr = None

m = folium.Map(location=center, zoom_start=12, tiles=tiles, attr=attr)
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

# City boundary - more visible
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {
        'fillColor': 'transparent',
        'color': '#1e3a8a',
        'weight': 3,
        'dashArray': '10,5'
    },
    name='City Boundary'
).add_to(m)

# Flood zones with better colors and opacity
if show_flood and selected_scenario in data['flood_zones']:
    # Color scheme: intensity increases with risk
    color_schemes = {
        '1ft_2030': {'fill': '#60a5fa', 'border': '#2563eb', 'opacity': 0.5},  # Light blue
        '3ft_2050': {'fill': '#fb923c', 'border': '#ea580c', 'opacity': 0.55}, # Orange
        '5ft_2070': {'fill': '#f87171', 'border': '#dc2626', 'opacity': 0.6},  # Red
        '7ft_2100': {'fill': '#b91c1c', 'border': '#7f1d1d', 'opacity': 0.65}  # Dark red
    }
    
    colors = color_schemes.get(selected_scenario, color_schemes['1ft_2030'])
    
    folium.GeoJson(
        data['flood_zones'][selected_scenario],
        style_function=lambda x: {
            'fillColor': colors['fill'],
            'color': colors['border'],
            'weight': 2,
            'fillOpacity': colors['opacity']
        },
        smooth_factor=1.0,
        name=f'Flood Zone ({scenario_data["rise_ft"]} ft)',
        tooltip=folium.GeoJsonTooltip(
            fields=['scenario', 'rise_ft', 'year'],
            aliases=['Scenario:', 'Sea Rise:', 'Year:'],
            style='background-color: white; color: black; font-size: 14px; padding: 10px; border-radius: 5px;'
        )
    ).add_to(m)

# Infrastructure with risk status
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
            
            facility_elevation = props.get('elevation_ft', 999)
            scenario_level = scenario_data['rise_ft'] * 3.28
            at_risk = facility_elevation <= scenario_level
            
            risk_html = f"""
            <div style='min-width:200px; font-family: Arial;'>
                <h4 style='margin:0 0 8px 0; color:#1e3a8a;'>{props.get('name', '')}</h4>
                <hr style='margin:8px 0;'>
                <p style='margin:4px 0;'><b>Type:</b> {props.get('type', '')}</p>
                <p style='margin:4px 0;'><b>Elevation:</b> {props.get('elevation_ft', 0)} ft above sea level</p>
                <p style='margin:4px 0;'><b>Scenario:</b> +{scenario_data['rise_ft']} ft by {scenario_data['year']}</p>
                <p style='margin:8px 0; padding:8px; background:{"#fee2e2" if at_risk else "#d1fae5"}; 
                   border-radius:4px; font-weight:bold; color:{"#991b1b" if at_risk else "#065f46"};'>
                    {"⚠️ AT RISK" if at_risk else "✅ SAFE"}
                </p>
            </div>
            """
            
            folium.Marker(
                location=[lat, lon],
                popup=folium.Popup(risk_html, max_width=300),
                tooltip=f"{props.get('name', '')} ({props.get('type', '')})",
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

# Enhanced legend with better visibility
color_for_legend = {
    '1ft_2030': '#60a5fa',
    '3ft_2050': '#fb923c',
    '5ft_2070': '#f87171',
    '7ft_2100': '#b91c1c'
}

_legend_html = f"""
{{% macro html() %}}
<div style="position: fixed; bottom: 20px; left: 20px; z-index: 9999;
            background: white; border: 2px solid #1e3a8a; border-radius: 10px;
            padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
            font-family: Arial; font-size: 13px; min-width: 200px;">
  <div style="font-weight:bold; font-size:14px; margin-bottom:10px; color:#1e3a8a; border-bottom: 2px solid #1e3a8a; padding-bottom:5px;">
    🗺️ Map Legend
  </div>
  
  <div style="margin:8px 0;">
    <div style="display:flex; align-items:center; gap:10px; margin:6px 0;">
      <span style="display:inline-block; width:20px; height:20px; 
                   background:{color_for_legend.get(selected_scenario, '#60a5fa')}; 
                   border:2px solid #1e3a8a; border-radius:3px;"></span>
      <span><b>Flood risk zone</b></span>
    </div>
    <div style="font-size:11px; color:#64748b; margin-left:30px;">
      Land at or below +{scenario_data['rise_ft']} ft
    </div>
  </div>
  
  <div style="margin:8px 0;">
    <div style="display:flex; align-items:center; gap:10px; margin:6px 0;">
      <span style="display:inline-block; width:20px; height:3px; 
                   background:#1e3a8a; border:1px dashed #1e3a8a;"></span>
      <span>City boundary</span>
    </div>
  </div>
  
  <div style="margin:8px 0;">
    <div style="display:flex; align-items:center; gap:10px; margin:6px 0;">
      <i class="fa fa-map-marker" style="color:#ef4444; font-size:16px;"></i>
      <span>Critical facilities</span>
    </div>
    <div style="font-size:11px; color:#64748b; margin-left:30px;">
      Click for risk status
    </div>
  </div>
  
  <div style="margin-top:12px; padding-top:10px; border-top:1px solid #e2e8f0;">
    <div style="font-size:11px; color:#64748b;">
      <b>Scenario:</b> {selected_scenario.replace('_', ' ').title()}<br>
      <b>Year:</b> {scenario_data['year']}
    </div>
  </div>
</div>
{{% endmacro %}}
"""

_legend_macro = MacroElement()
_legend_macro._template = Template(_legend_html)
m.get_root().add_child(_legend_macro)

st_folium(m, width=1400, height=650, returned_objects=[])

# Add color gradient explanation
st.markdown("""
**Color Guide:** 
- 🟦 Light blue = 2030 scenario (nearest term, lower risk)
- 🟧 Orange = 2050 scenario (mid-century, moderate risk)  
- 🟥 Red = 2070 scenario (late century, high risk)
- 🔴 Dark red = 2100 scenario (end century, highest risk)

*Darker colors = more severe flooding scenarios*
""")

st.markdown("---")

# Tabs
tab0, tab1, tab2, tab3, tab4 = st.tabs([
    "📖 Understanding This", 
    "🔬 Methodology & Math",
    "📊 Compare Scenarios", 
    "📈 Timeline", 
    "💡 What To Do"
])

with tab0:
    st.markdown("## 📖 What Is This Tool?")
    
    st.markdown("""
    This tool shows **what parts of Long Beach would be underwater** if sea levels rise by 
    different amounts. Think of it like looking at a bathtub — as water rises, lower areas 
    flood first.
    
    ### Why It Matters
    
    **Sea levels are rising** because climate change is:
    - Melting ice in Greenland and Antarctica
    - Making ocean water expand as it warms
    
    Long Beach sits right on the coast with many low-lying neighborhoods. Rising seas could flood:
    - 🏠 People's homes
    - 🏥 Hospitals and emergency services
    - 🚢 The Port (2nd busiest in the USA)
    - ✈️ Long Beach Airport
    - 🎭 Tourist attractions
    
    ### What The Map Shows
    
    **Colored areas** = Land at or below the selected sea level  
    **Markers** = Important buildings (click to see if they're safe)  
    **Colors** = Blue (low risk) → Red (high risk)
    
    ### What It Doesn't Show
    
    This is a simplified model. It doesn't include:
    - Storm surges from hurricanes
    - Existing flood walls
    - Drainage systems
    - Wave action
    
    **Use this to identify problem areas** that need detailed engineering studies.
    """)

with tab1:
    st.markdown("## 🔬 How We Built This: Methodology & Calculations")
    
    st.markdown("""
    Here's exactly how we created this analysis, including all the math and data sources.
    """)
    
    st.markdown("### Step 1: Get Elevation Data")
    
    st.markdown("""
    <div class='method-box'>
        <h4>📏 Data Source: USGS 3DEP</h4>
        <p><b>What:</b> Digital Elevation Model (DEM) — shows height of every point on the ground</p>
        <p><b>Resolution:</b> 1 meter (very detailed)</p>
        <p><b>Format:</b> GeoTIFF raster file</p>
        <p><b>Coverage:</b> Long Beach city boundary</p>
        <p><b>Units:</b> Meters above mean sea level</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("""
# Python code used to download elevation data
import subprocess

bbox = {
    'west': -118.25, 
    'south': 33.70, 
    'east': -118.08, 
    'north': 33.85
}

subprocess.run([
    'eio', 'clip', 
    '-o', 'long_beach_dem.tif',
    '--bounds', f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
    '--product', 'SRTM1'
])
    """, language='python')
    
    st.markdown("### Step 2: Define Sea Level Rise Scenarios")
    
    st.markdown("""
    <div class='method-box'>
        <h4>🌊 Data Source: NOAA Sea Level Rise Projections</h4>
        <p><b>Scenarios chosen:</b></p>
        <ul>
            <li><b>1 foot (0.30 m) by 2030</b> — High probability, near-term</li>
            <li><b>3 feet (0.91 m) by 2050</b> — Medium probability, mid-century</li>
            <li><b>5 feet (1.52 m) by 2070</b> — Lower probability, late century</li>
            <li><b>7 feet (2.13 m) by 2100</b> — Worst case, end of century</li>
        </ul>
        <p><b>Based on:</b> NOAA Intermediate-High to Extreme scenarios</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.code("""
# Scenario configuration
scenarios = {
    '1ft_2030': {'rise_ft': 1, 'rise_m': 0.3048, 'year': 2030},
    '3ft_2050': {'rise_ft': 3, 'rise_m': 0.9144, 'year': 2050},
    '5ft_2070': {'rise_ft': 5, 'rise_m': 1.524, 'year': 2070},
    '7ft_2100': {'rise_ft': 7, 'rise_m': 2.1336, 'year': 2100}
}
    """, language='python')
    
    st.markdown("### Step 3: Identify Flood Zones (The Math)")
    
    st.markdown("""
    <div class='method-box'>
        <h4>🧮 Calculation Method: Bathtub Model</h4>
        <p><b>Simple formula:</b></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.latex(r"""
    	ext{Flooded} = egin{cases} 
    	ext{True} & 	ext{if } h_{	ext{ground}} \leq h_{	ext{sea level rise}} \
    	ext{False} & 	ext{otherwise}
    \end{cases}
    """)
    
    st.markdown("""
    **In plain English:** If the ground is at or below the new sea level, it floods.
    
    **For each pixel in the elevation data:**
    """)
    
    st.code("""
# Python implementation
import numpy as np
import rasterio

with rasterio.open('long_beach_dem.tif') as src:
    elevation = src.read(1)  # Read elevation data
    
    # For each scenario
    for scenario_name, config in scenarios.items():
        sea_level = config['rise_m']  # Sea level rise in meters
        
        # Mark areas at or below sea level
        flood_mask = elevation <= sea_level
        
        # Calculate flooded area
        pixel_area = src.transform[0] * src.transform[4]  # m² per pixel
        flooded_pixels = np.sum(flood_mask)
        flooded_area_m2 = flooded_pixels * abs(pixel_area)
        flooded_area_km2 = flooded_area_m2 / 1_000_000
    """, language='python')
    
    st.markdown("### Step 4: Calculate Property Impacts")
    
    st.markdown("""
    <div class='method-box'>
        <h4>🏘️ Data Source: U.S. Census Bureau</h4>
        <p><b>City-wide statistics:</b></p>
        <ul>
            <li>Total population: 466,742</li>
            <li>Total housing units: 171,632</li>
            <li>Median home value: $600,000</li>
            <li>City area: 130.8 km²</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**Formulas used:**")
    
    st.latex(r"""
    	ext{Properties at risk} = rac{	ext{Flooded area (km²)}}{	ext{Total city area (km²)}} 	imes 	ext{Total housing units} 	imes 1.5
    """)
    
    st.caption("*The 1.5 multiplier accounts for concentration of development in coastal/low-lying areas*")
    
    st.latex(r"""
    	ext{Population at risk} = 	ext{Properties at risk} 	imes 2.72
    """)
    
    st.caption("*2.72 = average household size in Long Beach*")
    
    st.latex(r"""
    	ext{Economic impact} = 	ext{Properties at risk} 	imes \$600{,}000
    """)
    
    st.caption("*$600,000 = median home value in Long Beach*")
    
    st.code("""
# Python implementation
CITY_STATS = {
    'total_population': 466742,
    'total_housing_units': 171632,
    'median_home_value': 600000,
    'land_area_km2': 130.8
}

for scenario_name, scenario_data in flood_scenarios.items():
    # Calculate percentages
    area_pct = (scenario_data['area_km2'] / CITY_STATS['land_area_km2']) * 100
    
    # Estimate properties (with coastal concentration factor)
    properties = int(CITY_STATS['total_housing_units'] * (area_pct / 100) * 1.5)
    
    # Estimate population (2.72 people per household)
    population = int(properties * 2.72)
    
    # Economic impact
    economic = properties * CITY_STATS['median_home_value']
    
    impacts.append({
        'scenario': scenario_name,
        'properties_at_risk': properties,
        'population_at_risk': population,
        'economic_impact_millions': economic / 1_000_000
    })
    """, language='python')
    
    st.markdown("### Step 5: Create Interactive Map")
    
    st.markdown("""
    <div class='method-box'>
        <h4>🗺️ Visualization: Folium + Streamlit</h4>
        <p><b>Process:</b></p>
        <ol>
            <li>Convert flood masks to vector polygons (GeoJSON)</li>
            <li>Simplify geometries for faster loading</li>
            <li>Clip to city boundary</li>
            <li>Style by scenario (colors, opacity)</li>
            <li>Add infrastructure points with risk calculation</li>
            <li>Create interactive tooltips and popups</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("### Data Sources Summary")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Elevation Data:**
        - Source: USGS 3DEP
        - URL: [nationalmap.gov](https://www.usgs.gov/3d-elevation-program)
        - Format: GeoTIFF
        - Resolution: 1m
        
        **Sea Level Projections:**
        - Source: NOAA
        - URL: [sealevel.nasa.gov](https://sealevel.nasa.gov/)
        - Report: Global & Regional SLR Scenarios
        """)
    
    with col2:
        st.markdown("""
        **Demographics:**
        - Source: U.S. Census 2020
        - URL: [census.gov](https://www.census.gov/)
        - Area: Long Beach, CA
        
        **City Boundary:**
        - Source: OpenStreetMap
        - URL: [openstreetmap.org](https://www.openstreetmap.org/)
        - Format: GeoJSON
        """)
    
    st.markdown("### Limitations & Assumptions")
    
    st.warning("""
    **This is a screening-level analysis with the following limitations:**
    
    1. **Bathtub model:** Assumes water can reach all areas below threshold (no barriers)
    2. **No storm surge:** Doesn't model extreme weather events
    3. **No drainage:** Doesn't account for stormwater systems
    4. **No protection:** Ignores existing levees and seawalls
    5. **Static projection:** Doesn't model year-by-year changes
    6. **Uniform distribution:** Property estimates assume even distribution
    
    **Best for:** Initial risk screening and planning priorities  
    **Not for:** Final engineering design or property-specific decisions
    """)

with tab2:
    st.markdown("### 📊 Compare All Scenarios")
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='year',
            y='properties_at_risk',
            title='Homes at Risk by Year',
            labels={'properties_at_risk': 'Number of Homes', 'year': 'Year'},
            text='properties_at_risk',
            color='year',
            color_continuous_scale=['#60a5fa', '#fb923c', '#f87171', '#b91c1c']
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        fig = px.bar(
            data['impacts'].sort_values('year'),
            x='year',
            y='economic_impact_millions',
            title='Property Value at Risk',
            labels={'economic_impact_millions': 'Value ($M)', 'year': 'Year'},
            text='economic_impact_millions',
            color='year',
            color_continuous_scale=['#60a5fa', '#fb923c', '#f87171', '#b91c1c']
        )
        fig.update_traces(texttemplate='$%{text:.0f}M', textposition='outside')
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("### 📋 Full Comparison Table")
    
    comparison_df = data['impacts'].copy()
    comparison_df['area_pct'] = (comparison_df['flooded_area_km2'] / 130.8 * 100).round(1)
    comparison_df['prop_pct'] = (comparison_df['properties_at_risk'] / 171632 * 100).round(1)
    
    display_df = comparison_df[['year', 'rise_ft', 'flooded_area_km2', 'area_pct',
                                 'properties_at_risk', 'prop_pct', 'population_at_risk',
                                 'economic_impact_millions']].copy()
    
    display_df.columns = ['Year', 'Rise (ft)', 'Area (km²)', 'Area %',
                          'Homes', 'Homes %', 'People', 'Value ($M)']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### 📈 How Risk Grows Over Time")
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['impacts']['year'],
        y=data['impacts']['properties_at_risk'],
        mode='lines+markers',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=12),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title='Properties at Risk Over Time',
        xaxis_title='Year',
        yaxis_title='Number of Properties',
        height=450,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    fig2 = px.area(
        data['impacts'],
        x='year',
        y='population_at_risk',
        title='People Affected Over Time',
        labels={'population_at_risk': 'Population', 'year': 'Year'},
        color_discrete_sequence=['#f87171']
    )
    fig2.update_layout(height=400)
    st.plotly_chart(fig2, use_container_width=True)

with tab4:
    st.markdown("### 💡 What Can Long Beach Do?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🟢 Now (0-5 years)
        
        **Quick wins:**
        - Install flood sensors
        - Update building codes
        - Community education
        - Emergency planning
        - Drainage improvements
        
        **Cost:** $1-10M  
        **Impact:** High awareness, better prepared
        """)
        
        st.markdown("""
        ### 🟡 Mid-Term (5-15 years)
        
        **Major projects:**
        - Build sea walls
        - Upgrade infrastructure
        - Relocate facilities
        - Create wetlands
        - Improve drainage
        
        **Cost:** $10-100M  
        **Impact:** Protected critical areas
        """)
    
    with col2:
        st.markdown("""
        ### 🔴 Long-Term (15+ years)
        
        **Transformative:**
        - Complete defense systems
        - Resilient neighborhoods
        - Managed retreat
        - Regional coordination
        - Adaptive zones
        
        **Cost:** $100M-$1B  
        **Impact:** City-wide resilience
        """)
        
        st.markdown("""
        ### 📥 Download Data
        """)
        
        csv = data['impacts'].to_csv(index=False)
        st.download_button(
            "📊 Download Analysis (CSV)",
            csv,
            "sea_level_rise_long_beach.csv",
            "text/csv"
        )

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <p><strong>Sea Level Rise Impact Simulator</strong> | Long Beach, California</p>
    <p>Data: USGS 3DEP • NOAA • U.S. Census | Created by Hristova022</p>
    <p><a href='https://github.com/hristova022/gis-portfolio'>View Code on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
