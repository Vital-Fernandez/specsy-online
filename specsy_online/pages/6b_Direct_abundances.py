import streamlit as st
from streamlit import session_state as sstate
from specsy_online.utils.input_output import load_emiss_dataset
from specsy_online.utils.operations import structure_manager
from specsy_online.utils.formatting import REGION_LABELS, COLUMNS_STRUCT
from specsy_online.utils.interfaces import ionization_structure_interface, sampler_cfg_widget, make_sampling_callback, prior_configuration_widget
from specsy_online.utils.plots import trace_diagnostics_plots
from specsy import Nebula, cfg as specsy_cfg
from arviz import summary



def excluded_lines(df, struct_dict):

    valid_species, rejected_lines = [], []

    for idx, label in enumerate(REGION_LABELS[st.session_state['n_regions']]):
        valid_species += struct_dict['region'][f'r{idx}']['species']
        rejected_lines += struct_dict.get(f"region_{label}_exclude", [])

    idcs = df.particle.isin(valid_species) & ~df.index.isin(rejected_lines)

    return df.loc[idcs]

# Header
st.header("Multi-region direct method fitting")
st.write('You may use the widgets below to design the ionization structure and assign species to different regions. '
         'The current model version cannot manage merged lines. By default all the temperatures and densities are free '
         'parameters unless linked to other regions. You can also load the structure table from a tabulated file.')

# Check available data
if sstate.get('lines_df') is None:
    st.warning('No line measurements provided')

else:

    lines_df = sstate['lines_df']

    # Data preparation region
    with st.container(border=True):

        tab_NebStruc, tab_Priors, tab3 = st.tabs(["Ionization structure", "Priors", "Load model"])

        # Configure the regions temperature/density
        with tab_NebStruc:
            ionization_structure_interface(obs_df=lines_df)

        with tab_Priors:
            prior_cfg = prior_configuration_widget(specsy_cfg['direct_method_priors'],
                                                   REGION_LABELS[sstate["n_regions"]])

        # Prepare model data
        if st.button("Prepare model"):

            # Clear previous values
            sstate['nebula'] = None
            sstate['structure_dict'] = None
            sstate['trace'] = None

            # Prepare the model data
            st_warnings = structure_manager(REGION_LABELS, lines_df, norm_line='H1_4861A')
            if st_warnings is None:

                # Generate the object
                obj = Nebula.from_lines_frame(excluded_lines(lines_df, sstate['structure_dict']), sstate['structure_dict'])
                obj.infer.direct_method.prepare_inputs(emissivity_source=load_emiss_dataset(), prior_cfg=prior_cfg,
                                                       normalize_flux=sstate['norm_check'],
                                                       review_model=False, kinematic_component=sstate['kinem_order_specsy'])

                # Check the data is valid
                message = obj.infer.direct_method._review_inputs(return_message=True)

                if len(message) == 0:
                    sstate['nebula'] = obj
                    sstate['trace'] = None
                else:
                    sstate['nebula'] = None
                    sstate['trace'] = None
                    sstate['structure_dict'] = None
                    msg = '\n- '.join(message)
                    st.warning(f'Issue with lines data:\n\n- {msg}')

            else:
                msg = '\n- '.join(st_warnings)
                sstate['structure_dict'] = None
                st.warning(f'Issue defining the region structure:\n\n- {msg}')

    # Run the model
    if sstate.get('nebula') is not None:

        st.subheader('Run sampler')
        st.markdown('The line data is ready fit the model. You may use the widgets below to adjust the sampler '
                    'parameters')

        with st.form('specsy_sampler', border=True, enter_to_submit=False, clear_on_submit=False):

            # Display the data
            st.dataframe(sstate['nebula'].infer.direct_method.lines_structure, column_order=COLUMNS_STRUCT)

            # Sampler configuration
            sampler_cfg_widget()

            if st.form_submit_button("Run sampler"):

                # Run the sampler
                sstate['trace'] = None
                make_sampling_callback()

                # Save the trace
                sstate['trace'] = sstate['nebula'].infer.direct_method.trace


    if sstate.get('trace') is not None:

        st.subheader('Results')
        st.markdown('The sampling finished, please check that the sampler converged (You '
                    'may need to see the terminal outputs). You can download the input lines structure and output '
                    'measurements as text files.')

        tab_inputs, tab_outputs, _ = st.columns([0.1, 0.2, 0.7], gap='xxsmall')
        with tab_inputs:
            # Ready for download
            if sstate.get('id') is not None:
                table_name = sstate['id'].replace('.fits', "") + f'_ionization_structure.txt'
            else:
                table_name  = 'ionization_structure.txt'
            st.download_button(label='Download inputs', data=sstate['nebula'].infer.direct_method.lines_structure.to_string().encode('UTF-8'),
                               file_name=table_name)

        with tab_outputs:
            # Ready for download
            if sstate.get('id') is not None:
                table_name = sstate['id'].replace('.fits', "") + f'_specsy_measurements.txt'
            else:
                table_name  = 'specsy_measurements.txt'
            st.download_button(label='Download outputs', data=summary(sstate['trace']).to_string().encode('UTF-8'),
                               file_name=table_name)

        trace_diagnostics_plots(sstate['trace'])


# if sstate.get('structure_dict'):
#     st.json(sstate['structure_dict'])
#
# # ── Summary / output ──────────────────────────────────────────────────────────
# st.markdown("---")
# with st.expander("Current configuration (session state)", expanded=False):
#     summary = {}
#     for label in REGION_LABELS[st.session_state['n_regions']]:
#         summary[label] = {
#             "particles":        st.session_state.get(f"region_{label}_particles", []),
#             "exclude_lines":    st.session_state.get(f"region_{label}_exclude", []),
#             "temp_mode":        st.session_state.get(f"region_{label}_temp_mode"),
#             "den_mode":         st.session_state.get(f"region_{label}_den_mode"),
#             "temp_tied_to":     st.session_state.get(f"region_{label}_temp_tied_to"),
#             "den_tied_to":      st.session_state.get(f"region_{label}_den_tied_to"),
#             "temp_eq":          st.session_state.get(f"region_{label}_temp_relation"),
#             "den_eq":           st.session_state.get(f"region_{label}_den_relation"),
#         }
#     st.json(summary)