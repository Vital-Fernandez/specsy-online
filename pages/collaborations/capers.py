import streamlit as st
from streamlit import session_state as s_state,secrets
from streamlit_gsheets import GSheetsConnection
from numpy import floor, ceil, intersect1d, sum, array
from utils.interfaces import widget_text_to_list, unit_conversion_inputs
from utils.input_output import save_objSample, save_state, gdrive_service, download_from_path, hdr_to_df, load_spectrum
from numpy import sort
from utils.plots import bokeh_spectrum, bokeh_2D_spectrum
from lime.archives.read_fits import load_fits
from lime.tools import pd_get
from numpy import linspace
from pandas import notna

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
        msg = f'\n\n**Pointing:** {input_df.loc[idx_obj].pointing.values[0]}'
        msg += f'\n\n**Extraction:** {input_df.loc[idx_obj].ext.values[0]}'
        msg += f'\n\n**Sample:** {input_df.loc[idx_obj].index.values[0][0]}'
        st.markdown(msg)

    with col2:
        format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Photometry</span>**'
        st.write(format_hdr, unsafe_allow_html=True)
        # 'flux_F277W', 'flux_F356W', 'flux_F444W'
        tupple_index = tuple(idx_obj)[0]
        msg = f'**F277W:** {pd_get(input_df, tupple_index, "flux_F277W", default="Not available")}'
        msg += f'\n\n**F356W:** {pd_get(input_df, tupple_index, "flux_F356W", default="Not available")}'
        msg += f'\n\n**F444W:** {pd_get(input_df, tupple_index, "flux_F444W", default="Not available")}'
        msg += f'\n\n**F606W:** {pd_get(input_df, tupple_index, "flux_F606W", default="Not available")}'
        msg += f'\n\n**F814W:** {pd_get(input_df, tupple_index, "flux_F814W", default="Not available")}'
        st.markdown(msg)

    with col3:
        format_hdr = f'**<span style="color:#C69B6D;font-weight:bold;">Redshift</span>**'
        st.write(format_hdr, unsafe_allow_html=True)
        msg = f'\n\n**z_UNICORN:** {input_df.loc[idx_obj].z_UNICORN.values[0]}'
        msg += f'\n\n**z_Aspect:** {input_df.loc[idx_obj].z_aspect_key.values[0]}'
        msg += f'\n\n**z_LiMe:** {input_df.loc[idx_obj].z_gaussian.values[0]:0.3f}'
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


    # Connect to the online spreadsheet
    conn = st.connection("capers", type=GSheetsConnection)
    index_list = ['sample', 'id', 'file']
    df = conn.read(ttl=None, index_col=index_list, header=0)
    df.index.names = index_list

    # Widgets to adjust selection
    widgets_selection(df)

    # Get indexes of entry in sheet
    idcs_selection = indexing_sheets(df)

    # Display the sheet
    st.caption("")
    st.caption("Use the table tools to expand the table, hide columns or download the data")
    st.dataframe(df.loc[idcs_selection])

    # Download spectra
    st.markdown("***")
    st.markdown(f'### Import *.fits* file')

    # Cropped df
    df_selection = df.loc[idcs_selection]

    msg = (f'The current selection has <span style="color:#E1AD01;font-weight:bold;">{idcs_selection.sum()} files</span> '
           f' use the menus below to load the spectra from an individual source.')
    st.write(msg, unsafe_allow_html=True)

    # Object selection
    msa_unique = sort(df_selection.MPT_number.unique().astype(int))
    help_msg = 'Select the object'
    obj = st.selectbox('Object MSA', options=msa_unique, help=help_msg)

    # 1D selection
    idcs_obj = df_selection.MPT_number == obj
    idcs_1d = idcs_obj & (df_selection.ext.isin(['x1d', 'optext']))
    file1d_list = df_selection.loc[idcs_1d].index.get_level_values('file').to_numpy()
    file1d_list = array(sorted(file1d_list, key=lambda x: 'optext' not in x))

    help_msg = 'Select the 1D spectrum to download'
    file1d = st.selectbox('1D spectrum file', options=file1d_list, help=help_msg)
    idx_1d_target = df_selection[df_selection.index.get_level_values('file') == file1d].index

    # 2D selection
    idcs_2d = idcs_obj & (df_selection.ext == 's2d')
    file2d_list = df_selection.loc[idcs_2d].index.get_level_values('file').to_numpy()

    help_msg = 'Select the 2D spectrum to download'
    file2d = st.selectbox('2D spectrum file', options=file2d_list, help=help_msg)
    idx_2d_target = df_selection[df_selection.index.get_level_values('file') == file2d].index

    full_path1d = f"{s_state['username'].upper()}/{df_selection.loc[idx_1d_target, 'file_path'].values[0]}"
    full_path2d = f"{s_state['username'].upper()}/{df_selection.loc[idx_2d_target, 'file_path'].values[0]}"

    # Import spectra
    with st.form('load_capers', border=False, enter_to_submit=False, clear_on_submit=False):

        wave_units_str, flux_units_str = unit_conversion_inputs('Angstrom', 'FLAM')

        # Run the query
        st.write('')
        help_msg=f'Press to download the spectra from CAPERS google drive.'
        submitted = st.form_submit_button("Load observation", help=help_msg)

        if submitted:

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
                row = df_selection.loc[tuple(idx_1d_target)]
                z_obj = next((row[col] for col in ['z_gaussian', 'z_aspect_key', 'z_UNICORN'] if notna(row[col])), None)

                spec = load_spectrum(file1d_bytes, 'nirspec', z_obj, None, wave_units_str, flux_units_str, None)
                save_state('spec', spec)
            else:
                st.warning('1D spectrum was not located')

    #  Visualize the spectra
    spec = s_state['spec']
    fits_2d = s_state['2D_spectrum']
    st.markdown("***")

    # 1D spectrum display
    if spec is not None:

        # Object information
        object_description(df, idx_1d_target)

        st.write(f'#### 1D spectrum')
        plot_tab, objSheet_tab = st.tabs(['Plot', 'CAPERs data'])

        with plot_tab:
            bokeh_spectrum(spec)

        with objSheet_tab:
            st.dataframe(df_selection.loc[idx_1d_target].T)

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