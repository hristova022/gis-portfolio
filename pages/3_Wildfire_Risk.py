import streamlit as st
import pandas as pd
import pydeck as pdk
from pydeck.types import String as PDKString
import plotly.express as px
import requests, json, datetime

st.set_page_config(page_title="SoCal Wildfire Risk", page_icon="🔥", layout="wide")

st.title("🔥 Southern California Wildfire Risk")
st.subheader("Clear, data-driven mapping for anyone — using CAL FIRE/FRAP fire history")

@st.cache_data
def load_data():
    base = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/"
    pts   = pd.read_csv(base + "wildfire_points_real.csv")
    sm    = pd.read_csv(base + "wildfire_summary.csv")
    det   = requests.get(base + "wildfire_zones_detailed.json").json()
    bnds  = requests.get(base + "wildfire_kde_bounds.json").json()
    png   = base + "wildfire_kde.png"
    meta  = requests.get(base + "wildfire_methodology.json").json()
    ocean = requests.get(base + "ocean_mask_polys.json").json()
    return pts, sm, det, bnds, png, base, meta, ocean

points, summary, details, kde_bounds, kde_png, BASE_URL, META, OCEAN_POLYS = load_data()

# ---- Top summary from metadata ----
pts_count   = META["counts"]["points_filtered"]
zones_count = META["counts"]["zones_evaluated"]
year_min    = META["counts"]["years_covered_min"]
year_max    = META["counts"]["years_covered_max"]
half_life   = META["recency_weighting"]["half_life_years"]

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Data coverage (years)", f"{year_min}–{year_max}")
with c2: st.metric("🔥 Fire points (filtered)", f"{pts_count:,}")
with c3: st.metric("🚨 Zones evaluated", f"{zones_count}")
with c4: st.metric("📅 Recency weighting", f"Half-life ≈ {half_life} years")

st.markdown("---")

# ---- What you're looking at (add KDE explanation) ----
with st.container(border=True):
    st.markdown("### What you're looking at")
    st.markdown("""
- **Heat Map (points)** shows where historical fires cluster. Brighter = more nearby activity at your current zoom (Esri-style behavior).
- **Kernel Density (KDE)** builds a smooth surface in **meters**: each fire is treated like a small mound that softly spreads out; where many mounds overlap, the surface rises. We compute it in a meter-based projection (EPSG:3310) with a fixed search radius, and **clip it to land** so oceans and bays are transparent.
- Use the controls below to emphasize **recent activity** (recency × size) or **long-term activity** (size only), and to adjust the heat-map radius and intensity.
""")

# ---- Controls (friendly labels) ----
st.markdown("### 🗺️ Interactive wildfire heat surface")
label_to_field = {
    "Recent Activity (recency × size)": "weight_recent",
    "Long-Term Activity (size only)": "weight_hist",
}
colA, colB, colC, colD, colE, colF = st.columns([1.6,1,1,1,1,1.3])
with colA:
    weight_label = st.selectbox("Emphasize", list(label_to_field.keys()), index=0)
    weight_field = label_to_field[weight_label]
with colB:
    radius_px = st.slider("Heatmap radius (px)", 15, 120, 45)
with colC:
    intensity  = st.slider("Intensity", 1.0, 8.0, 3.0, 0.1)
with colD:
    threshold  = st.slider("Threshold", 0.0, 1.0, 0.05, 0.01)
with colE:
    palette = st.selectbox("Palette", ["YlOrRd (classic)", "Viridis (colorblind-friendly)"], index=0)
with colF:
    ocean_mask_on = st.checkbox("Hide heat over water", True, help="Adds a light ocean overlay so glow does not appear offshore.")

PALETTES = {
    "YlOrRd (classic)": [
        [255,255,204],[254,217,118],[254,178,76],
        [253,141,60],[252,78,42],[227,26,28],[189,0,38]
    ],
    "Viridis (colorblind-friendly)": [
        [68,1,84],[59,82,139],[44,113,142],
        [33,145,140],[39,173,129],[92,200,99],[253,231,37]
    ],
}

layers = []

# Heat map (point-based, zoom-relative)
heat = pdk.Layer(
    "HeatmapLayer",
    data=points,
    get_position=["longitude","latitude"],
    get_weight=weight_field,
    aggregation=PDKString("SUM"),
    radius_pixels=radius_px,
    intensity=intensity,
    threshold=threshold,
    color_range=PALETTES[palette],
    pickable=False
)
layers.append(heat)

# Analytical KDE bitmap (already clipped to land)
b = [kde_bounds["west"], kde_bounds["south"], kde_bounds["east"], kde_bounds["north"]]
layers.append(pdk.Layer("BitmapLayer", data=None, image=kde_png, bounds=b, opacity=0.65))

