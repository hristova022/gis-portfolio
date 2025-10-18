import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import json

st.set_page_config(page_title="SoCal Wildfire Risk", page_icon="🔥", layout="wide")

st.title("🔥 Southern California Wildfire Risk Zones")
st.subheader("8 High-Risk Areas: A Clear, Simple View")

@st.cache_data
def load_data():
    zones_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_zones.csv"
    summary_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_summary.csv"
    detail_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_zones_detailed.json"
    
    zones = pd.read_csv(zones_url)
    summary = pd.read_csv(summary_url)
    
    import requests
    details = requests.get(detail_url).json()
    
    return zones, summary, details

zones, summary, details = load_data()

# Simple introduction
with st.container():
    st.markdown("""
    ### Why This Analysis Matters
    
    Southern California has **8 major wildfire risk zones** - areas where fires happen repeatedly. 
    
    This map shows **WHERE** the risk is highest and **WHY** each area is dangerous.
    
    **Three main factors create extreme fire risk:**
    1. **Geography** - Mountains and canyons that channel winds and make fires spread uphill rapidly
    2. **Weather** - Hot, dry Santa Ana winds that can push fires at speeds up to 100 mph
    3. **Where homes are built** - Communities built directly in fire-prone wildlands with only one or two roads out
    
    When homes are built in canyons, on hillsides, or surrounded by brush and forests, they become part of the 
    fuel that fires burn. This is called the "Wildland-Urban Interface" - the dangerous zone where neighborhoods 
    meet wildland. **These areas have the highest property loss when fires occur.**
    """)

st.divider()

# Simple stats
col1, col2, col3 = st.columns(3)

with col1:
    total_homes = summary['homes_at_risk'].sum()
    st.metric("🏠 Homes at Risk", f"{total_homes:,}")

with col2:
    extreme_zones = len(summary[summary['risk_score'] >= 90])
    st.metric("🚨 Extreme Risk Zones", f"{extreme_zones} out of 8")

with col3:
    avg_risk = summary['risk_score'].mean()
    st.metric("📊 Average Risk Level", f"{avg_risk:.0f}/100")

st.divider()

# PROFESSIONAL HEXAGONAL HEATMAP with Working Tooltips
st.markdown("### 🗺️ Where Are The High-Risk Zones?")

st.markdown("**Each hexagon represents a geographic area. Red = highest risk, Orange = high risk, Yellow = elevated risk.**")

# Base hexagon layer for coverage
hex_layer = pdk.Layer(
    "HexagonLayer",
    data=zones,
    get_position=["longitude", "latitude"],
    auto_highlight=True,
    elevation_scale=0,
    pickable=False,
    elevation_range=[0, 0],
    extruded=False,
    coverage=0.95,
    get_elevation_weight="risk_score",
    get_color_weight="risk_score",
    color_range=[
        [255, 255, 204, 220],  # Light yellow
        [255, 237, 160, 230],  # Yellow
        [254, 217, 118, 240],  # Yellow-orange
        [254, 178, 76, 245],   # Orange
        [253, 141, 60, 250],   # Orange-red
        [252, 78, 42, 255],    # Red
        [227, 26, 28, 255],    # Dark red
        [177, 0, 38, 255],     # Deep red
    ],
    radius=8000,
    upper_percentile=100,
    lower_percentile=0,
)

# Add zone markers for tooltips that actually work
summary['color'] = summary['risk_score'].apply(
    lambda x: [200, 0, 0, 255] if x >= 90 else [255, 100, 0, 255] if x >= 85 else [255, 150, 0, 255]
)

marker_layer = pdk.Layer(
    "ScatterplotLayer",
    data=summary,
    get_position=["longitude", "latitude"],
    get_fill_color="color",
    get_radius=12000,
    pickable=True,
    auto_highlight=True,
    opacity=0.6,
)

view_state = pdk.ViewState(
    latitude=33.9,
    longitude=-117.5,
    zoom=7.5,
    pitch=0,
    bearing=0
)

