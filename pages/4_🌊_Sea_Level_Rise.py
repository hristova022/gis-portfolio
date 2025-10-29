"""
Sea Level Rise Simulator - Long Beach, California
Interactive coastal flooding analysis under different sea level rise scenarios
"""

import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

st.set_page_config(page_title="Sea Level Rise Simulator", page_icon="🌊", layout="wide")

# ── Utilities (no GeoPandas/GDAL required at runtime) ──────────────────────────
def _load_geojson(pathlike):
    with open(pathlike, 'r', encoding='utf-8') as f:
        return json.load(f)

def _bounds_from_geojson(gj):
    # Returns [minx, miny, maxx, maxy]
    def _walk_coords(geom):
        t = geom.get('type')
        if t == 'Point':
            yield geom['coordinates']
        elif t in ('MultiPoint', 'LineString'):
            for c in geom['coordinates']:
                yield c
        elif t in ('MultiLineString', 'Polygon'):
            for ring in geom['coordinates']:
                for c in ring:
                    yield c
        elif t == 'MultiPolygon':
            for poly in geom['coordinates']:
                for ring in poly:
                    for c in ring:
                        yield c
    xs, ys = [], []
    for feat in gj.get('features', []):
        for x, y in _walk_coords(feat['geometry']):
            xs.append(x); ys.append(y)
    return [min(xs), min(ys), max(xs), max(ys)] if xs else [-118.2, 33.7, -118.08, 33.85]

# Load data (all light-weight files)
@st.cache_data
def load_data():
    base_path = Path('data/sea_level_rise/processed')
    data = {}
    # JSON + CSV
    with open(base_path / 'flood_scenarios.json', 'r', encoding='utf-8') as f:
        data['scenarios'] = json.load(f)
    data['impacts'] = pd.read_csv(base_path / 'property_impact.csv')

    # GeoJSONs as dicts
    data['boundary'] = _load_geojson(base_path / 'long_beach_boundary.geojson')
    data['infrastructure'] = _load_geojson(base_path / 'infrastructure_all.geojson')

    # Flood zones per scenario as dicts
    data['flood_zones'] = {}
    for scenario in data['scenarios'].keys():
        p = base_path / f'flood_zone_{scenario}.geojson'
        if p.exists():
            data['flood_zones'][scenario] = _load_geojson(p)
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

        **Methodology:** Simple bathtub model (areas below projected sea levels)

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
bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3])/2, (bounds[0] + bounds[2])/2]
m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')

# Boundary
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {'fillColor': 'transparent', 'color': '#1e3a8a', 'weight': 2}
).add_to(m)

# Flood zone
if show_flood and selected_scenario in data['flood_zones']:
    colors = {'1ft_2030': '#3b82f6','3ft_2050': '#f59e0b','5ft_2070': '#ef4444','7ft_2100': '#991b1b'}
    folium.GeoJson(
        data['flood_zones'][selected_scenario],
        style_function=lambda x: {
            'fillColor': colors.get(selected_scenario, '#3b82f6'),
            'color': colors.get(selected_scenario, '#3b82f6'),
            'weight': 1, 'fillOpacity': 0.4
        },
        tooltip=folium.GeoJsonTooltip(fields=['scenario','rise_ft','year'],
                                      aliases=['Scenario:','Rise (ft):','Year:'])
    ).add_to(m)

# Infrastructure
if show_infra:
    icon_map = {'Hospital': ('plus', 'red'),'Airport': ('plane', 'blue'),
                'Port': ('ship', 'darkblue'),'Attraction': ('star', 'purple'),
                'Historic Ship': ('anchor', 'darkred')}
    for feat in data['infrastructure'].get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if geom and geom.get('type') == 'Point':
            lon, lat = geom['coordinates'][:2]
            icon_name, color = icon_map.get(props.get('type',''), ('circle','gray'))
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{props.get('name','')}</b><br>{props.get('type','')}<br>Elevation: {props.get('elevation_ft',0)}ft",
                tooltip=props.get('name',''),
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

st_folium(m, width=1400, height=600)
st.markdown("---")

# Analysis Tabs
tab1, tab2, tab3 = st.tabs(["📊 Scenario Comparison", "📈 Temporal Analysis", "💡 Key Insights"])
with tab1:
    st.markdown("### Compare All Scenarios")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(data['impacts'].sort_values('year'), x='scenario', y='properties_at_risk',
                     title='Properties at Risk', color='year', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(data['impacts'].sort_values('year'), x='scenario', y='economic_impact_millions',
                     title='Economic Impact ($M)', color='year', color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(data['impacts'], use_container_width=True, hide_index=True)

with tab2:
    st.markdown("### Impact Progression Over Time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['impacts']['year'], y=data['impacts']['properties_at_risk'],
                             name='Properties at Risk', line=dict(color='#3b82f6', width=3),
                             mode='lines+markers'))
    fig.update_layout(title='Properties at Risk Over Time', height=400)
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.area(data['impacts'], x='year', y='economic_impact_millions',
                   title='Economic Impact Progression', color_discrete_sequence=['#991b1b'])
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### 💡 Key Findings")
    worst_case = data['impacts'].sort_values('properties_at_risk', ascending=False).iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        - **Immediate Risk (2030):** {immediate:,} properties
        - **Long-term Risk (2100):** {worst:,} properties
        - **Total Economic Exposure:** ${econ:.0f}M
        - **Population Affected:** Up to {pop:,} residents
        """.format(
            immediate=int(data['impacts'].iloc[0]['properties_at_risk']),
            worst=int(worst_case['properties_at_risk']),
            econ=float(worst_case['economic_impact_millions']),
            pop=int(worst_case['population_at_risk'])
        ))
    with c2:
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
    c1, c2 = st.columns(2)
    with c1:
        csv = data['impacts'].to_csv(index=False)
        st.download_button("📊 Download Impact Analysis (CSV)", csv, "impact_analysis.csv", "text/csv")
    with c2:
        summary = json.dumps(data['scenarios'], indent=2)
        st.download_button("📋 Download Scenario Summary (JSON)", summary, "scenarios.json", "application/json")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b;">
    <p><strong>Sea Level Rise Simulator</strong> | GIS Portfolio Project</p>
    <p>Data: USGS 3DEP, NOAA, US Census | Created by Hristova022</p>
</div>
""", unsafe_allow_html=True)
