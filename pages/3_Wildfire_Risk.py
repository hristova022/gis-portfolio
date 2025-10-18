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

# SIMPLE BUT CLEAR - Named Risk Zones with Full Coverage
st.markdown("### 🗺️ Southern California Wildfire Risk Analysis")
st.markdown("**Past, Present & Future: 8 Major High-Risk Zones**")

# Create large visible zones
zones['radius'] = zones['risk_score'] * 300  # Larger based on risk
zones['color_rgb'] = zones['risk_score'].apply(
    lambda x: f"rgb({int(min(255, x*2.7))}, {int(max(0, 255-x*3))}, 0)"
)

import plotly.graph_objects as go

# Create map with large colored circles for each zone
fig = go.Figure()

# Add risk zones as large circles
fig.add_trace(go.Scattermapbox(
    lat=zones['latitude'],
    lon=zones['longitude'],
    mode='markers+text',
    marker=dict(
        size=zones['risk_score'] / 2.5,  # Size based on risk
        color=zones['risk_score'],
        colorscale=[
            [0, '#ffffe0'],      # Very light yellow
            [0.3, '#ffd700'],    # Gold
            [0.5, '#ffa500'],    # Orange
            [0.7, '#ff6347'],    # Tomato
            [0.85, '#ff0000'],   # Red
            [1, '#8b0000'],      # Dark red
        ],
        opacity=0.7,
        showscale=True,
        colorbar=dict(
            title="Risk<br>Score",
            x=1.02,
            tickvals=[20, 40, 60, 80, 95],
        ),
        sizemode='diameter'
    ),
    text=zones['zone_name'],
    textposition='top center',
    textfont=dict(size=10, color='black', family='Arial Black'),
    hovertemplate='<b>%{text}</b><br>' +
                  'Risk Score: %{marker.color:.0f}/100<br>' +
                  'Homes at Risk: %{customdata[0]}<br>' +
                  'Location: %{customdata[1]}<br>' +
                  '<extra></extra>',
    customdata=zones[['homes_display', 'area']].values,
    name='Risk Zones'
))

fig.update_layout(
    mapbox=dict(
        style='carto-positron',
        center=dict(lat=33.9, lon=-117.5),
        zoom=7.2
    ),
    height=650,
    margin={"r": 0, "t": 0, "l": 0, "b": 0},
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("**8 Named Risk Zones** - Each circle represents a major wildfire risk area. Size and color = risk level.")
    st.caption("Hover over zones to see: Risk score, homes at risk, and recent fire history")
with col2:
    st.info("💡 Hover for details")

# Add context about past/present/future
st.markdown("---")
st.markdown("### 📊 Understanding the Risk Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("#### 📅 PAST (Historical)")
    st.markdown("""
    **Major fires that shaped these zones:**
    - Thomas Fire (2017) - 281,893 acres
    - Woolsey Fire (2018) - 96,949 acres  
    - Bobcat Fire (2020) - 115,796 acres
    - Apple Fire (2020) - 33,424 acres
    
    These historical fires define where risk is highest.
    """)

with col2:
    st.markdown("#### 🔴 PRESENT (Current Factors)")
    st.markdown("""
    **What makes these zones dangerous today:**
    - Santa Ana wind corridors
    - Dense chaparral vegetation
    - Drought-stressed forests
    - Homes built in wildlands
    - Limited evacuation routes
    
    Current conditions amplify fire risk.
    """)

with col3:
    st.markdown("#### 🔮 FUTURE (Predictive)")
    st.markdown("""
    **Why these areas will remain high-risk:**
    - Climate change = hotter, drier
    - More homes being built in WUI
    - Aging infrastructure
    - Vegetation regrowth cycles
    - Wind pattern consistency
    
    Risk will likely increase over time.
    """)

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
