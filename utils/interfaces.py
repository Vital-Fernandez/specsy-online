import streamlit as st
from streamlit import session_state as s_state,secrets
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
from numpy import argsort, abs, array
from pyneb import RedCorr

from lime.transitions import au, Line
from specsy import extinction_coeff_calc
from numpy import floor, ceil, intersect1d, sum, unique, sort, searchsorted

from utils.input_output import (save_state, load_spectrum, parse_line_bands_df, get_text_spectrum, convert_for_download,
                                widget_text_to_list, save_edited_bands, clear_obj_data, widget_save_state, parse_fit_cfg)
from utils.tools import dynamic_input_data_editor
from utils.plots import bokeh_spectrum, bokeh_bands, bokeh_extinction, matplotlib_bands


FIT_CFG_PLACEHOLDER = ('[default_line_fitting]\n'
                       'H1_6563A_b="H1_6563A+N2_6583A+N2_6548A"\n'
                       'N2_6548A_amp="expr:N2_6584A_amp/2.94"\n'
                       'N2_6548A_kinem="N2_6584A"')

FIT_CFG_HELP = 'Please check LiMe documentation to read more on how to adjusts your fittings'


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

    return


def extinction_form(df_key):

    # Get the parameters for the calculation
    lines_df = s_state[df_key]
    lines_H1 = lines_df.loc[lines_df.particle == 'H1'].index.to_numpy()
    idx_column = lines_df.columns.get_loc('profile_flux') if 'profile_flux' in lines_df.columns else 0
    with ((st.form('extinction_form', border=True, enter_to_submit=False, clear_on_submit=False))):

        # Lines parameters
        st.write('Inputs/outputs:')
        colX, colY, colZ = st.columns([0.3, 0.3, 0.3])
        with colX:
            flux_column = st.selectbox('Flux column', lines_df.columns, index=idx_column)

        with colY:
            st.write("")
            st.write("")
            message = 'Recalculate the extinction coefficient to use the Balmer β wavelength as the relative value'
            Hbeta_conv_check = st.toggle(r'Convert to c(Hβ)', value='True', help=message)

        with colZ:
            st.write("")
            st.write("")
            message = 'Negative and NaN fluxes/uncertainties will be excluded from the calculation'
            non_phys_check = st.toggle(r'Exclude non-physical', value='True', help=message)

        # Lines parameters
        st.write("")
        st.write('Lines selection:')

        colA, colB, colC = st.columns([0.3, 0.3, 0.3])
        with colA:
            idx_default_norm = int(argsort(-lines_df.loc[lines_H1, lines_df.columns[idx_column]].to_numpy())[1])
            norm_line = st.selectbox('Normalization line', lines_H1, index=idx_default_norm)

        with colB:
            input_list = st.multiselect('Input lines', options=lines_H1, default=None, placeholder='All')
            input_list = None if len(input_list) == 0 else input_list

        with colC:
            exclude_list = st.multiselect('Exclude lines', options=lines_H1, default=None, placeholder='None')
            exclude_list = None if len(exclude_list) == 0 else exclude_list

        # Lines parameters
        st.write("")
        st.write('Physical model:')

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            reddening_laws = ["CCM89", "CCM89 Bal07", "CCM89 oD94", "S79 H83 CCM89","K76","SM79 Gal", "G03 LMC",
                              "MCC99 FM90 LMC", "F99-like", "F99","F88 F99 LMC"]
            law = st.selectbox("Reddening Law", reddening_laws)

        with col2:
            R_V = st.number_input("Rᵥ", min_value=0.0, value=3.1, step=0.1)

        with col3:
            tem = st.number_input("Temperature (K)", min_value=500, value=10000, step=1000)

        with col4:
            den = st.number_input("Density (1/cm³)", min_value=1.0, value=100.0, step=100.0)

        st.write("")
        submitted = st.form_submit_button("Compute extinction")

        if submitted:

            st.write('***')
            st.write('## Results')
            st.write("")
            cHbeta, cHbeta_err, log_extinc = extinction_coeff_calc(lines_df, norm_line, R_V, law, tem, den, rel_Hbeta=Hbeta_conv_check,
                                                       flux_column=flux_column, line_list=input_list, exclude_list=exclude_list)

            red_cor = RedCorr(R_V=R_V, law=law, cHbeta=cHbeta)

            out1, out2, out3 = st.columns([0.27, 0.32, 0.25])
            with out1:
                if Hbeta_conv_check:
                    coeff_label = r'c(H\beta)'
                else:
                    coeff_label = Line(norm_line).latex_label[0]
                    coeff_label = f'c({coeff_label.replace("$", "")})'
                st.markdown(rf"${coeff_label} = {cHbeta:.3f}\pm{cHbeta_err:.3f}$")

            with out2:
                E_BV_err = cHbeta_err * 2.5 / red_cor.X(4861.25)
                st.markdown(rf"$E(V - B) = {red_cor.E_BV:.3f}\pm{E_BV_err:.3f}$")

            with out3:
                A_V_err = E_BV_err * R_V
                st.markdown(rf"$A_{{V}} = {red_cor.AV:.3f}\pm{A_V_err:.3f}$")

            # Extinction plot
            bokeh_extinction(cHbeta, cHbeta_err, log_extinc, rel_Hbeta=Hbeta_conv_check)


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
            clear_obj_data()

            if uploaded_file:
                spec = load_spectrum(uploaded_file, instrument, z_string, norm_flux_string, wave_units_str, flux_units_str,
                                                        uploaded_file.name)
                if ml_components:
                    spec.infer.components()

                save_state('id', uploaded_file.name)
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

        st.markdown("")
        st.markdown(f'##### Transitions selection')
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

        st.markdown("")
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


