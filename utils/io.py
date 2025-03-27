import streamlit as st
from pathlib import Path
from PIL import Image
from streamlit import session_state as s_state
from toml import loads
from pandas import DataFrame
from lime import load_frame, Spectrum
from lime.io import parse_lime_cfg
from specsy import load_frame as load_frame_sy, Innate
from specsy.innate import load_inference_data
from innate import DataSet

# Current path
LOCAL_FOLDER = Path(__file__).parent

# Resources
LOGO_PATH = LOCAL_FOLDER.parent/'resources/images/specsy_logo.PNG'
# INSTRUMENT_LIST = ['SDSS', 'OSIRIS', 'ISIS', 'NIRSPEC', 'MANGA', 'MUSE', 'MEGARA']
FIT_CFG_PLACEHOLDER = ('[default_line_fitting]\n'
                       'H1_6563A_b="H1_6563A+N2_6583A+N2_6548A"\n'
                       'N2_6548A_amp="expr:N2_6584A_amp/2.94"\n'
                       'N2_6548A_kinem="N2_6584A"')
FIT_CFG_HELP = 'Please check LiMe documentation to read more on how to adjusts your fittings'
EXTINCTION_LAWS = ['G03 LMC', 'CCM89', 'CCM89 Bal07', 'CCM89 oD94', 'S79 H83 CCM89', 'K76', 'SM79 Gal',
                    'MCC99 FM90 LMC', 'F99-like', 'F99', 'F88 F99 LMC']
LOW_DIAGS = ['S3_6312A', 'Hagele_2006', 'S2_4069A']
HIGH_DIAGS = ['O3_4363A', 'Hagele_2006']

# Keys for the platform variables
DEFAULT_STATES = {'spec': None,
                  'id': None,
                  'redshift': None,
                  'bands_df': None,
                  'fit_cfg': None,
                  'frame_df': None,
                  'emiss_dataset': None,
                  'particle_list': ['H1_4340A', 'O3_4363A', 'O3_4959A', 'O3_5007A', 'S3_6312A',
                                    'H1_6563A', 'S2_6716A', 'S2_6731A', 'O2_7319A', 'O2_7330A'],
                  'redcorr': 'G03 LMC',
                  'Rv': 3.4,
                  'low_diag': 'Hagele_2006',
                  'high_diag': 'O3_4363A'}


def set_defaults():

    for item, value in DEFAULT_STATES.items():
        if f'{item}_hold' not in s_state:
            s_state[f'{item}_hold'] = value
        s_state[item] = s_state[f'{item}_hold']

    return


def save_state(param, value):
    s_state[f'{param}'] = value
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


def widget_save_state(param):
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return

@st.cache_resource
def load_emiss_grids(fname):
    return Innate(fname, x_space=[9000, 20000, 251], y_space=[1, 600, 101])


@st.cache_data
def load_logo(file_address=LOGO_PATH):
    return Image.open(file_address)


@st.cache_data
def load_spectrum(input_file, instrument, redshift, norm_flux, units_wave, units_flux, id_label):

    # Unit conversion if necessary
    spec_params = {'redshift': None if redshift is None or redshift == '' else float(redshift),
                   'id_label': None if id_label is None or id_label == '' else id_label}

    if norm_flux is not None and redshift != '' :
        spec_params['norm_flux'] = float(norm_flux)

    if units_wave is not None and units_wave != '' :
        spec_params['units_wave'] = units_wave

    if units_flux is not None and units_flux != '' :
        spec_params['units_flux'] = units_flux

    # For observations which provide redshift
    if instrument in ['SDSS']:
        spec_params.pop('redshift')

    # Load the object
    spec = Spectrum.from_file(input_file, instrument, **spec_params)
    spec.unit_conversion('AA', 'FLAM')

    return spec


@st.cache_data
def load_infer_data(file_address):
    return load_inference_data(file_address)


def parse_line_bands_df(uploaded_object):
    return load_frame(uploaded_object)


