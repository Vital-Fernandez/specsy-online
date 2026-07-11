import streamlit as st
from streamlit import session_state as s_state, secrets

from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.input_output import check_secrets, get_authenticator, clear_obj_data
from specsy_online.pages.collaborations.stsci import lyc_cos_selection
from specsy_online.pages.collaborations.observatory_tools import survey_selection, set_survey_user, SURVEY_LIST, authenticated_survey


# Page configuration
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Sidebar information
sidebar_widgets()

# Selection screen for sample
st.title(f'Virtual observatory')
st.space()

# Authenticate the user
if check_secrets() and st.secrets.get('collaborations', False):

    st.write("You may select a survey from the selection box below. Please note that some research projects may require "
             "authentication — please contact the project's Principal Investigator (P.I.) for access.")

    # Authenticate the user
    authenticator = get_authenticator()
    if s_state.get('authentication_status'):
        authenticator.logout(button_name='Collaboration logout', location='sidebar', callback=clear_obj_data)

    # Select the survey
    col_A, col_B = st.columns([0.25, 0.75], gap='large')
    st.space()

    with col_A:
        survey_hold = s_state.get('survey_selection_hold')
        index = 0 if survey_hold is None else SURVEY_LIST.index(survey_hold)
        survey = st.selectbox('Survey selection', options=SURVEY_LIST, index=index, key='survey_selection',
                              on_change=set_survey_user, args=('survey_selection', authenticator))

    # Survey section
    match survey:

        case 'CEERS':
            survey_selection(survey.lower())

        case 'CAPERS':
            authenticated_survey(authenticator, survey, 'CAPERS', 'capers',
                                 lambda: survey_selection(survey.lower()))

        case 'LzLCS_MIRI':
            authenticated_survey(authenticator, survey, 'LzLCS MIRI', 'lzlcs_miri',
                                 lambda: survey_selection(survey.lower()))

        case 'PID17515':
            authenticated_survey(authenticator, survey, 'Login LyC leakers (COS)', 'PID17515',
                                 lyc_cos_selection)
        case _:
            st.write('Project is not recognized')
else:
    st.warning('This installation does not have have access to the collaborations database. Please try the online version '
               'at [https://specsy.streamlit.app/](https://specsy.streamlit.app/)')
