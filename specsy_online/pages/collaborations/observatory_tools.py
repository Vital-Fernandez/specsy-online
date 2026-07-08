import lime
import requests
import streamlit as st
from streamlit import session_state as s_state, secrets

from numpy import floor, ceil, asarray, sort, squeeze, ones
from pandas import notnull
from pathlib import Path

from PIL import Image

from streamlit_gsheets import GSheetsConnection

from specsy_online.utils.interfaces import widget_text_to_list, unit_conversion_inputs
from specsy_online.utils.input_output import save_objSample, save_state, gdrive_service, download_from_path, \
                                             load_spectrum, spectrum_to_txt

from specsy_online.utils.plots import bokeh_spectrum
from specsy_online.utils.input_output import clear_obj_data
from specsy_online.pages.collaborations.lzlcs_miri import (product_interface, channel_interface,
                                                           band_interface,  aperture_interface)


SURVEY_LIST = ['CEERS', 'CAPERS', 'LzLCS_MIRI', 'PID17515']

SURVEY_PARAMS = lime.load_cfg(Path(__file__).parent/f'survey_cfg.toml')


def authenticated_survey(authenticator, survey, form_name, expected_user, selection_func):

    authenticator.login(location='main', fields={'Form name': form_name})

    if s_state.get('authentication_status'):
        if s_state.get('name') == expected_user:
            selection_func()
        else:
            st.write(f'Incorrect credentials for {survey} sample. Please logout or change survey selection.')
    elif s_state.get('authentication_status') is False:
        st.warning('Incorrect username or password')

    return


def set_survey_user(param, auth):

    # Clear the previous data
    clear_obj_data()

    # Holder for the survey
    s_state[f'{param}_hold'] = s_state[f'{param}']

    # Logout from collaboration
    if st.session_state['authentication_status']:
        auth.logout(location='unrendered')

    return


@st.cache_resource
def survey_params(name):
    return SURVEY_PARAMS[name]


@st.cache_data
def load_logo(fname):
    return Image.open(Path(__file__).parent.parent.parent / fname)


@st.cache_data
def read_collaboration_readme(survey):
    try:
        url = secrets.collaborations.credentials.usernames[survey]['readme']
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except KeyError:
        return 'Readme not available'


@st.cache_resource
def read_collaboration_file_log(collaboration_name, idx_list):
    conn = st.connection('gdrive', type=GSheetsConnection)
    sheet_name = st.secrets.collaborations.credentials.usernames[collaboration_name].get('file_sheet')
    df = conn.read(spreadsheet=sheet_name, ttl=None, header=0, sep=',')
    df = df.set_index(idx_list)

    return df


@st.cache_resource
def read_collaboration_flux_log(collaboration_name, index_list):
    conn = st.connection('gdrive', type=GSheetsConnection)
    sheet_name = st.secrets.collaborations.credentials.usernames[collaboration_name].get('flux_sheet')
    df = conn.read(spreadsheet=sheet_name, ttl=None, header=0, sep=',')
    df = df.set_index(index_list)

    return df


