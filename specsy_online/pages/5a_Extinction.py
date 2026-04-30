import streamlit as st
from streamlit import session_state as s_state

from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import extinction_form

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Gas extinction')
st.markdown(f'Using the menu below to calculate the gas extinction from the hydrogen emission line fluxes.')

if s_state['lines_df'] is not None:
    extinction_form('lines_df')
    # try: extinction_form('lines_df')
    # except Exception as e: st.error(f"An error occurred: {e}")
