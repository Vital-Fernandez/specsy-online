import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.interfaces import declare_line_measuring, load_frame_tab
from specsy_online.utils.plots import lime_spec_plotting, bokeh_spectrum
from specsy_online.utils.input_output import on_toml_change, save_state, parse_lime_cfg, parse_line_bands_df
from specsy_online.utils.formatting import CODE_FIT_FRAME_BASIC, CODE_FIT_FRAME_ADVANCED, CODE_FIT_FRAME_FILTERED
import tomlkit

if "toml_area_key" not in st.session_state:
    st.session_state.toml_area_key = 0

if "toml_text" not in st.session_state:
    st.session_state.toml_text = "[default_line_fitting]\n"

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Line Measuring')

st.markdown("Use the widgets below to measure the line fluxes and fit their profiles. The text block on the right hand side "
            "allows the user to introduce the [configuration](https://lime-stable.readthedocs.io/en/latest/1_introduction/5_fitting_configuration.html) for the line fittings . "
            "Please check the  LiME documentation for the [measurements description](https://lime-stable.readthedocs.io/en/latest/3_explanations/0_measurements.html).")


with st.expander("Code examples", icon=":material/laptop_windows:"):
    st.caption("Basic usage")
    st.code(CODE_FIT_FRAME_BASIC, language="python")
    st.caption("Filter lines and profile options")
    st.code(CODE_FIT_FRAME_FILTERED, language="python")
    st.caption("Advanced fitting options")
    st.code(CODE_FIT_FRAME_ADVANCED, language="python")


# Run the measurement
tab_fit, tab_upload = st.tabs(['Fit lines', 'Upload measurements'])


with tab_fit:

    if s_state.get('spec') is not None:

        col_args, col_fit_cfg = st.columns([0.5, 0.5], gap='large')
        with col_args:
            st.markdown(f'#### Function arguments')

            col_A, col_B, col_C = st.columns(3, gap='large')

            with col_A:
                min_method = st.selectbox(label='Minimization method', options=['leastsq', 'least_squares'],
                                          help='Minimization algorithm used by lmfit for profile fitting.')

            with col_B:
                profile = st.selectbox(label='Profile type', options=[None, 'g', 'l', 'pv'],
                                       format_func=lambda x: {None: 'Default (Gaussian)', 'g': 'Gaussian', 'l': 'Lorentzian', 'pv':'Pseudo-Voigt'}[x],
                                       help='Line profile type for fitting. Defaults to the line database entry if omitted.')

            with col_C:
                shape = st.selectbox(label='Line shape', options=[None, 'emi', 'abs'],
                                     format_func=lambda x: {None: 'Default (emission)', 'emi': 'Emission', 'abs': 'Absorption'}[x],
                                     help='Line shape keyword. Defaults to the line database entry if omitted.')

            col_D, col_E, col_F = st.columns(3, gap='large')

            with col_D:
                cont_source = st.selectbox(label='Continuum source', options=['central', 'adjacent', 'fitted'],
                                            format_func=lambda x: {'central': 'Central',
                                                                   'adjacent':'Adjacent bands (w1–w2, w5–w6)',
                                                                   'fitted':  'Pre-fitted continuum'}[x],
                                            help='Method used to estimate the continuum level for line fitting.')

            with col_E:
                err_from_bands = st.selectbox(label='Uncertainty source', options=[None, True, False],
                                              format_func=lambda x: {None: 'Auto (uncertainty spectrum)',
                                                                     True: 'Continua bands',
                                                                     False:'Uncertainty spectrum'}[x],
                                              help='Controls how pixel uncertainties are estimated during fitting.')

            with col_F:
                options = [None] if (s_state.get('bands_df') is None) else s_state['bands_df'].index.to_list()
                line_list = st.multiselect(label='Line list', options=options, default=None,
                                           help='Subset of lines to fit. If empty, all lines in the bands table are measured.')

        with col_fit_cfg:
            st.markdown(f'#### Fitting configuration')
            st.markdown(f'This section represents an [input toml file](https://toml.io/en/) for LiMe functions. Please check the '
                        f'[documentation](https://lime-stable.readthedocs.io/en/latest/1_introduction/5_fitting_configuration.html#loading-the-fitting-configuration-from-a-text-file) '
                        f'for more tips on how to adjust your fittings')
            st.text_area(label="Configuration toml", value=st.session_state.toml_text, height=300, on_change=on_toml_change,
                         key=f"toml_input_{st.session_state.toml_area_key}", label_visibility='collapsed')

        # Launch the fitting
        if st.button("Run fit", key='button_fit'):
            if s_state['spec'] is not None:
                if (s_state['bands_df'] is not None):

                    # Unpack the data
                    spec, bands = s_state['spec'], s_state['bands_df']
                    input_cfg = parse_lime_cfg(tomlkit.loads(st.session_state.toml_text).unwrap())

                    # Clear previous measurements
                    spec.clear_data()
                    s_state['lines_df'] = None

                    # Measuring the lines
                    try:
                        my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                        spec.fit.frame(bands,
                                       fit_cfg=input_cfg,
                                       line_list=None if (line_list is None or len(line_list) == 0) else line_list,
                                       profile=profile,
                                       shape=shape,
                                       cont_source=cont_source,
                                       err_from_bands=err_from_bands,
                                       min_method=min_method)
                        my_bar.empty()

                        # Save the dataframe which now contains the measurements
                        save_state('spec', spec)
                        save_state('lines_df', spec.frame.copy())

                    except Exception as e:
                        st.error(f"An error occurred during the measurement: {e}")

                else:
                    st.warning('Please define the line bands')
            else:
                st.warning('Please upload a spectrum')

    else:
        st.markdown(f'### No observation available')

        st.page_link("pages/1a_Load_spectrum.py", label='Please load an spectrum :yellow[**(link)**]',
                     icon=":material/upload:")
        st.page_link("pages/1a_Load_spectrum.py",
                     label='or get an observation from the virtual observatory page :yellow[**(link)**]',
                     icon=":material/archive:")

# Upload previous measurements surveys
with tab_upload:
    with st.container():
        uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

        if st.button("Load line measurements"):
            s_state['lines_df'] = None

            if uploaded_file:
                try:
                    df = parse_line_bands_df(uploaded_file)
                    save_state('lines_df', df)
                except Exception as e:
                    df = None
                    st.error(f"An error occurred loading the line measurements frame:\n{e}")

            else:
                st.warning(f'No measurements file declared')

            # Load the data on the spectrum after clearing it
            if s_state.get('spec') is not None:
                spec = s_state['spec']
                spec.clear_data()

                if df is not None:
                    spec.load_frame(df)
                    save_state('spec', spec)

# Show the measurements
if s_state.get('lines_df') is not None:
    st.space('medium')
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
            st.dataframe(s_state['lines_df'])

            # Ready for download
            if s_state['id'] is not None:
                table_name = s_state['id'].replace('.fits', '_frame.txt')
            else:
                table_name = 'line_measurements_df.txt'
            st.download_button('Download line measurements', data=s_state['lines_df'].to_string().encode('UTF-8'),
                               file_name=table_name)


    else:
        with tab_list[0]:
            log_df = s_state['lines_df']
            st.dataframe(log_df)

        # Ready for download
        if s_state['id'] is not None:
            table_name = s_state['id'].replace('.fits', '_frame.txt')
        else:
            table_name  = 'line_measurements_df.txt'
        st.download_button('Download line measurements', data=log_df.to_string().encode('UTF-8'), file_name=table_name)

st.write('***')

