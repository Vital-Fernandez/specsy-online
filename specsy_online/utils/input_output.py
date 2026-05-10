import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components

from streamlit import session_state as s_state, secrets
from streamlit_gsheets import GSheetsConnection


from os import cpu_count
from pathlib import Path
from contextlib import redirect_stdout
from importlib import metadata
from PIL import Image
from toml import loads
from pandas import DataFrame, isnull
from arviz import from_netcdf
from lime import load_frame, Spectrum, show_instrument_cfg, show_profile_parameters
from lime.io import parse_lime_cfg
from innate import DataSet, load_dataset
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO, StringIO
from numpy import array
from typing import Union, List, Dict
import base64
import json
import tomlkit


# Current path
LOCAL_FOLDER = Path(__file__).parent

# Resources
LOGO_PATH = LOCAL_FOLDER.parent/'resources/images/specsy_logo.PNG'

EXTINCTION_LAWS = ['G03 LMC', 'CCM89', 'CCM89 Bal07', 'CCM89 oD94', 'S79 H83 CCM89', 'K76', 'SM79 Gal',
                    'MCC99 FM90 LMC', 'F99-like', 'F99', 'F88 F99 LMC']

LOW_DIAGS = ['S3_6312A', 'Hagele_2006', 'S2_4069A']
HIGH_DIAGS = ['O3_4363A', 'Hagele_2006']

# Keys for the platform variables
DEFAULT_STATES = {'spec': None,
                  'id': None,
                  'redshift': None,
                  'bands_df': None,
                  'lines_df': None,
                  'fit_cfg': None,
                  'emiss_dataset': None,
                  'obs_type': None,
                  'redcorr': 'G03 LMC',
                  'Rv': 3.4,
                  'low_diag': 'Hagele_2006',
                  'high_diag': 'O3_4363A',
                  # 'survey_selection': None,

                  # Intermediate steps
                  "in_bands": None,

                  # CAPERs
                  "mpt_list": None,
                  "z_range": None,
                  "z_limits": None,
                  '2D_spectrum': None,
                  "line_selection": [],
                  # "sample_list": ['CAPERS-COSMOS_DR0.4', 'CAPERS-UDS_DR0.4', 'CAPERS-EGS_DR0.4'],
                  }

PACKAGES_dependencies = {
                        "LiMe": "lime-stable",
                        "Aspect": "aspect-stable",
                        "SpecSy": "specsy",
                        "SpecSy Online": "specsy_online",
                        "NumPy": "numpy",
                        "Astropy": "astropy",
                        "PyMC": "pymc",
                        "ArviZ": "arviz",
                        "Pandas": "pandas",
                        }

def set_defaults():

    for item, value in DEFAULT_STATES.items():
        if f'{item}_hold' not in s_state:
            s_state[f'{item}_hold'] = value
        s_state[item] = s_state[f'{item}_hold']

    return


def on_bands_edit():
    s_state['bands_df'] = st.session_state['edited_df']
    s_state[f'bands_df_hold'] = s_state['bands_df']
    st.success(f'Input change: {s_state['bands_df'].index.size}')
    return


def save_state(param, value):
    s_state[f'{param}'] = value
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


def widget_save_state(param):
    s_state[f'{param}_hold'] = s_state[f'{param}']

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


def clear_inputs_state(reset_defaults=True):

    s_state.clear()

    if reset_defaults:
        set_defaults()

    return


def clear_inputs_button():
    st.button('Clear input data', on_click=clear_inputs_state, icon=":material/delete:")
    return


def clear_obj_data():

    for item in ['spec', 'id', 'redshift', 'bands_df', 'lines_df']:
        s_state[item] = None
        s_state[f'{item}_hold'] = None

    return


def get_user_parameters(username: str, params: Union[str, List[str]]) -> Union[None, Dict[str, str], str]:

    """
    Retrieve one or more user-specific parameters from Streamlit secrets using the username.

    Parameters
    ----------
    username : str
        The key in `secrets.collaborations.credentials.usernames`.

    params : str or list of str
        One or more parameter names to retrieve.

    Returns
    -------
    dict or str or None
        - If one parameter is requested: returns a string or None.
        - If multiple parameters are requested: returns a dict {param: value}.
        - Returns None if username not found or secrets structure is invalid.

    """

    user_data = st.secrets.collaborations.credentials.usernames.get(username)
    if not user_data:
        return None

    if isinstance(params, str):
        return user_data.get(params)
    else:
        return {param: user_data.get(param) for param in params}


def parse_toml_input(toml_text):
    try:
        st.session_state.bands_cfg = dict(tomlkit.loads(toml_text))
        st.success("Configuration loaded successfully!")
    except tomlkit.exceptions.ParseError as e:
        st.error(f"Invalid TOML syntax: {e}")
    except Exception as e:
        st.error(f"Unexpected error parsing configuration: {e}")


