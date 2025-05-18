import streamlit as st
from streamlit import session_state as s_state

import lime
from utils.sidebar import sidebar_widgets
from utils.interfaces import extinction_form
from numpy import sort
from utils.plots import matrix_plot

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Gas extinction')
st.markdown(f'Using the menu below to calculate the gas extinction from the hydrogen emission line fluxes.')

if s_state['lines_df'] is not None:

    try: extinction_form('lines_df')
    except Exception as e: st.error(f"An error occurred: {e}")
