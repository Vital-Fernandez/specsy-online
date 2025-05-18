import streamlit as st
from streamlit import session_state as s_state, secrets
from numpy import floor, ceil, intersect1d, sum, array, linspace, sort
from pandas import notna, notnull
from pathlib import Path

import lime
from lime.tools import pd_get
from lime.archives.read_fits import load_fits

from utils.interfaces import widget_text_to_list, unit_conversion_inputs
from utils.input_output import save_objSample, save_state, gdrive_service, download_from_path, hdr_to_df, load_spectrum
from utils.input_output import read_collaboration_file_log, read_collaboration_flux_log, clear_obj_data
from utils.plots import bokeh_spectrum, bokeh_2D_spectrum


def read_flux_measurements(obj_series, obj_file, flux_sample):

    idx_flux = (obj_series.index[0][0], obj_series.iloc[0].MPT_number, obj_file)
    flux_df = flux_sample.xs(idx_flux, level=['sample', 'id', 'file'], drop_level=True)
    flux_df.index.name = None

    if flux_df.index.size == 0:
        flux_df = None

    return flux_df


def object_description(input_df, idx_obj):

    st.markdown(f'### Observation')

    msg = (f'**<span style="color:#AAD372;font-weight:bold;">MSA number</span>** '
           f'{int(input_df.loc[idx_obj].MPT_number.values[0])}')
    st.write(msg, unsafe_allow_html=True)
    # st.write('')

    col1, col2, col3 = st.columns(3)

    with col1:
        format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Identification</span>**'
        st.write(format_hdr, unsafe_allow_html=True)
        msg = f'\n\n**Pointing:** {input_df.loc[idx_obj].index.names[2]}'
        msg += f'\n\n**Optimal extraction:** {input_df.loc[idx_obj, "optext"].values[0]}'
        msg += f'\n\n**Sample:** {input_df.loc[idx_obj].index.values[0][0]}'
        st.markdown(msg)

    with col2:
        format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Photometry</span>**'
        st.write(format_hdr, unsafe_allow_html=True)
        # 'flux_F277W', 'flux_F356W', 'flux_F444W'
        tupple_index = tuple(idx_obj)[0]
        msg = f'**F277W:** {pd_get(input_df, tupple_index, "flux_f277w", default="Not available")}'
        msg += f'\n\n**F356W:** {pd_get(input_df, tupple_index, "flux_f356w", default="Not available")}'
        msg += f'\n\n**F444W:** {pd_get(input_df, tupple_index, "flux_f444w", default="Not available")}'
        msg += f'\n\n**F606W:** {pd_get(input_df, tupple_index, "flux_f606w", default="Not available")}'
        msg += f'\n\n**F814W:** {pd_get(input_df, tupple_index, "flux_f814w", default="Not available")}'
        st.markdown(msg)

    with col3:
        format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Redshift</span>**'
        st.write(format_hdr, unsafe_allow_html=True)
        msg = f'\n\n**z_UNICORN:** {input_df.loc[idx_obj].z_UNICORN.values[0]}'
        msg += f'\n\n**z_Aspect:** {input_df.loc[idx_obj].z_aspect_key.values[0]}'
        msg += f'\n\n**z_LiMe:** {input_df.loc[idx_obj].z_manual.values[0]:0.3f}'
        st.markdown(msg)

    return


def widgets_selection(input_df):


    col1, col2 = st.columns(2, gap='large')

    # Sample selection
    with col1:
        default_samples = input_df.index.get_level_values('sample').unique().to_numpy()
        st.multiselect('**Sample selection:**', options=list(default_samples),
                        key='sample_list', on_change=save_objSample, args=("sample_list",))

    # Redshift range selection
    with col2:
        label_text = '**Redshift range:**'
        help_text = 'The observations list will be limited to the input "z_UNICORN" range'
        z_limits = floor(input_df.z_UNICORN.min()), ceil(input_df.z_UNICORN.max())

        # Initial values for the range for first time
        if s_state.get('z_range') is None:
            save_state('z_range', z_limits)

        st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
                  key='z_range', help=help_text, on_change=save_objSample, args=("z_range",))


    # Object selection
    label_text = '**MSA IDs (comma separated)**'
    help_text = 'The observations list will be limited to the input IDs'
    place_holder_text = '3,1027,80026'
    st.text_area(label=label_text, value=None, key='mpt_list', help=help_text, placeholder=place_holder_text,
                 on_change=save_objSample, args=("mpt_list",),)

    return


