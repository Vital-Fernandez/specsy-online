import streamlit as st
from specsy_online.utils.input_output import save_objSample


def id_interface(file_df):
    options = sorted(file_df.index.get_level_values('id').dropna().unique())
    st.multiselect('**Object selection:**', key='id_list', options=options, default=options,
                   on_change=save_objSample, args=("id_list",))
    return


def product_interface(file_df):
    options = ['x1d_band', 'x1d_merged']
    help = 'Data product type: x1d for individual bands or merged spectra'
    st.multiselect('**Product selection:**', key='product_list', options=options, default=options,
                   on_change=save_objSample, args=("product_list",), help=help)
    return


def channel_interface(file_df):
    options = sorted(file_df.index.get_level_values('channel').dropna().unique())
    help = 'MRS IFU channel (1-4) or "merged" for the joined 1D spectrum'
    st.multiselect('**Channel selection:**', key='channel_list', options=options, default=options,
                   on_change=save_objSample, args=("channel_list",), help=help)
    return


def band_interface(file_df):
    options = sorted(file_df.index.get_level_values('band').dropna().unique())
    help = 'MRS band within each channel (short, medium, long)'
    st.multiselect('**Band selection:**', key='band_list', options=options, default=options,
                   on_change=save_objSample, args=("band_list",), help=help)
    return


def aperture_interface(file_df):
    options = sorted(file_df.index.get_level_values('aperture').dropna().unique())
    help = 'Extraction aperture: xPSF fractions (diameter, not radius) or fixed 1 arcsec'
    st.multiselect('**Aperture selection:**', key='aperture_list', options=options, default=options,
                   on_change=save_objSample, args=("aperture_list",), help=help)
    return
#
# def filter_file_df(file_df):
#     mask = file_df.index.get_level_values('id').isin(st.session_state['id_list'])
#     mask &= file_df.index.get_level_values('product').isin(st.session_state['product_list'])
#     for level in ('channel', 'band', 'aperture'):
#         values = file_df.index.get_level_values(level)
#         mask &= values.isin(st.session_state[f'{level}_list']) | values.isna()
#     return file_df.loc[mask]