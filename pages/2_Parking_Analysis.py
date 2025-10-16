
# Updated: 2025-10-16 21:50:32
import streamlit as st
import pandas as pd
import os
import pydeck as pdk

st.set_page_config(page_title="Long Beach Parking Analysis", page_icon="🅿️", layout="wide")

st.title("🅿️ Long Beach Parking Crisis Analysis")
st.subheader("A Data-Driven Look at Why Finding Parking Feels Impossible")

# Personal context box
with st.container():
    st.markdown("""
    ### Why This Analysis Matters
    
    As a Long Beach resident, I experience the parking crisis daily. Like many residents, I've:
    - Circled blocks for 20+ minutes looking for a spot
    - Received parking tickets despite following the rules
    - Missed appointments because I couldn't find parking
    - Paid for expensive garage parking when street parking wasn't available
    
    **This isn't just inconvenient—it's expensive.** Long Beach issues over **230,000 parking tickets annually**, 
    generating approximately **$15.6 million in revenue**. About half of these tickets are for street sweeping violations, 
    where residents simply had nowhere else to park.
    
    This analysis uses real data to show what every Long Beach resident already knows: 
    **we have a serious parking problem that needs solutions, not just more tickets.**
    """)

st.divider()

# Load ticket data for hero stats
try:
    df_tickets = pd.read_csv('data/parking_tickets_longbeach.csv')
    latest_year = df_tickets.iloc[-1]
    total_5yr = df_tickets['total_tickets'].sum()
    
    st.markdown("### The Numbers Tell the Story")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Annual Parking Tickets", f"{latest_year['total_tickets']:,}", 
                 help="Total parking citations issued in 2024")
    with col2:
        st.metric("Street Sweeping Tickets", f"{latest_year['street_sweeping']:,}",
                 help="Half of all tickets are for street sweeping")
    with col3:
        st.metric("5-Year Total", f"{total_5yr/1000:.0f}K tickets",
                 delta=f"+{((latest_year['total_tickets']/df_tickets.iloc[0]['total_tickets'])-1)*100:.0f}% since 2020",
                 delta_color="inverse")
    with col4:
        st.metric("Est. Annual Revenue", f"${latest_year['total_tickets']*68/1000000:.1f}M",
                 help="Based on $68 average ticket cost")
except:
    pass

st.divider()


# Main tabs - now with 5 tabs including Aerial Imagery
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧹 Street Sweeping", "🏢 Parking Structures", "🛰️ Aerial Imagery", "🎫 Parking Tickets", "📊 By Neighborhood"])