def on_toml_change():
    toml_text = st.session_state[f"toml_input_{st.session_state.toml_area_key}"]
    if toml_text.strip() == "":
        st.session_state.bands_cfg = tomlkit.loads("[default_line_fitting]\n")
        st.session_state.toml_text = "[default_line_fitting]\n"
    else:
        try:
            cfg = tomlkit.loads(toml_text)
            if "default_line_fitting" not in cfg:
                cfg.add("default_line_fitting", tomlkit.table())
            st.session_state.bands_cfg = cfg
            st.session_state.toml_text = tomlkit.dumps(cfg)
        except tomlkit.exceptions.ParseError as e:
            st.error(f"Invalid TOML syntax: {e}")
        except Exception as e:
            st.error(f"Unexpected error parsing configuration: {e}")

@st.cache_resource
def read_collaboration_file_log(collaboration_name, idx_list):

    conn = st.connection(collaboration_name, type=GSheetsConnection)
    sheet_name = get_user_parameters(collaboration_name, 'file_sheet')
    df = conn.read(spreadsheet=sheet_name, ttl=None, index_col=idx_list, header=0, sep=',')
    df.index.names = idx_list

    return df


@st.cache_resource
def read_collaboration_flux_log(collaboration_name, index_list):

    conn = st.connection(collaboration_name, type=GSheetsConnection)
    sheet_name = get_user_parameters(collaboration_name, 'flux_sheet')
    df = conn.read(spreadsheet=sheet_name, ttl=None, index_col=index_list, header=0, sep=',')
    df.index.names = index_list

    return df


@st.cache_resource
def load_emiss_grids(fname):
    return load_dataset(fname, x_space=[9000, 20000, 251], y_space=[1, 600, 101])


@st.cache_data
def load_logo(file_address=LOGO_PATH):
    return Image.open(file_address)


@st.cache_data
def get_versions(packages: dict[str, str] | None = None) -> dict[str, str]:
    if packages is None:
        packages = PACKAGES_dependencies
    return {
        label: metadata.version(pkg)
        for label, pkg in packages.items()
    }

@st.cache_data
def get_sampler_backends() -> dict[str, str | None]:
    backends = ["nutpie", "pymc", "numba", "numpyro", "blackjax"]
    return {
        pkg: metadata.version(pkg)
        if metadata.packages_distributions().get(pkg)
        else None
        for pkg in backends
    }


@st.cache_data
def get_device_info() -> dict:
    info = {"cpu_cores": cpu_count()}

    try:
        import jax
        info["jax_backend"] = jax.default_backend()
        info["jax_devices"] = [str(d) for d in jax.devices()]
    except Exception:
        info["jax_backend"] = None

    try:
        import pytensor
        info["pytensor_device"] = pytensor.config.device
        info["pytensor_floatX"] = pytensor.config.floatX
    except Exception:
        info["pytensor_device"] = None

    try:
        from numba import cuda
        info["cuda_available"] = cuda.is_available()
    except Exception:
        info["cuda_available"] = False

    return info

@st.cache_data
def load_spectrum(input_file, instrument, redshift, norm_flux, units_wave_in=None, units_flux_in=None,
                  crop_waves=None, crop_flux=None, id_label=None, delimiter=None,
                  comments='#', skiprows=1, usecols=None, wave_units_out=None,
                  flux_units_out=None):


    # Unit conversion if necessary
    spec_params = {'redshift': None if (redshift is None or redshift == '' or isnull(redshift)) else float(redshift),
                   'id_label': None if id_label is None or id_label == '' else id_label,
                   'norm_flux': None if norm_flux is None else float(norm_flux),
                   'units_wave': units_wave_in,
                   'units_flux': units_flux_in,
                   'crop_waves': crop_waves,
                   'crop_flux': crop_flux,
                   'delimiter': delimiter,
                   'comments': comments,
                   'skiprows': skiprows,
                   'usecols': usecols if usecols is None else array(usecols.replace(" ","").split(',')).astype(int)}

    if norm_flux is not None and redshift != '' :
        spec_params['norm_flux'] = float(norm_flux)

    # For observations which provide redshift
    if instrument in ['SDSS']:
        spec_params.pop('redshift')

    # Load the object
    spec = Spectrum.from_file(input_file, instrument, **spec_params)

    if (wave_units_out is not None) and (flux_units_out is not None):
        if spec.units_flux.physical_type != 'dimensionless':
            spec.unit_conversion(wave_units_out, flux_units_out)
        else:
            st.warning(f'The spectrum has dimensionless flux units. No conversion was applied.')

    return spec


@st.cache_data
def load_infer_data(file_address):
    return load_dataset(file_address)


