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
    pts   = pd.read_csv(base + "wildfire_points_real.csv")      # real points (centroids)
    sm    = pd.read_csv(base + "wildfire_summary.csv")          # data-driven zone metrics
    det   = requests.get(base + "wildfire_zones_detailed.json").json()
    bnds  = requests.get(base + "wildfire_kde_bounds.json").json()
    png   = base + "wildfire_kde.png"
    meta  = requests.get(base + "wildfire_methodology.json").json()
    return pts, sm, det, bnds, png, base, meta

points, summary, details, kde_bounds, kde_png, BASE_URL, META = load_data()

# --------- Top summary driven by metadata ---------
pts_count   = META["counts"]["points_filtered"]
zones_count = META["counts"]["zones_evaluated"]
year_min    = META["counts"]["years_covered_min"]
year_max    = META["counts"]["years_covered_max"]
half_life   = META["recency_weighting"]["half_life_years"]
last_updated = datetime.date.today().isoformat()

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("Data coverage (years)", f"{year_min}–{year_max}")
with c2: st.metric("🔥 Fire points (filtered)", f"{pts_count:,}")
with c3: st.metric("🚨 Zones evaluated", f"{zones_count}")
with c4: st.metric("📅 Recency weighting", f"Half-life ≈ {half_life} years")

st.markdown("---")

# --------- 2-minute tour (plain language) ---------
with st.container(border=True):
    st.markdown("### 🧭 A 2-minute tour — How to read this page")
    st.markdown("""
- **This is not a forecast.** It maps **where fires have clustered** in the past (and more recently),
  which helps show **areas of persistent risk**.
- **Two layers** on the map:
  1) **Heat Map (points):** a smooth glow where many historical fires cluster. Brighter = **more activity nearby**.
  2) **Kernel Density (KDE):** an analytical surface (in meters) summarizing fire activity across the region.
- **Controls** let you adjust the **radius**, **intensity**, and whether to weight by **recent** fires
  (emphasize the last decade) or **historical size** (long-term patterns).
- **Zoom & pan** like any web map. The heat map is **relative to your current view** (like Esri’s Heat Map).
""")

# --------- Map controls (with palette toggle) ---------
st.markdown("### 🗺️ Interactive wildfire heat surface")
colA, colB, colC, colD, colE = st.columns([1.1,1,1,1,1])
with colA:
    weight_field = st.selectbox("Weight fires by", ["weight_recent","weight_hist"], index=0,
        help="• recent = emphasizes the last ~10 years\n• hist = long-term magnitude (log of burned acres)")
with colB:
    radius_px = st.slider("Heatmap radius (px)", 15, 120, 45)
with colC:
    intensity  = st.slider("Intensity", 1.0, 8.0, 3.0, 0.1)
with colD:
    threshold  = st.slider("Threshold", 0.0, 1.0, 0.05, 0.01)
with colE:
    palette = st.selectbox("Color palette", ["YlOrRd (classic)", "Viridis (colorblind-friendly)"], index=0)

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

show_kde = st.checkbox("Show Kernel Density overlay (meters)", True)
kde_opac = st.slider("KDE opacity", 0.2, 1.0, 0.65) if show_kde else 0.0

# --------- Build map layers ---------
layers = []
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

if show_kde:
    b = [kde_bounds["west"], kde_bounds["south"], kde_bounds["east"], kde_bounds["north"]]
    bmp = pdk.Layer("BitmapLayer", data=None, image=kde_png, bounds=b, opacity=kde_opac)
    layers.append(bmp)

