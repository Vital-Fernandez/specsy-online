import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.plots import bokeh_spectrum

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Components detection')
st.markdown(f'Using the menus below, you can apply the ASPECT algorithm (alpha release) to detect spectral features')

# Check file has been uploaded
if s_state['spec'] is not None:

    with st.form('aspect_form', border=False, enter_to_submit=False, clear_on_submit=False):

        spec = s_state['spec']

        col1, col2 = st.columns([0.4, 0.5], gap='large')

        with col1:
            aspect_algorithm = st.selectbox("Algorithm", ("12_pixels_v6"))

        with col2:
            st.write("")
            st.write("")
            msg = 'The white-noise labels from the treatment'
            exclude_check = st.toggle('Exclude white-noise', value=False, help=msg)

        # Every form must have a submit button.
        submitted = st.form_submit_button("Run model")

        # Load the dataframe
        if submitted:
            spec.infer.components(exclude_continuum=exclude_check)

        # Show the plot
    st.write('***')
    if spec.infer.pred_arr is not None:
        bokeh_spectrum('spec', default_components=True, default_show_fits=False)

else:
    st.markdown(f'Please load an observation.')

