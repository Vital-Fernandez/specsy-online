import streamlit as st
import streamlit_authenticator as stauth
from streamlit import session_state as s_state,secrets
from streamlit_gsheets import GSheetsConnection
from numpy import floor, ceil, intersect1d, sum
from utils.input_output import (save_state, load_spectrum, parse_line_bands_df, widget_save_state, get_text_spectrum,
                           convert_for_download, widget_text_to_list)
from numpy import unique, sort
from .plots import bokeh_spectrum
from lime.transitions import au

INSTRUMENT_LIST = ['SDSS', 'OSIRIS', 'ISIS', 'NIRSPEC', 'TEXT']


def unit_conversion_inputs(default_wave_units=None, default_flux_units=None):

    col_units_wave, col_units_flux = st.columns([0.5, 0.5], gap='large')
    message_help = 'These are the default units. Please check astropy for the string unit declaration at this link.'

    # Read the units
    with col_units_wave:
        wave_units_str = st.text_input('Wavelength units', value=default_wave_units, placeholder='Angstrom', help=message_help)

    with col_units_flux:
        flux_units_str = st.text_input('Flux units', value=default_flux_units, placeholder='FLAM', help=message_help)

    # Review for empty cases
    wave_units_str = None if (wave_units_str is None) or (wave_units_str == "") else wave_units_str
    flux_units_str = None if (flux_units_str is None) or (flux_units_str == "") else flux_units_str

    # Confirm the units are astropy valid
    if wave_units_str is not None:
        try:
            au.Unit(wave_units_str)
        except:
            st.warning(f'Input wavelength units "{wave_units_str}" are not recognized please use astropy notation')
            wave_units_str = None

    if flux_units_str is not None:
        try:
            au.Unit(flux_units_str)
        except:
            st.warning(f'Input wavelength units "{flux_units_str}" are not recognized please use astropy notation')
            flux_units_str = None

    return wave_units_str, flux_units_str

def load_collaboration():

    # Title
    msg = f'## {s_state["username"].upper()} survey'
    st.write(msg)

    # Author block
    msg = (f'These observations belong to the CANDELS-Area Prism Epoch of Reionization Survey. Mark Dickinson at NOIRLab (AZ)'
           f' is the P.I. of this proposal with reference JWST-GO-6368. Please contact the P.I. before using this dataset.\n\n'
           f'This spreadsheet indexes the object characteristics and the observational files properties. Please check the '
           f'CAPERS README file for the columns parameters.\n\n'
           f'Use the widgets below to constrain the files selection.')
    st.write(msg)

    conn = st.connection("capers", type=GSheetsConnection)
    index_list = ['sample', 'id', 'file']
    df = conn.read(ttl=None, index_col=index_list, header=0)
    df.index.names = index_list

    # Sample indexing
    default_samples = df.index.get_level_values('sample').unique().to_numpy()
    sample_selection = st.multiselect('Sample selection:', default=default_samples, options=list(default_samples), key='sample_list')
                       #on_change=save_objSample, args=("sample_list",))
    idcs = df.index.get_level_values('sample').isin(sample_selection)

    # Redshift indexing
    label_text = 'Redshift range selection:'
    help_text = 'The observations list will be limited to the input redshift range'
    z_limits = floor(df.z_UNICORN.min()), ceil(df.z_UNICORN.max())
    z_range = st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
              key='z_range', value=z_limits, help=help_text)
    st.write(z_range)

    idcs = idcs & (df['z_UNICORN'] >= z_range[0]) & (df['z_UNICORN'] <= z_range[1])


    # Object indexing
    label_text = 'Comma-separated MSA IDs'
    help_text = 'The observations list will be limited to the input IDs'
    place_holder_text = '3,1027,80026'
    mpt_list = st.text_area(label=label_text, value=None, key='MPTUSERLIT', help=help_text, placeholder=place_holder_text)
                 #on_change=save_objSample, args=("MPTUSERLIT",),)

    mpt_array = widget_text_to_list(mpt_list)
    if mpt_array is not None:
        idcs_selection = df['MPT_number'].isin(mpt_array)
        mpt_found = df.loc[idcs_selection, 'MPT_number'].unique()
        mpt_common = intersect1d(mpt_found, mpt_array)
        if sum(mpt_common) > 0:
            st.info(f'Objects {", ".join(list(mpt_common.astype(str)))} were found the sample selection')
            idcs = idcs & idcs_selection
        else:
            st.warning('None of the objects in the input MPT list was found')



    msg = f'{idcs.sum()} files in selection'
    st.write(msg)
    st.dataframe(df.loc[idcs])

    # service = gdrive_service(s_state["username"])
    # list_file = service.files().list(fields="files(id,name,webViewLink)").execute()
    # st.write(list_file)

    # fname = 'examples/example_doc'
    # st.write(fname)
    # parent_id = resolve_drive_path(service, fname.split('/'))
    # st.write(parent_id)

    # list_root_contents(service)

    # full_path = "CAPERS/CAPERS_EGS_V0.2/CAPERS_EGS_P1/CAPERS_EGS_P1_s000240728_x1d_optext.fits"
    # folder_parts = full_path.split('/')
    #
    # folder_id = resolve_drive_path(service, folder_parts[:-1], starting_parent_id=secrets.connections.capers.root_id)
    #
    # if folder_id:
    #     file = find_file_in_folder(service, folder_parts[-1], folder_id)
    #     if file:
    #         st.write(f"✅ File found: {file['name']} (ID: {file['id']})")
    #         st.write(f"🔗 {file['webViewLink']}")
    #         file_bytes = download_binary_file(service, file['id'])
    #
    #         spec = lime.Spectrum.from_file(file_bytes, instrument='nirspec')
    #         bokeh_spectrum(spec)
    #
    #     else:
    #         st.write("❌ File not found in the target folder.")
    # else:
    #     st.write("❌ Could not resolve the folder path.")

    return

