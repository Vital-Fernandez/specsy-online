import streamlit as st
import specsy as sy
from pathlib import Path
from tools.io import load_logo

from tools.sidebar import sidebar_widgets

# Resources
INTRODUCTION_TEXT = r'Welcome to the Spectra Synthesis tools, use the sidebar menu to select the treatments.'

# Welcome screen
def run():

    # Url menus
    menu_items = {'About': f'## Specsy {sy.__version__} alpha release',
                  'Report a bug': "https://github.com/Vital-Fernandez/specsy"}
    st.set_page_config(page_title="SpecSy", menu_items=menu_items)

    # Title

    # Sidebar
    st.sidebar.success("Navigate the workflow from the sections above")
    sidebar_widgets()

    # CEERs logo and welcome
    col_logo, col_welcome = st.columns([0.4, 0.6], gap='large')

    with col_logo:
        image = load_logo()
        st.image(image, width=300)

    with col_welcome:
        st.markdown(f'# SpecSy')

    # Introduction text
    st.markdown("***")
    st.markdown(INTRODUCTION_TEXT, unsafe_allow_html=True)

    return


if __name__ == "__main__":

    run()