def load_frame_tab(frame_key):

    st.markdown(f'### Frame file address')

    try:

        # Get the file
        uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

        # Every form must have a submit button.
        submitted = st.form_submit_button("Upload frame")

        # Load the dataframe
        if submitted:
            save_state(frame_key, parse_line_bands_df(uploaded_file))

    except Exception as e:
        st.error(f"An error occurred: {e}")

    return


def declare_line_measuring():

    # Tabs for fitting lines and for loading measurements
    tab_fit, tab_upload = st.tabs(['Measure lines', 'Upload measurements'])

    with tab_fit:

        st.markdown(f'### Write the fitting configuration:')
        st.text_area('Please follow .toml style', key='fit_cfg', height=300, placeholder=FIT_CFG_PLACEHOLDER,
                     on_change=widget_save_state, help=FIT_CFG_HELP, args=("fit_cfg",))

        if s_state['spec'] is not None:

            # Show upload button if inputs are declared
            if (s_state['bands_df'] is not None) and (s_state['fit_cfg'] is not None):

                # Every form must have a submit button.
                submitted = st.button("Fit lines", key='button_bands')

                if submitted:

                    spec, bands = s_state['spec'], s_state['bands_df']
                    conf = parse_fit_cfg(s_state['fit_cfg'])

                    # Clear previous measurements
                    spec.frame = spec.frame.iloc[0:0]

                    # Measuring the lines
                    try:
                        my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                        spec.fit.frame(bands, fit_cfg=conf)
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
        with st.form('load_lines_form', border=False, enter_to_submit=False, clear_on_submit=False):
            load_frame_tab('lines_df')

            if s_state.lines_df is not None:
                st.success('Successful upload')
                st.dataframe(s_state.lines_df)

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


def handle_change():
    # Read the updated table from session_state
    st.session_state.bands_df = st.session_state["bands_df"]

    return


def band_slider(column, label, idcs, idx_central, wave_array, min_val, max_val, disabled=False):

    """
    Displays a Streamlit slider in a given column to adjust a wavelength band.

    Parameters:
    - column: st.column object
    - label: slider label
    - idcs: 2-element np.array of indices relative to wave_array
    - idx_central: central wavelength index
    - wave_array: numpy array of wavelength values
    - min_val, max_val: slider bounds
    - disabled: bool to disable the slider

    Returns:
    - 2-element array of updated wavelength values
    """

    with column:
        slider_val = st.slider(label=label, value=tuple(idcs - idx_central), min_value=min_val, max_value=max_val,
                               step=1, disabled=disabled)

        # Minimum number of pixels
        return slider_val[0] + idx_central, slider_val[1] + idx_central
        # return wave_array[slider_val[0] + idx_central], wave_array[slider_val[1] + idx_central]

