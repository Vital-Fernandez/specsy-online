import streamlit as st
from streamlit import session_state as s_state, secrets

from utils.sidebar import sidebar_widgets
from streamlit_authenticator import Authenticate
from utils.interfaces import load_spectrum_tab, display_menu
from pages.collaborations.capers import capers_selection

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Load observation file')
st.markdown(f'The menu below can be used to read a *.fits* file from the supported instruments.')

# Configuration menu
load_spectrum_tab()

# Show the input data
display_menu()

