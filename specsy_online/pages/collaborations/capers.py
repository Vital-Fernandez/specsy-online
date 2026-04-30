import streamlit as st
from streamlit import session_state as s_state, secrets
from numpy import floor, ceil, intersect1d, sum, sort, squeeze
from pandas import notnull
from pathlib import Path

import lime

from specsy_online.utils.interfaces import widget_text_to_list, unit_conversion_inputs
from specsy_online.utils.input_output import save_objSample, save_state, gdrive_service, download_from_path, \
    load_spectrum
from specsy_online.utils.input_output import read_collaboration_file_log, read_collaboration_flux_log, clear_obj_data,LOCAL_FOLDER
from specsy_online.utils.plots import bokeh_spectrum

from PIL import Image


@st.cache_data
def load_logo(fname):
    return Image.open(fname)


def survey_params(name):

    # Container
    data_dict = {}

    # Survey wording
    match name:
        case 'ceers':
            data_dict['intro'] = (f'These observations belong to the **CEERS (The Cosmic Evolution Early Release Science Survey**. '
                    f'Steven Finkelstein at University of Texas at Austin is the P.I. of this proposal (NOI #135). \n\n'
                    f'This widgets below can be used to constrain the sample. Please visit '
                    f'[https://ceers.github.io/](https://ceers.github.io/) for more information on the project.')

            data_dict['redshift_label'] = 'z_best'

            data_dict['disp_list'] = ['prism', 'comb-mgrat']

            data_dict['fits_extension'] = ['prism_x1d', 'prism_x1d-masked', 'prism_x1d-optext', 'prism_x1d-optext-masked',
                                           'comb-mgrat_x1d', 'comb-mgrat_x1d-masked', 'comb-mgrat_x1d-optext', 'comb-mgrat_x1d-optext-masked']

            data_dict['logo_path'] = LOCAL_FOLDER.parent / 'resources/images/CEERS_white.png'

        case 'capers':
            data_dict['intro'] = (f'These observations belong to the CANDELS-Area Prism Epoch of Reionization Survey. '
                                  f'Mark Dickinson at NOIRLab (AZ) is the P.I. of this proposal with reference JWST-GO-6368.'
                                  f' Please contact the P.I. before using this dataset.\n\n This widgets below can be '
                                  f'used to constrain the sample. Please check the CAPERS README file for the parameters '
                                  f'description.')

            data_dict['redshift_label'] = 'z_UNICORN'

            data_dict['fits_extension'] = ['optext', 'x1d']

            data_dict['logo_path'] = LOCAL_FOLDER.parent / 'resources/images/Logo_CAPERS_text_RGB.png'

    return data_dict


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


def object_selection_interface():

    # Object selection
    label_text = '**MSA IDs (comma separated)**'
    help_text = 'The observations list will be limited to the input IDs'
    place_holder_text = '3,1027,80026'
    st.text_area(label=label_text, value=None, key='mpt_list', help=help_text, placeholder=place_holder_text,
                 on_change=save_objSample, args=("mpt_list",),)

    return


def survey_intro(name, data_survey):

    # Title
    st.header(f'{name.upper()} survey:', divider='gray')
    st.write('')

    # Author block
    col_logo, col_author = st.columns([0.15, 0.85], gap='small')

    with col_logo:
        st.image(load_logo(data_survey['logo_path']), width=300)

    with col_author:
        st.space("large")
        st.markdown(data_survey['intro'], text_alignment='justify')

    return


def read_flux_measurements(obj_series, obj_file, flux_sample):

    idx_flux = (obj_series.index[0][0], obj_series.index[0][1], Path(obj_file).name)
    try:
        flux_df = flux_sample.xs(idx_flux, level=['sample', 'id', 'file'], drop_level=True)
        flux_df.index.name = None
        if flux_df.index.size == 0:
            flux_df = None
    except KeyError:
        flux_df = None

    return flux_df


def object_description(input_df, idx_obj):

    st.markdown(f'### Observation')

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

    # Line selection
    if flux_df is not None:
        line_selection_interface(flux_df)

    # Object selection
    object_selection_interface()


    return


def indexing_sheets(survey, files_df, flux_df, ref_redshift):

    # Sample indexing
    if s_state.get('sample_list') is not None:
        idcs = files_df.index.get_level_values('sample').isin(s_state['sample_list'])
    else:
        idcs = files_df.index

    # Redshift range indexing
    z_range = s_state.get('z_range')
    if z_range is not None:
        idcs = idcs & (files_df[ref_redshift].between(z_range[0], z_range[1]) | files_df[ref_redshift].isna())

    # Dispenser selection
    if survey == 'ceers':
        idcs = idcs & files_df[s_state.get('disp_list')].any(axis=1)

    # Line selection
    line_selection = s_state.get('line_selection')
    if len(line_selection) > 0:
        obj_wlines = flux_df.loc[flux_df.index.get_level_values('line').isin(line_selection)].index.get_level_values('id')
        idcs = idcs & files_df.index.get_level_values('id').isin(obj_wlines)

    # Name selection
    mpt_list = s_state.get('mpt_list')
    if mpt_list is not None and mpt_list != "":
        mpt_array = widget_text_to_list(mpt_list)
        idcs_name = files_df['MPT_number'].isin(mpt_array)
        mpt_found = files_df.loc[idcs_name, 'MPT_number'].unique()
        mpt_common = intersect1d(mpt_found, mpt_array)
        if sum(mpt_common) > 0:
            if len(mpt_common) == 1:
                msg = f'The object {mpt_found.astype(int)} was found on the dataset'
            else:
                msg = f'The objects {mpt_found.astype(int)} were found on the dataset'
            st.success(msg)

        idcs = idcs & idcs_name

    return idcs, idcs.sum()