view_state = pdk.ViewState(latitude=34.0, longitude=-118.2, zoom=7)
deck = pdk.Deck(layers=layers, initial_view_state=view_state,
                map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json')
st.pydeck_chart(deck, use_container_width=True)

# --------- Gentle “how to” hints ---------
colH1, colH2 = st.columns([3,1])
with colH1:
    st.markdown("**Tip:** Brighter colors = more historical fire activity. Switch to **weight_hist** for long-term corridors or **weight_recent** for recent hotspots.")
with colH2:
    st.info("💡 The heat map is **relative** to your current view.\nThe KDE overlay is **fixed in meters**.")

st.markdown("---")

# --------- Storytelling for non-experts ---------
st.markdown("### 🔍 What this map shows — in plain English")
colS1, colS2, colS3 = st.columns(3)
with colS1:
    st.markdown("#### 📅 Past")
    st.markdown(f"We include **years {year_min}–{year_max}**. Larger historical fires carry more weight.")
with colS2:
    st.markdown("#### 🔴 Present")
    st.markdown("**Recent fires** (last ~10 years) are emphasized when you pick *recent* weighting. This highlights **active corridors** under current conditions.")
with colS3:
    st.markdown("#### 🔮 Future")
    st.markdown("This is **not a forecast**, but it shows **where risk tends to cluster**. For future scenarios, analysts can adjust the KDE with climate or development projections.")

# --------- Zone details (clear wording) ---------
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

# --------- Non-expert guide sections ---------
with st.expander("ℹ️ Quick glossary (no jargon)", expanded=False):
    st.markdown("""
- **Heat map:** A smooth glow that shows **where many points are close together**. Here, the points are **fire centroids**.
- **Kernel Density (KDE):** A method that spreads each point into a small bump and **adds them up** to make a smooth surface.
- **Relative vs fixed:** The Heat Map is **relative** to your screen's current view; the KDE uses **fixed distances in meters**.
- **Weighting:** Count each fire equally (**recent**) or give bigger fires more influence (**hist** = log of burned acres).
- **WUI:** Wildland-Urban Interface — where neighborhoods border wildland vegetation; losses can be severe here.
""")

with st.expander("🧪 Methodology (exact math & settings)", expanded=False):
    st.markdown(f"""
**Weights**
- `weight_hist` = `log(1 + acres)`  
- `weight_recent` = `weight_hist × exp(-(this_year - YEAR_) / {half_life})`

**KDE (Spatial Analyst analog)**
- CRS: **{META['kde']['crs']}**, Kernel: **{META['kde']['kernel']}**  
- Cell size: **{META['kde']['cell_m']} m**, Bandwidth (search radius): **{META['kde']['bandwidth_m']} m**  
- Fast mode: **{META['kde']['fast_mode']}**, Weight used in KDE: **{META['weights']['weight_recent_uses']}**

**Zone scores (0–100)**
1) For each of 8 named zones, gather fires within **25 km** (haversine).  
2) Compute **count** and **total burned acres**.  
3) Normalize each to 0–100; score = **0.5 × count_norm + 0.5 × acres_norm**.
""")

with st.expander("📥 Data source & query (provenance)", expanded=False):
    bbox = META["data_source"]["bbox"]
    st.markdown(f"""
**Service:**  
{META['data_source']['service_url']}

**Extent (SoCal BBOX):**  
xmin **{bbox['xmin']}**, ymin **{bbox['ymin']}**, xmax **{bbox['xmax']}**, ymax **{bbox['ymax']}**

**Filters:**  
- `YEAR_ >= {META['data_source']['filters']['YEARS_MIN']}`  
- `GIS_ACRES >= {META['data_source']['filters']['ACRES_MIN']}`  
- returned **centroid-only** geometry; fields: {", ".join(META['data_source']['out_fields'])}

**Downloads:**  
- Points CSV: [{BASE_URL}wildfire_points_real.csv]({BASE_URL}wildfire_points_real.csv)  
- Zone summary: [{BASE_URL}wildfire_summary.csv]({BASE_URL}wildfire_summary.csv)  
- KDE PNG: [{BASE_URL}wildfire_kde.png]({BASE_URL}wildfire_kde.png)  
- KDE bounds: [{BASE_URL}wildfire_kde_bounds.json]({BASE_URL}wildfire_kde_bounds.json)  
- Methodology JSON: [{BASE_URL}wildfire_methodology.json]({BASE_URL}wildfire_methodology.json)
""")

with st.expander("🏘️ If you live in a high-risk area", expanded=False):
    st.markdown("""
- Create **defensible space** (clear dry vegetation, trim trees near structures).
- **Harden your home** (ember-resistant vents, Class-A roof, clean gutters).
- Plan **two ways out**; sign up for **local emergency alerts**.
- Talk with neighbors and prepare a **go-bag** for fast evacuations.
""")

st.caption("This page summarizes where wildfire activity has clustered in Southern California using public data. Heat map = visual density (relative). KDE = analytical density (meters). Not a forecast or official hazard designation.")
