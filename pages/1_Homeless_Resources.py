import streamlit as st
import pandas as pd
import json
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="LA County Homeless Analysis | GIS Portfolio", page_icon="🏠", layout="wide")

st.title("🏠 LA County Homeless Services: Are We Keeping Pace?")

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/la_county_homeless_temporal.json"
    try:
        import requests
        response = requests.get(url)
        data = response.json()
        return data
    except:
        st.error("Could not load temporal data. Loading basic data instead...")
        url_basic = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/homeless_services_data.json"
        response = requests.get(url_basic)
        return response.json()

data = load_data()
has_temporal = 'homeless_trends' in data

if has_temporal:
    st.markdown(f"""
    ## 📈 The Gap is Widening
    
    **From 2015 to 2025, LA County's homeless population grew {data['gap_analysis']['homeless_growth_pct']:.1f}% 
    while shelter capacity increased only {data['gap_analysis']['shelter_capacity_growth_pct']:.1f}%.**
    
    Despite adding {data['summary']['new_facilities_since_2015']} new facilities, there are now 
    **{data['gap_analysis']['beds_per_100_now']:.1f} beds per 100 homeless individuals** 
    (down from {data['gap_analysis']['beds_per_100_then']:.1f} in 2015).
    
    By 2027, we'll need **{data['forecast_2027']['additional_beds_needed']:,} additional beds** 
    just to maintain current service levels.
    """)
    
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
        
        fig.add_trace(go.Scatter(
            x=df_trends_norm['year'], y=df_trends_norm['homeless_index'],
            name='Homeless Population', line=dict(color='red', width=3), mode='lines+markers'
        ))
        
        fig.add_trace(go.Scatter(
            x=df_trends_norm['year'], y=df_trends_norm['beds_index'],
            name='Shelter Capacity', line=dict(color='green', width=3), mode='lines+markers'
        ))
        
        fig.update_layout(
            yaxis_title='Growth Index (2015 = 100)', xaxis_title='Year',
            hovermode='x unified', height=300, margin=dict(l=0, r=0, t=20, b=0), showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.caption("📈 Both metrics indexed to 2015 baseline (100) to show relative growth")
    
    st.divider()
    
    df_facilities = pd.DataFrame(data['historical_facilities'])
    df_year_facilities = df_facilities[df_facilities['year'] <= selected_year].drop_duplicates(subset=['name'])
else:
    st.markdown("### Why This Matters\n\nWhen someone experiencing homelessness needs help, **every mile matters**.")
    st.divider()
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
else:
    stats = data.get('stats', {})
    with col1:
        st.metric("Total Services", stats.get('total_services', len(df_year_facilities)))
    with col2:
        st.metric("Shelters", stats.get('shelters', 0))
    with col3:
        st.metric("Food Banks", stats.get('food_banks', 0))
    with col4:
        st.metric("Support Centers", stats.get('support_centers', 0))

st.divider()

st.subheader("Filter Services")
col1, col2, col3 = st.columns(3)

with col1:
    service_types = ['All'] + sorted(df_year_facilities['type'].unique().tolist())
    selected_type = st.selectbox("Service Type", service_types)
with col2:
    cities = ['All'] + sorted([c for c in df_year_facilities['city'].unique() if c])
    selected_city = st.selectbox("City", cities)
with col3:
    search_term = st.text_input("Search by name")

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
    st.subheader(f"Service Locations Map - {selected_year}")
    
    def get_color(service_type):
        colors = {'shelter': [255, 0, 0, 200], 'food_bank': [0, 200, 0, 200], 'social_facility': [0, 100, 255, 200]}
        return colors.get(service_type, [128, 128, 128, 200])
    
    def get_type_label(service_type):
        labels = {'shelter': 'Emergency Shelter', 'food_bank': 'Food Bank / Meal Program', 'social_facility': 'Support Services'}
        return labels.get(service_type, service_type)
    
    filtered_df['color'] = filtered_df['type'].apply(get_color)
    filtered_df['type_label'] = filtered_df['type'].apply(get_type_label)
    
    if has_temporal:
        df_coverage = pd.DataFrame(data['coverage_analysis'])
        gap_areas = df_coverage[df_coverage['service_count'] == 0].copy()
        gap_areas['radius'] = 1500
        gap_areas['color'] = [[255, 165, 0, 30]] * len(gap_areas)
        gap_areas['name'] = ['Service Gap Area'] * len(gap_areas)
        gap_areas['type_label'] = ['No nearby services - 1+ mile to nearest resource'] * len(gap_areas)
        
        gap_layer = pdk.Layer('ScatterplotLayer', data=gap_areas, get_position='[lon, lat]',
            get_color='color', get_radius='radius', pickable=True)
    else:
        gap_layer = None
    
    service_layer = pdk.Layer('ScatterplotLayer', data=filtered_df, get_position='[lon, lat]',
        get_color='color', get_radius=200, pickable=True)
    
    view_state = pdk.ViewState(latitude=33.95, longitude=-118.35, zoom=9.5, pitch=0)
    
    layers = [gap_layer, service_layer] if gap_layer else [service_layer]
    r = pdk.Deck(layers=layers, initial_view_state=view_state,
        tooltip={'html': '<b>{name}</b><br/><i>{type_label}</i><br/>{city}<br/>{address}',
                 'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}})
    
    st.pydeck_chart(r)

with col2:
    st.subheader("Geographic Distribution")
    
    if has_temporal:
        area_counts = df_coverage.groupby('area')['service_count'].sum().sort_values(ascending=False)
        fig_pie = px.pie(values=area_counts.values, names=area_counts.index, title='Services by Region')
        fig_pie.update_layout(height=250, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("---")
        st.markdown(f"**Service Gap Areas:** {data['summary']['service_gap_areas']}")
        st.markdown(f"**Total Population:** {data['summary']['total_population_analyzed']:,}")
    
    st.markdown("""
    ---
    **Map Legend:**
    - 🔴 Emergency shelters  
    - 🟢 Food banks & meals  
    - 🔵 Support services  
    - 🟠 Service gap zones
    
    *Hover for details*
    """)

st.divider()

st.markdown("### 📊 How This Analysis Was Conducted")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **Data Sources:**
    
    - **OpenStreetMap** - Community-contributed database verified by local organizations across LA County
    - **Manual Verification** - Cross-referenced with city resources and service providers
    - **LA Homeless Services Authority** - Historical homeless count data (2015-2025)
    - **Last Updated:** October 2025
    """)

with col2:
    st.markdown("""
    **Analysis Methodology:**
    
    - **County-Wide Coverage** - LA County divided into zones for service density measurement
    - **Temporal Analysis** - Historical facility data tracked over 10-year period
    - **Gap Calculation** - Comparing homeless growth vs shelter capacity expansion
    - **Predictive Modeling** - Linear projection to forecast 2027 needs
    """)

st.divider()

st.subheader(f"Service Directory ({len(filtered_df)} locations)")

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
    st.info(f"Showing first 20 of {len(filtered_df)} results. Use filters to narrow search.")

st.divider()

st.markdown("""
### 💡 Key Takeaways

This analysis reveals **LA County's homeless crisis is growing faster than our ability to provide services.** 
While we've made progress adding facilities, the gap between need and capacity continues to widen.

**What this means:**
- More people competing for fewer resources
- Longer wait times for shelter beds
- Increased strain on existing facilities
- Growing service gap areas

**What we need:**
- Strategic placement of new facilities in underserved areas
- Increased capacity at existing locations
- Coordinated regional approach across all LA County cities
""")