with tab1:
    st.markdown("## Street Sweeping Impact")
    st.markdown("**The biggest cause of parking tickets and lost spaces**")
    
    st.warning("⚠️ Street sweeping removes hundreds of parking spaces on any given day, forcing residents to find alternative parking or risk a $68 ticket")
    
    try:
        df_sweeping = pd.read_json('data/street_sweeping_zones_polygons.json')
        
        col_map, col_schedule = st.columns([2, 1])
        
        with col_map:
            st.markdown("### Street Sweeping Zones")
            st.caption("Color-coded areas show when different neighborhoods are swept")
            
            # Simple filter by day pattern
            day_options = ['All Zones'] + sorted(df_sweeping['days'].unique().tolist())
            selected_pattern = st.selectbox(
                "Filter by schedule",
                day_options,
                key="sweep_day_selector"
            )
            
            if selected_pattern == 'All Zones':
                df_display = df_sweeping
            else:
                df_display = df_sweeping[df_sweeping['days'] == selected_pattern]
            
            if len(df_display) > 0:
                # Use polygon layer to show zones
                sweep_layer = pdk.Layer(
                    'PolygonLayer',
                    data=df_display,
                    get_polygon='polygon',
                    get_fill_color='color',
                    get_line_color=[255, 255, 255, 80],
                    line_width_min_pixels=2,
                    pickable=True,
                    auto_highlight=True,
                    filled=True
                )
                
                view_state = pdk.ViewState(
                    latitude=33.77,
                    longitude=-118.17,
                    zoom=11.2,
                    pitch=0
                )
                
                deck = pdk.Deck(
                    map_style='mapbox://styles/mapbox/streets-v12',
                    layers=[sweep_layer],
                    initial_view_state=view_state,
                    tooltip={
                        'html': '<b>{name}</b><br/>{days} {time}<br/><i>{streets}</i>',
                        'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px', 'fontSize': '13px'}
                    }
                )
                
                st.pydeck_chart(deck)
                st.caption("🟣 Purple = Thu-Fri | 🔵 Blue = Tue-Wed & Wed-Thu | 🟢 Green = Mon-Thu | 🟠 Orange = East Side | 🩷 Pink = Mon-Tue")
            else:
                st.info("No zones match selected filter")
        
        with col_schedule:
            st.markdown("### Zone Summary")
            
            # Show zones grouped by schedule
            st.markdown(f"**Showing {len(df_display)} zones**")
            
            for _, zone in df_display.iterrows():
                with st.expander(f"**{zone['name']}**"):
                    st.write(f"**Schedule:** {zone['days']}")
                    st.write(f"**Time:** {zone['time']}")
    
    except FileNotFoundError:
        st.warning("Loading sweeping data...")
    except Exception as e:
        st.error(f"Error loading data: {e}")
    
    st.divider()
    
    st.markdown("""
    ### Real Impact on Residents
    
    **Downtown:** Multiple days per week. If you work from home or have a flexible schedule, you're constantly 
    moving your car. If you have a 9-5 job, you either pay for garage parking or circle endlessly after work.
    
    **Belmont Shore:** Regular sweeping in the tourist area with already limited parking loses even more 
    spaces. Weekend visitors often don't know about sweeping schedules and get ticketed.
    
    **The Result:** Over 118,000 street sweeping tickets issued in 2024 alone. That's $8 million from residents who 
    often had no other legal place to park their car.
    """)

with tab2:
    st.markdown("## Parking Structure Locations")
    st.markdown("**Where can you actually find covered parking?**")
    
    try:
        df_structures = pd.read_csv('data/parking_structures_accurate.csv')
        
        if len(df_structures) > 0:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### All Parking Facilities")
                
                # Separate structures and lots
                df_struct = df_structures[df_structures['type'] == 'structure'].copy()
                df_lots = df_structures[df_structures['type'] == 'lot'].copy()
                
                # Create layers list
                all_layers = []
                
                # Add structures layer if exists
                if len(df_struct) > 0:
                    df_struct['color'] = [[255, 140, 0, 220]] * len(df_struct)
                    struct_layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=df_struct,
                        get_position='[lon, lat]',
                        get_color='color',
                        get_radius=250,
                        radius_min_pixels=15,
                        radius_max_pixels=40,
                        pickable=True,
                        filled=True,
                        stroked=True,
                        get_line_color=[255, 255, 255],
                        line_width_min_pixels=2
                    )
                    all_layers.append(struct_layer)
                
                # Add lots layer if exists
                if len(df_lots) > 0:
                    df_lots['color'] = [[100, 200, 100, 200]] * len(df_lots)
                    lots_layer = pdk.Layer(
                        'ScatterplotLayer',
                        data=df_lots,
                        get_position='[lon, lat]',
                        get_color='color',
                        get_radius=150,
                        radius_min_pixels=10,
                        radius_max_pixels=25,
                        pickable=True,
                        filled=True
                    )
                    all_layers.append(lots_layer)
                
                view_state = pdk.ViewState(
                    latitude=33.77,
                    longitude=-118.19,
                    zoom=12,
                    pitch=0
                )
                
                deck = pdk.Deck(
                    layers=all_layers,
                    initial_view_state=view_state,
                    tooltip={
                        'html': '<b>{name}</b><br/>{neighborhood}<br/>Capacity: {capacity}<br/>Rate: {rate}',
                        'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}
                    }
                )
                
                st.pydeck_chart(deck)
                st.caption("🟠 Large orange circles = Multi-level parking structures | 🟢 Smaller green circles = Surface parking lots | Hover for details")
            
            with col2:
                st.markdown("### Summary")
                
                total_capacity = df_structures['capacity'].sum()
                structures = len(df_structures[df_structures['type'] == 'structure'])
                lots = len(df_structures[df_structures['type'] == 'lot'])
                
                st.metric("Total Facilities", len(df_structures))
                st.metric("Total Capacity", f"{total_capacity:,} spaces")
                st.metric("Structures", structures)
                st.metric("Surface Lots", lots)
                
                st.markdown("---")
                st.markdown("### By Neighborhood")
                
                for hood in df_structures['neighborhood'].unique():
                    hood_data = df_structures[df_structures['neighborhood'] == hood]
                    hood_capacity = hood_data['capacity'].sum()
                    st.write(f"**{hood}:** {len(hood_data)} facilities")
                    st.caption(f"   {hood_capacity:,} total spaces")
        
        st.divider()
        
        st.markdown("""
        ### The Reality
        - **Downtown has the most structures** (5 facilities, 1,850 spaces) but also the highest demand
        - **Belmont Shore has only 2 small lots** (330 spaces) for one of the busiest areas
        - **Many neighborhoods have ZERO parking structures** - residents rely entirely on street parking
        - **Weekend and evening occupancy often exceeds 90%** - finding a spot is like winning the lottery
        - **Paid parking creates inequity** - wealthier residents can afford structures while others circle or get ticketed
        """)
            
    except FileNotFoundError:
        st.warning("Loading structure data...")

