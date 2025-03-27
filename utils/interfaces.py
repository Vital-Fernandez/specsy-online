import streamlit as st
from streamlit import session_state as s_state
from .io import save_state, load_spectrum, parse_line_bands_df, widget_save_state
from numpy import unique, sort
from .plots import bokeh_spectrum, bokeh_bands

INSTRUMENT_LIST = ['SDSS', 'OSIRIS', 'ISIS', 'NIRSPEC', 'TEXT']

def unit_conversion_inputs():

    col_units_wave, col_units_flux = st.columns([0.5, 0.5], gap='large')
    message_help = 'These are the default units. Please check astropy for the string unit declaration at this link.'
    with col_units_wave:
        wave_units_str = st.text_input('Wavelength units', value=None, placeholder='Angstrom', help=message_help)

    with col_units_flux:
        flux_units_str = st.text_input('Flux units', value=None, placeholder='FLAM', help=message_help)

    return wave_units_str, flux_units_str

def load_spectrum_tab():

    # Input spectra definition
    col_load_spec, col_properties = st.columns([0.62, 0.38], gap='large')

    with col_load_spec:
        st.markdown(f'#### File address')
        message_label = ('Select or drag a *.fits* or *.txt* file from your computer. Make sure to specify the '
                   'instrument the observation comes from. ')
        message_help = 'The text file must follow the expect format'
        st.markdown(message_label)
        uploaded_file = st.file_uploader(label='Source', type=['.fits', '.txt'], accept_multiple_files=False, key='spec_uploader',
                                         help=message_help)

    with col_properties:
        st.markdown(f'#### Attributes')

        # Instrument
        message_help='Please contact the author if your instrument is not supported with an example file.'
        instrument = st.selectbox('Instrument:', INSTRUMENT_LIST, help=message_help)

        # Redshift
        message_help='Input observation redshift. The default value is 0. All measurements are reported on the observed frame.'
        z_string = st.text_input('Redshift', value=None, help=message_help)

        # Norm flux
        message_help='Optional normalization for the input flux, LiMe will calculate one if necessary'
        norm_flux_string = st.text_input('Normalization flux', value=None, help=message_help)

    # Unit conversion
    st.markdown(f'#### Unit conversion')
    wave_units_str, flux_units_str = unit_conversion_inputs()

    # Components detection
    col_title, col_bottom, col_options = st.columns([0.5, 0.3, 0.2])
    with col_title:
        st.markdown(f'#### Components detection')

    with col_bottom:
        st.markdown("")
        help_message = 'Run machine learning model to detect spectrum components'
        ml_components = st.toggle("Run model", value=False, key='ml_comps_check', help=help_message)

    # Every form must have a submit button.
    st.markdown("")
    message_label = 'Once you are satisfied with the attributes selection click the button below.'
    st.markdown(message_label)

    submitted = st.form_submit_button("Load observation")

    if submitted:

        # Clear the previous state
        save_state('id', None)
        save_state('spec', None)

        if uploaded_file:
            id = uploaded_file.name
            spec = load_spectrum(uploaded_file, instrument, z_string, norm_flux_string, wave_units_str, flux_units_str,
                                                    uploaded_file.name)
            if ml_components:
                spec.infer.components()

            save_state('id', id)
            save_state('spec', spec)

        else:
            st.write('Please declare spectrum address')

    return

