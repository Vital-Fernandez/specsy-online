import streamlit as st
from pathlib import Path
from PIL import Image
from astropy.io import fits
from streamlit import session_state as s_state
from toml import loads
from pandas import DataFrame

import lime
from lime import load_frame, Spectrum
from lime.io import parse_lime_cfg
from specsy import load_frame as load_frame_sy, Innate

# Resources
LOGO_PATH = Path('../resources/images/logo.png')
INSTRUMENT_LIST = ['SDSS', 'OSIRIS', 'ISIS', 'NIRSPEC', 'MANGA', 'MUSE', 'MEGARA']
FIT_CFG_PLACEHOLDER = ('[default_line_fitting]\n'
                       'H1_6563A_b="H1_6563A+N2_6583A+N2_6548A"\n'
                       'N2_6548A_amp="expr:N2_6584A_amp/2.94"\n'
                       'N2_6548A_kinem="N2_6584A"')
FIT_CFG_HELP = 'Please check LiMe documentation to read more on how to adjusts your fittings'

# Keys for the platform variables
DEFAULT_STATES = {'spec': 'No',
                  'id': None,
                  'redshift': None,
                  'bands_df': None,
                  'fit_cfg': None,
                  'frame_df': None}


def save_state(param, value):
    s_state[f'{param}'] = value
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


def widget_save_state(param):
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


def set_defaults():

    for item, value in DEFAULT_STATES.items():
        if f'{item}_hold' not in s_state:
            s_state[f'{item}_hold'] = value
        s_state[item] = s_state[f'{item}_hold']

    return


@st.cache_data
def load_emiss_grids(fname):
    return Innate(fname, x_space=[9000, 20000, 251], y_space=[1, 600, 101])


@st.cache_data
def load_logo(file_address=LOGO_PATH):
    return None#Image.open(file_address)


@st.cache_data
def load_spectrum(input_file, instrument, redshift, id_label):

    z_obj = None if redshift is None else float(redshift)
    spec = Spectrum.from_file(input_file, instrument, redshift=z_obj, id_label=id_label)

    return spec


@st.cache_data
def parse_line_bands_df(uploaded_object):

    bands_df = load_frame(uploaded_object)
    save_state('bands_df', bands_df)

    return


@st.cache_data
def parse_fit_cfg(conf_string):

    dict_toml = loads(conf_string)

    return parse_lime_cfg(dict_toml)

@st.cache_data
def parse_frame_normalization(df):

    return load_frame_sy(df, flux_type='profile', norm_line='H1_4861A')

def declare_spectrum():

    # Inputs
    col_load_spec, col_properties = st.columns([0.6, 0.4], gap='large')

    with col_load_spec:
        st.markdown(f'### File address')
        uploaded_file = st.file_uploader("Choose a '.fits' file", type=['.fits'])

    with col_properties:
        st.markdown(f'### Attributes')

        # Instrument
        instrument = st.selectbox('Instrument:', INSTRUMENT_LIST)
        st.write('Selection:', instrument)

        # Redshift
        z_string = st.text_input('Redshift', value=s_state['redshift'])

    if uploaded_file:

        # Every form must have a submit button.
        submitted = st.button("Upload", key='button_spec')

        if submitted:
            # s_state['id'] = uploaded_file.name
            save_state('id', uploaded_file.name)

            # s_state['spec'] = load_spectrum(uploaded_file, instrument, z_string)
            save_state('spec', load_spectrum(uploaded_file, instrument, z_string, uploaded_file.name))

    elif uploaded_file is False and s_state != 'No':
        st.write(f'Please specify a .fits file')

    return


def declare_spectrum_form():

    spec = f'No'

    with st.form('load_spec_form', border=True) as f:

        st.markdown(f'# Load spectrum')
        st.markdown(f'Please declare *.fits* file location and source instrument:')

        # Inputs
        col_load_spec, col_properties = st.columns([0.6, 0.4], gap='large')

        with col_load_spec:
            st.markdown(f'### File address')
            uploaded_file = st.file_uploader("Choose a '.fits' file", type=['.fits'])

        with col_properties:
            st.markdown(f'### Attributes')

            # Instrument
            instrument = st.selectbox('Instrument:', INSTRUMENT_LIST)
            st.write('Selection:', instrument)

            # Redshift
            z_string = st.text_input('Redshift', 'None')

        # Every form must have a submit button.
        submitted = st.form_submit_button("Upload")

        if submitted and (uploaded_file is not None):
            z_obj = None if z_string == 'None' else float(z_string)
            spec = Spectrum.from_file(uploaded_file, instrument, redshift=z_obj,
                                                      id_label='SHOC579')

            return spec, 'SHOC579'

    return spec, None


def declare_line_measuring():

    st.markdown(f'## Load the line bands and fitting configuration:')

    # Two columns for the bands
    # col_load_bands, col_fitCfg = st.columns([0.4, 0.6], gap='large')
    tab_bands, tab_conf = st.tabs(["Line bands", "Fitting configuration"])

    with tab_bands:
        st.markdown(f'### Bands file address')

        # Get the file
        uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

        # Load the dataframe
        if uploaded_file:
            parse_line_bands_df(uploaded_file)

        # Show the dataframe
        if s_state['bands_df'] is not None:
            st.dataframe(s_state['bands_df'])

    with tab_conf:
        st.markdown(f'### Fitting configuration')
        st.text_area('Please follow .toml style', key='fit_cfg', height=300, placeholder=FIT_CFG_PLACEHOLDER,
                     on_change=widget_save_state, help=FIT_CFG_HELP, args=("fit_cfg",))

    # Show upload button if inputs are declared
    if (s_state['bands_df'] is not None) and (s_state['fit_cfg'] is not None):

        # Every form must have a submit button.
        submitted = st.button("Fit lines", key='button_bands')

        if submitted:
            if s_state['spec'] is not None:

                if s_state['spec'] is not None:
                    if uploaded_file:
                        spec, bands = s_state['spec'], s_state['bands_df']
                        conf = parse_fit_cfg(s_state['fit_cfg'])

                        # Measuring the lines
                        my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                        spec.fit.frame(bands, fit_conf=conf)
                        my_bar.empty()

                        # Save the dataframe which now contains the measurements
                        save_state('spec', spec)

            else:
                st.write('Please upload a spectrum')
    return

