import streamlit as st
from streamlit import session_state as sstate
from .plots import lime_spec_plotting
from .input_output import save_state


def compute_redshift(spec):

    # Toggle to launch the redshift fitting
    label, help = 'Fit redshift', 'Infer the presence of lines and measure the redshift'
    on = st.button(label, help=help)

    if on:
        spec.infer.bands()
        z_fit = spec.infer.redshift(detection_bands='line_2d_pred')
        save_state('redshift', z_fit)
        spec.update_redshift(z_fit)
        save_state('spec', spec)
        lime_spec_plotting(spec, detection_band='line_2d_pred', rest_frame=True)
        st.write(f'Fitted redshift: z={z_fit:0.3f}')

    else:
        st.write('No redshift measurement')

    return


def structure_manager(region_label):

    struct_dict = {'region': {}}
    st_warnings = []

    for idx, label in enumerate(region_label[st.session_state['n_regions']]):
        struct_dict['region'][f'r{idx}'] = {"name": label,
                                            "temp_mode": sstate.get(f"region_{label}_temp_mode"),
                                            "den_mode": sstate.get(f"region_{label}_den_mode"),
                                            "temp_ref": sstate.get(f"region_{label}_temp_tied_to"),
                                            "den_ref": sstate.get(f"region_{label}_den_tied_to"),
                                            "temp_eq": sstate.get(f"region_{label}_temp_relation"),
                                            "den_eq": sstate.get(f"region_{label}_den_relation")}

        if len(sstate.get(f"region_{label}_particles", [])) > 0:
            struct_dict['region'][f'r{idx}']['species'] = sstate.get(f"region_{label}_particles")
        else:
            struct_dict['region'][f'r{idx}']['species'] = None
            st_warnings.append(f"No species declared in region {label}")

        if len(sstate.get(f"region_{label}_exclude", [])) > 0:
            struct_dict[f"region_{label}_exclude"] = sstate.get(f"region_{label}_exclude")

        if struct_dict['region'][f'r{idx}']['temp_eq'] is 'None':
            struct_dict['region'][f'r{idx}']['temp_eq'] = None

        if struct_dict['region'][f'r{idx}']['den_eq'] is 'None':
            struct_dict['region'][f'r{idx}']['den_eq'] = None

    sstate['structure_dict'] = struct_dict
    st_warnings = None if len(st_warnings) == 0 else st_warnings

    return st_warnings