@st.cache_data
def get_instrument_cfg() -> dict[str, DataFrame]:
    """Capture lime.show_instrument_cfg() output and parse into DataFrames per type."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        show_instrument_cfg()

    sections, current_label, current_rows = {}, None, []
    for line in buffer.getvalue().splitlines():
        if line.endswith(":"):
            if current_label:
                sections[current_label] = current_rows
            current_label, current_rows = line.rstrip(":"), []
        elif line.strip() and current_label:
            parts = line.split("\t")
            idx, name = parts[0].strip(), parts[1].strip()
            fields = {k.strip(): v.strip() for k, v in (f.split(":") for f in parts[2:])}
            current_rows.append({"name": name, **fields})
    if current_label:
        sections[current_label] = current_rows

    return {label: DataFrame(rows) for label, rows in sections.items()}

@st.cache_data
def load_emiss_dataset():
    return load_dataset(LOCAL_FOLDER.parent/f'resources/data/emissivity_grids_pyneb_1.1.30.nc')


def parse_line_bands_df(uploaded_object):
    return load_frame(uploaded_object)


def parse_emiss_dataset(uploaded_object):
    return DataSet.from_file(uploaded_object)


@st.cache_data
def parse_fit_cfg(conf_string):
    dict_toml = loads(conf_string)
    return parse_lime_cfg(dict_toml)


# @st.cache_data
# def parse_frame_normalization(df):
#     return load_frame_sy(df, flux_type='profile', norm_line='H1_4861A')


@st.cache_data
def get_text_spectrum(spec_key):
    recarray = s_state[spec_key].save_spectrum()
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

@st.cache_data
def widget_text_to_list(str_list, id_types=int):

    if str_list is not None:
        output = str_list.replace('\n', '')
        output = output.replace(' ', '')
        output = array(output.split(',')).astype(id_types)
    else:
        output = None

    return output


@st.cache_data
def save_edited_bands(data_frame, key):

    df_hold = data_frame.copy()
    df_hold = df_hold.set_index('label')
    df_hold.index.name = None
    st.session_state[f'{key}_hold'] = df_hold

    return


def save_objSample(param):
    s_state[f'{param}_hold'] = s_state[f'{param}']

    return


@st.cache_resource
def gdrive_service(collab):

    service = build(serviceName='drive',
                    version='v3',
                    credentials=Credentials.from_service_account_info(secrets.connections.capers.to_dict(),
                                                                      scopes=['https://www.googleapis.com/auth/drive']))

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
            st.write(f'Hay {path_parts}')
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
            st.write(f"❌ File ({path_parts[-1]}) not found in the target folder ({parent_id}).")
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


def search_folder_by_name(service, folder_name):

    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    response = service.files().list(q=query, fields="files(id, name, parents)",
                                    supportsAllDrives=True, includeItemsFromAllDrives=True).execute()

    folders = response.get("files", [])
    if not folders:
        st.write(f"❌ No folders named '{folder_name}' found.")
    else:
        st.write(f"📁 Found {len(folders)} folders named '{folder_name}':")
        for f in folders:
            st.write(f"🔹 {f['name']} — ID: {f['id']}")
            st.write(f"   Parents: {f.get('parents', [])}")


def download_binary_file(service, file_id):
    # First: get metadata about the file
    file_metadata = service.files().get(fileId=file_id, fields="id, name, owners").execute()

    # # Owners info is a list of dicts
    # owners = file_metadata.get("owners", [])
    # if owners:
    #     for owner in owners:
    #         st.write(f"Owner: {owner.get('displayName')} ({owner.get('emailAddress')})")
    # else:
    #     st.write("No owner info available")

    # Then: download the content
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


def download_button(download_filename, object_to_download):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    """

    # File type
    if isinstance(object_to_download, DataFrame):
        object_to_download = object_to_download.to_string()
        object_to_download = object_to_download.encode('UTF-8')
    else:
        object_to_download = json.dumps(object_to_download)

    # Conversion
    try:
        b64 = base64.b64encode(object_to_download.encode()).decode()
    except AttributeError as e:
        b64 = base64.b64encode(object_to_download).decode()

    dl_link =   f"""
                <html>
                <head>
                <title>Start Auto Download file</title>
                <script src="http://code.jquery.com/jquery-3.2.1.min.js"></script>
                <script>
                $('<a href="data:text/csv;base64,{b64}" download="{download_filename}">')[0].click()
                </script>
                </head>
                </html>
                """

    return dl_link


def download_component(filename, df):
    components.html(download_button(filename, df), height=0)


def download_frame_form(fname, variable, button_label='Download', key_widget="Frame_download_form"):

    with st.form(key_widget, border=False):
        st.form_submit_button(button_label, on_click=download_component, args=(fname, variable))

    return


