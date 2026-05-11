import streamlit as st
from streamlit import session_state as s_state

from specsy_online.utils.input_output import save_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.plots import bokeh_spectrum
from aspect.io import _MODEL_FOLDER, cfg as aspect_cfg
from aspect.workflow import model_mgr, ModelManager


@st.cache_data()
def load_ml_model(model_name, n_cores):
    fname = aspect_cfg['models'][model_name]
    return ModelManager(_MODEL_FOLDER / fname, n_cores)


# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Components detection')
st.markdown(f'Using the menus below, you can apply the ASPECT algorithm (alpha release) to detect spectral features')

# Check file has been uploaded
if s_state['spec'] is not None:

    spec = s_state['spec']
    with st.container():

        col1, col2, col3 = st.columns([0.3, 0.3, 0.3], gap='large')

        with col1:
            model_key = st.selectbox(label="Algorithm", key='algorithm_select',
                                     options=("classifier_v10_RF", "classifier_v12_RF", "classifier_v12_MLP"))

        with col2:
            n_cores = st.number_input(label="Number of CPU cores", min_value=1, value=min(4, s_state['n_max_cores']), step=1,
                      max_value=s_state['n_max_cores'], help=f"Number of cores (4 recommended for offline individual spectra)")

        with col3:
            st.space(20)
            exclude_check = st.toggle('Exclude white-noise', value=False, help='Ignore white-noise pixels')

        # Rim the model
        if st.button("Run model"):

            # Reload the model
            spec.infer.model_mgr = load_ml_model(model_key, n_cores)

            # Clear previous data
            spec.infer.pred_arr = None
            spec.infer.conf_arr = None

            # Check if model has changed
            spec.infer.components(exclude_continuum=exclude_check)

            # Save the spec
            save_state('spec', spec)

    # Show the plot
    st.write('***')
    if spec.infer.pred_arr is not None:
        bokeh_spectrum('spec', default_components=True, default_show_fits=False)

else:
    st.markdown(f'Please load an observation.')

