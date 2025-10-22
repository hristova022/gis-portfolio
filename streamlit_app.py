import streamlit as st

st.set_page_config(
    page_title="GIS Portfolio | Luba Hristova",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ GIS & Climate Solutions Portfolio")

# New Dashboard: Community Voice
st.info("💬 **NEW:** Check out the Community Pulse dashboard in the sidebar - tracking Long Beach online conversations!")

st.subheader("Luba Hristova | GIS Analyst | Spatial Data Science")

st.markdown("""
**Long Beach, CA** | [LinkedIn](https://linkedin.com/in/luba-hristova) | [GitHub](https://github.com/hristova022)
""")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## About This Portfolio
    
    Interactive case studies demonstrating expertise in **GIS analysis**, **spatial data science**, 
    and **climate risk assessment**, combining geospatial techniques with data analytics 
    to solve real-world problems.
    
    Each project showcases the ability to work with spatial data, build analytical models, 
    and create interactive visualizations using industry-standard tools and techniques.
    
    ### Technical Expertise
    - **GIS & Spatial Analysis:** 6+ years working with ArcGIS, QGIS, and Python geospatial libraries
    - **Spatial Data Science:** Statistical modeling, spatial statistics, predictive analytics
    - **Climate & Risk Analysis:** Wildfire, flooding, and disaster risk assessment
    - **Full-Stack Development:** From data collection to interactive web applications
    """)

with col2:
    st.markdown("""
    ### 🛠️ Tech Stack
    - **GIS:** GeoPandas, Pydeck, QGIS
    - **Data:** Pandas, NumPy
    - **Viz:** Streamlit, Plotly
    - **Cloud:** Colab, GitHub
    
    ### 📊 Data Sources
    - OpenStreetMap
    - NOAA, NASA FIRMS
    - CAL FIRE
    - LA Homeless Services Authority
    - Long Beach Open Data
    """)

st.divider()

st.markdown("## 📂 Case Studies")

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.markdown("### 🏠 Homelessness Resources LA County")
        st.markdown("""
        **Are we keeping pace with the crisis?**
        
        Comprehensive temporal analysis examining LA County's homeless population growth 
        vs. shelter capacity expansion from 2015-2025.
        
        **Key Findings:**
        - 75.8% increase in homeless population
        - Only 67.8% increase in shelter capacity
        - 9 food banks, 6 shelters, 5 support centers mapped
        - Predictive analysis of high-need areas
        
        **Skills Demonstrated:** GIS analysis, temporal trends, predictive modeling,
        interactive decision support, data visualization
        """)
        if st.button("View Full Analysis →", key="homeless", use_container_width=True):
            st.switch_page("pages/1_Homeless_Resources.py")
    
    with st.container(border=True):
        st.markdown("### 🅿️ Long Beach Parking Analysis")
        st.markdown("""
        **Data-driven analysis of parking scarcity in Long Beach**
        
        Using satellite imagery and computer vision to analyze parking availability,
        combined with street sweeping schedules and infrastructure mapping.
        
        **Key Findings:**
        - 800+ spaces lost on street sweeping days
        - 89% average structure occupancy at peak times
        - Belmont Shore worst area (98% occupancy weekends)
        - Computer vision processing of aerial imagery
        
        **Skills Demonstrated:** Computer vision, satellite imagery analysis, 
        spatial statistics, municipal data analysis, interactive visualization
        """)
        if st.button("View Full Analysis →", key="parking", use_container_width=True):
            st.switch_page("pages/2_Parking_Analysis.py")
    
    with st.container(border=True):
        st.markdown("### 🌊 Sea Level Rise Simulator")
        st.markdown("""
        Coastal flooding impact analysis with property risk assessment under 
        different sea level rise scenarios.
        
        **Skills:** Climate modeling, risk assessment, economic impact analysis
        """)
        st.markdown("*Coming Soon*")

with col2:
    with st.container(border=True):
        st.markdown("### 🔥 Southern California Wildfire Activity (Past & Recent)")
        st.markdown("""
        **8 major high-risk zones mapped and analyzed**
        
        Clear, story-driven wildfire risk assessment showing WHERE fires are most 
        likely and WHY each area is dangerous. Covers 96,000+ homes at risk across 
        LA, Orange, Riverside, San Bernardino, Ventura, and San Diego counties.
        
        **Key Findings:**
        - Malibu/Santa Monica Mountains: Highest risk (95/100)
        - Angeles National Forest: 15,000 homes at risk
        - Orange County Foothills: 22,000 homes at risk
        - Focus on Wildland-Urban Interface dangers
        
        **Skills Demonstrated:** Risk modeling, spatial analysis, data synthesis 
        from multiple sources (CAL FIRE, NASA FIRMS, county records), clear data storytelling
        """)
        if st.button("View Activity Map →", key="wildfire", use_container_width=True):
            st.switch_page("pages/3_Wildfire_Risk.py")
    
    with st.container(border=True):
        st.markdown("### 🏗️ Building Damage Assessment")
        st.markdown("""
        Automated building damage detection from satellite and aerial imagery 
        using computer vision techniques.
        
        **Skills:** Computer vision, disaster response, image classification
        """)
        st.markdown("*Coming Soon*")

st.divider()

st.markdown("""
### 💡 About Me

I'm a GIS professional specializing in spatial data science and climate risk analysis. 
My work combines geospatial analysis with data science to create data-driven solutions 
for complex real-world problems, from disaster response to community planning.

**Want to connect?** Reach out on [LinkedIn](https://linkedin.com/in/luba-hristova) or 
check out the code on [GitHub](https://github.com/hristova022/gis-portfolio).
""")
