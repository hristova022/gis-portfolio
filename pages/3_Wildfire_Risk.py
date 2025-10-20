import streamlit as st
import pandas as pd
import pydeck as pdk
from pydeck.types import String as PDKString
import plotly.express as px
import requests, json

st.set_page_config(page_title="SoCal Wildfire Risk", page_icon="🔥", layout="wide")

st.title("🔥 Southern California Wildfire Risk Zones")
st.subheader("Esri-style Heat Map (points) + Kernel Density overlay (Spatial Analyst analog, meters) — using CAL FIRE/FRAP perimeters")

@st.cache_data
def load_data():
    base = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/"
    pts   = pd.read_csv(base + "wildfire_points_real.csv")              # real points (centroids)
    sm    = pd.read_csv(base + "wildfire_summary.csv")                  # data-driven zone metrics
    det   = requests.get(base + "wildfire_zones_detailed.json").json()
    bnds  = requests.get(base + "wildfire_kde_bounds.json").json()
    png   = base + "wildfire_kde.png"
    return pts, sm, det, bnds, png

points, summary, details, kde_bounds, kde_png = load_data()

# ---- Story intro (restored) ----
with st.container():
    st.markdown("""
    ### Why This Analysis Matters
    Southern California has **repeating wildfire corridors** driven by topography, **Santa Ana winds**, and the **Wildland-Urban Interface (WUI)**.
    This page shows **WHERE** risk concentrates using:
    - an Esri-style **Heat Map** (point density with adjustable radius/weight), and
    - a **Kernel Density** surface in **meters** (Spatial Analyst analog) for an analytical view.
    Data source: **CAL FIRE/FRAP Historic Fire Perimeters** (centroids, filtered).
    """)

st.divider()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🔥 Fire points (filtered)", f"{len(points):,}")
with col2:
    st.metric("🚨 Zones evaluated", "8")
with col3:
    st.metric("📅 Recency weighting", "Half-life ≈ 10 years")

st.divider()
st.markdown("### 🗺️ Southern California Wildfire Heat Surface")

c1, c2, c3, c4 = st.columns(4)
with c1:
    weight_field = st.selectbox("Weight field", ["weight_recent","weight_hist"], index=0,
        help="Esri Heat Map allows count or numeric weight. 'weight_recent' emphasizes newer fires.")
with c2:
    radius_px = st.slider("Heat map radius (px)", 15, 120, 45)
with c3:
    intensity  = st.slider("Intensity", 1.0, 8.0, 3.0, 0.1)
with c4:
    threshold  = st.slider("Threshold", 0.0, 1.0, 0.05, 0.01)

show_kde = st.checkbox("Show Kernel Density overlay (meters)", True)
kde_opac = st.slider("KDE opacity", 0.2, 1.0, 0.65) if show_kde else 0.0

layers = []
# (1) Esri-style Heat Map (deck.gl HeatmapLayer over many points)
heat = pdk.Layer(
    "HeatmapLayer",
    data=points,
    get_position=["longitude","latitude"],
    get_weight=weight_field,
    aggregation=PDKString("SUM"),
    radius_pixels=radius_px,
    intensity=intensity,
    threshold=threshold,
    color_range=[
        [255,255,204],[254,217,118],[254,178,76],
        [253,141,60],[252,78,42],[227,26,28],[189,0,38]
    ],
    pickable=False
)
layers.append(heat)

# (2) Analytical KDE raster overlay
if show_kde:
    b = [kde_bounds["west"], kde_bounds["south"], kde_bounds["east"], kde_bounds["north"]]
    bmp = pdk.Layer("BitmapLayer", data=None, image=kde_png, bounds=b, opacity=kde_opac)
    layers.append(bmp)

