import streamlit as st
import pandas as pd
import numpy as np
from utils.formatting import REGION_TAGS_STYLE, REGION_TAGS_COLORS, REGION_LABELS, card_formating



# Region cards
def get_taken_particles(current_region_idx: int) -> set:
    taken = set()
    for i, lbl in enumerate(region_labels):
        if i == current_region_idx:
            continue
        key = f"region_{lbl}_particles"
        taken.update(st.session_state.get(key, []))
    return taken

@st.cache_data
def load_demo_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    transitions = ["H1_4861A", "H1_6563A", "O2_3726A", "O2_3729A", "O3_4363A",
                    "O3_4959A", "O3_5007A", "S2_6717A", "S2_6731A", "S3_6312A",
                    "S3_9069A", "N2_6548A", "N2_6584A", "He1_5876A", "He2_4686A",
                    "Ar3_7136A", "Ar4_4711A", "Ar4_4740A", "Ne3_3869A", "Ne3_3968A",]
    particles = [t.split("_")[0] for t in transitions]
    fluxes    = rng.lognormal(mean=0.0, sigma=1.2, size=len(transitions)).round(4)
    return pd.DataFrame({"particle": particles, "flux": fluxes}, index=transitions)


TEM_DICT = {'eqT1': None, 'eqT2': None, 'eqT3': None, 'eqT4': None}
DEN_DICT = {'eqNe1': None, 'eqNe2': None, 'eqNe3': None, 'eqNe4': None}


# Formating for the labels
st.markdown(REGION_TAGS_STYLE, unsafe_allow_html=True)

obs_df = load_demo_data()
all_particles = sorted(obs_df["particle"].unique().tolist())

# Header
st.markdown("## Multi-Region direct method")
st.markdown("---")

# Number of regions selectbox
n_regions = st.selectbox(label="Number of regions", options=[1, 2, 3, 4], key="n_regions",
                         help="Changing the number of regions clears all widget state.")

# ── Session-state reset when n_regions changes ────────────────────────────────
_sentinel_key = f"__sentinel_{n_regions}__"
if _sentinel_key not in st.session_state:
    for k in list(st.session_state.keys()):
        if k.startswith("region_"):
            del st.session_state[k]
    st.session_state[_sentinel_key] = True

st.markdown("<br>", unsafe_allow_html=True)

region_labels = REGION_LABELS[n_regions]

# Loop through the regions and produce the widgets
cols = st.columns(n_regions, gap="medium")
for idx, (col, region_name) in enumerate(zip(cols, region_labels)):

    with col:

        # Region label
        st.markdown(card_formating(region_name), unsafe_allow_html=True)

        # Particle selection
        taken = get_taken_particles(idx)
        available_particles = [p for p in all_particles if p not in taken]
        sel_particles = st.multiselect(label="Species", options=available_particles, key=f"region_{region_name}_particles",
                                       help="Select the ionic species assigned to this region. Particles chosen here are"
                                            " removed from other regions.")

        # Line selection
        matching_lines = obs_df[obs_df["particle"].isin(sel_particles)].index.tolist() if sel_particles else []
        st.multiselect(label="Lines to exclude", options=matching_lines, default=[], key=f"region_{region_name}_exclude",
                       help="Lines selected here will be excluded from the fit. By default all matching lines are included.")

        # Temperature - density modes
        c3, c4 = st.columns(2)
        select_box_msg = "Tied to region or empirical relation ->"

        with c3:
            temp_mode = st.selectbox(label="Temperature mode", options=["free", "tied"],
                                     key=f"region_{region_name}_temp_mode")
            if temp_mode == "tied":
                options = REGION_LABELS[n_regions] + ['relation']
                options.remove(region_name)
                temp_tied_to = st.selectbox(label=select_box_msg, options=options,
                                            key=f"region_{region_name}_temp_tied_to")
                if temp_tied_to == 'relation':
                    st.selectbox(label="Temperature equation", options=list(TEM_DICT.keys()),
                                 key=f"region_{region_name}_temp_relation")

        with c4:
            den_mode = st.selectbox(label="Density mode", options=["free", "tied"],
                                    key=f"region_{region_name}_den_mode")
            if den_mode == "tied":
                options = REGION_LABELS[n_regions] + ['relation']
                options.remove(region_name)
                den_tied_to = st.selectbox(label=select_box_msg, options=options,
                                           key=f"region_{region_name}_den_tied_to")
                if den_tied_to == 'relation':
                    st.selectbox(label="Density equation", options=list(DEN_DICT.keys()),
                                 key=f"region_{region_name}_den_relation")

        st.markdown("</div>", unsafe_allow_html=True)

