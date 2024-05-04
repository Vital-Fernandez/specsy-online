import streamlit as st
from streamlit import session_state as s_state
from tools.sidebar import sidebar_widgets
from tools.io import declare_line_measuring
from tools.plots import lime_spec_plotting

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line Measuring')

# Run the measurement
declare_line_measuring()

# Plot the results
spec = s_state['spec']
if spec.frame is not None:

    st.markdown("***")

    tab_spectrum, tab_grid, tab_table = st.tabs(["Spectrum", "Grid plot", "Table"])

    with tab_spectrum:
        st.markdown(f'## Line fittings over-plotted over spectrum')
        lime_spec_plotting(spec, 'spectrum', rest_frame=True)

    with tab_grid:
        st.markdown(f'## Profile plot grid')
        lime_spec_plotting(spec, 'grid')

    with tab_table:
        st.markdown(f'## Measurements table')
        log_df = spec.frame
        st.dataframe(log_df)

        # Ready for download
        string_DF = log_df.to_string()
        table_name = s_state['id'].replace('.fits', '_frame.txt')
        st.download_button('Download', data=string_DF.encode('UTF-8'), file_name=table_name)