# Working tooltip with actual data
tooltip = {
    "html": "<div style='background: white; padding: 12px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.2);'>"
            "<h4 style='margin: 0 0 8px 0; color: #d32f2f;'>{zone_name}</h4>"
            "<p style='margin: 4px 0; color: #333;'><strong>Risk Score:</strong> {risk_score}/100</p>"
            "<p style='margin: 4px 0; color: #333;'><strong>Homes at Risk:</strong> {homes_at_risk:,}</p>"
            "<p style='margin: 4px 0; color: #666;'><strong>Location:</strong> {area}</p>"
            "</div>",
    "style": {
        "backgroundColor": "transparent",
        "color": "black"
    }
}

deck = pdk.Deck(
    layers=[hex_layer, marker_layer],
    initial_view_state=view_state,
    map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
    tooltip=tooltip
)

try:
    st.pydeck_chart(deck, use_container_width=True)
except Exception as e:
    st.warning("Interactive map couldn't load. Showing alternative visualization...")
    
    # Fallback: Simple plotly map
    import plotly.express as px
    
    fig = px.scatter_mapbox(
        summary,
        lat="latitude",
        lon="longitude",
        color="risk_score",
        size="homes_at_risk",
        color_continuous_scale="YlOrRd",
        size_max=30,
        zoom=7,
        hover_name="zone_name",
        hover_data={"risk_score": True, "homes_at_risk": True, "area": True, "latitude": False, "longitude": False},
        labels={"risk_score": "Risk Score", "homes_at_risk": "Homes at Risk"}
    )
    fig.update_layout(mapbox_style="carto-positron", height=600)
    st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**Color Scale:** 🟡 Light Yellow = Lower Risk → 🟠 Orange = High Risk → 🔴 Dark Red = Extreme Risk")
    st.caption("Hover over hexagons to see zone details | Geographic grid shows risk across SoCal")
with col2:
    st.info("💡 Hover to see details")

# Add zone selector below map
st.markdown("#### 📍 Select a Zone for Details")

zone_names = summary['zone_name'].tolist()
selected_zone = st.selectbox(
    "Choose a high-risk zone:",
    zone_names,
    index=0,
    label_visibility="collapsed"
)

# Show details for selected zone
zone_info = summary[summary['zone_name'] == selected_zone].iloc[0]
detail_info = [d for d in details if d['name'] == selected_zone][0]

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Risk Score", f"{zone_info['risk_score']}/100")
with col2:
    st.metric("Homes at Risk", f"{zone_info['homes_at_risk']:,}")
with col3:
    st.metric("Location", zone_info['area'])

with st.expander("📋 Zone Details", expanded=True):
    st.markdown(f"**{detail_info['description']}**")
    st.markdown(f"**Key Risk Factors:** {zone_info['key_factors']}")
    st.markdown(f"**Recent Major Fires:** {zone_info['recent_fires']}")

st.divider()

# RISK ZONE CARDS - One card per zone
st.markdown("### 📍 The 8 Risk Zones")

# Show top 3 in detail
top3 = summary.nlargest(3, 'risk_score')

for idx, row in top3.iterrows():
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.markdown(f"### {row['zone_name']}")
            st.markdown(f"**{row['area']}**")
            st.caption(row['description'])
        
        with col2:
            # Risk badge
            if row['risk_score'] >= 90:
                st.error(f"**{row['risk_score']}/100**")
                st.caption("EXTREME RISK")
            elif row['risk_score'] >= 85:
                st.warning(f"**{row['risk_score']}/100**")
                st.caption("VERY HIGH RISK")
            else:
                st.info(f"**{row['risk_score']}/100**")
                st.caption("HIGH RISK")
        
        with col3:
            st.metric("Homes at Risk", f"{row['homes_at_risk']:,}")
        
        with st.expander("See why this area is high-risk"):
            st.markdown(f"**Key Risk Factors:** {row['key_factors']}")
            st.markdown(f"**Recent Major Fires:** {row['recent_fires']}")
    
    st.divider()

# Show remaining zones in a simple table
st.markdown("### Other High-Risk Zones")

remaining = summary.iloc[3:]
display = remaining[['zone_name', 'risk_score', 'homes_at_risk', 'area']].copy()
display.columns = ['Zone', 'Risk Score', 'Homes at Risk', 'County']

st.dataframe(
    display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Risk Score": st.column_config.ProgressColumn(
            "Risk Score",
            format="%d/100",
            min_value=0,
            max_value=100,
        ),
    }
)

st.divider()

# Simple comparison chart
st.markdown("### 📊 Risk Levels Compared")

