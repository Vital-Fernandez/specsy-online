import streamlit as st
from streamlit import session_state as s_state, secrets

from utils.sidebar import sidebar_widgets
from utils.interfaces import  SURVEY_LIST
from utils.input_output import set_survey_user
from pages.collaborations.capers import survey_selection
from pages.collaborations.stsci import lyc_cos_selection
from streamlit_authenticator import Authenticate

# Page configuration
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Authenticate the user
authenticator = Authenticate(secrets.collaborations.credentials.to_dict(),
                             cookie_name=secrets.cookie.name,
                             cookie_key=secrets.cookie.key,
                             cookie_expiry_days=secrets.cookie.expiry_days)

if s_state.get('authentication_status'):
    authenticator.logout(button_name='Collaboration logout', location='sidebar')

# Sidebar information
sidebar_widgets()

# Selection screen for sample
st.title(f'Virtual observatory')
st.space()
st.write("You may select a survey from the selection box below. Please note that some research projects may require "
         "authentication — please contact the project's Principal Investigator (P.I.) for access.")
col_A, col_B = st.columns([0.25, 0.75], gap='large')
st.space()

# Select the survey
with col_A:
    index = 0 if st.session_state.get('survey_selection') is None else SURVEY_LIST.index(st.session_state['survey_selection'])
    survey = st.selectbox('Survey selection', options=SURVEY_LIST, index=index, key='survey_selection',
                          on_change=set_survey_user, args=('survey_selection', authenticator))

match survey:

    case 'CEERS':
        survey_selection(survey.lower())

    case 'CAPERS':
        authenticator.login(location='main', fields={'Form name': 'CAPERS'})
        if s_state.get('authentication_status'):
            if st.session_state.get("name") == 'capers':
                survey_selection(survey.lower())
            else:
                st.write(f'Incorrect credentials for {survey} sample. Please logout or change survey selection.')

    case 'PID17515':
        authenticator.login(location='main', fields={'Form name': 'Login LyC leakers (COS)'})
        if s_state.get('authentication_status'):
            if st.session_state.get("name") == 'PID17515':
                lyc_cos_selection()
            else:
                st.write(f'Incorrect credentials for {survey} sample. Please logout or change survey selection.')

    case _:
        st.write('Project is not recognized')

