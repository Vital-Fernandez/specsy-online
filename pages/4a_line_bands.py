import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.interfaces import bands_review, match_bands_tab, load_frame_tab
from utils.input_output import download_frame_form

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line bands')
st.markdown(f'Using the menu below you can generate a table with bands for your observation or upload one'
            f'computer. The current lines database can be found at this [link](https://docs.google.com/spreadsheets/d/10S_2iW7ygyM9_aMPtHAsIPIISwv72SwPFiSSKcV-n7s/edit?usp=sharing).')

# Check file has been uploaded
if s_state['spec'] is None:
    st.markdown(f'Please load a spectrum.')

# Use the observation to create reference bands
else:

    # Generate the bands
    with st.form('load_bands_form', border=True, enter_to_submit=False, clear_on_submit=False):

        tab_infer, tab_upload = st.tabs(["Match to observation", "Load from file"])

        # Load spectrum
        with tab_infer:
            match_bands_tab()

        # Query surveys
        with tab_upload:
            load_frame_tab('bands_df')

    # Adjust the bands
    if s_state.bands_df is not None:

        st.markdown('')
        st.subheader('Manual adjustment', help=None, divider='gray', width="stretch", text_alignment="left")

        st.markdown(f'You can modify the cell values directly in the table below. Additionally, in the "Individual bands" tab,'
                    f' you can interactively adjust the wavelength intervals.')
        bands_review()

        # Download the bands to a file
        st.subheader('Download', help=None, divider='gray', width="stretch", text_alignment="left")
        st.markdown(f'Save bands selection to a text file.')
        download_frame_form(f'{s_state["id"]}_bands_df.txt', s_state.bands_df)
