import streamlit as st
from streamlit import session_state as s_state
from .io import set_defaults


def sidebar_widgets():

    # Default key values
    set_defaults()

    # Adjust the sidebar to the sample
    with st.sidebar:

        # Show the spectrum
        if s_state['spec'] != 'No':
            st.write(f'Input spectrum:')
            st.write(f'{s_state["spec"].label}')

        # Show the spectrum
        if s_state['redshift'] is not None:
            st.write(f'Redshift:')
            st.write(f'{s_state["spec"].redshift:0.3f}')
