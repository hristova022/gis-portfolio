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

# ── Lightweight helpers (no GeoPandas/Fiona at runtime) ───────────────────────
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

    # Prefer simplified overlays
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

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1 class='main-header' style='text-align:center;color:#1e3a8a;'>🌊 Sea Level Rise Impact Simulator</h1>", unsafe_allow_html=True)
st.markdown("### Long Beach, California — Coastal Flooding Analysis")

st.markdown("""
This tool estimates which parts of Long Beach are **lower than future sea levels** under multiple scenarios
and summarizes potential exposure for **homes, people, and dollars**. It’s a **screening map** to spark
planning conversations — not a detailed engineering model.
""")
st.markdown("---")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Seal_of_Long_Beach%2C_California.svg/200px-Seal_of_Long_Beach%2C_California.svg.png", width=100)
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

    st.markdown("### 📊 Scenario Details")
    st.metric("Sea Level Rise", f"{scenario_data['rise_ft']} ft ({scenario_data['rise_m']:.2f} m)")
    st.metric("Projected Year", scenario_data['year'])
    st.metric("Area Affected", f"{scenario_data['area_km2']:.2f} km²")

    st.markdown("---")
    st.markdown("### 🗺️ Map Layers")
    show_flood = st.checkbox("Show Flood Zone", value=True)
    show_infra = st.checkbox("Show Infrastructure", value=True)

# ── Key Metrics ────────────────────────────────────────────────────────────────
impact_row = data['impacts'][data['impacts']['scenario'] == selected_scenario].iloc[0]
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("🌊 Area Flooded", f"{impact_row['flooded_area_km2']:.1f} km²",
              f"{impact_row['flooded_area_km2']/130.8*100:.1f}% of city")
with c2:
    st.metric("🏠 Properties at Risk", f"{impact_row['properties_at_risk']:,}",
              f"{impact_row['properties_at_risk']/171632*100:.1f}% of total")
with c3:
    st.metric("👥 Population at Risk", f"{impact_row['population_at_risk']:,}",
              f"{impact_row['population_at_risk']/466742*100:.1f}% of total")
with c4:
    st.metric("💰 Economic Impact", f"${impact_row['economic_impact_millions']:.0f}M",
              "Property value at risk")
st.markdown("---")

# ── Map ────────────────────────────────────────────────────────────────────────
st.markdown("### 🗺️ Interactive Flood Map")

bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')

# Boundary
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {'fillColor':'transparent','color':'#1e3a8a','weight':2}
).add_to(m)

# Flood zone (smoothed; clipped already in preprocessing)
if show_flood and selected_scenario in data['flood_zones']:
    colors = {'1ft_2030':'#3b82f6','3ft_2050':'#f59e0b','5ft_2070':'#ef4444','7ft_2100':'#991b1b'}
    folium.GeoJson(
        data['flood_zones'][selected_scenario],
        style_function=lambda x: {
            'fillColor': colors.get(selected_scenario, '#3b82f6'),
            'color': colors.get(selected_scenario, '#3b82f6'),
            'weight': 1, 'fillOpacity': 0.35
        },
        smooth_factor=1.2,
        tooltip=folium.GeoJsonTooltip(fields=['scenario','rise_ft','year'],
                                      aliases=['Scenario:','Rise (ft):','Year:'])
    ).add_to(m)

# Infrastructure
if show_infra:
    icon_map = {'Hospital': ('plus','red'),'Airport': ('plane','blue'),'Port': ('ship','darkblue'),
                'Attraction': ('star','purple'),'Historic Ship': ('anchor','darkred')}
    for feat in data['infrastructure'].get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if geom and geom.get('type') == 'Point':
            lon, lat = geom['coordinates'][:2]
            icon_name, color = icon_map.get(props.get('type',''), ('circle','gray'))
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{props.get('name','')}</b><br>{props.get('type','')}<br>Elevation: {props.get('elevation_ft',0)} ft",
                tooltip=props.get('name',''),
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