view_state = pdk.ViewState(latitude=34.0, longitude=-118.2, zoom=7)
deck = pdk.Deck(layers=layers, initial_view_state=view_state,
                map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json')
st.pydeck_chart(deck, use_container_width=True)

colA, colB = st.columns([3,1])
with colA:
    st.markdown("**Interpretation** — The Heat Map shows *relative* density (zoom/extent-relative, like ArcGIS Insights). The KDE overlay is a fixed-bandwidth surface in meters (akin to Spatial Analyst's Kernel Density).")
with colB:
    st.info("💡 Toggle **weight_hist** vs **weight_recent** to compare long-term corridors vs recent hotspots.")

st.markdown("---")
st.markdown("### 📊 Understanding the Risk Analysis")

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("#### 📅 PAST (Historical)")
    st.markdown("""
    We include fires since the selected year filter (see code). Larger historical events influence density via **log(area)**.
    """)
with c2:
    st.markdown("#### 🔴 PRESENT (Current Factors)")
    st.markdown("""
    **Recency weighting** (≈10-yr half-life) emphasizes corridors active in the last decade,
    reflecting current fuels, ignition patterns, Santa Ana corridors, and WUI exposure.
    """)
with c3:
    st.markdown("#### 🔮 FUTURE (Scenarios)")
    st.markdown("""
    For scenarios, apply uplifts to the KDE based on projected **hot/dry/windy days** or new WUI growth.
    (This page focuses on observed data; scenario sliders can be added later.)
    """)

st.markdown("#### 📍 Select a Zone for Details")
zone_names = summary['zone_name'].tolist()
selected_zone = st.selectbox("Choose a high-risk zone:", zone_names, index=0, label_visibility="collapsed")
zr = summary[summary['zone_name']==selected_zone].iloc[0]
detail = [d for d in details if d['name']==selected_zone][0]

d1, d2, d3 = st.columns(3)
d1.metric("Risk Score (0–100)", f"{int(zr['risk_score'])}")
d2.metric("Fires since 2000 (25 km)", f"{int(zr['fires_since_2000'])}")
d3.metric("Acres burned since 2000", f"{int(zr['burned_acres_since_2000']):,}")

with st.expander("📋 Zone Details", expanded=True):
    st.markdown(f"**{detail['description']}**")
    st.markdown(f"**Key Factors:** {summary.loc[summary['zone_name']==selected_zone, 'key_factors'].iloc[0]}")

st.divider()
st.markdown("### 📍 The 8 Risk Zones (data-driven)")

top3 = summary.nlargest(3, 'risk_score')
for _, row in top3.iterrows():
    with st.container():
        a,b,c = st.columns([3,1,1])
        with a:
            st.markdown(f"### {row['zone_name']}")
            st.markdown(f"**{row['area']}**")
        with b:
            if row['risk_score'] >= 90:
                st.error(f"**{int(row['risk_score'])}/100**"); st.caption("EXTREME RISK")
            elif row['risk_score'] >= 85:
                st.warning(f"**{int(row['risk_score'])}/100**"); st.caption("VERY HIGH RISK")
            else:
                st.info(f"**{int(row['risk_score'])}/100**"); st.caption("HIGH RISK")
        with c:
            st.metric("Fires (since 2000)", f"{int(row['fires_since_2000'])}")
            st.metric("Acres burned", f"{int(row['burned_acres_since_2000']):,}")
    st.divider()

st.markdown("### Other High-Risk Zones")
remaining = summary.iloc[3:][['zone_name','risk_score','fires_since_2000','burned_acres_since_2000','area']].copy()
remaining.columns = ['Zone','Risk Score','Fires since 2000','Acres burned','County']
st.dataframe(remaining, use_container_width=True, hide_index=True,
    column_config={"Risk Score": st.column_config.ProgressColumn("Risk Score", format="%d/100", min_value=0, max_value=100)})

st.divider()
st.markdown("### 📊 Risk Levels Compared")
fig = px.bar(summary.sort_values('risk_score', ascending=True), y='zone_name', x='risk_score',
             orientation='h', color='risk_score', color_continuous_scale='YlOrRd',
             labels={'zone_name':'Zone','risk_score':'Risk Score (0–100)'})
fig.update_layout(showlegend=False, height=420, xaxis_range=[0,100])
st.plotly_chart(fig, use_container_width=True)

st.caption("Data: CAL FIRE / FRAP Historic Fire Perimeters (centroids, filtered). Heat map = point-based, zoom-relative (Insights). KDE = fixed-bandwidth (Spatial Analyst analog).")