# Optional ocean overlay to visually mask any heatmap glow over water
if ocean_mask_on and len(OCEAN_POLYS) > 0:
    ocean_color = [228, 235, 240, 230]  # soft light-grey water to match basemap
    ocean_data = [{"poly": p} for p in OCEAN_POLYS]
    ocean_layer = pdk.Layer(
        "PolygonLayer",
        data=ocean_data,
        get_polygon="poly",
        get_fill_color=ocean_color,
        stroked=False,
        pickable=False
    )
    layers.append(ocean_layer)

view_state = pdk.ViewState(latitude=34.0, longitude=-118.2, zoom=7)
deck = pdk.Deck(layers=layers, initial_view_state=view_state,
                map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json')
st.pydeck_chart(deck, use_container_width=True)

st.markdown("---")

# ---- Zone details ----
st.markdown("### 📍 Eight well-known high-risk areas")
zone_names = summary['zone_name'].tolist()
selected_zone = st.selectbox("Select a zone:", zone_names, index=0)
zr = summary[summary['zone_name']==selected_zone].iloc[0]
detail = [d for d in details if d['name']==selected_zone][0]

c1, c2, c3 = st.columns(3)
c1.metric("Composite risk (0–100)", f"{int(zr['risk_score'])}")
c2.metric("Fires since 2000 (25 km)", f"{int(zr['fires_since_2000'])}")
c3.metric("Acres burned since 2000", f"{int(zr['burned_acres_since_2000']):,}")

with st.expander("Why this area is repeatedly at risk", expanded=True):
    st.markdown(f"**{detail['description']}**")
    st.markdown(f"**Key factors:** {summary.loc[summary['zone_name']==selected_zone, 'key_factors'].iloc[0]}")

st.divider()
st.markdown("### 📊 Compare the zones")
fig = px.bar(
    summary.sort_values('risk_score', ascending=True),
    y='zone_name', x='risk_score',
    orientation='h',
    color='risk_score',
    color_continuous_scale='Viridis' if 'Viridis' in palette else 'YlOrRd',
    labels={'zone_name':'Zone','risk_score':'Composite risk (0–100)'}
)
fig.update_layout(showlegend=False, height=420, xaxis_range=[0,100])
st.plotly_chart(fig, use_container_width=True)

# ---- Methodology & provenance (concise) ----
with st.expander("🧪 Methodology (math & settings)", expanded=False):
    st.markdown(f"""
**Weights**
- *Long-Term Activity*: `weight_hist = log(1 + acres)`  
- *Recent Activity*: `weight_recent = weight_hist × exp(-(this_year − YEAR_) / {half_life})`

**KDE (fixed-distance surface)**
- CRS: **{META['kde']['crs']}**, Kernel: **{META['kde']['kernel']}**  
- Cell size: **{META['kde']['cell_m']} m**, Bandwidth: **{META['kde']['bandwidth_m']} m**  
- **Clipped to land** to avoid any ocean/bay glow.

**Zone scores (0–100)**
1) Count fires and total burned acres within **25 km** of each zone center.  
2) Normalize each to 0–100; score = **0.5 × count_norm + 0.5 × acres_norm**.
""")

with st.expander("📥 Data source & query", expanded=False):
    bbox = META["data_source"]["bbox"]
    st.markdown(f"""
**Service:**  
{META['data_source']['service_url']}

**Extent:** xmin **{bbox['xmin']}**, ymin **{bbox['ymin']}**, xmax **{bbox['xmax']}**, ymax **{bbox['ymax']}**

**Filters:**  
- `YEAR_ >= {META['data_source']['filters']['YEARS_MIN']}`  
- `GIS_ACRES >= {META['data_source']['filters']['ACRES_MIN']}`  
- Returned **centroid-only** geometry; fields: FIRE_NAME, YEAR_, GIS_ACRES  
- Land source for masking: **{META['data_source']['land_source']}**

**Downloads:**  
- Points CSV: [{BASE_URL}wildfire_points_real.csv]({BASE_URL}wildfire_points_real.csv)  
- Zone summary: [{BASE_URL}wildfire_summary.csv]({BASE_URL}wildfire_summary.csv)  
- KDE PNG: [{BASE_URL}wildfire_kde.png]({BASE_URL}wildfire_kde.png)  
- KDE bounds: [{BASE_URL}wildfire_kde_bounds.json]({BASE_URL}wildfire_kde_bounds.json)  
- Methodology JSON: [{BASE_URL}wildfire_methodology.json]({BASE_URL}wildfire_methodology.json)
""")

st.caption("This summarizes where wildfire activity has clustered in Southern California using public data. Heat map = visual density (zoom-relative). KDE = analytical surface in meters (fixed distance), land-clipped. Not a forecast or official hazard designation.")