st_folium(m, width=1400, height=600)
st.markdown("---")

# ── Story + Charts + Insights ─────────────────────────────────────────────────
tab0, tab1, tab2, tab3 = st.tabs(["📖 Story", "📊 Scenario Comparison", "📈 Temporal Analysis", "💡 Key Insights"])

with tab0:
    st.markdown("## 📖 What you’re looking at — and why it matters")
    st.markdown("""
**The question:** *If the ocean rises by 1–7 feet, which parts of Long Beach are most exposed?*

**The map:** The blue area shows land inside the **city boundary** that sits **at or below** the chosen sea level.
It highlights neighborhoods and critical facilities that are most at risk during high tides or storms.

**Why this matters**
- **People & homes:** Floods displace families and damage property.
- **Economy:** Ports, airports, hospitals and attractions keep the city running.
- **Planning:** Knowing where water can go helps target upgrades (drainage, levees, building codes).

### 🧪 How this was made (plain English)
1. Start with **elevation data** for Long Beach (digital elevation model).
2. Choose a **sea-level scenario** (e.g., +3 ft by 2050).
3. Flag places where ground is **at or below** that height (“bathtub” model).
4. **Clip** the result to the **city boundary** (no shading the open ocean).
5. **Simplify** shapes so the map loads fast and stays readable.
6. Estimate **impacts** (homes, people, dollars) using city statistics.

> This is a **screening-level** view. It does **not** include storm surge, levees, groundwater rise, or drainage capacity.

### 📚 Data sources
- **Elevation:** USGS 3DEP/SRTM (with a high-quality synthetic fallback in Colab if the live download fails)
- **City boundary:** OpenStreetMap (Long Beach)
- **Population & housing:** U.S. Census (city totals)
- **Scenarios:** NOAA global sea-level guidance summarized as +1 ft, +3 ft, +5 ft, +7 ft

### ⚠️ Keep in mind
Real flooding depends on **tides, storms, defenses, drainage**, and local topography that can block/channel water.
Use this to **prioritize deeper studies** where exposure looks high.
""")

with tab1:
    st.markdown("### Compare all scenarios")
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
    st.markdown("### Impact progression over time")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data['impacts']['year'], y=data['impacts']['properties_at_risk'],
                             name='Properties at Risk',
                             line=dict(color='#3b82f6', width=3), mode='lines+markers'))
    fig.update_layout(title='Properties at Risk Over Time', height=400)
    st.plotly_chart(fig, use_container_width=True)
    fig2 = px.area(data['impacts'], x='year', y='economic_impact_millions',
                   title='Economic Impact Progression', color_discrete_sequence=['#991b1b'])
    st.plotly_chart(fig2, use_container_width=True)

with tab3:
    st.markdown("### Key insights")
    worst = data['impacts'].sort_values('properties_at_risk', ascending=False).iloc[0]
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"""
- **Immediate Risk (2030):** {int(data['impacts'].iloc[0]['properties_at_risk']):,} properties  
- **Long-term Risk (2100):** {int(worst['properties_at_risk']):,} properties  
- **Total Economic Exposure:** ${float(worst['economic_impact_millions']):.0f}M  
- **Population Affected:** up to {int(worst['population_at_risk']):,} residents
""")
    with c2:
        st.markdown("""
**Immediate (0–5 yrs)**  
• Enhance flood monitoring • Update building codes • Begin infrastructure hardening

**Medium-term (5–15 yrs)**  
• Coastal barriers • Upgrade stormwater • Relocate critical facilities

**Long-term (15+ yrs)**  
• Complete defense systems • Establish resilient zones
""")

st.markdown("---")
st.markdown("<div style='text-align:center;color:#64748b;'>"
            "<p><strong>Sea Level Rise Simulator</strong> | GIS Portfolio Project</p>"
            "<p>Data: USGS 3DEP, NOAA, US Census | Created by Hristova022</p>"
            "</div>", unsafe_allow_html=True)