fig = px.bar(
    summary.sort_values('risk_score', ascending=True),
    y='zone_name',
    x='risk_score',
    orientation='h',
    color='risk_score',
    color_continuous_scale='YlOrRd',
    labels={'zone_name': 'Zone', 'risk_score': 'Risk Score (out of 100)'}
)
fig.update_layout(
    showlegend=False,
    height=400,
    xaxis_range=[75, 100]
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# What it means section
st.markdown("### 🎯 What This Means For You")

# Add new section about wildland-urban interface
with st.expander("🏘️ **Understanding the Wildland-Urban Interface (WUI)**", expanded=True):
    st.markdown("""
    ### What Is the Wildland-Urban Interface?
    
    The Wildland-Urban Interface (WUI) is where houses and wildland vegetation meet. Think of it as the 
    "edge" where neighborhoods bump up against forests, brush, and canyons.
    
    **Why It's Dangerous:**
    
    In these areas, your home becomes part of the fuel:
    - **Embers travel** - Wind-blown embers can land on wood decks, in gutters, or near fences
    - **Radiant heat** - The heat from nearby burning vegetation can ignite your home before flames arrive
    - **Continuous fuel** - Brush touching your fence, trees over your roof create a path for fire
    
    **Real Examples from Southern California:**
    
    - **Paradise Fire (2018)** - 85 people died, mostly trapped on evacuation routes with only 1-2 exits
    - **Woolsey Fire (2018, Malibu)** - Homes built in canyons with wooden decks burned when embers landed
    - **Holy Fire (2018, Orange County)** - Hillside homes with no defensible space lost, while those with cleared space survived
    
    **The Pattern:** Communities built in beautiful canyons and hillsides look amazing, but they're built 
    in the exact places that fires naturally burn. Add strong winds, and fires move faster than people can evacuate.
    """)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### If You Live In These Areas:")
    st.markdown("""
    1. **Know your zone's risk level** - Check the map above
    2. **Create defensible space** - Clear brush 100ft from your home
    3. **Harden your home** - Replace wood roofs, cover vents, remove dead vegetation
    4. **Have an evacuation plan** - Know 2 ways out, practice the route
    5. **Sign up for alerts** - Get emergency notifications on your phone
    6. **Prepare a go-bag** - Be ready to leave in 10 minutes
    """)

with col2:
    st.markdown("#### Why These Zones Are High-Risk:")
    st.markdown("""
    **Geography & Weather:**
    - **Santa Ana Winds** - Hot, dry winds that can spread fires at 100+ mph
    - **Mountain Canyons** - Act like chimneys, pushing fires uphill rapidly
    - **Dense Vegetation** - Dry brush, chaparral, and forests fuel fires
    
    **How Communities Are Built:**
    - **Homes in Wildlands** - Built directly in or next to fire-prone brush and forests
    - **Narrow Canyon Roads** - Only one or two ways out, creating evacuation bottlenecks  
    - **Wooden Decks & Roofs** - Construction materials that catch embers easily
    - **No Defensible Space** - Houses surrounded by flammable vegetation within 30 feet
    - **Remote Locations** - Far from fire stations, limited water for firefighting
    
    These areas are called the "Wildland-Urban Interface" - where homes meet wildland. 
    **When fire comes, it burns both the forest AND the neighborhood together.**
    """)

st.divider()

# Simple methodology
with st.expander("ℹ️ How We Calculated Risk"):
    st.markdown("""
    ### Simple Risk Scoring
    
    Each zone's risk score is based on:
    
    - **Past Fires** (30%) - Has it burned before?
    - **Weather** (25%) - Is it in a Santa Ana wind zone?
    - **Vegetation** (20%) - How much dry brush and trees?
    - **Communities** (15%) - How many homes are there?
    - **Access** (10%) - Can firefighters get there easily?
    
    **Data Sources:**
    - CAL FIRE (California fire history)
    - County records (home counts)
    - NOAA (weather patterns)
    - Local fire departments
    
    **Important:** Risk scores show probability and impact, but they can't predict 
    exactly when or where a fire will start. Weather and human actions also matter.
    """)

st.markdown("---")
st.caption("🔥 Southern California Wildfire Risk Analysis | Data: CAL FIRE, County Records, NOAA | By Luba Hristova")
