import bokeh
import streamlit as st

from pathlib import Path
from numpy import floor, ceil, sort, loadtxt
from streamlit import session_state as s_state, secrets
from utils.input_output import read_collaboration_file_log, clear_obj_data
from utils.input_output import save_state, gdrive_service, download_from_path, load_spectrum
from utils.interfaces import samples_widgets_selection, indexing_sheets, unit_conversion_inputs
from utils.plots import LyC_bokeh_spectrum



def lyc_cos_selection():

    # Title
    msg = f'## {s_state["username"].upper()}'
    st.write(msg)
    st.write('')

    # Author block
    msg = (f'These observations are part of the Chasing Lyman Continuum Leakers in the Local Universe HST proposal.\n\n'
           f'Svea Hernández at the Space Telescope Science Institute (STScI) is the P.I. with PID17515 identifier.\n\n')
    st.write(msg)

    # Table with the data
    st.write('The table below contains the objects')
    files_df = read_collaboration_file_log('PID17515', ['sample', 'id', 'offset_id', 'state'])

    # Pre-selection widgets
    samples_widgets_selection(files_df, id_check='True', id_label='object', example_ids='Haro2, Izw18, Pox186...')

    # Get indexes of selection
    idcs_selection, n_objs = indexing_sheets(files_df, mpt_list=s_state.get('mpt_list'), ID_hdr='object', ID_types=str)

    # Download spectra
    st.markdown("***")
    st.markdown(f'### Import *.fits* file')

    # Cropped df
    df_selection = files_df.loc[idcs_selection]
    msg = (f'The current selection has <span style="color:#E1AD01;font-weight:bold;">{df_selection.index.shape[0]} objects</span> '
           f' use the menus below to load the spectra from an individual source.')
    st.write(msg, unsafe_allow_html=True)

    # Object selection
    identifier = sort(df_selection.object.unique().astype(str))
    obj = st.selectbox('Object name', options=identifier, help='Select the object')
    idcs_obj = df_selection['object'] == obj

    # 1D selection
    file1d_list = df_selection.loc[idcs_obj, ["filepath", "LyAlpha_fitting", "metals_fitting"]].values.flatten().tolist()
    file1d = st.selectbox('1D spectrum file', options=file1d_list, help='Select spectrum to download')
    reg_key = None if file1d.endswith('.fits') else ('LyAlpha' if 'LyAlpha' in file1d else 'metals')


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
        help_msg = f'Press to download the spectra from CAPERS google drive.'
        submitted = st.form_submit_button("Load observation", help=help_msg)

        if submitted:

            # Clear the previous data
            clear_obj_data()

            # Connect to drive
            service = gdrive_service(s_state["username"])

            # Download the 1D spectrum
            with st.spinner(f'1D spectrum file query'):
                file1d_bytes = download_from_path(service, file1d, secrets["collaborations"]["credentials"]["usernames"]["PID17515"]["root_id"])

                if reg_key is not None:
                    filereg = f'LyC_leakers_COS/{obj}_{reg_key}_best_fit.reg'
                    reg1d_bytes = download_from_path(service, filereg, secrets["collaborations"]["credentials"]["usernames"]["PID17515"]["root_id"])

            if file1d_bytes is not None:
                st.info('1D spectrum located')

                # Recover redshift from type priority
                z_obj = df_selection.loc[idcs_obj, 'redshift'].values

                # Get spectrum
                instrument = 'cos' if file1d.endswith('.fits') else 'text'
                spec = load_spectrum(file1d_bytes, instrument, z_obj, norm_flux=None, id_label=f'{obj}',
                                     wave_units_out=wave_units_str, flux_units_out=flux_units_str)

                # Save the data
                save_state('spec', spec)
                save_state('id', Path(file1d).stem)

            else:
                st.warning('1D spectrum was not located')

    # 1D spectrum display
    if s_state.get('spec') is not None:

        #  Visualize the spectra
        st.markdown("***")

        st.write(f'#### 1D spectrum')
        plot_tab, objSheet_tab = st.tabs(['Plot', 'Object data'])

        with plot_tab:
            st.write(" ")

            # Add the LyC analysis data
            if reg_key is not None:
                wave_reg, flux_reg, err_reg, best_fit, mask_reg,  = loadtxt(reg1d_bytes, comments='#', unpack=True)
                reg_params = {'wave_reg': wave_reg, 'flux_reg': best_fit}
            else:
                reg_params = None

            LyC_bokeh_spectrum(spec_key='spec', reg_params=reg_params)

        with objSheet_tab:
            st.write(" ")
            # st.dataframe(df_selection.loc[idcs_obj].T)

    return