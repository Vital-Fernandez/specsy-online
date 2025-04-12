import streamlit as st
from utils.input_output import load_logo
from utils.sidebar import sidebar_widgets

# Resources
INTRODUCTION_TEXT = r'Welcome to the Spectra Synthesis utils, use the sidebar menu to select the treatments.'


# Url menus
menu_items = {  # 'About': f'## Specsy {sy.__version__} alpha release',
    'Report a bug': "https://github.com/Vital-Fernandez/specsy"}
st.set_page_config(page_title="SpecSy", menu_items=menu_items)

# Sidebar
st.sidebar.success("Navigate the workflow from the sections above")
sidebar_widgets()

# Specsy logo and welcome
col_logo, col_welcome = st.columns([0.4, 0.6], gap='large')

with col_logo:
    image = load_logo()
    # st.logo(image=image)

    st.image(image, width=300)

with col_welcome:
    st.markdown(f'# SpecSy')

# Introduction text
st.markdown("***")
st.markdown(INTRODUCTION_TEXT, unsafe_allow_html=True)
