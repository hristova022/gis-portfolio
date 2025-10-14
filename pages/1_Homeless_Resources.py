import streamlit as st
import pandas as pd
import json
import pydeck as pdk
import plotly.graph_objects as go

st.set_page_config(page_title="LA County Homeless Analysis | GIS Portfolio", page_icon="🏠", layout="wide")

st.title("🏠 LA County Homeless Services: Are We Keeping Pace?")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/la_county_homeless_temporal.json"
    try:
        import requests
        response = requests.get(url)
        return response.json()
    except:
        url_basic = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/homeless_services_data.json"
        response = requests.get(url_basic)
        return response.json()

data = load_data()
has_temporal = 'homeless_trends' in data

if has_temporal:
    st.markdown(f'''
    ## 📈 The Gap is Widening
    
    **From 2015 to 2025, LA County's homeless population grew {data['gap_analysis']['homeless_growth_pct']:.1f}% 
    while shelter capacity increased only {data['gap_analysis']['shelter_capacity_growth_pct']:.1f}%.**
    
    Despite adding {data['summary']['new_facilities_since_2015']} new facilities, there are now 
    **{data['gap_analysis']['beds_per_100_now']:.1f} beds per 100 homeless individuals** 
    (down from {data['gap_analysis']['beds_per_100_then']:.1f} in 2015).
    
    By 2027, we'll need **{data['forecast_2027']['additional_beds_needed']:,} additional beds** 
    just to maintain current service levels.
    ''')
    
    st.divider()
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📅 View Services By Year")
        selected_year = st.select_slider("Select Year", options=[2015, 2018, 2020, 2023, 2025], value=2025)
        
        df_trends = pd.DataFrame(data['homeless_trends'])
        year_data = df_trends[df_trends['year'] == selected_year].iloc[0] if selected_year in df_trends['year'].values else df_trends.iloc[-1]
        
        st.metric("Homeless Count", f"{int(year_data['homeless_count']):,}")
        st.metric("Shelter Beds", f"{int(year_data['total_beds']):,}")
        st.metric("Beds per 100", f"{year_data['beds_per_100_homeless']:.1f}")
    
    with col2:
        st.markdown("### 📊 The Growing Gap: 2015-2025")
        
        df_trends_norm = df_trends.copy()
        df_trends_norm['homeless_index'] = (df_trends_norm['homeless_count'] / df_trends_norm['homeless_count'].iloc[0]) * 100
        df_trends_norm['beds_index'] = (df_trends_norm['total_beds'] / df_trends_norm['total_beds'].iloc[0]) * 100
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_trends_norm['year'], y=df_trends_norm['homeless_index'],
            name='Homeless Population', line=dict(color='red', width=3), mode='lines+markers'))
        fig.add_trace(go.Scatter(x=df_trends_norm['year'], y=df_trends_norm['beds_index'],
            name='Shelter Capacity', line=dict(color='green', width=3), mode='lines+markers'))
        fig.update_layout(yaxis_title='Growth Index (2015 = 100)', xaxis_title='Year',
            hovermode='x unified', height=300, margin=dict(l=0, r=0, t=20, b=0), showlegend=True)
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📈 Both metrics indexed to 2015 baseline (100) to show relative growth")
    
    st.divider()
    
    df_facilities = pd.DataFrame(data['historical_facilities'])
    df_year_facilities = df_facilities[df_facilities['year'] <= selected_year].drop_duplicates(subset=['name'])
else:
    df_year_facilities = pd.DataFrame(data['services'])
    selected_year = 2025

col1, col2, col3, col4 = st.columns(4)

if has_temporal:
    with col1:
        st.metric(f"Services in {selected_year}", len(df_year_facilities))
    with col2:
        st.metric("Emergency Shelters", len(df_year_facilities[df_year_facilities['type'] == 'shelter']))
    with col3:
        st.metric("Current Homeless", f"{data['summary']['current_homeless_count']:,}")
    with col4:
        gap_pct = data['gap_analysis']['homeless_growth_pct'] - data['gap_analysis']['shelter_capacity_growth_pct']
        st.metric("Service Gap", f"+{gap_pct:.1f}%", delta_color="inverse")