def load_spectrum_tab():

    with st.form('load_spec_form', border=True, enter_to_submit=False, clear_on_submit=False):

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
            save_state('obs_type',None)

            if uploaded_file:
                id = uploaded_file.name
                spec = load_spectrum(uploaded_file, instrument, z_string, norm_flux_string, wave_units_str, flux_units_str,
                                                        uploaded_file.name)
                if ml_components:
                    spec.infer.components()

                save_state('id', id)
                save_state('spec', spec)
                save_state('obs_type', 'upload')


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
                                         adjust_central_band=adjust_central_bands,
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

    tab_load, tab_collabs, tab_query = st.tabs(["Load spectrum", "Collaborations", "Query survey"])

    # Load spectrum
    with tab_load:
        load_spectrum_tab()

    # Check from collaborations
    with tab_collabs:

        # Authenticate the user
        authenticator = stauth.Authenticate(secrets.collaborations.credentials.to_dict(), cookie_name=secrets.cookie.name,
                                            cookie_key=secrets.cookie.key, cookie_expiry_days=secrets.cookie.expiry_days)
        authenticator.login(location='main')

        if s_state.get('authentication_status'):
            st.write(s_state["username"])

            # Give the option to logout
            authenticator.logout(button_name='Collaboration logout')

    # Query surveys
    with tab_query:
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
        st.markdown(f'The widgets below can be used to manually change the cell values or delete rows.')

        tab_all, tab_single = st.tabs(["All", "Individual"])
        with tab_all:
            save_state('bands_df', st.data_editor(bands, num_rows="dynamic", on_change=widget_save_state, args=("bands_df",)))
            bokeh_spectrum(s_state['spec'], bands)

        with tab_single:
            # if bands.index.size > 0:
            #     help_message = 'Select one line to modify and visualize'
            #     input_line = st.selectbox('Line', bands.index, index=0, key=None, help=help_message)
            #     st.data_editor(bands.loc[input_line], num_rows="dynamic", on_change=widget_save_state, args=("bands_df",))
            #     bokeh_bands(s_state['spec'], input_line, bands)
            # else:
            #     st.write('No lines in input bands')
            st.markdown('Not implemented')

        st.markdown('')
        st.markdown('***')
        st.markdown(f'Save bands selection to a text file.')
        string_DF = s_state.get('bands_df').to_string()
        table_name = s_state['id'] + '_bands.txt'
        st.download_button('Download', data=string_DF.encode('UTF-8'), file_name=table_name)


    return

def display_menu():

    # Check file has been uploaded
    if s_state['spec'] is not None:

        if s_state['obs_type'] == 'upload':
            # Show the spectrum
            st.markdown("***")
            st.markdown(f'## Input observation')

            # Plot spectrum
            bokeh_spectrum(s_state['spec'])

            # Download
            rec_arr = get_text_spectrum('spec')
            csv = convert_for_download(rec_arr)
            st.markdown(f'Click the button below to download the spectrum as a text file.')
            st.download_button(label="Download", data=csv, file_name="spectrum.csv", mime="text/csv",
                               icon=":material/download:")

        elif s_state['obs_type'] == 'collaboration':
            if s_state["username"] == 'capers':
                st.write(f'Capers visualization is not implemented')

        elif s_state['obs_type'] == 'query':
            st.write(f'Query visualization is not implemented')

        else:
            return

    return