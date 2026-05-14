import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import bands_review, compute_bands, load_frame_tab
from specsy_online.utils.formatting import CODE_LINES_FRAME_BASIC, CODE_LINES_FRAME_FILTERED, CODE_LINES_FRAME_ADVANCED
# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line bands preparation')
st.markdown("Use the widgets below to build a line bands table for your observation, or upload an existing one. "
            "Please check the documentation for more details on the [line bands model](https://lime-stable.readthedocs.io/en/latest/1_introduction/3_line_bands.html) "
            "and how to adjust the [default lines database](https://lime-stable.readthedocs.io/en/latest/1_introduction/4_lines_database.html).")

# Check file has been uploaded
if s_state['spec'] is None:
    st.markdown(f'### No observation available')

    st.page_link("pages/1a_Load_spectrum.py", label='Please load an spectrum :yellow[**(link)**]',
                 icon=":material/upload:")
    st.page_link("pages/1a_Load_spectrum.py",
                 label='or get an observation from the virtual observatory page :yellow[**(link)**]',
                 icon=":material/archive:")

# Use the observation to create reference bands
else:

    # Compute bands
    st.space('small')
    st.subheader('Template', help=None, divider='gray', width="stretch", text_alignment="left")
    compute_bands()

    # Adjust the bands
    if s_state.bands_df is not None:

        st.space('small')
        st.subheader('Editor', help=None, divider='gray', width="stretch", text_alignment="left")
        st.markdown(f'You can modify the cell values directly in the table below. Additionally, in the "Individual bands" tab,'
                    f' you can interactively adjust the wavelength intervals.')
        bands_review()

        # Download the bands to a file
        if s_state.get('id') is not None:
            table_name = s_state['id'].replace('.fits', "") + f'_line_bands.txt'
        else:
            table_name  = 'line_bands.txt'
        st.download_button(label='Download line bands to a .txt file', file_name=table_name,
                           data=s_state.bands_df.to_string().encode('UTF-8'))

# Code example
st.write('***')
with st.expander("Code examples", icon=":material/laptop_windows:"):
    st.caption("Get all lines in range")
    st.code(CODE_LINES_FRAME_BASIC, language="python")
    st.caption("Filter by particle and velocity")
    st.code(CODE_LINES_FRAME_FILTERED, language="python")
    st.caption("Per-line band customization")
    st.code(CODE_LINES_FRAME_ADVANCED, language="python")