def object_selection(survey, data_survey, n_objs, df_selection):

    st.caption("")

    st.caption("Use the tools in the upper-right corner to expand the table, hide columns, or download it.")
    column_order = ['MPT_number', 'ra', 'dec', 'disp', 'z_med', 'z_UNICORN', 'z_tier', 'z_aspect_key', 'z_manual',
                    'z_gaussian', 'Notes', 's2d', 'x1d', 'optext']
    st.dataframe(df_selection, column_order=column_order)

    # Download spectra
    st.space(size="small")
    st.subheader("Object selection", divider='gray')

    # Cropped df
    msg = (f'The current selection has <span style="color:#E1AD01;font-weight:bold;">{n_objs} objects</span> '
           f' use the menus below to load the spectra from an individual source.')
    st.write(msg, unsafe_allow_html=True)

    # Object selection
    id_idx = df_selection.index.get_level_values('id')
    help_msg = 'Select the object'
    obj = st.selectbox('Object MSA', options=sort(id_idx.unique()), help=help_msg)
    idcs_obj = id_idx == str(obj)

    # 1D selection
    file1d_list = squeeze(df_selection.loc[idcs_obj, data_survey['fits_extension']].to_numpy())
    file1d_list = file1d_list[notnull(file1d_list)]
    st.write(f'Number of 1d: {len(file1d_list)}')

    help_msg = 'Select the 1D spectrum to download'
    file1d = st.selectbox('1D spectrum file', options=file1d_list, help=help_msg)
    disp = 'prism' if 'prism' in file1d else 'comb-mgrat'
    path1d = Path(file1d)

    if survey == 'ceers':
        ext1D = path1d.stem.split('_')[-1]
        idx_1D = idcs_obj & (df_selection[f'{disp}_{ext1D}'] == file1d)
    else:
        ext1D = 'optext' if 'optext' in file1d else 'x1d'
        idx_1D = idcs_obj & (df_selection[ext1D] == file1d)


    return obj, idx_1D, file1d


def download_spectrum(survey, data_survey, obj, df_selection, idx_1D, file1d, flux_df):

    # Import spectra
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
        submitted = st.form_submit_button("Load observation", help=help_msg)

        if submitted:

            # Clear the previous data
            clear_obj_data()

            # Connect to drive
            service = gdrive_service(s_state["username"])

            # Download the 1D spectrum
            with st.spinner(f'1D spectrum file query'):
                full_path1d = f"{survey.upper()}/{df_selection.loc[idx_1D, 'file_path'].values[0]}/{file1d}"
                file1d_bytes = download_from_path(service, full_path1d, secrets.connections.capers.root_id)

            if file1d_bytes is not None:
                st.info('1D spectrum located')

                # Recover redshift from type priority
                row = df_selection.loc[idx_1D]
                z_obj = row[data_survey['redshift_label']].values[0]

                # Get spectrum
                spec = load_spectrum(file1d_bytes, 'nirspec', z_obj, norm_flux=None, id_label=f'{obj}',
                                     wave_units_out=wave_units_str, flux_units_out=flux_units_str)
                obj_flux = read_flux_measurements(row, file1d, flux_df)

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


def survey_selection(survey):

    # Page data
    data_survey = survey_params(survey)

    # Author block
    survey_intro(survey, data_survey)

    # Connect to the online spreadsheets
    files_df = read_collaboration_file_log(survey, ['sample', 'id', 'pointing'])
    flux_df = read_collaboration_flux_log(survey, ['sample', 'id', 'file', 'line'])

    # Widgets to select sub-sample properties
    widgets_selection(survey, data_survey, files_df, flux_df)

    # Get indexes of selection
    idcs_selection, n_objs = indexing_sheets(survey, files_df, flux_df, data_survey['redshift_label'])

    # No objects in selection
    if n_objs == 0:
        st.warning(f'There are no spectra for the input selection criteria')

    else:

        # Select object from sub-sample
        df_selection = files_df.loc[idcs_selection]
        obj, idx_1D, file1d = object_selection(survey, data_survey, n_objs, df_selection)

        # Form to dowload the spectrum with the sample/user properties
        download_spectrum(survey, data_survey, obj, df_selection, idx_1D, file1d, flux_df)

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

    return


def survey_ceers(auth):
    st.write(f'Welcome CEERs')
    return


def survey_capers(auth):
    st.write('CAPERS')
    auth.login(location='main')

    return


def survey_lyc(auth):
    st.write('Lycleakers')
    auth.login(location='main')

    return