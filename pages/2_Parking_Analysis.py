import streamlit as st
import pandas as pd
import pydeck as pdk
import os

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
tab1, tab2, tab3, tab4 = st.tabs(["🧹 Street Sweeping", "🏢 Parking Structures", "🎫 Ticket Hotspots", "📊 By Neighborhood"])

with tab1:
    st.markdown("## Street Sweeping Impact")
    st.markdown("**The biggest cause of parking tickets and lost spaces**")
    
    st.warning("⚠️ Street sweeping removes hundreds of parking spaces on any given day, forcing residents to find alternative parking or risk a $68 ticket")
    
    col_map, col_info = st.columns([2, 1])
    
    with col_map:
        st.markdown("### Street Sweeping Schedule Map")
        st.caption("Official Long Beach Public Works street sweeping zones")
        
        # Display the official map image directly
        if os.path.exists('data/street_sweeping_official.png'):
            st.image('data/street_sweeping_official.png',
                    caption="Official Long Beach Street Sweeping Schedule - Phase 1",
                    use_container_width=True)
            
        else:
            st.warning("⚠️ Official map image not found")
            st.info("""
            To add the official map:
            1. Go to: https://github.com/hristova022/gis-portfolio/tree/main/data
            2. Click "Add file" → "Upload files"
            3. Upload your street sweeping map image as 'street_sweeping_official.png'
            4. Commit
            """)
        
    with col_info:
        st.markdown("### Map Features")
        
        st.markdown("""
        **From Official Long Beach Map:**
        
        🩷 **MON-TUE AREAS**
        Various times (8-11am, 12:30-2:30pm)
        
        🟢 **MON-THU AREAS**  
        1:30-3:30 PM
        
        🔵 **TUE-WED AREAS**
        12:30-2:30 PM
        
        🔵 **WED-THU AREAS**
        8-10 AM
        
        🟣 **THU-FRI AREAS**
        9-11 AM, 10-12 PM
        
        🟠 **VARIOUS SCHEDULES**
        Different times by zone
        
        ---
        
        **Blue Lines** = Streets swept before 8am
        
        **Hatched Areas** = Schools, Parks, City Boundary
        """)
        
        st.markdown("---")
        st.markdown("""
        **Impact:**
        
        - 118,000+ sweeping tickets annually
        - $68 per violation
        - Must move car 2-4 times monthly
        - Many areas have overlapping schedules
        """)
    
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
                
                df_struct = df_structures[df_structures['type'] == 'structure'].copy()
                df_lots = df_structures[df_structures['type'] == 'lot'].copy()
                
                all_layers = []
                
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
    st.markdown("## Parking Ticket Hotspots")
    st.markdown("**Where tickets are issued most frequently**")
    
    st.warning("⚠️ Some locations issue over 900 tickets per year - that's $61,000+ from a single block")
    
    try:
        df_hotspots = pd.read_csv('data/parking_ticket_hotspots.csv')
        
        col_map, col_stats = st.columns([2, 1])
        
        with col_map:
            st.markdown("### Ticket Concentration Map")
            st.caption("Larger circles = more tickets issued. Red = highest, Orange = medium, Yellow = lower")
            
            violation_types = ['All Violations'] + sorted(df_hotspots['primary_violation'].unique().tolist())
            selected_violation = st.selectbox(
                "Filter by violation type",
                violation_types,
                key="violation_filter"
            )
            
            if selected_violation == 'All Violations':
                df_display = df_hotspots
            else:
                df_display = df_hotspots[df_hotspots['primary_violation'] == selected_violation]
            
            hotspot_layer = pdk.Layer(
                'ScatterplotLayer',
                data=df_display,
                get_position='[lon, lat]',
                get_color='color',
                get_radius='size',
                radius_scale=1,
                radius_min_pixels=10,
                radius_max_pixels=80,
                pickable=True,
                opacity=0.7,
                stroked=True,
                filled=True,
                line_width_min_pixels=2,
                get_line_color=[255, 255, 255]
            )
            
            view_state = pdk.ViewState(
                latitude=33.775,
                longitude=-118.17,
                zoom=11.5,
                pitch=0
            )
            
            deck = pdk.Deck(
                map_style='mapbox://styles/mapbox/dark-v11',
                layers=[hotspot_layer],
                initial_view_state=view_state,
                tooltip={
                    'html': '<b>{tickets} tickets/year</b><br/>Top violation: {primary_violation}',
                    'style': {'color': 'white', 'backgroundColor': 'rgba(0,0,0,0.8)', 'padding': '10px'}
                }
            )
            
            st.pydeck_chart(deck)
            st.caption("🔴 Red = 700+ tickets/year | 🟠 Orange = 500-700 | 🟡 Yellow = <500")
        
        with col_stats:
            st.markdown("### Hotspot Statistics")
            
            total_tickets = df_display['tickets'].sum()
            avg_per_spot = df_display['tickets'].mean()
            worst_spot = df_display.nlargest(1, 'tickets').iloc[0]
            
            st.metric("Total Annual Tickets", f"{total_tickets:,}")
            st.metric("Avg per Hotspot", f"{avg_per_spot:.0f}")
            st.metric("Worst Location", f"{worst_spot['tickets']} tickets",
                     help=f"Primary violation: {worst_spot['primary_violation']}")
            
            st.markdown("---")
            st.markdown("### Top 5 Worst Spots")
            
            top5 = df_display.nlargest(5, 'tickets')
            for idx, (_, row) in enumerate(top5.iterrows(), 1):
                st.write(f"**#{idx}** - {row['tickets']} tickets/year")
                st.caption(f"   {row['primary_violation']}")
            
            st.markdown("---")
            st.markdown("### By Violation Type")
            
            violation_counts = df_hotspots.groupby('primary_violation')['tickets'].sum()
            for violation, count in violation_counts.sort_values(ascending=False).items():
                st.write(f"**{violation}:** {count:,}")
    
    except FileNotFoundError:
        st.warning("Loading hotspot data...")
    
    st.divider()
    
    st.markdown("""
    ### Why This Matters
    
    **High-ticket zones tell us where parking policy fails residents:**
    
    - **Belmont Shore 2nd Street:** 920 tickets/year for expired meters means there aren't enough spaces for the demand
    - **Downtown core:** 850+ tickets/year for street sweeping means residents have nowhere else to park
    - **Concentrated hotspots:** When one block generates $60k+ in tickets, that's a policy problem, not a parking problem
    
    **The pattern is clear:** The city makes the most money from areas with the worst parking shortages. 
    Instead of adding parking solutions, we ticket residents who have no alternatives.
    
    **Cost to residents in these hotspots:**
    - Top hotspot area: ~$62,000/year from one location
    - Average $68 per ticket
    - Many residents get multiple tickets per year
    - Disproportionately impacts those who can't afford garage parking
    """)

with tab4:
    st.markdown("## Neighborhood Breakdown")
    st.markdown("**Which areas have it worst?**")
    
    try:
        df_neighborhoods = pd.read_csv('data/neighborhoods_parking.csv')
        df_impact = pd.read_csv('data/neighborhood_ticket_impact.csv')
        
        df_combined = df_neighborhoods.merge(df_impact, on='neighborhood', how='left')
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
- **Street Sweeping:** Long Beach ArcGIS Open Data (official city data)
- **Parking Structures:** OpenStreetMap + field verification
- **Parking Tickets:** Long Beach City financial reports
- **Demographics:** US Census Bureau

All visualizations and analysis performed using Python, GeoPandas, Pydeck, and Streamlit.
""")

st.caption("Analysis by Luba Hristova | Long Beach Resident & GIS Analyst")
