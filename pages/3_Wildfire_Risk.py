import streamlit as st
import pandas as pd
import pydeck as pdk
from pydeck.types import String as PDKString
import plotly.express as px
import requests, json

st.set_page_config(page_title="SoCal Wildfire Risk", page_icon="🔥", layout="wide")
st.title("🔥 Southern California Wildfire Heat Map (Esri-style)")
st.caption("Point-based heat map with zoom/extent-relative smoothing and weight-by-field, matching ArcGIS Insights.")

@st.cache_data
def load_data():
    points_url  = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_points.csv"
    summary_url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_summary.csv"
    detail_url  = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/wildfire_zones_detailed.json"
    pts = pd.read_csv(points_url)
    sm  = pd.read_csv(summary_url)
    details = requests.get(detail_url).json()
    return pts, sm, details

points, summary, details = load_data()

# ---- Controls (Esri Insights lets you change radius and choose a field) ----
st.sidebar.header("Heat map controls")
weight_field = st.sidebar.selectbox(
    "Weight by field (numeric)", 
    ["risk_score", "homes_at_risk"],
    help="Esri heat maps use counts or a numeric field for weight."
)
radius_px = st.sidebar.slider("Radius (pixels)", 10, 80, 40, help="Similar to Insights' radius in the Appearance tab.")
intensity = st.sidebar.slider("Intensity (multiplier)", 1.0, 8.0, 3.0, 0.1)
threshold = st.sidebar.slider("Threshold (0–1)", 0.0, 1.0, 0.05, 0.01)

# Normalize optional large-magnitude fields (so homes_at_risk doesn't dominate)
pts = points.copy()
if weight_field == "homes_at_risk":
    # scale to ~0–100 to be in the same ballpark as risk_score
    s = pts[weight_field].astype(float)
    pts["weight"] = 100.0 * (s - s.min()) / (s.max() - s.min())
else:
    pts["weight"] = pts["risk_score"].astype(float)

# ---- HeatmapLayer (deck.gl) ----
# Matches Esri "Heat map": relative densities by zoom/extent, with user radius control.
heat_layer = pdk.Layer(
    "HeatmapLayer",
    data=pts,
    get_position=["longitude", "latitude"],
    get_weight="weight",
    aggregation=PDKString("SUM"),
    radius_pixels=radius_px,
    intensity=intensity,
    threshold=threshold,
    color_range=[
        [255,255,204], [254,217,118], [254,178,76],
        [253,141,60], [252,78,42], [227,26,28], [189,0,38]
    ],
    pickable=False,
)

view_state = pdk.ViewState(latitude=34.0, longitude=-118.2, zoom=7, pitch=0, bearing=0)

deck = pdk.Deck(
    layers=[heat_layer],
    initial_view_state=view_state,
    map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json'
)

st.pydeck_chart(deck, use_container_width=True)

st.markdown("**Tip:** As in ArcGIS Insights, this heat map shows *relative* density based on the current zoom and extent. Adjust the radius on the left.")

st.divider()

# Metrics
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("🏠 Homes at Risk (sum)", f"{int(summary['homes_at_risk'].sum()):,}")
with col2:
    st.metric("🚨 Zones ≥90 risk", int((summary['risk_score'] >= 90).sum()))
with col3:
    st.metric("📊 Avg Risk", f"{summary['risk_score'].mean():.0f}/100")

# Zone selector
st.subheader("📍 Zone Details")
selected = st.selectbox("Choose a zone:", summary['zone_name'].tolist(), index=0)
row = summary[summary['zone_name'] == selected].iloc[0]
detail = [d for d in details if d['name'] == selected][0]

c1, c2, c3 = st.columns(3)
c1.metric("Risk Score", f"{int(row['risk_score'])}/100")
c2.metric("Homes at Risk", f"{int(row['homes_at_risk']):,}")
c3.metric("Area", row['area'])

with st.expander("See details", expanded=True):
    st.markdown(f"**{detail['description']}**")
    st.markdown(f"**Key Factors:** {row['key_factors']}")
    st.markdown(f"**Recent Fires:** {row['recent_fires']}")

st.divider()
st.subheader("Risk levels compared")
fig = px.bar(
    summary.sort_values('risk_score', ascending=True),
    y='zone_name', x='risk_score', orientation='h',
    color='risk_score', color_continuous_scale='YlOrRd',
    labels={'zone_name':'Zone','risk_score':'Risk Score (0–100)'}
)
fig.update_layout(showlegend=False, height=420, xaxis_range=[75,100])
st.plotly_chart(fig, use_container_width=True)

st.caption("Heat map behavior follows ArcGIS Insights: relative densities by zoom/extent with a user-tunable radius and optional numeric weighting.")
