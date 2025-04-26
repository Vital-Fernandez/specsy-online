import streamlit as st
from pathlib import Path
from PIL import Image
from streamlit import session_state as s_state, secrets
from toml import loads
from pandas import DataFrame
from lime import load_frame, Spectrum
from lime.io import parse_lime_cfg
from specsy import load_frame as load_frame_sy, Innate
from specsy.innate import load_inference_data
from innate import DataSet
import streamlit_authenticator as stauth
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload
from numpy import array, linspace
from astropy.io import fits

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
                  'obs_type': None,
                  'redcorr': 'G03 LMC',
                  'Rv': 3.4,
                  'low_diag': 'Hagele_2006',
                  'high_diag': 'O3_4363A',

                  # CAPERs
                  "sample_list": ['CAPERS_EGS_V0.2.1', 'CAPERS_UDS_V0.1', 'CAPERS_COSMOS_V0.2'],
                  "mpt_list": None,
                  "z_range": None,
                  "z_limits": None,
                  '2D_spectrum': None,
                  }


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

def clear_inputs_state(reset_defaults=True):
    s_state.clear()

    if reset_defaults:
        set_defaults()

    return

def clear_inputs_button():
    st.button('Clear input data', on_click=clear_inputs_state, icon=":material/delete:")
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

    # For observations which provide redshift
    if instrument in ['SDSS']:
        spec_params.pop('redshift')

    # Load the object
    spec = Spectrum.from_file(input_file, instrument, **spec_params)
    spec.unit_conversion(units_wave, units_flux)

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


def user_logging():

    credentials = secrets.collaborations.credentials.to_dict()

    authenticator = stauth.Authenticate(credentials, cookie_name='CAPERS_specsy', cookie_key='capersKey', cookie_expiry_days=60)
    authenticator.login(location='main')

    return


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
                spec.fit.frame(bands, fit_cfg=conf)
                my_bar.empty()

                # Save the dataframe which now contains the measurements
                save_state('spec', spec)

            else:
                st.write('Please upload a spectrum')
    return

@st.cache_data
def widget_text_to_list(str_list):

    if str_list is not None:
        output = str_list.replace('\n', '')
        output = output.replace(' ', '')
        output = array(output.split(',')).astype(int)
    else:
        output = None

    return output

def save_objSample(param):
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


@st.cache_resource
def gdrive_service(collab):


    credentials = Credentials.from_service_account_info(secrets.connections.capers.to_dict(),
                                                        scopes=['https://www.googleapis.com/auth/drive'])
    service = build('drive', 'v3', credentials=credentials)

    return service


def download_from_path(service, file_path, starting_parent_id='root'):

    path_parts = file_path.split('/')
    parent_id = starting_parent_id
    file_bytes = None

    # Resolve the folder path
    for folder_name in path_parts[:-1]:
        # st.write(f"🔍 Looking for '{folder_name}' inside '{parent_id}'...")
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
        fields = "files(id, name)"
        response = service.files().list(q=query, fields=fields, supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        folders = response.get('files', [])

        if not folders:
            st.write(f"❌ Folder '{folder_name}' not found under '{parent_id}'")
            return file_bytes

        parent_id = folders[0]['id']

    # Locate the file in the folder
    if parent_id:
        query = f"name = '{path_parts[-1]}' and '{parent_id}' in parents and trashed = false"
        response = service.files().list(q=query, fields="files(id, name, webViewLink)", supportsAllDrives=True,
                                        includeItemsFromAllDrives=True).execute()
        files = response.get('files', [])
        file_obj = files[0] if files else None

        if file_obj:
            file_bytes = download_binary_file(service, file_obj['id'])
        else:
            st.write(f"❌ File ({file_obj['name']}) not found in the target folder ({parent_id}).")
    else:
        st.write(f"❌ Could not resolve the folder path ({file_path}).")

    return file_bytes

def resolve_drive_path(service, folder_path, starting_parent_id='root'):

    parent_id = starting_parent_id
    for folder_name in folder_path:
        st.write(f"🔍 Looking for '{folder_name}' inside '{parent_id}'...")
        query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{parent_id}' in parents and trashed = false"
        response = service.files().list(q=query, fields="files(id, name)",
                                            supportsAllDrives=True,
                                            includeItemsFromAllDrives=True
                                        ).execute()
        folders = response.get('files', [])
        if not folders:
            st.write(f"❌ Folder '{folder_name}' not found under '{parent_id}'")
            return None
        parent_id = folders[0]['id']

    return parent_id

def find_file_in_folder(service, file_name, folder_id):
    """
    Returns file info (id, name, webViewLink) if the file exists in the folder.
    """
    query = f"name = '{file_name}' and '{folder_id}' in parents and trashed = false"
    response = service.files().list(
        q=query,
        fields="files(id, name, webViewLink)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()
    files = response.get('files', [])
    return files[0] if files else None


    # if folders:
    #     for folder in folders:
    #         st.write(f"✅ Folder: {folder['name']} — ID: {folder['id']}")
    #         st.write(f"   Shared: {folder.get('shared', False)}")
    #         st.write(f"   Parents: {folder.get('parents', [])}")
    # else:
    #     st.write(f"❌ No folder named '{target_name}' found.")

def search_folder_by_name(service, folder_name):
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(
        q=query,
        fields="files(id, name, parents)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    folders = response.get("files", [])
    if not folders:
        st.write(f"❌ No folders named '{folder_name}' found.")
    else:
        st.write(f"📁 Found {len(folders)} folders named '{folder_name}':")
        for f in folders:
            st.write(f"🔹 {f['name']} — ID: {f['id']}")
            st.write(f"   Parents: {f.get('parents', [])}")

def download_binary_file(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
    fh.seek(0)
    return fh

def hdr_to_df(header):

    key_list = list(header.keys())
    comments_list = header.comments

    df = DataFrame(index=key_list, columns=['Value', 'Comment']).fillna('')
    for idx in df.index:
        df.loc[idx, 'Value'] = header.get(idx, '')
        df.loc[idx, 'Comment'] = comments_list[idx]

    return df