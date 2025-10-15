import streamlit as st

st.set_page_config(
    page_title="GIS & AI Portfolio | Luba Hristova",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ GIS & AI Solutions Portfolio")
st.subheader("Luba Hristova | GIS Analyst & AI Developer")

st.markdown("""
**Long Beach, CA** | [LinkedIn](https://linkedin.com/in/luba-hristova) | [GitHub](https://github.com/hristova022)
""")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## About This Portfolio
    
    Interactive case studies demonstrating expertise in **geospatial analysis** and **artificial intelligence**, 
    combining GIS techniques with machine learning to solve complex spatial problems.
    
    Each project showcases the ability to work with spatial data, build analytical models, 
    and create interactive visualizations using industry-standard tools and techniques.
    
    ### Technical Expertise
    - **GIS & Spatial Analysis:** 6+ years working with ArcGIS, QGIS, and Python geospatial libraries
    - **AI & Machine Learning:** Predictive modeling, computer vision, data-driven decision making
    - **Data Engineering:** Processing large datasets, API integration, cloud-based workflows
    - **Full-Stack Development:** From data collection to interactive web applications
    """)

with col2:
    st.markdown("""
    ### 🛠️ Tech Stack
    - **GIS:** GeoPandas, Pydeck, QGIS
    - **ML/AI:** TensorFlow, scikit-learn
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
        st.markdown("### 🏠 LA County Homeless Services Analysis")
        st.markdown("""
        **Are we keeping pace with the crisis?**
        
        Comprehensive temporal analysis examining LA County's homeless population growth 
        vs. shelter capacity expansion from 2015-2025.
        
        **Key Findings:**
        - 75.8% increase in homeless population
        - Only 67.8% increase in shelter capacity
        - 9 food banks, 6 shelters, 5 support centers mapped
        - Service gap zones identified across LA County
        
        **Skills Demonstrated:** GIS analysis, temporal trends, policy impact assessment, 
        data visualization, reproducible research
        """)
        if st.button("View Full Analysis →", key="homeless", use_container_width=True):
            st.switch_page("pages/1_Homeless_Resources.py")
    
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
        st.markdown("### 🔥 Wildfire Risk Dashboard")
        st.markdown("""
        Predictive risk modeling for Southern California wildfires with 
        real-time weather and vegetation data.
        
        **Skills:** ML modeling, disaster response, spatial analysis, predictive analytics
        """)
        st.markdown("*Coming Soon*")
    
    with st.container(border=True):
        st.markdown("### 🏗️ AI Damage Assessment")
        st.markdown("""
        Machine learning model for automated building damage detection 
        from satellite and aerial imagery.
        
        **Skills:** Computer vision, AI/ML, disaster response, image classification
        """)
        st.markdown("*Coming Soon*")

st.divider()

st.markdown("""
### 💡 About Me

I'm a GIS professional with expertise in artificial intelligence and spatial data science. 
My work combines geospatial analysis with machine learning to create data-driven solutions 
for complex real-world problems, from disaster response to community planning.

**Want to connect?** Reach out on [LinkedIn](https://linkedin.com/in/luba-hristova) or 
check out the code on [GitHub](https://github.com/hristova022/gis-portfolio).
""")
