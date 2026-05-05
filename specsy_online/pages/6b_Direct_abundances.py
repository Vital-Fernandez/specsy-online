import streamlit as st
from streamlit import session_state as sstate
from specsy_online.utils.operations import structure_manager
from specsy_online.utils.formatting import REGION_LABELS, COLUMNS_STRUCT
from specsy_online.utils.interfaces import ionization_structure_interface, sampler_cfg_widget, make_sampling_callback
from specsy_online.utils.plots import trace_diagnostics_plots
from specsy import Nebula
from arviz import from_netcdf
from lime import load_frame

# import numpyro
#
# # Number of cores available
# numpyro.set_host_device_count(8)
#
# import jax
#
# # Selecting CPU sampling with JAX
# jax.config.update("jax_platform_name", "cpu")
#
# import specsy as sy

@st.cache_resource
def load_trace(address):
    return from_netcdf(address)

# Header
st.markdown("## Multi-Region direct method")
st.markdown("---")

fname = '/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Tutorial/synthetic_spectrum_lines_region_v3.txt'
emis_name = '/home/vital/Dropbox/Astrophysics/Tools/SpectralSynthesis/Tutorial/emissivity_grids_pyneb_1.1.30.nc'
df = load_frame(fname)
df.drop(columns=['region', 'temp', 'den', 'eq_temp', 'eq_den'], inplace=True)

# Data preparation region
with st.container(border=True):

    tab1, tab2, tab3 = st.tabs(["Ionization structure", "Priors", "Load model"])

    # Configure the regions temperature/density
    with tab1:
        ionization_structure_interface(obs_df=df)

    # Prepare model data
    if st.button("Prepare model"):

        # Reset previous values
        sstate['nebula'] = None
        sstate['structure_dict'] = None
        sstate['trace'] = None

        # Prepare the model data
        structure_manager(REGION_LABELS)

        # Generate the object
        obj = Nebula.from_lines_frame(df, sstate['structure_dict'])
        obj.infer.direct_method.prepare_inputs(emissivity_source=emis_name, normalize_flux=False, review_model=False)

        # Check the data is valid
        message = obj.infer.direct_method._review_inputs(return_message=True)

        if len(message) == 0:
            sstate['nebula'] = obj
            sstate['trace'] = None

        else:
            sstate['nebula'] = None
            sstate['structure_dict'] = None
            sstate['trace'] = None
            st.warning(message)

# Run the model
if sstate.get('nebula') is not None:

    with st.form('specsy_sampler', border=True, enter_to_submit=False, clear_on_submit=False):

        # Display the data
        st.dataframe(sstate['nebula'].infer.direct_method.lines_structure, column_order=COLUMNS_STRUCT)

        # Sampler configuration
        sampler_cfg_widget()
        submitted = st.form_submit_button("Run sampler")

        if submitted:

            # Reset previous results
            sstate['trace'] = None

            # Run the sampler
            make_sampling_callback()

            # Save the trace
            sstate['trace'] = sstate['nebula'].infer.direct_method.trace


if sstate.get('trace') is not None:
    trace_diagnostics_plots(sstate['trace'])

if sstate.get('structure_dict'):
    st.json(sstate['structure_dict'])

# ── Summary / output ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("Current configuration (session state)", expanded=False):
    summary = {}
    for label in REGION_LABELS[st.session_state['n_regions']]:
        summary[label] = {
            "particles":        st.session_state.get(f"region_{label}_particles", []),
            "exclude_lines":    st.session_state.get(f"region_{label}_exclude", []),
            "temp_mode":        st.session_state.get(f"region_{label}_temp_mode"),
            "den_mode":         st.session_state.get(f"region_{label}_den_mode"),
            "temp_tied_to":     st.session_state.get(f"region_{label}_temp_tied_to"),
            "den_tied_to":      st.session_state.get(f"region_{label}_den_tied_to"),
            "temp_eq":          st.session_state.get(f"region_{label}_temp_relation"),
            "den_eq":           st.session_state.get(f"region_{label}_den_relation"),
        }
    st.json(summary)