def survey_selection(survey):

    # Page data
    data_survey = survey_params(survey)

    # Author block
    survey_intro(survey, data_survey)

    # Connect to the online spreadsheets
    files_df = read_collaboration_file_log(survey, data_survey['file_sample_headers'])
    flux_df = read_collaboration_flux_log(survey, data_survey['flux_sample_headers'])

    tabSpecSelect, tabReadme = st.tabs(['Spectra selection', 'README'])

    with tabSpecSelect:

        # Widgets to select sub-sample properties
        idcs_selection, n_objs = widgets_selection(survey, data_survey, files_df, flux_df)

        # No objects in selection
        if n_objs == 0:
            st.warning(f'There are no spectra for the input selection criteria')

        else:

            # Select object from sub-sample
            df_selection = files_df.loc[idcs_selection]
            obj, idx_1D, file1d = object_selection(survey, data_survey, n_objs, df_selection, flux_df)

            # Form to dowload the spectrum with the sample/user properties
            fetch_observation(survey, data_survey, obj, df_selection, idx_1D, file1d, flux_df)

            #  Visualize the spectra
            st.markdown("***")

            # 1D spectrum display
            if s_state.get('spec') is not None:

                # Object information
                object_description(df_selection, idx_1D)

                st.write(f'#### 1D spectrum')
                plot_tab, objSheet_tab = st.tabs(['Plot', 'Data'])

                with plot_tab:
                    st.write(" ")
                    bokeh_spectrum('spec')

                with objSheet_tab:
                    st.write(" ")
                    st.dataframe(df_selection.loc[idx_1D].T)

                # Give the option to download the measurements
                st.write(f'##### ⬇ Downloads')
                col1, col2, _ = st.columns([0.20, 0.20, 0.6])

                with col1:
                    txt_data = spectrum_to_txt(s_state['spec'])
                    st.download_button(' Spectrum', data=txt_data, file_name=f'{Path(file1d).stem}_spectrum.txt',
                                       mime='text/plain', width='stretch')

                with col2:
                    if (s_state['spec'].frame.index.size > 0):
                        st.download_button('Line measurements', data=s_state['spec'].frame.to_string().encode('UTF-8'),
                                           file_name=f'{Path(file1d).stem}_line_measurements.txt', key='survey_line_downloads',
                                           width='stretch')

    with tabReadme:
        st.markdown(read_collaboration_readme(survey))


    return


def widgets_selection(survey, data_survey, file_df, flux_df):
    match survey:

        case 'capers':
            col1, col2 = st.columns(2, gap='large')

            # Sample selection
            with col1:
                sample_interface(file_df)

            # Redshift range selection
            with col2:
                redshift_interface(file_df, data_survey.get('redshift_label'))

        case 'ceers':

            col1, col2, col3 = st.columns(3, gap='large')

            with col1:
                sample_interface(file_df)

            with col2:
                disp_interface(file_df, data_survey.get('disp_list'))

            with col3:
                redshift_interface(file_df, data_survey.get('redshift_label'))

        case 'lzlcs_miri':

            col1, col2, col3, col4 = st.columns(4, gap='medium')

            with col1:
                product_interface(file_df)

            with col2:
                channel_interface(file_df)

            with col3:
                band_interface(file_df)

            with col4:
                aperture_interface(file_df)

    # Line selection
    if flux_df is not None:
        line_selection_interface(flux_df)

    # Object selection
    object_selection_interface(survey, file_df)

    return indexing_sheets(survey, file_df, flux_df, data_survey)


def indexing_sheets(survey, files_df, flux_df, data_survey):

    mask = ones(len(files_df.index), dtype=bool)

    if survey != 'lzlcs_miri':

        # Sample indexing
        sample_list = s_state.get('sample_list')
        if sample_list is not None:
            mask &= files_df.index.get_level_values('sample').isin(sample_list)

        # Redshift range indexing (NaN passthrough)
        z_range = s_state.get('z_range')
        if z_range is not None:
            mask &= files_df[data_survey['redshift_label']].between(z_range[0], z_range[1]) | files_df[data_survey['redshift_label']].isna()

        # Disperser selection: CEERS has one-hot boolean columns, CAPERS a single string column
        disp_list = s_state.get('disp_list')
        if disp_list:
            if survey == 'ceers':
                mask &= files_df[disp_list].any(axis=1)
            else:
                mask &= files_df['disp'].isin(disp_list)

        # Line selection (object level: keep all files of objects with the lines)
        line_selection = s_state.get('line_selection')
        if line_selection is not None and len(line_selection) > 0:

            idcs_lines = flux_df.index.get_level_values('line').isin(line_selection)

            match survey:
                case 'ceers':
                    objs_wlines = flux_df.loc[idcs_lines].index.get_level_values('id').unique()
                    mask &= files_df.index.get_level_values('id').isin(objs_wlines)
                case 'capers':
                    objs_wlines = flux_df.loc[idcs_lines].index.get_level_values('id').unique()
                    mask &= files_df.MPT_number.isin(objs_wlines)

        # Name selection
        mpt_list = s_state.get('mpt_list')
        if mpt_list is not None and mpt_list != "":
            mpt_array = asarray(widget_text_to_list(mpt_list), dtype=files_df['MPT_number'].dtype)
            idcs_name = files_df['MPT_number'].isin(mpt_array)
            mpt_found = files_df.loc[idcs_name, 'MPT_number'].unique()
            if mpt_found.size > 0:
                label = 'object' if mpt_found.size == 1 else 'objects'
                st.success(f'The {label} {mpt_found.astype(int)} found on the dataset')
            else:
                st.warning('None of the requested objects were found on the dataset')
            mask &= idcs_name

    else:

        # Object and product selection
        mask &= files_df.index.get_level_values('id').isin(s_state['id_list'])
        mask &= files_df.index.get_level_values('product').isin(s_state['product_list'])

        # Levels that do not apply to every product (NaN passthrough)
        for level in ('channel', 'band', 'aperture'):
            values = files_df.index.get_level_values(level)
            mask &= values.isin(s_state[f'{level}_list']) | values.isna()

        # Line selection (file level: keep only the spectra containing the lines)
        line_selection = s_state.get('line_selection')
        if line_selection is not None and len(line_selection) > 0:
            idcs_lines = flux_df.index.get_level_values('line').isin(line_selection)
            files_wlines = flux_df.loc[idcs_lines].index.get_level_values('file').unique()
            mask &= files_df['path'].isin(files_wlines)

    return mask, mask.sum()


