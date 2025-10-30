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

# Simple, clean styling - matches your other pages
st.markdown("""
<style>
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
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

# Simple header - matches your style
st.title("🌊 Sea Level Rise Impact Simulator")
st.subheader("Long Beach, California — Coastal Flooding Analysis")

st.markdown("""
This interactive tool shows what could happen to Long Beach if sea levels rise. 
Think of it like filling a bathtub — as the water level goes up, which neighborhoods 
get flooded first? This helps us understand **who and what is at risk** so we can 
plan ahead and protect our communities.

**Why this matters:** Climate change is causing oceans to rise. Some parts of Long Beach 
are close to sea level, which means homes, businesses, and important buildings could 
flood in the future. This tool helps us see where the biggest risks are.
""")

st.markdown("---")

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Seal_of_Long_Beach%2C_California.svg/200px-Seal_of_Long_Beach%2C_California.svg.png", width=100)
    st.title("🌊 Choose a Scenario")
    
    st.markdown("""
    **What's a scenario?** Each scenario shows a different possible future based on 
    how much the ocean might rise and when. Scientists give us these predictions 
    based on climate models.
    """)
    
    scenario_labels = {
        '1ft_2030': '1 foot by 2030 (Very Likely)',
        '3ft_2050': '3 feet by 2050 (Likely)',
        '5ft_2070': '5 feet by 2070 (Possible)',
        '7ft_2100': '7 feet by 2100 (Worst Case)'
    }
    
    selected_label = st.selectbox("Select a future scenario:", list(scenario_labels.values()))
    selected_scenario = [k for k, v in scenario_labels.items() if v == selected_label][0]
    scenario_data = data['scenarios'][selected_scenario]
    
    st.markdown("### 📊 About This Scenario")
    st.metric("Sea Level Rise", f"{scenario_data['rise_ft']} feet ({scenario_data['rise_m']:.2f} meters)")
    st.metric("Expected By", scenario_data['year'])
    st.metric("Area Affected", f"{scenario_data['area_km2']:.2f} km²")
    st.caption(f"That's about {scenario_data['area_km2']/130.8*100:.1f}% of Long Beach")
    
    st.markdown("---")
    
    st.markdown("### 🗺️ What to Show on Map")
    show_flood = st.checkbox("Show flooded areas (blue)", value=True)
    show_infra = st.checkbox("Show important buildings", value=True)
    
    st.markdown("---")
    
    with st.expander("ℹ️ About This Tool"):
        st.markdown("""
        **What it does:** Shows which parts of Long Beach are at or below future sea levels.
        
        **How it works:** Uses elevation data (height above sea level) to identify 
        low-lying areas that could flood.
        
        **What it doesn't include:** Storm surges, existing flood walls, or drainage systems. 
        This is a simplified view to help with planning.
        
        **Data from:** U.S. Geological Survey, NOAA, and U.S. Census
        """)

# Impact metrics - simple and clear
impact_row = data['impacts'][data['impacts']['scenario'] == selected_scenario].iloc[0]

st.markdown("### 📊 What's at Risk in This Scenario")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "🌊 Flooded Area", 
        f"{impact_row['flooded_area_km2']:.1f} km²",
        f"{impact_row['flooded_area_km2']/130.8*100:.1f}% of city"
    )
    st.caption("Land that would be underwater")

with col2:
    st.metric(
        "🏠 Homes at Risk", 
        f"{int(impact_row['properties_at_risk']):,}",
        f"{impact_row['properties_at_risk']/171632*100:.1f}% of all homes"
    )
    st.caption("Houses and buildings affected")

with col3:
    st.metric(
        "👥 People Affected", 
        f"{int(impact_row['population_at_risk']):,}",
        f"{impact_row['population_at_risk']/466742*100:.1f}% of residents"
    )
    st.caption("Residents living in flood zones")

with col4:
    st.metric(
        "💰 Property Value", 
        f"${impact_row['economic_impact_millions']:.0f}M",
        "at risk"
    )
    st.caption("Total value of threatened property")

st.markdown("---")

# Map
st.markdown("### 🗺️ Interactive Flood Risk Map")

st.markdown("""
**How to read this map:**
- **Blue shaded areas** = Land that would be at or below the selected sea level
- **City outline** = Long Beach boundaries (dark blue dashed line)
- **Icons** = Important places like hospitals, airports, and the port
- **Click on anything** to learn more about it
""")

bounds = _bounds_from_geojson(data['boundary'])
center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
m = folium.Map(location=center, zoom_start=12, tiles='CartoDB positron')
m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

# Boundary
folium.GeoJson(
    data['boundary'],
    style_function=lambda x: {'fillColor':'transparent','color':'#1e3a8a','weight':2, 'dashArray':'5,5'}
).add_to(m)

# Flood zone
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
        tooltip=folium.GeoJsonTooltip(
            fields=['scenario','rise_ft','year'],
            aliases=['Scenario:','Sea Level Rise (ft):','Expected Year:']
        )
    ).add_to(m)

# Infrastructure
if show_infra:
    icon_map = {
        'Hospital': ('plus','red'),
        'Airport': ('plane','blue'),
        'Port': ('ship','darkblue'),
        'Attraction': ('star','purple'),
        'Historic Ship': ('anchor','darkred')
    }
    for feat in data['infrastructure'].get('features', []):
        props = feat.get('properties', {})
        geom = feat.get('geometry', {})
        if geom and geom.get('type') == 'Point':
            lon, lat = geom['coordinates'][:2]
            icon_name, color = icon_map.get(props.get('type',''), ('circle','gray'))
            
            # Check if facility is at risk
            facility_elevation = props.get('elevation_ft', 999)
            scenario_level = scenario_data['rise_ft'] * 3.28  # Convert scenario to feet
            at_risk = facility_elevation <= scenario_level
            risk_status = "⚠️ AT RISK" if at_risk else "✅ Currently Safe"
            
            folium.Marker(
                location=[lat, lon],
                popup=f"<b>{props.get('name','')}</b><br>{props.get('type','')}<br>Height above sea: {props.get('elevation_ft',0)} ft<br><b>{risk_status}</b>",
                tooltip=props.get('name',''),
                icon=folium.Icon(color=color, icon=icon_name, prefix='fa')
            ).add_to(m)

# Legend
_legend_html = """
{% macro html() %}
<div style="position: fixed; bottom: 16px; left: 16px; z-index: 9999;
            background: white; border: 1px solid #cbd5e1; border-radius: 8px;
            padding: 10px 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); font-size: 13px;">
  <div style="font-weight:bold;margin-bottom:6px;">Map Legend</div>
  <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
    <span style="display:inline-block;width:14px;height:14px;background:#3b82f6;opacity:0.35;border:1px solid #3b82f6;"></span>
    <span>Flooded area</span>
  </div>
  <div style="display:flex;align-items:center;gap:8px;margin:4px 0;">
    <span style="display:inline-block;width:14px;height:2px;background:#1e3a8a;border:1px dashed #1e3a8a;"></span>
    <span>City boundary</span>
  </div>
