from pathlib import Path

import numpy as np
import streamlit as st
from streamlit import session_state as s_state

from specsy_online.utils.sidebar import sidebar_widgets
from streamlit_bokeh import streamlit_bokeh

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Stellar population synthesis')

# Check if observation is available
spec = s_state.get('spec')

if spec is not None:

    st.write(np.sum(spec.wave.mask))
    spec.bokeh.spectrum(in_fig=None)
    streamlit_bokeh(spec.bokeh.fig, key='bokeh_spsynth_plot', use_container_width=True)