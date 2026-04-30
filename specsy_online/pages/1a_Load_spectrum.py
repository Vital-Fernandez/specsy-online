import streamlit as st
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import load_spectrum_tab, display_menu

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Load observation')
st.markdown(
            "Use the menus below to load a spectrum from a text file "
            "(*.txt*, *.csv*) or a *.fits* file from one of the supported instruments."
            )

# Configuration menu
with st.container(key='este'):
    load_spectrum_tab()

# Show the input data
display_menu()