def sample_interface(file_df):

    default_samples = file_df.index.get_level_values('sample').unique().to_list()
    st.multiselect('**Sample selection:**', key='sample_list',
                   options=list(default_samples), default=list(default_samples),
                   on_change=save_objSample, args=("sample_list",))

    return


def disp_interface(file_df, default_disp):

    # default_disp = list(file_df['disp'].unique())
    help = 'The "comb_Mgrat" option contains the combined G235M and G395 joined observations of the target'
    st.multiselect('**Dispenser selection:**', key='disp_list', options=default_disp, default=default_disp,
                   on_change=save_objSample, args=("disp_list",), help=help)

    return


def redshift_interface(file_df, redshift_label):

    label_text = '**Redshift range:**'
    help_text = 'The observations list will be limited to the input "z_UNICORN" range'
    z_limits = floor(file_df[redshift_label].min()), ceil(file_df[redshift_label].max())

    # Initial values for the range for first time
    if s_state.get('z_range') is None:
        save_state('z_range', z_limits)

    st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
              key='z_range', help=help_text, on_change=save_objSample, args=("z_range",))

    return


def line_selection_interface(flux_df):

    line_list = sorted(flux_df.index.get_level_values('line').unique().tolist())
    if line_list is not None:
        help_text = 'The object selection will be limited to objects with the input lines'
        st.multiselect('**Observed lines:**', options=line_list, key='line_selection',
                       on_change=save_objSample, args=("line_selection",), help=help_text)

    return


def object_selection_interface(survey, file_df):

    # Object selection
    help_text = 'The observations list will be limited to the input IDs'

    if survey != 'lzlcs_miri':
        label_text = '**MSA IDs (comma separated)**'
        place_holder_text = '3,1027,80026'
        st.text_area(label=label_text, value=None, key='mpt_list', help=help_text, placeholder=place_holder_text,
                     on_change=save_objSample, args=("mpt_list",),)

    else:
        label_text = '**Object selection:**'
        options = sorted(file_df.index.get_level_values('id').dropna().unique()) # TODO we should use the same key
        st.multiselect(label_text, key='id_list', options=options, default=options,
                       on_change=save_objSample, args=("id_list",), help=help_text)

    return


def survey_intro(name, data_survey):

    # Title
    st.header(f'{name.upper()} survey:', divider='gray')

    # Author block
    if 'logo_path' in data_survey:
        col_logo, col_author = st.columns([0.15, 0.85], gap='small')
        with col_logo:
            st.image(load_logo(data_survey['logo_path']), width=300)
        with col_author:
            st.space("large")
            st.markdown(data_survey['intro'], text_alignment='justify')
    else:
        st.markdown(data_survey['intro'], text_alignment='justify')

    st.space('small')

    return


