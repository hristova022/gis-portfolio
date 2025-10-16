import streamlit as st
import pandas as pd
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

# Main tabs
tab1, tab2, tab3, tab4 = st.tabs(["🧹 Street Sweeping", "🏢 Parking Structures", "🎫 Parking Tickets", "📊 By Neighborhood"])

with tab1:
    st.markdown("## Street Sweeping Impact")
    st.markdown("**The biggest cause of parking tickets and lost spaces**")
    
    st.warning("⚠️ Street sweeping removes hundreds of parking spaces on any given day, forcing residents to find alternative parking or risk a $68 ticket")
    
    try:
        df_sweeping = pd.read_json('data/street_sweeping_lines.json')
        
        col_map, col_schedule = st.columns([2, 1])
        
        with col_map:
            st.markdown("### Sweeping Schedule Map")
            
            selected_day = st.selectbox(
                "View sweeping schedule by day",
                ['All Days', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'],
                key="sweep_day_selector"
            )
            
            if selected_day == 'All Days':
                df_display = df_sweeping
            else:
                df_display = df_sweeping[df_sweeping['day'] == selected_day]
            
            if len(df_display) > 0:
                # Use line segments to show actual streets
                sweep_layer = pdk.Layer(
                    'PathLayer',
                    data=df_display,
                    get_path='path',
                    get_color='color',
                    get_width=40,
                    width_min_pixels=3,
                    width_max_pixels=8,
                    pickable=True,
                    auto_highlight=True
                )
                
                view_state = pdk.ViewState(
                    latitude=33.77,
                    longitude=-118.19,
                    zoom=12,
                    pitch=0
                )
                
                deck = pdk.Deck(
                    layers=[sweep_layer],
                    initial_view_state=view_state,
                    tooltip={
                        'html': '<b>{neighborhood}</b><br/>{day} {time}',
                        'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}
                    }
                )
                
                st.pydeck_chart(deck)
                st.caption(f"🔴 Red = Monday | 🔵 Blue = Tuesday | 🟢 Green = Wednesday | 🟠 Orange = Thursday | 🟣 Purple = Friday | Lines show actual streets where sweeping occurs")
            else:
                st.info(f"No sweeping on {selected_day}")
        
        with col_schedule:
            st.markdown("### Weekly Impact")
            
            # Show tickets by day
            try:
                df_impact = pd.read_csv('data/neighborhood_ticket_impact.csv')
                
                for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
                    day_sweeps = df_sweeping[df_sweeping['day'] == day]
                    if len(day_sweeps) > 0:
                        neighborhoods = day_sweeps['neighborhood'].unique()
                        with st.expander(f"**{day}** - {len(day_sweeps)} blocks", expanded=(selected_day==day)):
                            for hood in neighborhoods:
                                count = len(day_sweeps[day_sweeps['neighborhood'] == hood])
                                time = day_sweeps[day_sweeps['neighborhood'] == hood].iloc[0]['time']
                                st.write(f"**{hood}:** {count} blocks")
                                st.caption(f"   {time}")
            except:
                pass
    
    except FileNotFoundError:
        st.warning("Loading sweeping data...")
    
    st.divider()
    
    st.markdown("""
    ### Real Impact on Residents
    
    **Downtown:** Monday & Thursday mornings, 8-10am. If you work from home or have a flexible schedule, you're constantly 
    moving your car. If you have a 9-5 job, you either pay for garage parking or circle endlessly after work.
    
    **Belmont Shore:** Tuesday & Friday mornings, 9-11am. The tourist area with already limited parking loses even more 
    spaces twice a week. Weekend visitors often don't know about sweeping schedules and get ticketed.
    
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
        
        st.markdown("### The Reality")
        st.markdown("""
        - **Downtown has the most structures** (5 facilities, 1,850 spaces) but also the highest demand
        - **Belmont Shore has only 2 small lots** (330 spaces) for one of the busiest areas
        - **Many neighborhoods have ZERO parking structures** - residents rely entirely on street parking
        - **Weekend and evening occupancy often exceeds 90%** - finding a spot is like winning the lottery
        - **Paid parking creates inequity** - wealthier residents can afford structures while others circle or get ticketed
        """)
            
    except FileNotFoundError:
        st.warning("Loading structure data...")


with tab3:
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

with tab4:
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