def parse_emiss_dataset(uploaded_object):
    return DataSet.from_file(uploaded_object)


@st.cache_data
def parse_fit_cfg(conf_string):
    dict_toml = loads(conf_string)
    return parse_lime_cfg(dict_toml)


@st.cache_data
def parse_frame_normalization(df):
    return load_frame_sy(df, flux_type='profile', norm_line='H1_4861A')


@st.cache_data
def get_text_spectrum(spec_key):
    recarray = s_state[spec_key].retrieve.spectrum()
    return DataFrame.from_records(recarray)

@st.cache_data
def convert_for_download(df):
    return df.to_csv(index=False).encode("utf-8")


# def declare_spectrum_form():
#
#     with st.form('load_spec_form', border=True, clear_on_submit=False):
#
#         # Inputs
#         col_load_spec, col_properties = st.columns([0.6, 0.4], gap='large')
#
#         with col_load_spec:
#             st.markdown(f'### File address')
#             uploaded_file = st.file_uploader("Choose a '.fits' file", type=['.fits'])
#
#         with col_properties:
#             st.markdown(f'### Attributes')
#
#             # Instrument
#             instrument = st.selectbox('Instrument:', INSTRUMENT_LIST)
#
#             # Redshift
#             z_string = st.text_input('Redshift', value=s_state['redshift'])
#
#         # Every form must have a submit button.
#         submitted = st.form_submit_button("Upload")
#
#         if submitted:
#
#             if uploaded_file:
#
#                 # s_state['id'] = uploaded_file.name
#                 save_state('id', uploaded_file.name)
#
#                 # s_state['spec'] = load_spectrum(uploaded_file, instrument, z_string)
#                 save_state('spec', load_spectrum(uploaded_file, instrument, z_string, uploaded_file.name))
#
#             else:
#                 st.write('Please declare spectrum address')
#
#
#     return


# def declare_line_bands():
#
#     with st.form('load_bands_form', border=True, clear_on_submit=False):
#
#         st.markdown(f'### Bands file address')
#
#         # Get the file
#         uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])
#
#         # Every form must have a submit button.
#         submitted = st.form_submit_button("Upload")
#
#         # Load the dataframe
#         if submitted:
#             save_state('bands_df', parse_line_bands_df(uploaded_file))
#
#         else:
#             st.write('Please declare bands file address')
#
#     return

def declare_atomic_data():

    with st.form('load_emiss_dataset', border=True, clear_on_submit=False):

        st.markdown(f'### Grid file address')

        # Get the file
        uploaded_file = st.file_uploader("Choose a HDF5 ('.nc') or FITS (.fits) file", type=['.nc', '.fits'])

        # Every form must have a submit button.
        submitted = st.form_submit_button("Upload")

        # Load the dataframe
        if submitted:
            save_state('emiss_dataset', parse_emiss_dataset(uploaded_file))

        else:
            st.write('Please declare dataset file address')

    return


def declare_line_measuring():

    st.markdown(f'### Write the fitting configuration:')
    st.text_area('Please follow .toml style', key='fit_cfg', height=300, placeholder=FIT_CFG_PLACEHOLDER,
                 on_change=widget_save_state, help=FIT_CFG_HELP, args=("fit_cfg",))

    # Show upload button if inputs are declared
    if (s_state['bands_df'] is not None) and (s_state['fit_cfg'] is not None):

        # Every form must have a submit button.
        submitted = st.button("Fit lines", key='button_bands')

        if submitted:
            if s_state['spec'] is not None:

                spec, bands = s_state['spec'], s_state['bands_df']
                conf = parse_fit_cfg(s_state['fit_cfg'])

                # Clear previous measurements
                spec.frame = spec.frame.iloc[0:0]

                # Measuring the lines
                my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                spec.fit.frame(bands, fit_conf=conf)
                my_bar.empty()

                # Save the dataframe which now contains the measurements
                save_state('spec', spec)

            else:
                st.write('Please upload a spectrum')
    return