# ── Summary / output ──────────────────────────────────────────────────────────
st.markdown("---")
with st.expander("Current configuration (session state)", expanded=False):
    summary = {}
    for label in region_labels:
        summary[label] = {
            "particles":     st.session_state.get(f"region_{label}_particles", []),
            "exclude_lines": st.session_state.get(f"region_{label}_exclude", []),
            "temp_mode":     st.session_state.get(f"region_{label}_temp_mode"),
            "den_mode":      st.session_state.get(f"region_{label}_den_mode"),
            "temp_tied_to":  st.session_state.get(f"region_{label}_temp_tied_to"),
            "den_tied_to":   st.session_state.get(f"region_{label}_den_tied_to"),
            "temp_eq":       st.session_state.get(f"region_{label}_temp_relation"),
            "den_eq":        st.session_state.get(f"region_{label}_den_relation"),
        }
    st.json(summary)




# -------------------------------------------------------------------------------------

# import streamlit as st
#
# import lime
# import specsy as sy
# from numpy import argsort
# from utils.sidebar import sidebar_widgets
# from utils.input_output import EXTINCTION_LAWS, widget_save_state, LOW_DIAGS, HIGH_DIAGS
# from utils.plots import specy_infer_plotting
# from pathlib import Path
# from streamlit import session_state as s_state
#
#
# # Run the sidebar
# sidebar_widgets()
#
# # Page structure
# st.markdown(f'# Direct abundances')
#
# # Read the emissivities
# LOCAL_FOLDER = Path(__file__).parent.parent
#
# data_frame = '/home/vital/PycharmProjects/lime/examples/scripts/SHOC579_sdss_measurements.txt'
# df = lime.load_frame(data_frame)
# st.dataframe(df)
#
# if s_state['spec'] is not None:
#
#     spec = s_state['spec']
#     if spec.frame.index.size > 0:
#
#         emiss_dataset = s_state['emiss_dataset']
#         if emiss_dataset is not None:
#
#             st.markdown(f'### Model parameters:')
#
#             # Get indices that would sort the 'Surname' column
#             st.markdown("***")
#             df = s_state['spec'].frame
#             sorted_indices = argsort(df['particle'])
#             sorted_particles = df.index[sorted_indices].tolist()
#             line_list = st.multiselect("Select lines for analysis", options=sorted_particles, key='particle_list',
#                                             on_change=widget_save_state, args=("particle_list",))
#
#             # Get extinction
#             col_redcor, col_rv = st.columns([0.7, 0.3], gap='large')
#
#             with col_redcor:
#                 extinction = st.selectbox('Extinction law', EXTINCTION_LAWS, key='redcorr',
#                                           on_change=widget_save_state, args=("redcorr",))
#             with col_rv:
#                 Rv = st.number_input(r"$R_{V}$", key='Rv', on_change=widget_save_state, args=("Rv",))
#
#             # Get extinction
#             col_lowIonization, col_highIonization = st.columns([0.5, 0.5], gap='large')
#
#             with col_lowIonization:
#                 low_diag = st.selectbox('Low temperature diagnostic', LOW_DIAGS, key='low_diag',
#                                           on_change=widget_save_state, args=("low_diag",))
#
#             with col_highIonization:
#                 high_diag = st.selectbox('High temperature diagnostic', HIGH_DIAGS, key='high_diag',
#                                           on_change=widget_save_state, args=("high_diag",))
#
#             col_technique, col_nada = st.columns([0.3, 0.7], gap='large')
#
#             with col_technique:
#                 approx_list = ['rgi', 'eqn', 'nn']
#                 technique_label = st.selectbox('Select approximation', approx_list, key='tech_selection2')
#
#             # Run the model
#             submitted = st.button("Fit model", key='button_dm')
#
#             # Launch the fitting
#             if submitted:
#
#                 output_file = LOCAL_FOLDER / 'results' / 'SHOC579_infer_db.nc'
#
#                 spec_cfg = None
#                 st.dataframe(spec.frame.loc[line_list])
#                 obj = sy.Nebula.from_lines_frame(spec.frame.loc[line_list], spec_cfg)
#
#                 # Generate the chemical model
#                 obj.infer.direct_method.prepare_inputs(emissivity_source=emiss_dataset, norm_list='H1_4861A',
#                                                        normalize_flux=False,
#                                                        prior_cfg=spec_cfg.get('direct_method_priors'))
#
#                 with st.spinner('Fitting model'):
#                     obj.save(output_file)
#
#                 st.write('Sampling finished')
#                 if output_file.is_file():
#                     st.markdown("***")
#                     st.markdown(f'### Output plots:')
#
#                     tab_traces, tab_flux, tab_matrix = st.tabs(['Traces', 'Flux posteriors', 'Scatter matrix'])
#
#                     with tab_traces:
#                         specy_infer_plotting(output_file, 'traces')
#
#                     with tab_flux:
#                         specy_infer_plotting(output_file, 'flux')
#
#                     with tab_matrix:
#                         specy_infer_plotting(output_file, 'matrix')
#
#         else:
#             st.markdown("***")
#             st.markdown(f'### Please upload the emissivity grids')
#
#     else:
#         st.markdown("***")
#         st.markdown(f'### Please declare a spectrum and fit its lines')
#
# else:
#     st.markdown("***")
#     st.markdown(f'### Please declare a spectrum and fit its lines')