</div>
{% endmacro %}
"""
_legend_macro = MacroElement()
_legend_macro._template = Template(_legend_html)
m.get_root().add_child(_legend_macro)

st_folium(m, width=1400, height=600)

st.markdown("---")

# Tabs with plain language
tab0, tab1, tab2, tab3 = st.tabs(["📖 Understanding This Tool", "📊 Compare All Scenarios", "📈 Timeline View", "💡 What Can We Do?"])

with tab0:
    st.markdown("## 📖 Understanding Sea Level Rise (Plain English)")
    
    st.markdown("""
    ### What is sea level rise?
    
    Sea level rise is exactly what it sounds like — the ocean is getting higher. This happens 
    because of climate change, which causes two main things:
    
    1. **Ice is melting** — Glaciers and ice sheets in places like Greenland and Antarctica 
       are melting and adding more water to the oceans
    2. **Water expands when it's warm** — As the ocean gets warmer, the water actually takes 
       up more space, making sea levels rise
    
    ### Why does this matter for Long Beach?
    
    Long Beach sits right on the coast, and many neighborhoods are pretty close to sea level. 
    If the ocean rises, these low-lying areas could flood. We're not just talking about beaches — 
    we're talking about:
    
    - **Homes where families live** 🏠
    - **Schools and hospitals** 🏥
    - **Roads and utilities** 🚗
    - **Businesses and jobs** 💼
    - **The Port of Long Beach** (the 2nd busiest port in America!) 🚢
    
    ### How did you make this map?
    
    Here's what we did, step by step:
    
    **Step 1: Get elevation data**  
    We used information from the U.S. Geological Survey that tells us how high every piece 
    of land is above sea level. Think of it like a 3D model of the city.
    
    **Step 2: Pick a sea level**  
    We chose different amounts the ocean might rise (1 foot, 3 feet, 5 feet, 7 feet) and 
    different years when this might happen (2030, 2050, 2070, 2100).
    
    **Step 3: Find the low spots**  
    We marked every place in Long Beach that's at or below each sea level. These are the 
    areas that would be underwater if there was a flood.
    
    **Step 4: Calculate impacts**  
    We used census data to estimate how many homes, how many people, and how much property 
    value is in these risky areas.
    
    **Step 5: Make it interactive**  
    We put it all on a map so you can explore different scenarios and see what's at risk.
    
    ### What this tool does NOT show
    
    It's important to understand what this tool doesn't include:
    
    - **Storm surge** — When hurricanes or big storms push water inland, flooding can be much 
      worse than just sea level rise alone
    - **Existing protections** — Long Beach has some flood walls and levees, but we didn't 
      model these
    - **Drainage systems** — How well water drains away during floods
    - **Groundwater** — Rising seas can also push groundwater up from below
    
    Think of this as a **starting point** — it helps us identify problem areas so engineers 
    and city planners can do more detailed studies.
    
    ### Where does the data come from?
    
    - **Elevation:** U.S. Geological Survey (USGS) 3DEP program — high-quality height measurements
    - **Sea level scenarios:** NOAA (National Oceanic and Atmospheric Administration) — scientists 
      who study oceans and climate
    - **Population and homes:** U.S. Census Bureau — official count of people and housing
    - **City boundary:** OpenStreetMap — community-created geographic data
    
    ### Questions you might have
    
    **Q: Will this definitely happen?**  
    A: The amount and speed of sea level rise depends on future greenhouse gas emissions. Lower 
    emissions = less rise. Higher emissions = more rise. The scenarios show a range of possibilities.
    
    **Q: When will this happen?**  
    A: The ocean is already rising slowly (about 1 inch every 8 years currently). The bigger 
    impacts come later this century, but some areas are already seeing more flooding during 
    high tides.
    
    **Q: Can we stop it?**  
    A: We can slow it down by reducing emissions, but some sea level rise is already "locked in" 
    from past emissions. That's why planning and adaptation are important.
    
    **Q: What can Long Beach do?**  
    A: Many things! Build sea walls, improve drainage, update building codes, move critical 
    facilities to higher ground, create green space that can absorb water, and plan emergency 
    evacuations.
    """)

with tab1:
    st.markdown("### 📊 Compare All Scenarios Side-by-Side")
    
    st.markdown("""
    Here you can see all four possible futures at once. Notice how the numbers get bigger 
    as we look further into the future — that's because sea levels will continue rising 
    throughout this century.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            data['impacts'].sort_values('year'), 
            x='year', 
            y='properties_at_risk',
            title='How Many Homes Are at Risk?',
            labels={'properties_at_risk': 'Number of Homes', 'year': 'Year'},
            text='properties_at_risk'
        )
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("Each bar shows the number of homes that would be in flood risk zones for that year.")
    
    with col2:
        fig = px.bar(
            data['impacts'].sort_values('year'), 
            x='year', 
            y='economic_impact_millions',
            title='How Much Property Value Is at Risk?',
            labels={'economic_impact_millions': 'Property Value (Millions $)', 'year': 'Year'},
            text='economic_impact_millions'
        )
        fig.update_traces(texttemplate='$%{text:.0f}M', textposition='outside')
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
        st.caption("This shows the total dollar value of all the property in flood risk zones.")
    
    st.markdown("### 📋 All the Numbers in One Table")
    
    comparison_df = data['impacts'].copy()
    comparison_df['area_pct'] = (comparison_df['flooded_area_km2'] / 130.8 * 100).round(1)
    comparison_df['prop_pct'] = (comparison_df['properties_at_risk'] / 171632 * 100).round(1)
    
    display_df = comparison_df[['year', 'rise_ft', 'flooded_area_km2', 'area_pct', 
                                 'properties_at_risk', 'prop_pct', 'population_at_risk', 
                                 'economic_impact_millions']].copy()
    
    display_df.columns = ['Year', 'Sea Rise (ft)', 'Flooded Area (km²)', 'Area %', 
                          'Homes at Risk', 'Homes %', 'People Affected', 'Property Value ($M)']
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    st.markdown("""
    ### What This Tells Us
    
    Looking at all scenarios together, we can see:
    
    - **2030** (near future): Even 1 foot of sea level rise affects **{:,} homes** and 
      **${:.0f}M** in property
    - **2050** (mid-century): By the time today's kids are adults, risks triple
    - **2100** (end of century): In the worst case, over **{:,} homes** could be at risk
    
    The good news? **We have time to prepare.** But we need to start planning now.
    """.format(
        int(data['impacts'].iloc[0]['properties_at_risk']),
        data['impacts'].iloc[0]['economic_impact_millions'],
        int(data['impacts'].iloc[-1]['properties_at_risk'])
    ))

