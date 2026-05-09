import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.plots import bokeh_spectrum
import aspect
from aspect.io import _MODEL_FOLDER
from aspect.workflow import model_mgr, ModelManager

def load_ml_model():

    match st.session_state['algorithm_select']:
        case '12_pixels_v10_RF':
            fname = 'aspect_min-max-log_12_pixels_v10_model.joblib'
        case '12_pixels_v12_RF':
            fname = 'aspect_min-max-log_12_pixels_v12_randomforest_model.joblib'
        case _:
            fname = None

    # Load the model
    if fname is not None:
        model_mgr = ModelManager(_MODEL_FOLDER/fname)

    else:
        st.error('Model is not recognized')

    return



# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Components detection')
st.markdown(f'Using the menus below, you can apply the ASPECT algorithm (alpha release) to detect spectral features')

# Check file has been uploaded
if s_state['spec'] is not None:
    st.write(aspect.__version__)
    st.write(model_mgr.model_address)
    with st.container():

        spec = s_state['spec']

        col1, col2 = st.columns([0.4, 0.5], gap='large')

        with col1:
            aspect_algorithm = st.selectbox(label="Algorithm", options=("12_pixels_v10_RF", "12_pixels_v12_RF"),
                                            key='algorithm_select', on_change=load_ml_model)

        with col2:
            st.write("")
            st.write("")
            msg = 'The white-noise labels from the treatment'
            exclude_check = st.toggle('Exclude white-noise', value=False, help=msg)

        # Rim the model
        if st.button("Run model"):

            # Check if model has changed
            spec.infer.components(exclude_continuum=exclude_check)

            # Show the plot
            st.write('***')
            if spec.infer.pred_arr is not None:
                bokeh_spectrum('spec', default_components=True, default_show_fits=False)

else:
    st.markdown(f'Please load an observation.')

