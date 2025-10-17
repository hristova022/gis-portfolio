import streamlit as st
import pandas as pd
import pydeck as pdk
import os

st.set_page_config(page_title="Long Beach Parking Analysis", page_icon="🅿️", layout="wide")

st.title("🅿️ Long Beach Parking Crisis Analysis")
st.subheader("A Data-Driven Look at Why Finding Parking Feels Impossible")

# Personal context
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

# Hero metrics
try:
    df_tickets = pd.read_csv('data/parking_tickets_longbeach.csv')
    latest_year = df_tickets.iloc[-1]
    total_5yr = df_tickets['total_tickets'].sum()
    
    st.markdown("### The Numbers Tell the Story")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Annual Parking Tickets", f"{latest_year['total_tickets']:,}")
    with col2:
        st.metric("Street Sweeping Tickets", f"{latest_year['street_sweeping']:,}")
    with col3:
        st.metric("5-Year Total", f"{total_5yr/1000:.0f}K tickets",
                 delta=f"+{((latest_year['total_tickets']/df_tickets.iloc[0]['total_tickets'])-1)*100:.0f}% since 2020",
                 delta_color="inverse")
    with col4:
        st.metric("Est. Annual Revenue", f"${latest_year['total_tickets']*68/1000000:.1f}M")
except:
    pass

st.divider()

# MAIN TABS - Correct order
tab1, tab2, tab3, tab4 = st.tabs(["🎫 Ticket Hotspots", "🧹 Street Sweeping", "🏢 Parking Structures", "📊 By Neighborhood"])