def read_flux_measurements(survey, obj_series, obj_file, flux_sample, levels):

    match survey:
        case 'ceers':
            idx_flux = (obj_series.index[0][0], str(obj_series.index[0][1]), Path(obj_file).name)
        case 'capers':
            idx_flux = (obj_series.index[0][0], obj_series.MPT_number.values[0], Path(obj_file).name)
        case 'lzlcs_miri':
            idx_flux = (obj_series.index[0][0], obj_file)
        case _:
            st.error('Survey flux measurement log is not recognized')

    try:
        flux_df = flux_sample.xs(idx_flux, level=levels[:-1], drop_level=True)
        flux_df.index.name = None
        if flux_df.index.size == 0:
            flux_df = None
    except KeyError:
        flux_df = None

    return flux_df


def object_description(input_df, idx_obj):

    if 'MPT_number' in input_df.columns:

        msg = (f'**<span style="color:#AAD372;font-weight:bold;">MSA number</span>** '
               f'{int(input_df.loc[idx_obj].MPT_number.values[0])}')
        st.write(msg, unsafe_allow_html=True)

        col1, col2, col3 = st.columns(3)

        with col1:
            format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Identification</span>**'
            st.write(format_hdr, unsafe_allow_html=True)
            msg = f'\n\n**Pointing:** {input_df.loc[idx_obj].index.names[2]}'
            # msg += f'\n\n**Optimal extraction:** {input_df.loc[idx_obj, "optext"].values[0]}'
            msg += f'\n\n**Sample:** {input_df.loc[idx_obj].index.values[0][0]}'
            st.markdown(msg)

        with col2:
            format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Photometry</span>**'
            st.write(format_hdr, unsafe_allow_html=True)
            # 'flux_F277W', 'flux_F356W', 'flux_F444W'
            tupple_index = tuple(idx_obj)[0]
            # msg = f'**F277W:** {pd_get(input_df, tupple_index, "flux_f277w", default="Not available")}'
            # msg += f'\n\n**F356W:** {pd_get(input_df, tupple_index, "flux_f356w", default="Not available")}'
            # msg += f'\n\n**F444W:** {pd_get(input_df, tupple_index, "flux_f444w", default="Not available")}'
            # msg += f'\n\n**F606W:** {pd_get(input_df, tupple_index, "flux_f606w", default="Not available")}'
            # msg += f'\n\n**F814W:** {pd_get(input_df, tupple_index, "flux_f814w", default="Not available")}'
            # st.markdown(msg)

        with col3:
            format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Redshift</span>**'
            st.write(format_hdr, unsafe_allow_html=True)
            # msg = f'\n\n**z_UNICORN:** {input_df.loc[idx_obj].z_UNICORN.values[0]}'
            msg = f'\n\n**z_Aspect:** {input_df.loc[idx_obj].z_aspect_key.values[0]}'
            msg += f'\n\n**z_LiMe:** {input_df.loc[idx_obj].z_manual.values[0]:0.3f}'
            st.markdown(msg)

    return


def extract_n_measurements_file(survey, file1d_list, flux_df):

    files = flux_df.index.get_level_values('file')

    match survey:
        case 'capers' | 'ceers':
            file_names = [Path(f).name for f in file1d_list]
            counts = files[files.isin(file_names)].value_counts()

            def labeller(fpath):
                fname = Path(fpath).name
                n = counts.get(fname, 0)
                return f'{fname} (✅  {n} line{"s" if n > 1 else ""})' if n > 0 else fname

        case 'lzlcs_miri':
            file_names = file1d_list
            counts = files[files.isin(file_names)].value_counts()

            def labeller(fpath):
                fname = fpath
                n = counts.get(fname, 0)
                return f'{fname} (✅  {n} line{"s" if n > 1 else ""})' if n > 0 else fname

    return labeller


