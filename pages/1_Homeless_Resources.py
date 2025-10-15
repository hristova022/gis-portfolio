import streamlit as st
import pandas as pd
import json
import pydeck as pdk
import plotly.graph_objects as go

st.set_page_config(page_title="LA County Homeless Analysis | GIS Portfolio", page_icon="🏠", layout="wide")

st.title("🏠 LA County Homeless Services: Are We Keeping Pace?")

@st.cache_data(ttl=60)
def load_data():
    url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/la_county_homeless_temporal.json?v=1729000000"
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
    
    if selected_year == 2025 and 'current_services' in data:
        df_year_facilities = pd.DataFrame(data['current_services'])
    else:
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
    search_term = st.text_input("Search Facility Name", placeholder="e.g., Food Bank",
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
    st.caption(f"Showing {len(filtered_df)} facilities. Zoom and pan to explore.")
    
    def get_color(service_type):
        colors = {'shelter': [255, 0, 0, 200], 'food_bank': [0, 200, 0, 200], 'social_facility': [0, 100, 255, 200]}
        return colors.get(service_type, [128, 128, 128, 200])
    
    def get_type_label(service_type):
        labels = {'shelter': 'Emergency Shelter', 'food_bank': 'Food Bank / Meal Program', 'social_facility': 'Support Services'}
        return labels.get(service_type, service_type)
    
    filtered_df['color'] = filtered_df['type'].apply(get_color)
    filtered_df['type_label'] = filtered_df['type'].apply(get_type_label)
    
    if len(filtered_df) > 0:
        center_lat = filtered_df['lat'].mean()
        center_lon = filtered_df['lon'].mean()
        
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
    
    map_key = f"{selected_city}_{selected_type}_{selected_year}_{len(filtered_df)}"
    
    r = pdk.Deck(layers=layers, initial_view_state=view_state,
        tooltip={'html': '<b>{name}</b><br/><i>{type_label}</i><br/>{city}<br/>{address}',
                 'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}})
    
    st.pydeck_chart(r, key=map_key)

with col2:
    st.subheader("📊 Analysis Summary")
    st.metric("Facilities Shown", len(filtered_df))
    
    st.markdown("**Services by Type:**")
    type_counts = filtered_df['type'].value_counts()
    for service_type, count in type_counts.items():
        st.markdown(f"• {get_type_label(service_type)}: {count}")
    
    if has_temporal:
        st.markdown("---")
        st.markdown(f"**Service Gap Areas:** {data['summary']['service_gap_areas']}")
        st.caption("Orange zones show areas lacking nearby services")
    
    st.markdown('''
    ---
    **Map Legend:**
    - 🔴 **Emergency Shelters** - Overnight housing
    - 🟢 **Food Banks** - Meals and groceries  
    - 🔵 **Support Services** - Case management
    - 🟠 **Service Gap Zones** - No facilities within 1+ mile
    ''')

st.divider()

st.markdown(f"### 📋 Service Directory")

# Show facilities in a more compact format
if 'show_all_facilities' not in st.session_state:
    st.session_state.show_all_facilities = False

show_count = len(filtered_df) if st.session_state.show_all_facilities else min(5, len(filtered_df))

st.caption(f"Showing {show_count} of {len(filtered_df)} facilities")

# Compact table view
for idx, row in filtered_df.head(show_count).iterrows():
    with st.expander(f"📍 {row['name']} ({row.get('city', 'LA County')})"):
        st.markdown(f"**{row['type_label']}** | {row['address']}")
        if row.get('description'):
            st.caption(row['description'])

if len(filtered_df) > 5:
    if not st.session_state.show_all_facilities:
        if st.button(f"📄 Show All {len(filtered_df)} Facilities", key="show_all_btn"):
            st.session_state.show_all_facilities = True
            st.rerun()
    else:
        if st.button("📄 Show Less", key="show_less_btn"):
            st.session_state.show_all_facilities = False
            st.rerun()

st.divider()

# AI Predictive Heatmap Section
if 'predictive_analysis' in data:
    st.markdown("## 🤖 AI-Powered Predictive Analysis")
    st.caption("Machine Learning model identifying areas with highest need for homeless services")
    
    show_ai = st.checkbox("Show Predictive Heatmap", value=False, 
                          help="Random Forest model analyzes distance to services, population density, and poverty rates")
    
    if show_ai:
        st.caption("**How it works:** Analyzes 6 features (distance to facilities, density, demographics) to predict service need")
        
        col_a, col_b = st.columns([3, 1])
        
        with col_a:
            df_pred = pd.DataFrame(data['predictive_analysis']['prediction_grid'])
            df_pred['color'] = df_pred['predicted_need'].apply(
                lambda x: [int(255 * x/100), int(255 * (1 - x/100)), 0, 100]
            )
            
            pred_layer = pdk.Layer(
                'ScatterplotLayer',
                data=df_pred,
                get_position='[lon, lat]',
                get_color='color',
                get_radius=1000,
                radius_min_pixels=3,
                radius_max_pixels=20,
                pickable=True
            )
            
            view_pred = pdk.ViewState(latitude=33.95, longitude=-118.35, zoom=9.5)
            
            deck_pred = pdk.Deck(
                layers=[pred_layer],
                initial_view_state=view_pred,
                tooltip={
                    'html': '<b>Need Score:</b> {predicted_need:.0f}<br/><b>Level:</b> {risk_level}',
                    'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}
                }
            )
            
            st.pydeck_chart(deck_pred, key="ai_heatmap")
            st.caption("🔴 Red = High Need | 🟡 Yellow = Medium | 🟢 Green = Low Need")
        
        with col_b:
            stats = data['predictive_analysis']['statistics']
            st.metric("High Need Areas", stats['high_need_areas'])
            st.metric("Medium Need", stats['medium_need_areas'])
            st.metric("Low Need", stats['low_need_areas'])
            
            with st.expander("Model Details"):
                st.write("**Features:**")
                features = {
                    'distance_to_nearest': 'Distance to Services',
                    'nearby_facility_count': 'Facility Count',
                    'population_density': 'Population Density',
                    'poverty_rate': 'Poverty Rate',
                    'distance_to_shelter': 'Distance to Shelter',
                    'distance_to_food': 'Distance to Food'
                }
                for key, val in features.items():
                    st.write(f"• {val}")
    
    st.divider()

# What-If Scenario Builder
st.markdown("## 🎯 What-If Scenario Builder")
st.caption("Interactive decision support tool: Add hypothetical facilities and see coverage impact")

if 'hypothetical_facilities' not in st.session_state:
    st.session_state.hypothetical_facilities = []

col_w1, col_w2 = st.columns([2, 1])

with col_w1:
    st.markdown("### Add Hypothetical Facility")
    
    col_a, col_b, col_c = st.columns(3)
    
    with col_a:
        new_lat = st.number_input("Latitude", min_value=33.70, max_value=34.35, value=34.05, step=0.01, key="new_lat")
    with col_b:
        new_lon = st.number_input("Longitude", min_value=-118.67, max_value=-118.05, value=-118.25, step=0.01, key="new_lon")
    with col_c:
        new_type = st.selectbox("Type", ["shelter", "food_bank", "social_facility"], 
                                format_func=lambda x: {"shelter": "Emergency Shelter", 
                                                       "food_bank": "Food Bank", 
                                                       "social_facility": "Support Services"}[x])
    
    col_add, col_clear = st.columns(2)
    
    with col_add:
        if st.button("➕ Add Facility", use_container_width=True, key="add_facility_btn"):
            st.session_state.hypothetical_facilities.append({
                'lat': new_lat,
                'lon': new_lon,
                'type': new_type,
                'name': f'Hypothetical {new_type.replace("_", " ").title()}',
                'city': 'Proposed',
                'address': f'{new_lat:.3f}, {new_lon:.3f}',
                'hypothetical': True
            })
            st.success(f"✓ Added {new_type.replace('_', ' ')}!")
            st.rerun()
    
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True, disabled=len(st.session_state.hypothetical_facilities)==0, key="clear_facilities_btn"):
            st.session_state.hypothetical_facilities = []
            st.rerun()
    
    if len(st.session_state.hypothetical_facilities) > 0:
        st.markdown("**Showing scenario with hypothetical facilities:**")
        
        combined_df = pd.concat([
            df_year_facilities,
            pd.DataFrame(st.session_state.hypothetical_facilities)
        ], ignore_index=True)
        
        combined_df['color'] = combined_df.apply(
            lambda row: [255, 255, 0, 220] if row.get('hypothetical') else get_color(row['type']),
            axis=1
        )
        combined_df['type_label'] = combined_df['type'].apply(get_type_label)
        
        combined_layer = pdk.Layer(
            'ScatterplotLayer',
            data=combined_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=250,
            radius_min_pixels=4,
            radius_max_pixels=25,
            pickable=True
        )
        
        view_whatif = pdk.ViewState(latitude=34.00, longitude=-118.30, zoom=9.5)
        
        deck_whatif = pdk.Deck(
            layers=[combined_layer],
            initial_view_state=view_whatif,
            tooltip={'html': '<b>{name}</b><br/>{type_label}<br/>{city}',
                     'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}}
        )
        
        st.pydeck_chart(deck_whatif, key="whatif_scenario")
        st.caption("🟡 Yellow markers = Your hypothetical facilities")

with col_w2:
    st.markdown("### Impact Analysis")
    
    if len(st.session_state.hypothetical_facilities) > 0:
        original = len(df_year_facilities)
        added = len(st.session_state.hypothetical_facilities)
        
        st.metric("Original Facilities", original)
        st.metric("Added Facilities", added, delta=f"+{added}")
        st.metric("Total", original + added)
        
        improvement = (added / original) * 100
        st.metric("Coverage Increase", f"+{improvement:.1f}%", 
                 help="Estimated improvement in geographic coverage")
        
        st.markdown("---")
        st.markdown("**Added Facilities:**")
        for fac in st.session_state.hypothetical_facilities:
            type_label = fac['type'].replace('_', ' ').title()
            st.write(f"• {type_label}")
            st.caption(f"  📍 {fac['lat']:.3f}, {fac['lon']:.3f}")
    else:
        st.info("Add facilities to see impact")
        st.markdown('''**How to use:**
        
1. Enter coordinates
2. Select type  
3. Click Add
4. See coverage change
        ''')

st.divider()



# What-If Scenario Builder
st.markdown("## 🎯 What-If Scenario Builder")
st.caption("Interactive decision support: Add hypothetical facilities and see coverage impact")

if 'hypothetical_facilities' not in st.session_state:
    st.session_state.hypothetical_facilities = []

col_w1, col_w2 = st.columns([2, 1])

with col_w1:
    st.markdown("### Add Hypothetical Facility")
    
    use_address = st.checkbox("Use address instead of coordinates", value=True)
    
    if use_address:
        address_input = st.text_input("Enter address in LA County", 
                                      placeholder="e.g., 1600 Pacific Ave, Long Beach, CA")
        
        if address_input and st.button("🔍 Find Location", key="geocode_btn"):
            try:
                import requests
                geocode_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': address_input + ", Los Angeles County, California",
                    'format': 'json',
                    'limit': 1
                }
                headers = {'User-Agent': 'GIS-Portfolio'}
                
                response = requests.get(geocode_url, params=params, headers=headers)
                results = response.json()
                
                if results:
                    st.session_state.temp_lat = float(results[0]['lat'])
                    st.session_state.temp_lon = float(results[0]['lon'])
                    st.success(f"✓ Found location!")
                else:
                    st.error("Location not found. Try a more specific address.")
            except:
                st.error("Geocoding failed. Try coordinates instead.")
        
        if 'temp_lat' in st.session_state:
            st.caption(f"📍 {st.session_state.temp_lat:.4f}, {st.session_state.temp_lon:.4f}")
            new_lat = st.session_state.temp_lat
            new_lon = st.session_state.temp_lon
        else:
            new_lat = 34.05
            new_lon = -118.25
    else:
        col_a, col_b = st.columns(2)
        with col_a:
            new_lat = st.number_input("Latitude", min_value=33.70, max_value=34.35, value=34.05, step=0.01)
        with col_b:
            new_lon = st.number_input("Longitude", min_value=-118.67, max_value=-118.05, value=-118.25, step=0.01)
    
    new_type = st.selectbox("Facility Type", ["shelter", "food_bank", "social_facility"], 
                            format_func=lambda x: {"shelter": "Shelter", "food_bank": "Food Bank", "social_facility": "Support Services"}[x])
    
    col_add, col_clear = st.columns(2)
    
    with col_add:
        if st.button("➕ Add Facility", use_container_width=True, key="add_facility_btn"):
            st.session_state.hypothetical_facilities.append({
                'lat': new_lat,
                'lon': new_lon,
                'type': new_type,
                'name': f'Hypothetical {new_type.replace("_", " ").title()}',
                'city': 'Proposed',
                'address': f'{new_lat:.3f}, {new_lon:.3f}',
                'hypothetical': True
            })
            st.success("✓ Added!")
            st.rerun()
    
    with col_clear:
        if st.button("🗑️ Clear All", use_container_width=True, disabled=len(st.session_state.hypothetical_facilities)==0, key="clear_facilities_btn"):
            st.session_state.hypothetical_facilities = []
            st.rerun()
    
    if len(st.session_state.hypothetical_facilities) > 0:
        combined_df = pd.concat([df_year_facilities, pd.DataFrame(st.session_state.hypothetical_facilities)], ignore_index=True)
        combined_df['color'] = combined_df.apply(lambda row: [255, 255, 0, 220] if row.get('hypothetical') else get_color(row['type']), axis=1)
        combined_df['type_label'] = combined_df['type'].apply(get_type_label)
        
        combined_layer = pdk.Layer('ScatterplotLayer', data=combined_df, get_position='[lon, lat]',
            get_color='color', get_radius=250, radius_min_pixels=4, radius_max_pixels=25, pickable=True)
        
        view_whatif = pdk.ViewState(latitude=34.00, longitude=-118.30, zoom=9.5)
        deck_whatif = pdk.Deck(layers=[combined_layer], initial_view_state=view_whatif,
            tooltip={'html': '<b>{name}</b><br/>{type_label}<br/>{city}',
                     'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}})
        
        st.pydeck_chart(deck_whatif, key="whatif_scenario")
        st.caption("🟡 Yellow = Your hypothetical facilities")

with col_w2:
    st.markdown("### Impact Analysis")
    
    if len(st.session_state.hypothetical_facilities) > 0:
        original = len(df_year_facilities)
        added = len(st.session_state.hypothetical_facilities)
        st.metric("Original", original)
        st.metric("Added", added, delta=f"+{added}")
        st.metric("Total", original + added)
        st.metric("Coverage +", f"{(added/original)*100:.1f}%")
        
        st.markdown("---")
        for fac in st.session_state.hypothetical_facilities:
            st.write(f"• {fac['type'].replace('_', ' ').title()}")
            st.caption(f"  {fac['lat']:.3f}, {fac['lon']:.3f}")
    else:
        st.info("Add facilities to see impact")

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
