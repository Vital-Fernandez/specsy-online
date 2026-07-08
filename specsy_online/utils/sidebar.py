import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.input_output import set_defaults, clear_inputs_button, restore_authentication

from multiprocessing import cpu_count
from platform import processor
from os import environ

def is_streamlit_cloud() -> bool:
    return (processor() == "" or environ.get("STREAMLIT_SHARING_MODE") is not None
            or environ.get("HOME") == "/home/appuser")


@st.cache_data()
def get_max_cores() -> int:
    if is_streamlit_cloud():
        return 2
    return cpu_count()


def sidebar_widgets():

    # Recover login from cookie on page changes
    restore_authentication()

    # Default key values
    set_defaults()

    s_state['n_max_cores'] = get_max_cores()

    # Adjust the sidebar to the sample
    with st.sidebar:

        # Show the spectrum
        if s_state['spec'] is not None:
            st.write(f'Input spectrum:')
            st.write(f'{s_state["spec"].label}')

        # Show the spectrum
        if s_state['redshift'] is not None:
            st.write(f'Redshift:')
            st.write(f'{s_state["spec"].redshift:0.3f}')

        # Clear option
        clear_inputs_button()
