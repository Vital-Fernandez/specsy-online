import streamlit as st
from streamlit import session_state as s_state
from tools.sidebar import sidebar_widgets
from tools.io import declare_line_bands

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line bands')

# Run the measurement
declare_line_bands()

if s_state['bands_df'] is not None:

    st.markdown(f'### Input bands dataframe:')
    st.dataframe(s_state['bands_df'])

