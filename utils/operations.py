import streamlit as st
from .plots import lime_spec_plotting
from .io import save_state
from specsy.models import DirectMethod
import lime
from matplotlib import pyplot as plt


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


def parce_direct_method(_emiss_grids, R_v, extinction_law, temp_low_diag):
    return DirectMethod(emiss_grids=_emiss_grids, R_v=R_v, extinction_law=extinction_law, temp_low_diag=temp_low_diag)