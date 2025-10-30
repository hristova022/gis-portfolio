"""
Sea Level Rise Simulator - Long Beach, California
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

# Enhanced CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(120deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .insight-box {
        background: #f0f9ff;
        border-left: 4px solid #3b82f6;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Keep your existing helper functions
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

# Keep your existing load_data
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

with st.spinner("🌊 Loading data..."):
    data = load_data()

# Enhanced header
st.markdown("""
<div class='main-header'>
    <h1>🌊 Sea Level Rise Impact Simulator</h1>
    <p>Long Beach, California — Coastal Flooding Analysis</p>
</div>
""", unsafe_allow_html=True)

# Quick stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Scenarios", f"{len(data['scenarios'])}", "2030-2100")
with col2:
    st.metric("Max Properties", f"{int(data['impacts']['properties_at_risk'].max()):,}")
with col3:
    st.metric("Max Impact", f"${data['impacts']['economic_impact_millions'].max():.0f}M")
with col4:
    st.metric("Study Area", "130.8 km²")

st.markdown("---")

# Sidebar - keep your existing sidebar code
with st.sidebar:
    st.title("🌊 Scenario Selector")
    
    scenario_labels = {
        '1ft_2030': '1 ft by 2030 (High)',
        '3ft_2050': '3 ft by 2050 (Medium)',
        '5ft_2070': '5 ft by 2070 (Low)',
        '7ft_2100': '7 ft by 2100 (Very Low)'
    }
    
    selected_label = st.selectbox("Select Scenario", list(scenario_labels.values()))
    selected_scenario = [k for k, v in scenario_labels.items() if v == selected_label][0]
    scenario_data = data['scenarios'][selected_scenario]
    
    st.markdown("### 📊 Details")
    st.metric("Rise", f"{scenario_data['rise_ft']} ft")
    st.metric("Year", scenario_data['year'])
    st.metric("Area", f"{scenario_data['area_km2']:.2f} km²")
    
    st.markdown("---")
    st.markdown("### 🗺️ Layers")
    show_flood = st.checkbox("Flood Zone", value=True)
    show_infra = st.checkbox("Infrastructure", value=True)

# Metrics
impact_row = data['impacts'][data['impacts']['scenario'] == selected_scenario].iloc[0]
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🌊 Area", f"{impact_row['flooded_area_km2']:.1f} km²")
with c2:
    st.metric("🏠 Properties", f"{int(impact_row['properties_at_risk']):,}")
with c3:
    st.metric("👥 Population", f"{int(impact_row['population_at_risk']):,}")
with c4:
    st.metric("💰 Impact", f"${impact_row['economic_impact_millions']:.0f}M")

st.markdown("---")

# Map - keep your existing map code
st.markdown("### 🗺️ Interactive Map")

bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')

folium.GeoJson(data['boundary'],
    style_function=lambda x: {'fillColor':'transparent','color':'#1e3a8a','weight':2}
).add_to(m)

if show_flood and selected_scenario in data['flood_zones']:
    colors = {'1ft_2030':'#3b82f6','3ft_2050':'#f59e0b','5ft_2070':'#ef4444','7ft_2100':'#991b1b'}
    folium.GeoJson(data['flood_zones'][selected_scenario],
        style_function=lambda x: {
            'fillColor': colors.get(selected_scenario, '#3b82f6'),
            'color': colors.get(selected_scenario, '#3b82f6'),
            'weight': 1, 'fillOpacity': 0.35
        }
    ).add_to(m)

if show_infra:
    icon_map = {'Hospital':('plus','red'),'Airport':('plane','blue'),'Port':('ship','darkblue')}
    for feat in data['infrastructure'].get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if geom and geom.get('type') == 'Point':
            lon, lat = geom['coordinates'][:2]
            icon_name, color = icon_map.get(props.get('type',''), ('circle','gray'))
            folium.Marker([lat, lon],
                popup=f"<b>{props.get('name','')}</b><br>{props.get('type','')}",
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

st_folium(m, width=1400, height=600)

st.markdown("---")

# Tabs - simplified version
tab1, tab2, tab3 = st.tabs(["📊 Compare", "📈 Timeline", "💡 Insights"])

with tab1:
    st.markdown("### Compare Scenarios")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.bar(data['impacts'].sort_values('year'), 
                     x='scenario', y='properties_at_risk', title='Properties at Risk')
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        fig = px.bar(data['impacts'].sort_values('year'),
                     x='scenario', y='economic_impact_millions', title='Economic Impact ($M)')
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### Timeline")
    fig = px.line(data['impacts'], x='year', y='properties_at_risk', 
                  markers=True, title='Properties at Risk Over Time')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### Key Insights")
    worst = data['impacts'].sort_values('properties_at_risk', ascending=False).iloc[0]
    st.markdown(f"""
    - **2030:** {int(data['impacts'].iloc[0]['properties_at_risk']):,} properties at risk
    - **2100:** {int(worst['properties_at_risk']):,} properties at risk
    - **Total exposure:** ${worst['economic_impact_millions']:.0f}M
    """)
    
    # Export
    csv = data['impacts'].to_csv(index=False)
    st.download_button("📥 Download Data", csv, "slr_analysis.csv", "text/csv")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#64748b;'>"
            "<p>Created by Hristova022 | Data: USGS, NOAA, Census</p></div>", 
            unsafe_allow_html=True)