def object_selection(survey, data_survey, n_objs, df_selection, flux_df):

    st.caption("")

    st.caption("Use the tools in the upper-right corner to expand the table, hide columns, or download it.")
    st.dataframe(df_selection, column_order=data_survey['column_order'])

    # Download spectra
    st.space(size="small")
    st.subheader("Object selection", divider='gray')

    # Cropped df
    msg = (f'The current selection has <span style="color:#E1AD01;font-weight:bold;">{n_objs} observations</span> '
           f' use the menus below to load the spectra from an individual source.')
    st.write(msg, unsafe_allow_html=True)

    # Object selection
    id_idx = df_selection.index.get_level_values('id')
    help_msg = 'Select the object'
    obj = st.selectbox('Object ID', options=sort(id_idx.unique()), help=help_msg)
    idcs_obj = id_idx == str(obj)

    # 1D selection
    file1d_list = squeeze(df_selection.loc[idcs_obj, data_survey['fits_extension']].to_numpy())
    file1d_list = file1d_list[notnull(file1d_list)]

    # Check how many of the files have measurements before letting the user select one
    format_function = None if flux_df is None else extract_n_measurements_file(survey, file1d_list, flux_df)
    file1d = st.selectbox(f'1D spectrum file ({len(file1d_list)} file{"s" if len(file1d_list) > 1 else ""})',
                          options=file1d_list, help='Select the 1D spectrum to download', format_func=format_function)

    match survey:
        case 'ceers':
            disp = 'prism' if 'prism' in file1d else 'comb-mgrat'
            ext1D = Path(file1d).stem.split('_')[-1]
            idx_1D = idcs_obj & (df_selection[f'{disp}_{ext1D}'] == file1d)

        case 'capers':
            ext1D = 'optext' if 'optext' in file1d else 'x1d'
            idx_1D = idcs_obj & (df_selection[ext1D] == file1d)

        case 'lzlcs_miri':
            idx_1D = idcs_obj

    return obj, idx_1D, file1d


def fetch_observation(survey, data_survey, obj, df_selection, idx_1D, file1d, flux_df):

    # Survey dependent parameters
    match survey:

        case 'ceers' | 'capers':
            full_path1d = f"{data_survey['root_folder']}/{df_selection.loc[idx_1D, data_survey['file_header']].values[0]}/{file1d}"
            instrument = 'nirspec'

        case 'lzlcs_miri':
            full_path1d = f"{data_survey['root_folder']}/{file1d}"
            if 'x1d_custom' in full_path1d:
                instrument = 'lzlcs_miri_merged'
            else:
                instrument = 'lzlcs_miri_x1d'

    with st.form('load_capers', border=False, enter_to_submit=False, clear_on_submit=False):

        col_A, col_B, _, _ = st.columns([0.25, 0.25, 0.25, 0.25], gap='large')
        wave_units_str, flux_units_str = unit_conversion_inputs(col_A, col_B,
                                                                label_wave='Wavelength units out',
                                                                label_flux='Flux units out',
                                                                default_wave_units='Angstrom',
                                                                default_flux_units='FLAM')

        # Run the query
        st.write('')
        help_msg = f'Press to download the spectra from {survey.upper()} google drive.'
        submitted = st.form_submit_button("Fetch observation", help=help_msg)

        if submitted:

            # Clear the previous data
            clear_obj_data()

            # Connect to drive
            service = gdrive_service(s_state["username"])

            # Download the 1D spectrum
            with st.spinner(f'1D spectrum file query'): # TODO clean this one
                file1d_bytes = download_from_path(service, survey, full_path1d)

            if file1d_bytes is not None:
                st.info('1D spectrum located')

                # Recover redshift from type priority
                row = df_selection.loc[idx_1D]
                z_obj = row[data_survey['redshift_label']].values[0]

                # Get spectrum
                spec = load_spectrum(file1d_bytes, instrument, z_obj, norm_flux=None, id_label=f'{obj}',
                                     wave_units_out=wave_units_str, flux_units_out=flux_units_str)
                obj_flux = read_flux_measurements(survey, row, file1d, flux_df, levels=data_survey['flux_sample_headers'])

                # Get line measurements
                if obj_flux is not None:
                    spec.load_frame(obj_flux)
                    save_state('lines_df', obj_flux)
                    save_state('bands_df', lime.bands_from_measurements(obj_flux))
                    st.info('Line measurements located')

                # Save the data
                save_state('spec', spec)
                save_state('id', Path(file1d).stem)

            else:
                st.warning('1D spectrum was not located')

    return


