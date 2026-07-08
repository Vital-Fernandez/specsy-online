import streamlit as st
from streamlit import session_state as sstate
from specsy_online.utils.input_output import load_emiss_dataset, save_state
from specsy_online.utils.operations import structure_manager
from specsy_online.utils.formatting import REGION_LABELS, COLUMNS_STRUCT
from specsy_online.utils.interfaces import (ionization_structure_interface, sampler_cfg_widget, make_sampling_callback,
                                            prior_configuration_widget, extinction_parameters_dm)
from specsy_online.utils.plots import trace_diagnostics_plots
from specsy import Nebula, cfg as specsy_cfg
from arviz import summary
from lime import load_frame


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


with st.container(border=True):

    tab_NebStruc, tab_Priors, tab_extinct, tab_upload = st.tabs(["Ionization structure", "Priors", 'Extinction', "Load region structure"])

    # Configure the regions temperature/density
    with tab_NebStruc:
        if sstate.get('lines_df') is None:
            st.warning('No line measurements provided')
        else:
            ionization_structure_interface(obs_df=sstate['lines_df'])

    with tab_Priors:
        n_regions = sstate["n_regions"] if sstate.get('lines_df') is not None else 4
        prior_cfg = prior_configuration_widget(specsy_cfg['direct_method_priors'],
                                               REGION_LABELS[n_regions])
    with tab_extinct:
        extinction_parameters_dm()

    with tab_upload:
        uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

# Prepare model data
if st.button("Prepare model"):

    # Clear previous values
    sstate['nebula'] = None
    sstate['trace'] = None
    sstate['structure_dict'] = None

    if uploaded_file is None:
        st_warnings = structure_manager(REGION_LABELS, sstate.get('lines_df'), norm_line='H1_4861A')
    else:
        st.warning('Using input line structure file')
        save_state('lines_df', load_frame(uploaded_file))
        st_warnings = None

    if st_warnings is None:

        # Generate the object
        if uploaded_file is None:
            obj = Nebula.from_lines_frame(excluded_lines(sstate['lines_df'], sstate['structure_dict']), sstate['structure_dict'])
        else:
            obj = Nebula.from_structure_table(sstate['lines_df'])

        obj.infer.direct_method.prepare_inputs(emissivity_source=load_emiss_dataset(), prior_cfg=prior_cfg,
                                               normalize_flux=sstate['norm_check'],
                                               review_model=False,
                                               R_V=sstate['Rv_dm'],
                                               law=sstate['rLaw_dm'],
                                               norm_line=sstate['norm_line_dm'],
                                               kinematic_component=sstate.get('kinem_order_specsy', 0),
                                               exclude_merged=sstate['merged_toggle'])
        # st.write(sstate['merged_toggle'])
        # Check the data is valid
        message = obj.infer.direct_method._review_inputs(return_message=True)
        # message = []

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
        if sstate.get('id') is not None:
            table_name = sstate['id'].replace('.fits', "") + f'_ionization_structure.txt'
        else:
            table_name  = 'ionization_structure.txt'
        st.download_button(label='Download inputs', data=sstate['nebula'].infer.direct_method.lines_structure.to_string().encode('UTF-8'),
                           file_name=table_name)

    with tab_outputs:
        if sstate.get('id') is not None:
            table_name = sstate['id'].replace('.fits', "") + f'_specsy_measurements.txt'
        else:
            table_name  = 'specsy_measurements.txt'
        st.download_button(label='Download outputs', data=summary(sstate['trace']).to_string().encode('UTF-8'),
                           file_name=table_name)

    st.space('xsmall')
    trace_diagnostics_plots(sstate['trace'])