with tab3:
    st.markdown("## Aerial Imagery Analysis")
    st.markdown("**Satellite imagery and vehicle detection for Long Beach**")
    
    try:
        # Load detection results
        # os is already imported at top
        df_results = pd.read_csv('data/parking_detection_results.csv')
        
        st.success(f"✅ Analysis complete for {len(df_results)} neighborhoods using high-resolution satellite imagery")
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        total_vehicles = df_results['vehicles_detected'].sum()
        avg_occupancy = df_results['occupancy_rate'].mean()
        
        with col1:
            st.metric("Total Vehicles Detected", f"{total_vehicles:,}")
        with col2:
            st.metric("Average Occupancy", f"{avg_occupancy:.1f}%")
        with col3:
            st.metric("Areas Analyzed", len(df_results))
        
        st.divider()
        
        # Area selector
        area_names = df_results['area'].tolist()
        selected_area = st.selectbox(
            "Select neighborhood to view",
            area_names,
            key="aerial_area_select"
        )
        
        area_data = df_results[df_results['area'] == selected_area].iloc[0]
        area_file = selected_area.lower().replace(' ', '_')
        
        col_img, col_stats = st.columns([2, 1])
        
        with col_img:
            st.markdown(f"### {selected_area}")
            
            # Check if files exist
            orig_exists = os.path.exists(f'data/{area_file}_aerial.png')
            detect_exists = os.path.exists(f'data/{area_file}_detected.png')
            
            if orig_exists or detect_exists:
                tab_orig, tab_detect = st.tabs(["📸 Satellite Image", "🤖 Vehicle Detection"])
                
                with tab_orig:
                    if orig_exists:
                        st.image(f'data/{area_file}_aerial.png', 
                                caption=f"High-resolution NAIP satellite imagery of {selected_area}",
                                use_container_width=True)
                    else:
                        st.warning("Original imagery not available")
                
                with tab_detect:
                    if detect_exists:
                        st.image(f'data/{area_file}_detected.png',
                                caption=f"Vehicle detection using computer vision (YOLO model)",
                                use_container_width=True)
                        st.caption("🟦 Blue boxes = Detected vehicles")
                    else:
                        st.warning("Detection results not available")
            else:
                st.warning("Imagery files not found")
        
        with col_stats:
            st.markdown("### Detection Results")
            
            st.metric("Vehicles Found", int(area_data['vehicles_detected']))
            st.metric("Estimated Spaces", int(area_data['estimated_spaces']))
            st.metric("Occupancy Rate", f"{area_data['occupancy_rate']:.1f}%",
                     delta=f"{area_data['occupancy_rate'] - avg_occupancy:.1f}% vs avg",
                     delta_color="inverse")
            
            st.markdown("---")
            st.markdown("### Technical Details")
            st.caption(f"**Image Size:** {area_data['image_size']}")
            st.caption(f"**Data Source:** USDA NAIP Imagery")
            st.caption(f"**Detection:** YOLOv8 (COCO dataset)")
            st.caption(f"**Coverage:** ~500m radius")
            
            st.markdown("---")
            st.markdown("### How It Works")
            st.caption("""
            1. Download satellite imagery from NAIP
            2. Run vehicle detection model
            3. Count detected vehicles
            4. Estimate parking occupancy
            5. Compare across neighborhoods
            """)
        
        st.divider()
        
        # Comparison table
        st.markdown("### Comparison Across All Areas")
        
        # Format the dataframe for display
        display_df = df_results.copy()
        display_df['occupancy_rate'] = display_df['occupancy_rate'].apply(lambda x: f"{x:.1f}%")
        display_df.columns = ['Area', 'Vehicles Detected', 'Est. Spaces', 'Occupancy', 'Image Size']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    except FileNotFoundError:
        st.warning("⚠️ Detection results not found")
    except Exception as e:
        st.error(f"Error: {str(e)}")

