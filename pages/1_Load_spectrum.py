import streamlit as st
from streamlit import session_state as s_state

from utils.sidebar import sidebar_widgets
from utils.interfaces import declare_spectrum_form
from utils.plots import bokeh_spectrum
from utils.io import get_text_spectrum, convert_for_download

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Declare observation')
st.markdown(f'The tabs below provide different methods to import spectroscopic data.')

# Form to load the data
declare_spectrum_form()

# Check file has been uploaded
if s_state['spec'] is not None:

    # Show the spectrum
    st.markdown("***")
    st.markdown(f'## Input observation')

    # Plot spectrum
    bokeh_spectrum(s_state['spec'])

    # Download
    rec_arr = get_text_spectrum('spec')
    csv = convert_for_download(rec_arr)
    st.markdown(f'Click the button below to download the spectrum as a text file.')
    st.download_button(label="Download", data=csv, file_name="spectrum.csv", mime="text/csv", icon=":material/download:")