def start_bounds(spec, output_bands,):
    s_state.idx_label = output_bands.index[output_bands["label"] == s_state.line_selected][0]
    s_state.idx_central = searchsorted(spec.wave_rest.data, output_bands.loc[s_state.idx_label, 'wavelength'])
    idcs_in = searchsorted(spec.wave_rest, output_bands.loc[s_state.idx_label, 'w1':'w6'].to_numpy()) - s_state.idx_central
    s_state.lower = tuple(idcs_in[0:2])
    s_state.central = tuple(idcs_in[2:4])
    s_state.upper = tuple(idcs_in[4:6])
    review_bounds()

    return

def review_bounds():

    idx2, idx3 = st.session_state.central

    # Update lower limit
    idx0, idx1 = st.session_state.lower
    if idx1 > idx2:
        idx1 = idx2 - 2
        if idx0 > idx1:
            idx0 = idx1 - 2
        st.session_state.lower = (idx0, idx1)

    # Update upper
    idx4, idx5 = st.session_state.upper
    if idx3 > idx4:
        idx4 = idx3 + 2
        if idx4 > idx5:
            idx5 = idx4 + 2
        st.session_state.upper = (idx4, idx5)

    return

def bands_review():


    spec = st.session_state.spec

    # Select the generate the bands to edit
    if st.session_state['in_bands'] is None:
        if st.session_state['bands_df'] is not None:
            in_bands = st.session_state.bands_df.copy()
        else:
            in_bands = spec.retrieve.line_bands(particle_list=['O3', 'O2'])

        # Reset the index to avoid conflict issues and store in session state
        in_bands.index.name = "label"
        st.session_state.in_bands = in_bands.reset_index()

    # Tabs showing the full spectrum
    tabs_all, tab_single = st.tabs(['Full spectrum', 'Individual bands'])
    with tabs_all:

        # Editable bands widget
        output_bands = dynamic_input_data_editor(st.session_state.in_bands, key="my_editor")

        # Display the bands
        bokeh_spectrum('spec', output_bands)

    with tab_single:

        colLabel, colWidth, colCont = st.columns(3, gap="large", vertical_alignment="center")
        with colLabel:
            if 'line_selected' not in s_state:
                s_state['line_selected'] = output_bands.label.to_numpy()[0]
                start_bounds(spec, output_bands)

            label_selected = st.selectbox('Line', output_bands.label.to_numpy(), index=0, key='line_selected',
                                          on_change=start_bounds, args=(spec, output_bands, ))

        with colWidth:
            message_help = 'The maximum number of band pixels. Increase this number to extend the range of the bands'
            n_pixels = st.number_input('Band max pixels number', min_value=5, max_value=150, value=30, step=1,
                                       help=message_help)

        with colCont:
            st.write("")
            st.write("")
            message_help = 'The manual selection excludes the line bands'
            exclude_cont_check = st.toggle("Exclude continua", value=True, key='toggle_exclude_continua', help=message_help)

        # Display sliders
        colBlue, colCentral, colRed = st.columns(3, gap="large", vertical_alignment="center")
        with colCentral:
            st.slider("Central band idcs", -n_pixels, n_pixels, key="central", on_change=review_bounds)

        with colBlue:
            st.slider("Lower band idcs", -n_pixels, 0, key="lower", on_change=review_bounds, disabled=exclude_cont_check)

        with colRed:
            st.slider("Upper band idcs", 0, n_pixels, key="upper", on_change=review_bounds, disabled=exclude_cont_check)

        # Save the bands
        idcs_array = array([s_state.lower[0], s_state.lower[1],
                           s_state.central[0], s_state.central[1],
                           s_state.upper[0], s_state.upper[1]]) + s_state.idx_central
        bands_arr = spec.wave_rest.data[idcs_array.astype(int)]

        # bokeh_bands('spec', label_selected, bands=bands_arr, exclude_continua=exclude_cont_check)
        matplotlib_bands('spec', label_selected, bands=bands_arr, exclude_continua=exclude_cont_check)
        output_bands.loc[s_state.idx_label, 'w1':'w6'] = bands_arr

    # Save modifications
    save_edited_bands(output_bands, 'bands_df')

    return


def display_menu():

    # Check file has been uploaded
    if s_state['spec'] is not None:

        if s_state['obs_type'] == 'upload':

            # Show the spectrum
            st.markdown("***")
            st.markdown(f'## Input observation')

            # Plot spectrum
            bokeh_spectrum('spec')

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