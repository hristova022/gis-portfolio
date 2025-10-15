# Restore clean homepage

import os
from getpass import getpass

github_token = getpass('Enter your GitHub token: ')

!git config --global user.email "hristova022@gmail.com"
!git config --global user.name "Luba Hristova"

repo_url = f"https://{github_token}@github.com/hristova022/gis-portfolio.git"

!rm -rf gis-portfolio
!git clone {repo_url}
os.chdir('gis-portfolio')

print("\nRestoring clean homepage...")

clean_homepage = '''import streamlit as st

st.set_page_config(
    page_title="GIS Portfolio | Luba Hristova",
    page_icon="🗺️",
    layout="wide"
)

st.title("🗺️ GIS & AI Solutions Portfolio")
st.subheader("Luba Hristova | GIS Analyst | Spatial Data Science & AI")

st.markdown("""
**Long Beach, CA** | [LinkedIn](https://linkedin.com/in/luba-hristova) | [GitHub](https://github.com/hristova022)
""")

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
    ## About This Portfolio
    
    Interactive case studies demonstrating expertise in **GIS analysis**, **spatial data science**, 
    and **artificial intelligence**, combining geospatial techniques with advanced analytics 
    to solve complex spatial problems.
    
    Each project showcases the ability to work with spatial data, build analytical models, 
    and create interactive visualizations using industry-standard tools and techniques.
    
    ### Technical Expertise
    - **GIS & Spatial Analysis:** 6+ years working with ArcGIS, QGIS, and Python geospatial libraries
    - **Spatial Data Science:** Statistical modeling, spatial statistics, predictive analytics
    - **AI & Machine Learning:** Computer vision, predictive modeling, data-driven insights
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
        
        **Skills Demonstrated:** GIS analysis, temporal trends, ML predictive modeling,
        data visualization, interactive decision support tools
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

I'm a GIS professional specializing in spatial data science and artificial intelligence. 
My work combines geospatial analysis with machine learning to create data-driven solutions 
for complex real-world problems, from disaster response to community planning.

**Want to connect?** Reach out on [LinkedIn](https://linkedin.com/in/luba-hristova) or 
check out the code on [GitHub](https://github.com/hristova022/gis-portfolio).
""")
'''

with open('streamlit_app.py', 'w') as f:
    f.write(clean_homepage)

!git add streamlit_app.py
!git commit -m "Fix: Restore clean homepage"
!git push

print("\n✅ Homepage fixed!")
print("\nYour app should be working now")
print("Check: https://hristova022-gis-portfolio-streamlit-app-dvsj0a.streamlit.app")
