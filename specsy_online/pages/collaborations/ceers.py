# import streamlit as st
# from streamlit import session_state as s_state, secrets
# from utils.input_output import read_collaboration_file_log, read_collaboration_flux_log, clear_obj_data, LOCAL_FOLDER
# from PIL import Image
# from numpy import floor, ceil, intersect1d, sum, array, linspace, sort
# from utils.input_output import save_objSample, save_state, gdrive_service, download_from_path, hdr_to_df, load_spectrum
#
#
# @st.cache_data
# def load_logo_ceers(file_address=LOCAL_FOLDER.parent / 'resources/images/CEERS_white.png'):
#     return Image.open(file_address)
#
#
# def widgets_selection(file_df, flux_df):
#
#     col1, col2 = st.columns(2, gap='large')
#
#     # Sample selection
#     with col1:
#         default_samples = file_df.index.get_level_values('sample').unique().to_list()
#         st.multiselect('**Sample selection:**', options=list(default_samples),
#                         key='sample_list', on_change=save_objSample, args=("sample_list",))
#
#     # Redshift range selection
#     with col2:
#         label_text = '**Redshift range:**'
#         help_text = 'The observations list will be limited to the input "z_UNICORN" range'
#         z_limits = floor(file_df['z_best'].min()), ceil(file_df['z_best'].max())
#
#         # Initial values for the range for first time
#         if s_state.get('z_range') is None:
#             save_state('z_range', z_limits)
#
#         st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
#                   key='z_range', help=help_text, on_change=save_objSample, args=("z_range",))
#
#     # Line selection
#     if flux_df is not None:
#         line_list = sorted(flux_df.index.get_level_values('line').unique().tolist())
#         if line_list is not None:
#             help_text = 'The object selection will be limited to objects with the input lines'
#             st.multiselect('**Observed lines:**', options=line_list,  key='line_selection',
#                            on_change=save_objSample, args=("line_selection",), help=help_text)
#
#     # Object selection
#     label_text = '**MSA IDs (comma separated)**'
#     help_text = 'The observations list will be limited to the input IDs'
#     place_holder_text = '3,1027,80026'
#     st.text_area(label=label_text, value=None, key='mpt_list', help=help_text, placeholder=place_holder_text,
#                  on_change=save_objSample, args=("mpt_list",),)
#
#     return
#
# def ceers_selection():
#
#     # Title
#     st.header(f'CEERs survey:', divider='gray')
#     st.write('')
#
#     # Author block
#     col_logo, col_author = st.columns([0.15, 0.85], gap='small')
#
#     with col_logo:
#         st.image(load_logo_ceers(), width=300)
#
#     with col_author:
#         st.space("large")
#         msg = (f'These observations belong to the **CEERS (The Cosmic Evolution Early Release Science Survey**. '
#                f'Steven Finkelstein at University of Texas at Austin is the P.I. of this proposal (NOI #135). \n\n'
#                f'This widgets below can be used to constrain the sample. Please visit '
#                f'[https://ceers.github.io/](https://ceers.github.io/) for more information on the project.')
#         st.markdown(msg, text_alignment='justify')
#
#     # Connect to the online spreadsheets
#     files_df = read_collaboration_file_log('ceers', ['sample', 'id', 'pointing'])
#     flux_df = read_collaboration_flux_log('ceers', ['sample', 'id', 'file', 'line'])
#
#     # Widgets to adjust selection
#     widgets_selection(files_df, flux_df)
#
#
#     return