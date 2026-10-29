import streamlit as st
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import load_spectrum_tab, display_menu
from specsy_online.utils.formatting import CODE_FROM_FILE_OBSERVATION, CODE_ARRAYS_OBSERVATION


# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Load observation')
st.markdown("Use the widgets below to upload an spectrum from a **.fits** from the supported instruments or from a "
            "text file (**.txt**, **.csv**, **.dat**...). Please check the [LiMe documentation](https://lime-stable.readthedocs.io/en/latest/2_guides/0_creating_observations.html) "
            "for more examples on how to load spectroscopic data")

# Code example
with st.expander("Code examples", icon=":material/laptop_windows:"):
    st.caption("Spectrum creation from data arrays")
    st.code(CODE_ARRAYS_OBSERVATION, language="python")
    st.caption("Spectrum creation by loading a FITS file from supported instruments")
    st.code(CODE_FROM_FILE_OBSERVATION, language="python")

# Configuration menu
st.write('***')
with st.container(key='este'):
    load_spectrum_tab()

# Show the input data
display_menu()