def indexing_sheets(input_df, ref_redshift='z_UNICORN'):

    # Sample indexing
    if s_state.get('sample_list') is not None:
        idcs = input_df.index.get_level_values('sample').isin(s_state['sample_list'])
    else:
        idcs = input_df.index

    # Redshift range indexing
    z_range = s_state.get('z_range')
    if z_range is not None:
        idcs = idcs & (input_df[ref_redshift] >= z_range[0]) & (input_df[ref_redshift] <= z_range[1])

    # Object selection
    mpt_list = s_state.get('mpt_list')
    if mpt_list is not None and mpt_list != "":
        mpt_array = widget_text_to_list(mpt_list)

        idcs_selection = input_df['MPT_number'].isin(mpt_array)
        mpt_found = input_df.loc[idcs_selection, 'MPT_number'].unique()
        mpt_common = intersect1d(mpt_found, mpt_array)
        if sum(mpt_common) > 0:
            st.info(f'Objects {", ".join(list(mpt_common.astype(str)))} were found the sample selection')
            idcs = idcs & idcs_selection
        else:
            st.warning('None of the objects in the input MPT list was found')


    return idcs


def capers_selection():

    # Title
    msg = f'## {s_state["username"].upper()}'
    st.write(msg)
    st.write('')

    # Author block
    msg = (f'These observations belong to the CANDELS-Area Prism Epoch of Reionization Survey. Mark Dickinson at NOIRLab (AZ)'
           f' is the P.I. of this proposal with reference JWST-GO-6368. Please contact the P.I. before using this dataset.\n\n'
           f'This widgets below can be used to constrain the sample. Please check the CAPERS README file for the parameters description.')
    st.write(msg)

    # Connect to the online spreadsheets
    files_df = read_collaboration_file_log('capers')
    flux_df = read_collaboration_flux_log('capers')

    # Widgets to adjust selection
    widgets_selection(files_df)

    # Get indexes of entry in sheet
    idcs_selection = indexing_sheets(files_df)

    # Display the sheet
    st.caption("")
    st.caption("Use the tools in the upper-right corner to expand the table, hide columns, or download the data.")
    default_tab, obser_tab, z_tab, files_tab = st.tabs(['ID', 'Observation', 'Redshift', 'Files'])
    with default_tab:
        column_order = ['MPT_number', 'ra', 'dec', 'disp', 'Notes']
        st.dataframe(files_df.loc[idcs_selection], column_order=column_order)
    with obser_tab:
        column_order = ['MPT_number', 'MSA_weight', 'n_nods_vis1', 'n_nods_vis2', 'n_nods_vis3', 'eff_exp_time', 'shutter_centering']
        st.dataframe(files_df.loc[idcs_selection], column_order=column_order)
    with z_tab:
        column_order = ['MPT_number', 'z_med', 'z_UNICORN', 'z_tier', 'z_aspect_key', 'z_manual', 'z_gaussian']
        st.dataframe(files_df.loc[idcs_selection], column_order=column_order)
    with files_tab:
        column_order = ['MPT_number', 's2d', 'x1d', 'optext']
        st.dataframe(files_df.loc[idcs_selection], column_order=column_order)

    # Download spectra
    st.markdown("***")
    st.markdown(f'### Import *.fits* file')

    # Cropped df
    df_selection = files_df.loc[idcs_selection]
    msg = (f'The current selection has <span style="color:#E1AD01;font-weight:bold;">{idcs_selection.sum()} objects</span> '
           f' use the menus below to load the spectra from an individual source.')
    st.write(msg, unsafe_allow_html=True)

    # Object selection
    msa_unique = sort(df_selection.MPT_number.unique().astype(int))
    help_msg = 'Select the object'
    obj = st.selectbox('Object MSA', options=msa_unique, help=help_msg)
    idcs_obj = df_selection.MPT_number == obj

    # 1D selection
    file1d_list = df_selection.loc[idcs_obj, ['optext', 'x1d']].to_numpy()
    file1d_list = file1d_list[notnull(file1d_list)]
    help_msg = 'Select the 1D spectrum to download'
    file1d = st.selectbox('1D spectrum file', options=file1d_list, help=help_msg)
    ext1D = 'optext' if 'optext' in file1d else 'x1d'
    idx_1D = idcs_obj & df_selection.loc[idcs_obj, ext1D].index

    # 2D selection
    file2d_list = df_selection.loc[idcs_obj, 's2d'].to_numpy()
    help_msg = 'Select the 2D spectrum to download'
    file2d = st.selectbox('2D spectrum file', options=file2d_list, help=help_msg)
    idx_2D = idcs_obj & df_selection.loc[idcs_obj, 's2d'].index

    full_path1d = f"{s_state['username'].upper()}/{df_selection.loc[idx_1D, 'file_path'].values[0]}/{file1d}"
    full_path2d = f"{s_state['username'].upper()}/{df_selection.loc[idx_2D, 'file_path'].values[0]}/{file2d}"

    # Import spectra
    with st.form('load_capers', border=False, enter_to_submit=False, clear_on_submit=False):

        wave_units_str, flux_units_str = unit_conversion_inputs('Angstrom', 'FLAM')

        # Run the query
        st.write('')
        help_msg=f'Press to download the spectra from CAPERS google drive.'
        submitted = st.form_submit_button("Load observation", help=help_msg)

        if submitted:

            # Clear the previous data
            clear_obj_data()

            # Connect to drive
            service = gdrive_service(s_state["username"])

            # Download the 2D spectrum
            with st.spinner(f'2D spectrum file query'):
                file2d_bytes = download_from_path(service, full_path2d, secrets.connections.capers.root_id)

            if file2d_bytes is not None:
                st.info('2D spectrum located')
                data_list, hdr_list = load_fits(file2d_bytes, data_ext_list=[1, 2], hdr_ext_list=[0, 1], url_check=False)
                save_state('2D_spectrum', (data_list, hdr_list))
            else:
                st.warning('2D spectrum was not located')

            # Download the 1D spectrum
            with st.spinner(f'1D spectrum file query'):
                file1d_bytes = download_from_path(service, full_path1d, secrets.connections.capers.root_id)

            if file1d_bytes is not None:
                st.info('1D spectrum located')

                # Recover redshift from type priority
                row = df_selection.loc[idx_1D]
                z_obj = next((row[col].values[0] for col in ['z_gaussian', 'z_manual', 'z_aspect_key', 'z_UNICORN'] if notna(row[col].values)), None)

                # Get spectrum
                spec = load_spectrum(file1d_bytes, 'nirspec', z_obj, None, wave_units_str, flux_units_str, None)
                obj_flux = read_flux_measurements(row, file1d, flux_df)

                # Get line measurements
                if obj_flux is not None:
                    spec.load_frame(obj_flux)
                    save_state('lines_df', obj_flux)
                    save_state('bands_df', lime.bands_from_measurements(obj_flux))

                # Save the data
                save_state('spec', spec)
                save_state('id', Path(file1d).stem)

            else:
                st.warning('1D spectrum was not located')

    #  Visualize the spectra
    spec = s_state['spec']
    fits_2d = s_state['2D_spectrum']
    st.markdown("***")

    # 1D spectrum display
    if spec is not None:

        # Object information
        object_description(df_selection, idx_1D)

        st.write(f'#### 1D spectrum')
        plot_tab, objSheet_tab = st.tabs(['Plot', 'CAPERs data'])

        with plot_tab:
            st.write(" ")
            bokeh_spectrum('spec')

        with objSheet_tab:
            st.write(" ")
            st.dataframe(df_selection.loc[idx_1D].T)

    # 2D spectrum display
    if fits_2d is not None:
        st.write(f'#### 2D spectrum')

        # Unpack the 2D data and display in tabs
        data_list, hdr_list = fits_2d
        spec2D_tab, hdr0_tab, hdr1_tab = st.tabs(['Plot', 'Header 0', 'Header 1'])

        with spec2D_tab:
            wave_array = linspace(hdr_list[1]['WAVSTART']*1000000, hdr_list[1]['WAVEND']*1000000, hdr_list[1]['NAXIS1'])
            flux_array = data_list[0]
            bokeh_2D_spectrum(wave_array, flux_array)

        with hdr0_tab:
            hdr_df = hdr_to_df(hdr_list[0])
            st.dataframe(hdr_df, width=800)

        with hdr1_tab:
            hdr_df = hdr_to_df(hdr_list[1])
            st.dataframe(hdr_df, width=800)

    return