# Continue with tab4 and tab5 from the original file...

with tab5:
    st.markdown("## Parking Ticket Analysis")
    st.markdown("**Following the money: who pays the price?**")
    
    try:
        df_tickets = pd.read_csv('data/parking_tickets_longbeach.csv')
        df_impact = pd.read_csv('data/neighborhood_ticket_impact.csv')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Tickets Over Time")
            
            import plotly.graph_objects as go
            
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df_tickets['year'], y=df_tickets['street_sweeping'],
                                name='Street Sweeping', marker_color='#ff4444'))
            fig.add_trace(go.Bar(x=df_tickets['year'], y=df_tickets['overtime'],
                                name='Overtime/Meter', marker_color='#ff9944'))
            fig.add_trace(go.Bar(x=df_tickets['year'], y=df_tickets['no_permit'],
                                name='No Permit', marker_color='#ffdd44'))
            
            fig.update_layout(barmode='stack', 
                            title='Parking Tickets by Type (2020-2024)',
                            xaxis_title='Year',
                            yaxis_title='Number of Tickets',
                            height=400)
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### By Neighborhood (2024)")
            
            fig2 = go.Figure(go.Bar(
                x=df_impact['tickets_per_year'],
                y=df_impact['neighborhood'],
                orientation='h',
                marker_color='#4488ff'
            ))
            
            fig2.update_layout(
                title='Annual Tickets by Area',
                xaxis_title='Tickets per Year',
                yaxis_title='',
                height=400
            )
            
            st.plotly_chart(fig2, use_container_width=True)
        
        st.divider()
        
        st.markdown("### What This Means for Residents")
        
        col_a, col_b, col_c = st.columns(3)
        
        with col_a:
            st.markdown("""
            **Financial Burden**
            - Average ticket: $68
            - Many residents get 2-3 tickets/year
            - That's $136-$204 annually just for parking
            - Disproportionately impacts lower-income residents
            """)
        
        with col_b:
            st.markdown("""
            **Time Cost**
            - Average 15-25 min searching for parking
            - 2x per day = 30-50 min daily
            - That's 180+ hours per year circling
            - Plus stress and frustration
            """)
        
        with col_c:
            st.markdown("""
            **Community Impact**
            - $15.6M taken from residents annually
            - Money that could go to rent, food, savings
            - Enforcement prioritized over solutions
            - Residents feel nickeled-and-dimed
            """)
        
    except:
        st.warning("Loading ticket data...")

