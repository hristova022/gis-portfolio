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
    
    Southern California has **8 major wildfire risk zones** - areas where fires happen repeatedly due to geography, 
    weather patterns, and how communities are built.
    
    This map shows **WHERE** the risk is highest and **WHY** each area is dangerous.
    
    **No technical jargon. Just clear information.**
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

# SIMPLE MAP - Just colored circles, no fancy 3D
st.markdown("### 🗺️ Where Are The High-Risk Zones?")

st.markdown("**Each circle is a high-risk area. Bigger and redder = more dangerous.**")

# Simple scatter plot layer
map_data = summary.copy()

# Create simple color based on risk
def get_color(risk):
    if risk >= 90:
        return [180, 0, 0, 200]  # Dark red
    elif risk >= 85:
        return [255, 0, 0, 180]  # Red
    else:
        return [255, 100, 0, 160]  # Orange

map_data['color'] = map_data['risk_score'].apply(get_color)
map_data['radius'] = map_data['risk_score'] * 600  # Size based on risk

layer = pdk.Layer(
    'ScatterplotLayer',
    data=map_data,
    get_position='[longitude, latitude]',
    get_color='color',
    get_radius='radius',
    pickable=True,
    auto_highlight=True,
)

view_state = pdk.ViewState(
    latitude=33.9,
    longitude=-117.5,
    zoom=7,
    pitch=0,
    bearing=0
)

deck = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style='mapbox://styles/mapbox/light-v10',
    tooltip={
        "html": "<b style='font-size:16px'>{zone_name}</b><br/>"
                "<b>Risk:</b> {risk_score}/100<br/>"
                "<b>Homes:</b> {homes_at_risk:,}<br/>"
                "<b>County:</b> {area}",
        "style": {"backgroundColor": "white", "color": "black", "fontSize": "14px", "padding": "10px"}
    }
)

st.pydeck_chart(deck, use_container_width=True)

col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("🔴 **Extreme Risk (90-95)** | 🟠 **Very High Risk (85-90)** | 🟠 **High Risk (80-85)**")
with col2:
    st.info("💡 Hover over circles for details")

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

col1, col2 = st.columns(2)

with col1:
    st.markdown("#### If You Live In These Areas:")
    st.markdown("""
    1. **Know your zone's risk level** - Check the map above
    2. **Create defensible space** - Clear brush 100ft from your home
    3. **Have an evacuation plan** - Know 2 ways out
    4. **Sign up for alerts** - Get emergency notifications
    5. **Prepare a go-bag** - Be ready to leave quickly
    """)

with col2:
    st.markdown("#### Why These Zones Are High-Risk:")
    st.markdown("""
    - **Santa Ana Winds** - Dry, powerful winds spread fires fast
    - **Dense Vegetation** - Lots of fuel for fires
    - **Mountain Terrain** - Fires move uphill quickly
    - **Many Homes** - Built in fire-prone areas
    - **History** - These areas have burned before
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
