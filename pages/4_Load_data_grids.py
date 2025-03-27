import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.io import declare_atomic_data
from numpy import sort
from utils.plots import matrix_plot

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Datasets')

# Run the measurement
declare_atomic_data()

if s_state['emiss_dataset'] is not None:

    # Get grid properties
    dataset = s_state['emiss_dataset']
    grid_list = sort(dataset.data_labels)
    data_type = dataset[grid_list[0]].description
    grid_size = dataset[grid_list[0]].shape

    st.markdown(f'### Input grids: "{data_type}" {grid_size}')

    col_gridlogo, col_technique = st.columns([0.7, 0.3])

    with col_gridlogo:
        grid_label = st.selectbox('Select grid', grid_list, key='grid_selection')

    with col_technique:
        approx_list = ['rgi', 'eqn', 'nn']
        technique_label = st.selectbox('Select approximation', approx_list, key='tech_selection')

    data_grid = dataset[grid_label]
    matrix_plot(data_grid)