st.divider()

st.markdown("### 🔍 Filter Services")
st.caption("Narrow down the facilities shown on the map using the filters below")

col1, col2, col3 = st.columns(3)

with col1:
    service_types_raw = ['All'] + sorted(df_year_facilities['type'].unique().tolist())
    service_types_display = {'All': 'All Services', 'shelter': 'Emergency Shelters',
        'food_bank': 'Food Banks & Meal Programs', 'social_facility': 'Support Services & Programs'}
    selected_type_display = st.selectbox("Service Type", 
        [service_types_display.get(t, t) for t in service_types_raw], help="Filter by the type of service provided")
    selected_type = [k for k, v in service_types_display.items() if v == selected_type_display][0]

with col2:
    cities = ['All'] + sorted([c for c in df_year_facilities['city'].unique() if c])
    selected_city = st.selectbox("City", cities, help="Focus on facilities in a specific city")
    if selected_city != 'All':
        st.caption(f"🎯 Filtering to {selected_city}")

with col3:
    search_term = st.text_input("Search Facility Name", placeholder="e.g., Union Rescue",
        help="Search for a specific facility by name")

filtered_df = df_year_facilities.copy()
if selected_type != 'All':
    filtered_df = filtered_df[filtered_df['type'] == selected_type]
if selected_city != 'All':
    filtered_df = filtered_df[filtered_df['city'] == selected_city]
