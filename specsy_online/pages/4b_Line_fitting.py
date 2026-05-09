import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import declare_line_measuring, load_frame_tab
from specsy_online.utils.plots import lime_spec_plotting, bokeh_spectrum
from specsy_online.utils.input_output import on_toml_change, save_state, parse_lime_cfg
import tomlkit

if "toml_area_key" not in st.session_state:
    st.session_state.toml_area_key = 0

if "toml_text" not in st.session_state:
    st.session_state.toml_text = "[default_line_fitting]\n"

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line Measuring')

# Run the measurement
tab_fit, tab_upload = st.tabs(['Fit lines', 'Upload measurements'])

with tab_fit:

    st.markdown(f'### Write the fitting configuration:')

    st.text_area(label="Configuration toml", value=st.session_state.toml_text, height=300, on_change=on_toml_change,
                 key=f"toml_input_{st.session_state.toml_area_key}",
                 help='Please check LiMe documentation to read more on how to adjusts your fittings',)

    if s_state['spec'] is not None:

        # Show upload button if inputs are declared
        if (s_state['bands_df'] is not None):

            # Every form must have a submit button.
            if st.button("Fit lines", key='button_bands'):

                # Clear previous measurements
                s_state['lines_df'] = None

                spec, bands = s_state['spec'], s_state['bands_df']
                st.dataframe(s_state['bands_df'])
                input_cfg = parse_lime_cfg(tomlkit.loads(st.session_state.toml_text).unwrap())

                # Clear previous measurements
                spec.frame = spec.frame.iloc[0:0]

                # Measuring the lines
                try:
                    my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                    spec.fit.frame(bands, fit_cfg=input_cfg)
                    my_bar.empty()
                except Exception as e:
                    st.error(f"An error occurred: {e}")

                # Save the dataframe which now contains the measurements
                save_state('spec', spec)
                save_state('lines_df', spec.frame.copy())

        else:
            st.write('Please declare the line bands')

    else:
        st.write('Please upload a spectrum')

# Query surveys
with tab_upload:
    with st.container():
        load_frame_tab()
        if s_state.lines_df is not None:
            st.success('Successful upload')

# Show the measurements
if s_state.get('lines_df') is not None:

    st.markdown(f'## Results')
    if s_state.get('spec') is not None:
        tabs_list = ["Spectrum", "Grid plot", "Table"]
    else:
        tabs_list = ["Table"]

    tab_list = st.tabs(tabs_list)

    if len(tabs_list) > 1:
        with tab_list[0]:
            st.markdown(f'## Line fittings over-plotted on spectrum')
            bokeh_spectrum('spec')

        with tab_list[1]:
            st.markdown(f'## Line profile grid')
            fig_conf = {'figure.figsize': (3 * 2, 1.5 + 10 * int(s_state['spec'].frame.index.size / 3)), 'figure.dpi' : 200}
            lime_spec_plotting(s_state['spec'], 'grid', n_cols=2, fig_cfg=fig_conf)

        with tab_list[2]:
            st.markdown(f'## Measurements table')
            log_df = s_state['lines_df']
            st.dataframe(log_df)

            # Ready for download
            string_DF = log_df.to_string()
            table_name = s_state['id'].replace('.fits', '_frame.txt')
            st.download_button('Download', data=string_DF.encode('UTF-8'), file_name=table_name)

    else:
        with tab_list[0]:
            log_df = s_state['lines_df']
            st.dataframe(log_df)

        # Ready for download
        if s_state['id'] is not None:
            table_name = s_state['id'].replace('.fits', '_frame.txt')
        else:
            table_name  = 'line_measurements_df.txt'
        st.download_button('Download', data=log_df.to_string().encode('UTF-8'), file_name=table_name)