with tab2:
    st.markdown("### 📈 How Risk Grows Over Time")
    
    st.markdown("""
    This timeline shows how sea level rise impacts build up gradually over the decades. 
    It's not a sudden event — it's a slow process that gives us time to adapt if we 
    plan ahead.
    """)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=data['impacts']['year'],
        y=data['impacts']['properties_at_risk'],
        mode='lines+markers',
        name='Homes at Risk',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=10),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))
    
    fig.update_layout(
        title='Homes at Risk: Growing Over Time',
        xaxis_title='Year',
        yaxis_title='Number of Homes',
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.caption("The line goes up because more area floods as sea levels rise.")
    
    st.markdown("### Property Value at Risk Over Time")
    
    fig2 = px.area(
        data['impacts'],
        x='year',
        y='economic_impact_millions',
        title='Economic Impact: Growing Over Time',
        labels={'economic_impact_millions': 'Property Value ($M)', 'year': 'Year'},
        color_discrete_sequence=['#ef4444']
    )
    fig2.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig2, use_container_width=True)
    
    st.caption("This shows the dollar value of property in flood zones increasing over time.")
    
    st.markdown("""
    ### What the Timeline Shows
    
    - **Early years (2030s)**: Modest impacts, but still significant for affected families
    - **Mid-century (2050s)**: Impacts accelerate as more coastal areas are affected
    - **Late century (2070s-2100)**: Cumulative impacts become very large
    
    The rising line reminds us that **action today prevents bigger problems tomorrow**.
    """)

