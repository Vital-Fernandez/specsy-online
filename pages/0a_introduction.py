import streamlit as st
from utils.input_output import load_logo
from utils.sidebar import sidebar_widgets


# Url menus
st.set_page_config(page_title="SpecSy",
                   menu_items={'Report a bug': "https://github.com/Vital-Fernandez/specsy"},
                   layout='wide')

# Sidebar
sidebar_widgets()

# Specsy logo and welcome
col_logo, col_welcome = st.columns([0.4, 0.6], gap='large')

with col_logo:
    image = load_logo()

    st.image(image, width=300)

with col_welcome:
    st.markdown(f'# SpecSy')

# Introduction text
st.markdown("***")
st.markdown(
                """
                <p style='font-size:20px;'>
                Welcome to the Spectra Synthesis platform.
                Use the sidebar menu to navigate the tools.
                </p>
                """,
                unsafe_allow_html=True
            )

# References
with st.expander("Tools references", icon=":material/handyman:"):
    st.markdown(
        """
        **(LiMe) Fernández, V., Morisset, C., & Hernández, S. (2024).**  
        *[LIME: A LIne MEasuring library for large and complex spectroscopic datasets.](https://www.aanda.org/articles/aa/full_html/2024/08/aa49224-24/aa49224-24.html)*  

        **(SpecSy) Fernández, V., Amorín, R., Sánchez-Janssen, R., del Valle-Espinosa, M. G., & Papaderos, P.(2023).**   
        *[The resolved chemical composition of the starburst dwarf galaxy CGCG007-025: direct method versus
         photoionization model fitting.](https://doi.org/10.1093/mnras/stad198)*  
        """,

        unsafe_allow_html=True
    )

with st.expander("Data references", icon=":material/import_contacts:"):
    st.markdown(
        """
        **(PyNeb) Luridiana, V., Morisset, C., & Shaw, R. A.(2015).**   
        *[PyNeb: A new tool for analyzing emission lines.](https://www.aanda.org/articles/aa/full_html/2015/01/aa23152-13/aa23152-13.html)*  

        **Chatzikos, M., Bianchi, S., Camilloni, F., et al. (2023).**  
        *[The 2023 release of Cloudy.](https://arxiv.org/abs/2308.06396)*  
        """,

        unsafe_allow_html=True
    )