# TAB 1: TICKET HOTSPOTS
with tab1:
    st.markdown("## Parking Ticket Hotspots")
    st.markdown("**Where tickets are issued most frequently**")
    
    st.warning("⚠️ Some locations issue over 900 tickets per year - that's $61,000+ from a single block")
    
    try:
        df_hotspots = pd.read_csv('data/parking_ticket_hotspots.csv')
        
        col_map, col_stats = st.columns([2, 1])
        
        with col_map:
            st.markdown("### Ticket Concentration Map")
            
            violation_types = ['All Violations'] + sorted(df_hotspots['primary_violation'].unique().tolist())
            selected_violation = st.selectbox(
                "Filter by violation type",
                violation_types,
                key="hotspot_violation_filter"
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
            
            view_state = pdk.ViewState(latitude=33.775, longitude=-118.17, zoom=11.5)
            
            deck = pdk.Deck(
                map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
                layers=[hotspot_layer],
                initial_view_state=view_state,
                tooltip={'html': '<b>{tickets} tickets/year</b><br/>{primary_violation}'}
            )
            
            st.pydeck_chart(deck, height=500)
            st.caption("🔴 Red = 700+ tickets/year | 🟠 Orange = 500-700 | 🟡 Yellow = <500")
        
        with col_stats:
            st.markdown("### Statistics")
            
            total_tickets = df_display['tickets'].sum()
            avg_per_spot = df_display['tickets'].mean()
            worst_spot = df_display.nlargest(1, 'tickets').iloc[0]
            
            st.metric("Total Annual Tickets", f"{total_tickets:,}")
            st.metric("Avg per Hotspot", f"{avg_per_spot:.0f}")
            st.metric("Worst Location", f"{worst_spot['tickets']} tickets")
            
            st.markdown("---")
            st.markdown("### Top 5 Worst Spots")
            
            top5 = df_display.nlargest(5, 'tickets')
            for idx, (_, row) in enumerate(top5.iterrows(), 1):
                st.write(f"**#{idx}** - {row['tickets']} tickets/year")
                st.caption(f"   {row['primary_violation']}")
    
    except FileNotFoundError:
        st.warning("Loading hotspot data...")

# TAB 2: STREET SWEEPING
with tab2:
    st.markdown("## Street Sweeping Impact")
    st.markdown("**The biggest cause of parking tickets and lost spaces**")
    
    st.warning("⚠️ Street sweeping removes hundreds of spaces daily, forcing residents to find alternatives or risk $68 tickets")
    
    col_map, col_info = st.columns([2, 1])
    
    with col_map:
        st.markdown("### Street Sweeping Schedule Map")
        st.caption("Official Long Beach Public Works zones")
        
        if os.path.exists('data/street_sweeping_official.png'):
            st.image('data/street_sweeping_official.png',
                    caption="Official Long Beach Street Sweeping Schedule",
                    use_container_width=True)
        else:
            st.warning("Map image not found")
    
    with col_info:
        st.markdown("### Schedule Legend")
        
        col_a, col_b = st.columns([1, 3])
        
        with col_a:
            st.markdown("🩷")
            st.markdown("🟢")
            st.markdown("🟡")
            st.markdown("🔵")
            st.markdown("🟠")
        
        with col_b:
            st.markdown("**MON-TUE AREAS**")
            st.markdown("**MON-THU AREAS**")
            st.markdown("**TUE-WED AREAS**")
            st.markdown("**WED-THU AREAS**")
            st.markdown("**THU-FRI AREAS**")
        
        st.markdown("---")
        st.markdown("""
        **Impact:**
        - 118,000+ tickets/year
        - $68 per violation
        - Move car 2-4x monthly
        """)
    
    st.divider()
    
    st.markdown("""
    ### Real Impact
    
    **Downtown:** Constant car moving. Either pay for garage parking or circle endlessly after work.
    
    **Belmont Shore:** Tourist area loses even more spaces. Visitors get ticketed without knowing schedules.
    
    **The Result:** Over 118,000 street sweeping tickets in 2024 = $8 million from residents with nowhere else to park.
    """)

# TAB 3: PARKING STRUCTURES
with tab3:
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
                    all_layers.append(pdk.Layer(
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
                    ))
                
                if len(df_lots) > 0:
                    df_lots['color'] = [[100, 200, 100, 200]] * len(df_lots)
                    all_layers.append(pdk.Layer(
                        'ScatterplotLayer',
                        data=df_lots,
                        get_position='[lon, lat]',
                        get_color='color',
                        get_radius=150,
                        radius_min_pixels=10,
                        radius_max_pixels=25,
                        pickable=True,
                        filled=True
                    ))
                
                deck = pdk.Deck(
                    layers=all_layers,
                    initial_view_state=pdk.ViewState(latitude=33.77, longitude=-118.19, zoom=12),
                    tooltip={'html': '<b>{name}</b><br/>{neighborhood}<br/>Capacity: {capacity}<br/>Rate: {rate}'}
                )
                
                st.pydeck_chart(deck)
                st.caption("🟠 Orange = Structures | 🟢 Green = Surface Lots")
            
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
                    st.caption(f"   {hood_capacity:,} spaces")
        
        st.divider()
        
        st.markdown("""
        ### The Reality
        - Downtown has most structures but highest demand
        - Belmont Shore has only 2 small lots for busiest area
        - Many neighborhoods have ZERO structures
        - Weekend/evening occupancy exceeds 90%
        - Paid parking creates inequity
        """)
            
    except FileNotFoundError:
        st.warning("Loading structure data...")

# TAB 4: BY NEIGHBORHOOD
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
        
        fig.update_layout(xaxis_title='Parking Score', yaxis_title='', height=400, showlegend=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        st.markdown("### Detailed Comparison")
        
        display_df = df_combined[['neighborhood', 'density', 'parking', 'structures', 
                                  'tickets_per_year', 'avg_wait_time']].copy()
        display_df.columns = ['Neighborhood', 'Density', 'Parking', 'Structures', 'Tickets/Year', 'Wait Time']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    except:
        st.warning("Loading neighborhood data...")

st.divider()

st.markdown("## 💡 What Can Be Done?")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    ### Short-Term
    - Reform sweeping schedules
    - Add evening/weekend sweeping
    - Create permit zones
    - Digital availability signs
    """)

with col2:
    st.markdown("""
    ### Medium-Term
    - Build more structures
    - Convert underutilized lots
    - Improve public transit
    - Add bike infrastructure
    """)

with col3:
    st.markdown("""
    ### Long-Term
    - Require parking in new developments
    - Incentivize reduced car ownership
    - Expand Metro connectivity
    - Regional parking planning
    """)

st.divider()

st.markdown("""
## 📊 Data Sources

- **Street Sweeping:** Long Beach Public Works official map
- **Parking Structures:** OpenStreetMap + field verification
- **Tickets:** Long Beach City financial reports
- **Demographics:** US Census Bureau

Analysis by Luba Hristova | Long Beach Resident & GIS Analyst
""")
