import streamlit as st

# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0a_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1a_Load_spectrum.py", title="Load spectrum"),
                                    st.Page("pages/1b_Load_collaboration.py", title="Virtual observatory")],

             "Aspect": [st.Page("pages/2a_Components_detection.py", title="Components detection")],

             "Continuum": [st.Page("pages/3a_continuum_fitting.py", title="Polynomial fitting")],

             "LiMe":    [st.Page("pages/4a_line_bands.py", title="Bands"),
                         st.Page("pages/4b_Line_fitting.py", title="Fitting"), ],

             "Diagnostics": [st.Page("pages/5a_Extinction.py", title="Gas extinction")],

             "SpecSy": [st.Page("pages/6a_Load_data_grids.py", title="Emissivity grids"),
                        st.Page("pages/6b_Direct_abundances.py", title="Direct method"),
                        st.Page("pages/6c_Photo-ionization_modelling.py", title="Photoionization models"), ], }

    pg = st.navigation(pages)
    pg.run()

    return


def review_bounds():

    idx2, idx3 = st.session_state.central

    # Update lower limit
    idx0, idx1 = st.session_state.lower
    if idx1 > idx2:
        idx1 = idx2 - 2
        if idx0 > idx1:
            idx0 = idx1 - 2
        st.session_state.lower = (idx0, idx1)

    # Update upper
    idx4, idx5 = st.session_state.upper
    if idx3 > idx4:
        idx4 = idx3 + 2
        if idx4 > idx5:
            idx5 = idx4 + 2
        st.session_state.upper = (idx4, idx5)

    return


if __name__ == "__main__":

    run()


#     # import streamlit as st
#     # from google.oauth2 import service_account
#     # from googleapiclient.discovery import build
#     #
#     # creds = service_account.Credentials.from_service_account_info(
#     #         st.secrets["connections"]['capers'], scopes=["https://www.googleapis.com/auth/drive.readonly"])
#     # drive_service = build("drive", "v3", credentials=creds)
#     #
#     # stscifolder_id = "1waRVtgElXjqkDfi_4P8VDpVzgswzDKtj"
#     #
#     # results = drive_service.files().list(
#     #     q=f"'{stscifolder_id}' in parents",
#     #     fields="files(id, name, mimeType)",
#     #     pageSize=100,
#     #     supportsAllDrives=True,
#     #     includeItemsFromAllDrives=True
#     # ).execute()
#     #
#     # items = results.get("files", [])
#     # st.write(f"Contents of STScI folder ({stscifolder_id}):")
#     # for item in items:
#     #     st.write(f"{item['name']} ({item['id']}) — {item['mimeType']}")
#     #
#     # # Load credentials from secrets
#     # creds = service_account.Credentials.from_service_account_info(
#     #         st.secrets["connections"]['capers'], scopes=["https://www.googleapis.com/auth/drive.readonly"])
#     #
#     # # Build the Drive API client
#     # drive_service = build("drive", "v3", credentials=creds)
#     #
#     # results = drive_service.files().list(
#     #     pageSize=10,
#     #     fields="files(id, name, parents)"
#     # ).execute()
#     #
#     # items = results.get("files", [])
#     #
#     # for item in items:
#     #     st.write(f"{item['name']} ({item['id']}) → Parents: {item.get('parents')}")
#     #
#     # st.write('The drives')
#     # drives = drive_service.drives().list(pageSize=10).execute()
#     # for d in drives.get("drives", []):
#     #     st.write(f"AQUI: Shared Drive: {d['name']} ({d['id']})")
#     #
#     # # Example: list 10 files
#     # results = drive_service.files().list( pageSize=10, fields="files(id, name)").execute()
#     # items = results.get("files", [])
#     #
#     # st.write("Files available:")
#     # for item in items:
#     #     st.write(f"{item['name']} ({item['id']})")
#     #
#     # # Try method A: use alias "root"
#     # root_id = "root"
#     # st.write(f"Using root alias: {root_id}")
#     #
#     # # Try method C: try files.get("root") to get actual id
#     # try:
#     #     root_resp = drive_service.files().get(fileId="root", fields="id").execute()
#     #     root_id_real = root_resp.get("id")
#     #     st.write(f"Root real ID from files.get('root'): {root_id_real}")
#     # except Exception as e:
#     #     st.write(f"Error getting real root ID: {e}")
#     #
#     # # List folders under root or alias
#     # query = f"'{root_id}' in parents and mimeType = 'application/vnd.google-apps.folder'"
#     # results = drive_service.files().list(
#     #     q=query,
#     #     fields="files(id, name)",
#     #     pageSize=100,
#     #     supportsAllDrives=True,
#     #     includeItemsFromAllDrives=True,
#     # ).execute()
#     #
#     # folders = results.get("files", [])
#     # if not folders:
#     #     st.write("No folders found under the root alias.")
#     # else:
#     #     st.write("Folders accessible under root:")
#     #     for f in folders:
#     #         st.write(f"{f['name']} ({f['id']})")
#
#
#
#
# # import streamlit as st
# # from bokeh.plotting import figure
# # from streamlit_bokeh import streamlit_bokeh
# #
# # st.write('Hi')
# #
# # # Sample Data
# # x = [1, 2, 3, 4, 5]
# # y = [2, 4, 8, 16, 32]
# #
# # # Create Plot
# # p = figure(title="Exponential Growth", x_axis_label="x", y_axis_label="y")
# # p.line(x, y, legend_label="Growth", line_width=3, color="green")
# #
# # # Display in Streamlit
# # streamlit_bokeh(p, use_container_width=True, key="plot1")