def match_bands_tab():

    # Input spectra definition
    col_parameters_1, col_parameters_2 = st.columns([0.5, 0.5], gap='large')

    spec = s_state['spec']
    default_bands = spec.retrieve.line_bands()
    default_line_list = list(default_bands.index)
    default_particle_list = list(sort(unique(default_bands.particle.to_numpy())))

    with col_parameters_1:

        # Transistions selection
        st.markdown(f'##### Transistions selection')
        st.markdown("")

        # Line selection
        with st.expander('Line selection',expanded=True):
            help_message = 'Bands will be limited to these transitions. These candidate list was cropped to the observation wavelength range'
            line_selection = st.multiselect(label='Limit to selection', options=default_line_list, default=None,
                                            key='lines_band_list', help=help_message, placeholder='All', label_visibility="collapsed")

        # Particle selection
        help_message = 'Bands will be limited to these particles. These candidate list was cropped to the observation wavelength range'
        particle_selection = st.multiselect('Particle selection:', options=default_particle_list, placeholder='All', default=None,
                                        key='particle_bands_list', help=help_message)

        # All wavelengths are in vacuum
        st.markdown("")
        help_message = 'Set all transition wavelengths to vacuum values. The default behaviour is transitions 2000Å < λ < 10000Å with air values.'
        vacuum_check = st.toggle("Vacuum wavelengths", value=False, key='vacuum_check', help=help_message)

    with col_parameters_2:

        st.markdown(f'##### Central bands width')
        st.markdown("")

        # Central bandwidth correction
        message_help='Adjust the central line band using the "bands kinematic" width and the "sigma number"'
        adjust_central_bands = st.toggle("Adjust bands", value=True, key='adjust_central_bands', help=message_help)

        # band_vsigma
        message_help='This is the bands with in Gaussian standard deviations. The default value is 70 km/s for emission line galaxies.'
        v_bands_str = st.text_input('Bands kinematic width (km/s)', value=70, help=message_help)

        # number of sigmas
        message_help='This is the number of Gaussian sigmas to compute the bands with.'
        n_sigma_str = st.text_input('Sigma number', value=4, key='n_sigma_str', help=message_help)

        # Instrument correction check
        message_help = 'Use an approximation for the observation resolving power to account for the instrument broadening'
        instr_corr_check = st.toggle("Instrumental correction", value=True, key='instr_corr_check', help=message_help)

    # Detect spectrum components correction check
    st.markdown("")
    st.markdown(f'##### Features detection')
    message_help = 'Limits the line bands to the regions where lines are detected via [ASPECT algorithm](https://pypi.org/project/aspect-stable/)'
    components_check = st.toggle("ML prediction", value=False, key='run_aspect_check', help=message_help)

    st.markdown("")
    submitted = st.form_submit_button("Generate bands")

    if submitted:

        # Delete previous bands df if present
        if s_state['bands_df'] is not None:
            save_state('bands_df', None)

        # Generate bands
        spec = s_state['spec']
        bands = spec.retrieve.line_bands(line_list=None if len(line_selection) == 0 else line_selection,
                                         particle_list=None if len(particle_selection) == 0 else particle_selection,
                                         vacuum_waves=vacuum_check,
                                         components_detection=components_check,
                                         adjust_central_bands=adjust_central_bands,
                                         band_vsigma=None if v_bands_str is None else float(v_bands_str),
                                         n_sigma=None if n_sigma_str is None else float(n_sigma_str),
                                         instrumental_correction=instr_corr_check,
                                         update_latex=False)
        save_state('bands_df', bands)

    return

def load_bands_tab():

    st.markdown(f'### Bands file address')

    # Get the file
    uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

    # Every form must have a submit button.
    submitted = st.form_submit_button("Upload bands")

    # Load the dataframe
    if submitted:
        save_state('bands_df', parse_line_bands_df(uploaded_file))

    return

def declare_spectrum_form():

    with st.form('load_spec_form', border=True, enter_to_submit=False, clear_on_submit=False):

        tab_load, tab_query, tab_collabs = st.tabs(["Load spectrum", "Query survey", "Collaborations data"])

        # Load spectrum
        with tab_load:
            load_spectrum_tab()

        # Query surveys
        with tab_query:
            st.write('Not implemented')

        # Check from collaborations
        with tab_collabs:
            st.write('Not implemented')



    return

def declare_bands_form():

    with st.form('load_bands_form', border=True, enter_to_submit=False, clear_on_submit=False):

        tab_infer, tab_upload = st.tabs(["Match to observation", "Load from file"])

        # Load spectrum
        with tab_infer:
            match_bands_tab()

        # Query surveys
        with tab_upload:
            load_bands_tab()

    return

def bands_review():

    # Put the bands as a dataframe
    bands = s_state.get('bands_df')
    if bands is not None:

        # Adjust
        st.markdown('')
        st.markdown(f'##### Manual adjustment:')
        st.markdown(f'The widgets below can be used to manually change the cell values or delete rows. Please try to fill'
                    f' all columns.')

        tab_all, tab_single = st.tabs(["All", "Individual"])
        with tab_single:
            help_message = 'Select one line to modify and visualize'
            input_line = st.selectbox('Line', bands.index, index=0, key=None, help=help_message)
            st.data_editor(bands.loc[input_line], num_rows="dynamic", on_change=widget_save_state, args=("bands_df",))
            bokeh_bands(s_state['spec'], input_line, bands)

        with tab_all:
            save_state('bands_df', st.data_editor(bands, num_rows="dynamic", on_change=widget_save_state, args=("bands_df",)))

            spec = s_state['spec']

            # Figure configuration
            bokeh_spectrum(spec, bands)

        st.markdown('')
        st.markdown('***')
        st.markdown(f'Download line bands selection to a text file.')
        string_DF = s_state.get('bands_df').to_string()
        table_name = s_state['id'] + '_bands.txt'
        st.download_button('Download', data=string_DF.encode('UTF-8'), file_name=table_name)


    return