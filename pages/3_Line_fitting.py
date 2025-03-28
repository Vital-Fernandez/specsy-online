import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.io import declare_line_measuring
from utils.plots import lime_spec_plotting, bokeh_spectrum

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line Measuring')

# Run the measurement
declare_line_measuring()

# Plot the results
spec = s_state['spec']

if spec is not None:

    if spec.frame is not None:

        if len(spec.frame.index) > 0:

            st.markdown("***")

            tab_spectrum, tab_grid, tab_table = st.tabs(["Spectrum", "Grid plot", "Table"])

            with tab_spectrum:
                st.markdown(f'## Line fittings over-plotted over spectrum')
                bokeh_spectrum(spec)

            with tab_grid:
                st.markdown(f'## Profile plot grid')
                fig_conf = {'figure.figsize': (3 * 2, 1.5 + 10 * int(spec.frame.index.size / 3)), 'figure.dpi' : 200}
                lime_spec_plotting(spec, 'grid', n_cols=2, fig_cfg=fig_conf)

            with tab_table:
                st.markdown(f'## Measurements table')
                log_df = spec.frame
                st.dataframe(log_df)

                # Ready for download
                string_DF = log_df.to_string()
                table_name = s_state['id'].replace('.fits', '_frame.txt')
                st.download_button('Download', data=string_DF.encode('UTF-8'), file_name=table_name)

else:
    st.markdown("***")
    st.markdown(f'#### Please upload a spectrum before fitting the lines')