if search_term:
    filtered_df = filtered_df[filtered_df['name'].str.contains(search_term, case=False, na=False)]

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader(f"📍 Service Locations Map - {selected_year}")
    st.caption("Zoom and pan to explore. Hover over markers for facility details.")
    
    def get_color(service_type):
        colors = {'shelter': [255, 0, 0, 200], 'food_bank': [0, 200, 0, 200], 'social_facility': [0, 100, 255, 200]}
        return colors.get(service_type, [128, 128, 128, 200])
    
    def get_type_label(service_type):
        labels = {'shelter': 'Emergency Shelter', 'food_bank': 'Food Bank / Meal Program', 'social_facility': 'Support Services'}
        return labels.get(service_type, service_type)
    
    filtered_df['color'] = filtered_df['type'].apply(get_color)
    filtered_df['type_label'] = filtered_df['type'].apply(get_type_label)
    
    # Calculate center from filtered data
    if len(filtered_df) > 0:
        center_lat = filtered_df['lat'].mean()
        center_lon = filtered_df['lon'].mean()
        
        # Adjust zoom based on spread
        lat_range = filtered_df['lat'].max() - filtered_df['lat'].min()
        lon_range = filtered_df['lon'].max() - filtered_df['lon'].min()
        max_range = max(lat_range, lon_range)
        
        if max_range < 0.05:
            zoom = 13
        elif max_range < 0.15:
            zoom = 11
        elif max_range < 0.3:
            zoom = 10
        else:
            zoom = 9.5
    else:
        center_lat, center_lon, zoom = 33.95, -118.35, 9.5
    
    if has_temporal:
        df_coverage = pd.DataFrame(data['coverage_analysis'])
        gap_areas = df_coverage[df_coverage['service_count'] == 0].copy()
        gap_areas['color'] = [[255, 165, 0, 30]] * len(gap_areas)
        gap_areas['name'] = ['Service Gap Zone'] * len(gap_areas)
        gap_areas['type_label'] = ['Area with no services within 1+ mile'] * len(gap_areas)
        gap_areas['address'] = [''] * len(gap_areas)
        gap_areas['city'] = [''] * len(gap_areas)
        
        gap_layer = pdk.Layer('ScatterplotLayer', data=gap_areas, get_position='[lon, lat]',
            get_color='color', get_radius=1500, radius_min_pixels=5, radius_max_pixels=50, pickable=True)
    else:
        gap_layer = None
    
    service_layer = pdk.Layer('ScatterplotLayer', data=filtered_df, get_position='[lon, lat]',
        get_color='color', get_radius=200, radius_min_pixels=3, radius_max_pixels=20, pickable=True)
    
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=zoom, pitch=0)
    
    layers = [gap_layer, service_layer] if gap_layer else [service_layer]
    
    # Force map update with unique key
    map_key = f"{selected_city}_{selected_type}_{selected_year}_{len(filtered_df)}"
    
    r = pdk.Deck(layers=layers, initial_view_state=view_state,
        tooltip={'html': '<b>{name}</b><br/><i>{type_label}</i><br/>{city}<br/>{address}',
                 'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}})
    
    st.pydeck_chart(r, key=map_key)

with col2:
    st.subheader("📊 Analysis Summary")
    st.metric("Facilities Shown", len(filtered_df))
    
    if has_temporal:
        st.markdown("**Services by Type:**")
        type_counts = filtered_df['type'].value_counts()
        for service_type, count in type_counts.items():
            st.markdown(f"• {get_type_label(service_type)}: {count}")
        st.markdown("---")
        st.markdown(f"**Service Gap Areas:** {data['summary']['service_gap_areas']}")
        st.caption("Orange zones on map show areas lacking nearby services")
    
    st.markdown('''
    ---
    **Map Legend:**
    - 🔴 **Emergency Shelters** - Overnight housing
    - 🟢 **Food Banks** - Meals and groceries  
    - 🔵 **Support Services** - Case management, healthcare, job help
    - 🟠 **Service Gap Zones** - No facilities within walking distance (1+ mile)
    ''')

st.divider()

# DETAILED METHODOLOGY SECTION
st.markdown("## 📊 Methodology & Data Sources")
st.markdown("*How this analysis was conducted and how you can verify the data*")

tab1, tab2, tab3 = st.tabs(["📥 Data Collection", "🔬 Analysis Process", "✅ Verification & Reproducibility"])

with tab1:
    st.markdown("""
    ### Data Collection Methods
    
    This analysis combines multiple authoritative data sources to create a comprehensive picture of homeless services in LA County.
    
    #### 1. OpenStreetMap (OSM) - Primary Geospatial Data
    **Source:** [OpenStreetMap](https://www.openstreetmap.org/)
    
    - **What it is:** Community-maintained global map database with over 9 million contributors
    - **How we use it:** Query OSM using Overpass API for facilities tagged as:
      - `amenity=shelter` - Emergency shelters
      - `amenity=food_bank` - Food distribution centers
      - `amenity=social_facility` - Support service centers
    - **API Used:** [Overpass API](https://wiki.openstreetmap.org/wiki/Overpass_API)
    - **Query Region:** LA County bounding box (33.70°N to 34.35°N, -118.67°W to -118.05°W)
    
    **Verify the data yourself:**
    - Visit [Overpass Turbo](https://overpass-turbo.eu/) 
    - Paste this query to see shelters in Long Beach:
    ```
    [out:json];
    (
      node["amenity"="shelter"](33.70,-118.25,33.85,-118.05);
      way["amenity"="shelter"](33.70,-118.25,33.85,-118.05);
    );
    out center;
    ```
    
    #### 2. Manual Verification - Ground Truth Data
    **Sources:**
    - [LA Homeless Services Authority (LAHSA)](https://www.lahsa.org/) - Official provider directory
    - [211 LA County](https://211la.org/) - Community resource database
    - Direct verification with city websites and facility contacts
    
    **Process:**
    - Cross-referenced OSM data with official provider lists
    - Added major facilities not yet mapped in OSM
    - Verified addresses and service types through facility websites
    - Excluded defunct or relocated facilities
    
    #### 3. Historical Homeless Count Data
    **Source:** [LAHSA Point-in-Time Count](https://www.lahsa.org/data)
    
    - **What it is:** Annual census of homeless individuals conducted every January
    - **Methodology:** Combination of street counts and shelter surveys
    - **Data Used:** 2015-2024 counts (2025 estimated based on trend)
    - **Access:** [Download raw data](https://www.lahsa.org/documents?id=4702-2023-greater-los-angeles-homeless-count-data)
    
    #### 4. Shelter Capacity Data
    **Source:** LAHSA Annual Reports + LA County Department of Health Services
    
    - Bed capacity tracked from shelter inventory reports
    - Includes emergency, transitional, and permanent supportive housing
    - [2023 Report](https://www.lahsa.org/documents?id=6388-2023-annual-report)
    """)

with tab2:
    st.markdown("""
    ### Analysis Process
    
    #### Step 1: Data Processing (Python/Pandas)
    **Tools:** Google Colab, GeoPandas, Pandas
    
    1. **API Query:** Retrieved facility data from Overpass API
    2. **Data Cleaning:** 
       - Removed duplicates by name and location
       - Standardized address formats
       - Categorized facility types
    3. **Geocoding:** All facilities have verified lat/lon coordinates
    
    **Code Available:** All processing notebooks stored in project GitHub repository
    
    #### Step 2: Spatial Analysis (GIS)
    **Method:** Grid-based coverage analysis
    
    1. **Grid Creation:** 
       - Divided LA County into 380 grid cells (~20x19 grid)
       - Each cell approximately 0.05° x 0.05° (roughly 3 miles x 3 miles)
    
    2. **Service Density Calculation:**
       - Counted facilities within each grid cell
       - Identified cells with zero services = "gap zones"
    
    3. **Distance Analysis:**
       - Used Euclidean distance (straight-line) as proxy for accessibility
       - 1 mile = walking distance threshold (approximately 20 minutes walk)
       - Cells >1 mile from nearest service flagged as underserved
    
    **Why this matters:** People experiencing homelessness often lack transportation. Walking distance is critical.
    
    #### Step 3: Temporal Trend Analysis
    **Method:** Historical comparison + linear projection
    
    1. **Trend Calculation:**
       - Indexed 2015 as baseline (100)
       - Tracked year-over-year growth rates
       - Calculated per-capita metrics (beds per 100 homeless individuals)
    
    2. **Gap Analysis:**
       - Compared homeless population growth rate vs shelter capacity growth rate
       - Formula: Service Gap = (Homeless Growth % - Capacity Growth %)
    
    3. **Forecasting:**
       - Linear regression on 2020-2024 data
       - Projected 2027 needs assuming current trends continue
       - Conservative estimate (doesn't account for policy interventions)
    
    #### Step 4: Visualization (Streamlit + Pydeck)
    **Platform:** Streamlit Cloud (free tier)
    **Mapping:** Pydeck (GPU-accelerated visualization)
    
    - Interactive filters allow exploration by city, service type, year
    - Color coding: Red=shelters, Green=food, Blue=support, Orange=gaps
    - Dynamic zoom adjusts to filtered data
    """)

with tab3:
    st.markdown("""
    ### Verification & Reproducibility
    
    #### How to Verify This Analysis
    
    **1. Check the Raw Data**
    - All processed data available in [GitHub repository](https://github.com/hristova022/gis-portfolio/tree/main/data)
    - Download `la_county_homeless_temporal.json` to inspect facility lists
    - Compare against [LAHSA provider directory](https://www.lahsa.org/portal/apps/la-hop/)
    
    **2. Reproduce the Analysis**
    - All Colab notebooks available in `/notebooks` folder
    - Run notebooks yourself:
      1. `01_homeless_resources_data.ipynb` - Data collection
      2. `01c_la_county_temporal_homeless_analysis.ipynb` - Temporal analysis
    - No API keys required for OSM data
    
    **3. Cross-Reference Facilities**
    Test a specific facility:
    - Find it on the map
    - Google the address to verify it exists
    - Call the facility to confirm services offered
    
    **4. Validate Homeless Count Numbers**
    - Visit [LAHSA Data Portal](https://www.lahsa.org/data)
    - Compare our numbers with official reports
    - Our data: {data['homeless_trends'][0] if has_temporal else 'See data'} 
    
    #### Known Limitations
    
    **1. OSM Data Completeness**
    - Not all facilities may be mapped in OSM
    - Bias toward larger, well-known facilities
    - Mitigation: Manual verification added 15+ major facilities
    
    **2. Service Hours Not Included**
    - Analysis shows location only, not operating hours
    - Some facilities may be daytime-only or seasonal
    - Future enhancement: Add hours of operation
    
    **3. Capacity vs. Availability**
    - Shelter bed counts show total capacity, not current availability
    - Many shelters operate at or near 100% capacity
    - Does not account for admission requirements or waitlists
    
    **4. Simplified Distance Metric**
    - Uses straight-line distance, not walking routes
    - Doesn't account for barriers (highways, rivers, terrain)
    - Future enhancement: Network analysis with actual walking paths
    
    #### Assumptions Made
    
    1. **Historical Facility Data:** Facilities before 2020 estimated using sampling (60% of current in 2015, scaling up)
    2. **2025 Projections:** Based on 2020-2024 trend, assumes no major policy changes
    3. **Service Gap Threshold:** 1 mile = underserved (standard urban planning metric)
    
    #### Updates & Maintenance
    
    - **Data Freshness:** Last updated October 2025
    - **Update Frequency:** Can be re-run quarterly with latest LAHSA data
    - **Community Contributions:** Submit corrections via GitHub issues
    
    #### Academic References
    
    This analysis methodology aligns with:
    - **Spatial Accessibility Analysis:** [Luo & Wang, 2003](https://doi.org/10.1068/b29120) - Two-step floating catchment area method
    - **Service Gap Analysis:** [Guagliardo, 2004](https://doi.org/10.1186/1476-072X-3-3) - Spatial accessibility to healthcare
    - **Urban Planning Standards:** [American Planning Association](https://www.planning.org/) - 1/4 to 1/2 mile walkability standards
    
    #### Contact for Questions
    
    Questions about methodology? Found an error?
    - GitHub: [@hristova022](https://github.com/hristova022/gis-portfolio)
    - LinkedIn: [Luba Hristova](https://linkedin.com/in/luba-hristova)
    """)

st.divider()

# Service directory
st.markdown(f"### 📋 Service Directory")
st.caption(f"Showing {min(20, len(filtered_df))} of {len(filtered_df)} facilities matching your filters")

for idx, row in filtered_df.head(20).iterrows():
    with st.expander(f"📍 {row['name']} - {row.get('city', 'LA County')}"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Type:** {row['type_label']}")
            st.markdown(f"**Address:** {row['address']}")
        with col2:
            st.markdown(f"**City:** {row.get('city', 'N/A')}")
            if row.get('description'):
                st.markdown(f"**Services:** {row['description']}")

if len(filtered_df) > 20:
    st.info(f"📌 Showing first 20 of {len(filtered_df)} results. Use filters above to narrow your search.")

st.divider()

st.markdown('''
### 💡 Key Takeaways

This analysis reveals **LA County's homeless crisis is growing faster than our ability to provide services.** 
While we've made progress adding facilities, the gap between need and capacity continues to widen.

**What this means:**
- More people competing for fewer resources
- Longer wait times for shelter beds
- Increased strain on existing facilities
- Growing service gap areas where no help is available nearby

**What we need:**
- Strategic placement of new facilities in underserved areas
- Increased capacity at existing locations
- Coordinated regional approach across all LA County cities
''')
