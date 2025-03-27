from matplotlib import pyplot as plt
from bokeh.plotting import figure
import streamlit as st
from lime.plotting.format import spectrum_figure_labels, theme as theme_lime
from specsy.plotting.plots import theme as theme_specsy, plot_traces, plot_corner_matrix, plot_flux_grid
from .io import load_infer_data
from innate.plotting import theme as theme_innate
from streamlit import session_state as s_state
from streamlit_bokeh import streamlit_bokeh

theme_lime.set_style('dark')
theme_specsy.set_style('dark')
theme_innate.set_style('dark')

def lime_spec_plotting(spec, plot_type='spectrum', **kwargs):

    if plot_type == 'spectrum':
        fig = plt.figure()
        spec.plot.spectrum(in_fig=fig, **kwargs)

    elif plot_type == 'grid':
        fig = plt.figure(tight_layout=True, figsize=(3 * 2, 1.5 + 1.5 * int(spec.frame.index.size / 3)),
                         dpi=200)
        spec.plot.grid(in_fig=fig, **kwargs)

    else:
        fig = plt.figure()
        st.write('Plot not recognized')

    st.pyplot(fig, transparent=True)

    return

def specy_infer_plotting(address_db, plot_type):

    infer_db = load_infer_data(address_db)
    fig = plt.figure()

    # Load database
    if plot_type == 'traces':
        fig = plt.figure()
        plot_traces(infer_db, in_fig=fig)

    if plot_type == 'matrix':
        fig = plt.figure()
        fig_cfg = {'figure.figsize': (15, 15), 'figure.dpi': 200, 'axes.titlesize': 5,
                   "axes.labelsize" : 4, "xtick.labelsize" : 4, "ytick.labelsize" : 4}
        plot_corner_matrix(infer_db, in_fig=fig, fig_cfg=fig_cfg)

    if plot_type == 'flux':
        fig = plt.figure()
        n_lines = len(infer_db.inputs.labels.values)
        st.write(f'Line number {n_lines}')
        fig_cfg = {'figure.figsize': (22, 4), 'figure.dpi': 100,
                   'axes.titlesize': 8}
        plot_flux_grid(infer_db, in_fig=fig, n_cols=2, fig_cfg=fig_cfg)

    st.pyplot(fig, transparent=True)

    return

def matrix_plot(grid):

    fig = plt.figure()#(tight_layout=True, figsize=(8,8), dpi=200)
    ax_cfg = {'title': grid.label}
    grid.plot.matrix_diagnostic(in_fig=fig, ax_cfg=ax_cfg)

    st.pyplot(fig, transparent=True)

    return

def bokeh_bands(spec, line, bands=None, fig_cfg=None):

    # Columns for the widgets
    col1, col2, col3 = st.columns(3, gap="small", vertical_alignment="top", border=False)

    with col1:
        label = f'Rest frame (z = {spec.redshift:0.3f})'
        rest_frame = st.toggle(label, value=False, key='rest_frame_check1', help='Display the observation in the observer rest frame.')

    with col2:
        log_scale = st.toggle("Log scale", value=True, key='log_scale_check1',
                              help='Display the observation in the observer rest frame.')

    fig_cfg = {'width':450, 'height':250} if fig_cfg is None else fig_cfg
    fig = spec.bokeh.bands(line, return_fig=True, ref_bands=bands, fig_cfg=fig_cfg, rest_frame=rest_frame, log_scale=log_scale)
    streamlit_bokeh(fig, key='bands_plot')

    return

def bokeh_spectrum(spec, bands=None, fig_cfg=None):

    # Columns for the widgets
    col1, col2, col3 = st.columns([0.3, 0.3, 0.3], gap="small", vertical_alignment="top", border=False)

    with col1:
        label = f'Rest frame (z = {spec.redshift:0.3f})'
        rest_frame = st.toggle(label, value=False, key='rest_frame_check', help='Display the observation in the observer rest frame.')

    with col2:
        log_scale = st.toggle("Log scale", value=False, key='log_scale_check',
                              help='Display the observation in the observer rest frame.')

    with col3:
        comps_scale = st.toggle("Show Components", value=False, key='components_check',
                                help='Show spectral components if detected.')

    fig_cfg = {'width':450, 'height':250} if fig_cfg is None else fig_cfg
    fig = spec.bokeh.spectrum(return_fig=True, bands=bands, fig_cfg=fig_cfg, rest_frame=rest_frame, log_scale=log_scale,
                              include_components=comps_scale)
    streamlit_bokeh(fig, key='input_spec')

    return