with tab5:
    st.markdown("## Neighborhood Breakdown")
    st.markdown("**Which areas have it worst?**")
    
    try:
        df_neighborhoods = pd.read_csv('data/neighborhoods_parking.csv')
        df_impact = pd.read_csv('data/neighborhood_ticket_impact.csv')
        
        # Merge data
        df_combined = df_neighborhoods.merge(df_impact, on='neighborhood', how='left')
        
        # Sort by parking score (lower = worse)
        df_combined = df_combined.sort_values('score')
        
        st.markdown("### Parking Difficulty Score")
        st.caption("Lower score = harder to find parking (0-100 scale)")
        
        import plotly.graph_objects as go
        
        fig = go.Figure(go.Bar(
            x=df_combined['score'],
            y=df_combined['neighborhood'],
            orientation='h',
            marker_color=df_combined['score'].apply(
                lambda x: '#ff4444' if x < 40 else '#ff9944' if x < 60 else '#44ff44'
            ),
            text=df_combined['score'],
            textposition='auto'
        ))
        
        fig.update_layout(
            xaxis_title='Parking Availability Score',
            yaxis_title='',
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.markdown("### Detailed Comparison")
        
        # Display as table
        display_df = df_combined[['neighborhood', 'density', 'parking', 'structures', 
                                  'tickets_per_year', 'avg_wait_time']].copy()
        display_df.columns = ['Neighborhood', 'Population Density', 'Parking Situation', 
                              'Structure Access', 'Annual Tickets', 'Avg. Wait Time']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.divider()
        
        st.markdown("### Worst Areas Explained")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔴 Belmont Shore (Score: 25)**
            - Tourist destination with narrow streets
            - Only 2 small parking lots
            - Street sweeping removes key spaces Tue/Fri
            - Weekend demand from visitors overwhelms supply
            - 38,000 tickets per year - mostly overtime violations
            
            **🔴 Downtown (Score: 35)**
            - Mix of business and residential creates all-day demand
            - Structures fill up by 5pm
            - Street sweeping Mon/Thu removes 300+ spaces
            - Event parking makes it unpredictable
            - 45,000 tickets per year - highest in the city
            """)
        
        with col2:
            st.markdown("""
            **🔴 Alamitos Beach (Score: 30)**
            - Very high residential density
            - Beach visitor overflow
            - Minimal structure capacity
            - Apartments have insufficient parking
            - 32,000 tickets per year
            
            **🟢 California Heights (Score: 70)**
            - Lower density residential
            - Wider streets with more spaces
            - Less competition from commercial/tourist traffic
            - Minimal street sweeping impact
            - Only 12,000 tickets per year
            """)
        
    except:
        st.warning("Loading neighborhood data...")


st.divider()

st.markdown("## 💡 What Can Be Done?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Short-Term Solutions
    - Reform street sweeping schedules
    - Add evening/weekend only sweeping
    - Create permit zones for residents
    - Add digital parking availability signs
    - Reduce ticket fines for first violations
    """)

with col2:
    st.markdown("""
    ### Medium-Term Solutions
    - Build more parking structures in high-need areas
    - Convert underutilized lots to parking
    - Improve public transit to reduce car dependency
    - Add bike infrastructure
    - Implement smart parking meters
    """)

with col3:
    st.markdown("""
    ### Long-Term Solutions
    - Require parking in new developments
    - Incentivize reduced car ownership
    - Expand Metro connectivity
    - Mixed-use development with parking
    - Regional parking planning
    """)

st.divider()

st.markdown("""
## 📊 Data Sources & Methods

This analysis combines multiple data sources:
- **Parking Structures:** OpenStreetMap + field verification
- **Street Sweeping:** Long Beach Public Works Department
- **Parking Tickets:** Long Beach City financial reports
- **Demographics:** US Census Bureau
- **Aerial Imagery:** USDA NAIP high-resolution satellite data

All visualizations and analysis performed using Python, GeoPandas, and Streamlit.
""")

st.caption("Analysis by Luba Hristova | Long Beach Resident & GIS Analyst")
