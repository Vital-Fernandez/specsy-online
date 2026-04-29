import streamlit as st
import specsy as sy
from numpy import argsort
from utils.sidebar import sidebar_widgets
from utils.input_output import EXTINCTION_LAWS, widget_save_state, LOW_DIAGS, HIGH_DIAGS
from utils.plots import specy_infer_plotting
from pathlib import Path
from streamlit import session_state as s_state


# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Direct abundances')

# Read the emissivities
LOCAL_FOLDER = Path(__file__).parent.parent

if s_state['spec'] is not None:

    spec = s_state['spec']
    if spec.frame.index.size > 0:

        emiss_dataset = s_state['emiss_dataset']
        if emiss_dataset is not None:

            st.markdown(f'### Model parameters:')

            # Get indices that would sort the 'Surname' column
            st.markdown("***")
            df = s_state['spec'].frame
            sorted_indices = argsort(df['particle'])
            sorted_particles = df.index[sorted_indices].tolist()
            line_list = st.multiselect("Select lines for analysis", options=sorted_particles, key='particle_list',
                                            on_change=widget_save_state, args=("particle_list",))

            # Get extinction
            col_redcor, col_rv = st.columns([0.7, 0.3], gap='large')

            with col_redcor:
                extinction = st.selectbox('Extinction law', EXTINCTION_LAWS, key='redcorr',
                                          on_change=widget_save_state, args=("redcorr",))
            with col_rv:
                Rv = st.number_input(r"$R_{V}$", key='Rv', on_change=widget_save_state, args=("Rv",))

            # Get extinction
            col_lowIonization, col_highIonization = st.columns([0.5, 0.5], gap='large')

            with col_lowIonization:
                low_diag = st.selectbox('Low temperature diagnostic', LOW_DIAGS, key='low_diag',
                                          on_change=widget_save_state, args=("low_diag",))

            with col_highIonization:
                high_diag = st.selectbox('High temperature diagnostic', HIGH_DIAGS, key='high_diag',
                                          on_change=widget_save_state, args=("high_diag",))

            col_technique, col_nada = st.columns([0.3, 0.7], gap='large')

            with col_technique:
                approx_list = ['rgi', 'eqn', 'nn']
                technique_label = st.selectbox('Select approximation', approx_list, key='tech_selection2')

            # Run the model
            submitted = st.button("Fit model", key='button_dm')

            # Launch the fitting
            if submitted:

                output_file = LOCAL_FOLDER / 'results' / 'SHOC579_infer_db.nc'

                spec_cfg = None
                st.dataframe(spec.frame.loc[line_list])
                obj = sy.Nebula.from_lines_frame(spec.frame.loc[line_list], spec_cfg)

                # Generate the chemical model
                obj.infer.direct_method.prepare_inputs(emissivity_source=emiss_dataset, norm_list='H1_4861A',
                                                       normalize_flux=False,
                                                       prior_cfg=spec_cfg.get('direct_method_priors'))

                with st.spinner('Fitting model'):
                    obj.save(output_file)

                st.write('Sampling finished')
                if output_file.is_file():
                    st.markdown("***")
                    st.markdown(f'### Output plots:')

                    tab_traces, tab_flux, tab_matrix = st.tabs(['Traces', 'Flux posteriors', 'Scatter matrix'])

                    with tab_traces:
                        specy_infer_plotting(output_file, 'traces')

                    with tab_flux:
                        specy_infer_plotting(output_file, 'flux')

                    with tab_matrix:
                        specy_infer_plotting(output_file, 'matrix')

        else:
            st.markdown("***")
            st.markdown(f'### Please upload the emissivity grids')

    else:
        st.markdown("***")
        st.markdown(f'### Please declare a spectrum and fit its lines')

else:
    st.markdown("***")
    st.markdown(f'### Please declare a spectrum and fit its lines')