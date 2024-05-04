import streamlit as st
import specsy as sy
from pathlib import Path
from tools.io import load_logo

from tools.sidebar import sidebar_widgets

# Resources
INTRODUCTION_TEXT = r'Welcome to the online site for the Spectra Synthesis tools. '

# Welcome screen
def run():

    # Url menus
    menu_items = {'About': f'## Specsy {sy.__version__} alpha release',
                  'Report a bug': "https://github.com/Vital-Fernandez/specsy"}
    st.set_page_config(page_title="SpecSy", menu_items=menu_items)

    # Title

    # Side bar
    st.sidebar.success("Navigate the workflow from the sections above")
    sidebar_widgets()

    # CEERs logo and welcome
    col_logo, col_welcome = st.columns([0.3, 0.7], gap='large')

    with col_logo:
        image = load_logo()
        #st.image(image, width=300)

    with col_welcome:
        st.markdown(f'# Spectra synthesis')

    # Introduction text
    st.markdown("***")
    st.markdown(INTRODUCTION_TEXT, unsafe_allow_html=True)

    return


if __name__ == "__main__":

    run()

