import streamlit as st
import pandas as pd
import json
import pydeck as pdk

st.set_page_config(page_title="Homeless Resources | GIS Portfolio", page_icon="🏠", layout="wide")

st.title("🏠 Long Beach Homeless Resources Mapper")

st.markdown("""
This interactive map shows homeless services, shelters, and food banks across Long Beach, 
with spatial analysis identifying service gaps and underserved areas.
""")

# Load data
@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/hristova022/gis-portfolio/main/data/homeless_services_data.json"
    try:
        import requests
        response = requests.get(url)
        data = response.json()
        return data
    except:
        st.error("Could not load data. Make sure the data file is pushed to GitHub.")
        return None

data = load_data()

if data:
    df_services = pd.DataFrame(data['services'])
    df_coverage = pd.DataFrame(data['coverage'])
    stats = data['stats']
    
    # Stats at the top
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Services", stats['total_services'])
    with col2:
        st.metric("Shelters", stats['shelters'])
    with col3:
        st.metric("Food Banks", stats['food_banks'])
    with col4:
        st.metric("Support Centers", stats['support_centers'])
    
    st.divider()
    
    # Filters
    st.subheader("Filter Services")
    col1, col2 = st.columns(2)
    
    with col1:
        service_types = ['All'] + sorted(df_services['type'].unique().tolist())
        selected_type = st.selectbox("Service Type", service_types)
    
    with col2:
        search_term = st.text_input("Search by name or address")
    
    # Apply filters
    filtered_df = df_services.copy()
    if selected_type != 'All':
        filtered_df = filtered_df[filtered_df['type'] == selected_type]
    if search_term:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_term, case=False, na=False) |
            filtered_df['address'].str.contains(search_term, case=False, na=False)
        ]
    
    st.divider()
    
    # Map
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Service Locations Map")
        
        # Color mapping
        def get_color(service_type):
            colors = {
                'shelter': [255, 0, 0, 200],
                'food_bank': [0, 200, 0, 200],
                'social_facility': [0, 100, 255, 200]
            }
            return colors.get(service_type, [128, 128, 128, 200])
        
        filtered_df['color'] = filtered_df['type'].apply(get_color)
        
        # Service gaps for circles
        gap_areas = df_coverage[df_coverage['service_count'] == 0].copy()
        gap_areas['radius'] = 800
        gap_areas['color'] = [[255, 165, 0, 50]] * len(gap_areas)
        
        # Create layers
        service_layer = pdk.Layer(
            'ScatterplotLayer',
            data=filtered_df,
            get_position='[lon, lat]',
            get_color='color',
            get_radius=150,
            pickable=True,
        )
        
        gap_layer = pdk.Layer(
            'ScatterplotLayer',
            data=gap_areas,
            get_position='[lon, lat]',
            get_color='color',
            get_radius='radius',
            pickable=True,
        )
        
        # Set view
        view_state = pdk.ViewState(
            latitude=33.77,
            longitude=-118.15,
            zoom=11.5,
            pitch=0,
        )
        
        # Render map
        r = pdk.Deck(
            layers=[gap_layer, service_layer],
            initial_view_state=view_state,
            tooltip={
                'html': '<b>{name}</b><br/>{type}<br/>{address}',
                'style': {'color': 'white'}
            }
        )
        
        st.pydeck_chart(r)
    
    with col2:
        st.subheader("Key Insights")
        
        # Calculate gaps
        gap_areas_count = len(df_coverage[df_coverage['service_count'] == 0])
        covered_areas = len(df_coverage[df_coverage['service_count'] > 0])
        
        st.markdown(f"""
        **Coverage Analysis:**
        - {covered_areas} areas with services
        - {gap_areas_count} areas with no services
        - {gap_areas_count / len(df_coverage) * 100:.1f}% of Long Beach lacks nearby services
        
        **Service Distribution:**
        """)
        
        type_counts = df_services['type'].value_counts()
        for service_type, count in type_counts.items():
            st.markdown(f"- {service_type.replace('_', ' ').title()}: {count}")
        
        st.markdown("""
        ---
        **🔴 Red dots:** Shelters  
        **🟢 Green dots:** Food banks  
        **🔵 Blue dots:** Support centers  
        **🟠 Orange circles:** Service gap areas
        
        *Hover over markers for details*
        """)
    
    st.divider()
    
    # Service list
    st.subheader(f"Service Directory ({len(filtered_df)} locations)")
    
    for idx, row in filtered_df.iterrows():
        with st.expander(f"📍 {row['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Type:** {row['type'].replace('_', ' ').title()}")
                st.markdown(f"**Address:** {row['address']}")
            with col2:
                st.markdown(f"**Coordinates:** {row['lat']:.4f}, {row['lon']:.4f}")
                if row['description']:
                    st.markdown(f"**Description:** {row['description']}")
    
    st.divider()
    
    st.markdown("""
    ### About This Analysis
    
    This project maps homeless services across Long Beach to identify service gaps 
    and help understand resource distribution. The spatial analysis reveals areas 
    where residents may lack access to critical services like emergency shelter, 
    food assistance, and support programs.
    
    **Data Sources:**
    - OpenStreetMap (community-contributed service locations)
    - Manual verification of known Long Beach homeless service providers
    
    **Methodology:**
    - Grid-based coverage analysis dividing Long Beach into zones
    - Service density calculation per zone
    - Gap identification highlighting underserved areas
    
    **Potential Applications:**
    - Resource allocation planning for city services
    - Identifying optimal locations for new facilities
    - Supporting outreach program coordination
    """)
