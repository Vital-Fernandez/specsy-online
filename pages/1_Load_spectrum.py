import streamlit as st
from streamlit import session_state as s_state

from tools.io import declare_spectrum
from tools.plots import plot_spectrum
from tools.sidebar import sidebar_widgets
from tools.operations import compute_redshift


# Sidebar information
sidebar_widgets()

# Widget to rea the spectrum
st.markdown(f'# Load spectrum')
st.markdown(f'Please declare *.fits* file location and source instrument:')
declare_spectrum()

# Check file has been uploaded
if s_state['spec'] != 'No':

    spec = s_state['spec']

    # Plot with the spectrum
    plot_spectrum(spec)
    st.markdown("***")

    # Fit the redshift if necesary
    if spec.redshift == 0:
        compute_redshift(spec)



