import streamlit as st
from streamlit import session_state as s_state, secrets

from utils.sidebar import sidebar_widgets
from streamlit_authenticator import Authenticate
from pages.collaborations.capers import capers_selection

st.set_page_config(
    # page_title="Ex-stream-ly Cool App",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Collaborations virtual observatory')

# Authenticate the user
authenticator = Authenticate(secrets.collaborations.credentials.to_dict(),
                             cookie_name=secrets.cookie.name,
                             cookie_key=secrets.cookie.key,
                             cookie_expiry_days=secrets.cookie.expiry_days)
authenticator.login(location='main')

if not s_state.get('authentication_status'):
    st.write('Please login')

else:

    # CAPERs survey
    if st.session_state.get("name") == 'capers':
        capers_selection()

    # New cases
    else:
        st.write('Collaboration is not recognized')

    # Give the option to logout
    authenticator.logout(button_name='Collaboration logout', location='sidebar')