with tab3:
    st.markdown("### 💡 What Can We Do About This?")
    
    st.markdown("""
    The good news is we're not helpless! Cities around the world are preparing for sea level 
    rise. Here's what Long Beach can do, organized by when we should do it:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🟢 Right Now (Next 5 Years)
        
        **Things we can start immediately:**
        
        1. **Better monitoring** 🔍
           - Install water level sensors
           - Track flooding during high tides
           - Create early warning systems
        
        2. **Update building codes** 📋
           - Require new buildings to be higher up
           - Make rules about flood-proof construction
           - Set standards for renovations
        
        3. **Community education** 📚
           - Help people understand the risks
           - Teach emergency preparedness
           - Create flood response plans
        
        4. **Start small projects** 🛠️
           - Fix drainage problems
           - Add water-absorbent landscaping
           - Upgrade vulnerable utilities
        
        **Why now?** These steps don't cost much but make a big difference in being ready.
        """)
        
        st.markdown("""
        ### 🟡 Medium-Term (5-15 Years)
        
        **Bigger projects that take time:**
        
        1. **Build protection** 🧱
           - Sea walls in critical areas
           - Levees along the coast
           - Raised roads and bridges
        
        2. **Improve infrastructure** 🏗️
           - Upgrade stormwater systems
           - Raise electrical equipment
           - Protect water treatment plants
        
        3. **Relocate facilities** 📍
           - Move hospitals to higher ground
           - Relocate emergency services
           - Protect critical equipment
        
        4. **Green solutions** 🌳
           - Create wetlands that absorb water
           - Build parks that can flood safely
           - Plant trees and vegetation
        
        **Why now?** These projects take years to design and build, so starting soon means 
        they're ready when we need them.
        """)
    
    with col2:
        st.markdown("""
        ### 🔴 Long-Term (15+ Years)
        
        **Major transformations:**
        
        1. **Complete protection systems** 🛡️
           - Integrated coastal defenses
           - Comprehensive flood barriers
           - Citywide drainage upgrades
        
        2. **Adapt neighborhoods** 🏘️
           - Designate "resilient zones"
           - Create floating developments
           - Build water-friendly communities
        
        3. **Managed retreat** 🚚
           - Help people move from highest-risk areas
           - Transition some land back to wetlands
           - Focus development in safer zones
        
        4. **Regional cooperation** 🤝
           - Work with neighboring cities
           - Share resources and planning
           - Coordinate protection strategies
        
        **Why now?** These are big, expensive changes that require public discussion and 
        careful planning. Starting the conversation now gives us time to do it right.
        """)
        
        st.markdown("""
        ### 💰 What Does It Cost?
        
        **Estimated costs:**
        - Small projects: $1-10 million each
        - Medium projects: $10-100 million each  
        - Large projects: $100M-$1B each
        
        **Compare to damages:**
        - Doing nothing: Could cost **${:.0f} million** in property losses (2100 scenario)
        - Protection costs: Usually 10-20% of total at-risk value
        - **Every $1 spent on prevention saves $4-6 in damages**
        
        It's expensive, but much cheaper than rebuilding after disasters!
        """.format(data['impacts']['economic_impact_millions'].max()))
    
    st.markdown("---")
    
    st.markdown("""
    ### 🎯 What You Can Do Personally
    
    Even if you're not a city planner, there are things you can do:
    
    - **Know your risk** — Check if your home is in a flood zone
    - **Get flood insurance** — Especially if you're in a risk area
    - **Prepare for emergencies** — Have an evacuation plan and emergency kit
    - **Stay informed** — Follow city updates about flood protection projects
    - **Support action** — Vote for leaders who take climate adaptation seriously
    - **Reduce your impact** — Lower emissions to slow future sea level rise
    
    ### 📥 Download the Data
    
    Want to dig deeper? Download the analysis data for your own use:
    """)
    
    csv = data['impacts'].to_csv(index=False)
    st.download_button(
        label="📊 Download Full Analysis (CSV)",
        data=csv,
        file_name="long_beach_sea_level_rise_analysis.csv",
        mime="text/csv",
        help="Get all the numbers in a spreadsheet format"
    )
    
    json_data = json.dumps(data['scenarios'], indent=2)
    st.download_button(
        label="📋 Download Scenarios (JSON)",
        data=json_data,
        file_name="sea_level_scenarios.json",
        mime="application/json",
        help="Get the technical scenario details"
    )

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #64748b;'>
    <p><strong>Sea Level Rise Impact Simulator</strong> | GIS Portfolio Project</p>
    <p>Data Sources: USGS 3DEP, NOAA, U.S. Census Bureau</p>
    <p>Created by Hristova022 | <a href='https://github.com/hristova022/gis-portfolio'>View on GitHub</a></p>
</div>
""", unsafe_allow_html=True)
