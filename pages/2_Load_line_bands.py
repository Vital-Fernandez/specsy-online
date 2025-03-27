import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.interfaces import declare_bands_form, bands_review
from utils.io import save_state, widget_save_state

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Define line bands')
st.markdown(f'Using the menu below you can generate a table with bands for your observation or upload one from the '
            f'computer. \nOnce the bands are properly declared they can be directly adjusted on the displayed table.')

# Check file has been uploaded
if s_state['spec'] is None:
    st.markdown(f'Please load an observation.')

# Use the observation to create reference bands
else:

    # Generate the bands
    declare_bands_form()

    # Adjust the bands
    bands_review()