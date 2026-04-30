from matplotlib import pyplot as plt
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper

from lime.plotting.format import theme as theme_lime
from specsy.plotting.plots import theme as theme_specsy, plot_traces, plot_corner_matrix, plot_flux_grid, extinction_gradient
from .input_output import load_infer_data
from innate.plotting import theme as theme_innate
import streamlit as st
from streamlit import session_state as s_state, secrets
from streamlit_bokeh import streamlit_bokeh
from utils.input_output import save_objSample
from astropy.visualization import ZScaleInterval

Z_FUNC_CMAP = ZScaleInterval()


theme_lime.set_style('dark')
theme_specsy.set_style('dark', library='bokeh')
theme_innate.set_style('dark')


DEFAULT_FIG_CFG = {'width':450, 'height':250, 'active_scroll': None,
                   "xaxis": {"axis_label_text_font_size": "16pt", "major_label_text_font_size":"14pt"},
                   "yaxis": {"axis_label_text_font_size": "16pt", "major_label_text_font_size":"14pt"}}


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

def bokeh_bands(spec_key, line, bands=None, fig_cfg=None, exclude_continua=True):

    # Recover the spectrum
    spec = s_state[spec_key]

    fig_cfg = None #{'width':450, 'height':250} if fig_cfg is None else fig_cfg
    fig_cfg = DEFAULT_FIG_CFG if fig_cfg is None else fig_cfg

    fig = spec.bokeh.bands(line, bands=bands, exclude_continua=exclude_continua, fig_cfg=fig_cfg, return_fig=True)
    streamlit_bokeh(fig, key='bands_plot')

    return

def matplotlib_bands(spec_key, line, bands=None, fig_cfg=None, exclude_continua=True):

    # Recover the spectrum
    spec = s_state[spec_key]

    fig_cfg = {'figure.figsize': (2, 2), 'figure.dpi' : 200}

    fig = plt.figure()
    spec.plot.bands(line, bands=bands, in_fig=fig, show_profile=False, rest_frame=True, show_continua=exclude_continua,
                    fig_cfg=fig_cfg)
    _colsA, colB, _colC = st.columns([0.2, 0.6, 0.2])

    with colB:
        st.pyplot(fig, transparent=True, use_container_width=True)

    return

def bokeh_spectrum(spec_key, bands=None, fig_cfg=None, default_show_fits=True, default_components=False,
                   default_show_cont=False, display_figure=True):

    # Recover the spectrum AQUI ESTUVE
    spec = s_state[spec_key]

    # Columns for the widgets
    col0, col1, col2, col3, col4 = st.columns([0.15, 0.25, 0.2, 0.2, 0.2], gap="small",
                                              vertical_alignment='center', border=False)

    with col1:
        label = f"Rest frame (z = {spec.redshift:0.3f})"
        rest_frame = st.checkbox(label, value=False, key='rest_frame_check',
                                  help='Display the observation in the observer rest frame.')

    with col2:
        log_scale = st.checkbox("Log scale", value=False, key='log_scale_check',
                                help='Display the spectrum in logaritmic scale.')

    with col3:
        comps_scale = st.checkbox("Show Components", value=default_components, key='components_check',
                                help='Show spectrum components.')

    with col4:
        comps_err = st.checkbox("Show uncertainty", value=False, key='show_err_check',
                                help='Show spectrum flux uncertainty.')

    st.write("")
    fig_cfg = DEFAULT_FIG_CFG if fig_cfg is None else fig_cfg

    # Get the line labels and the bands labels for the lines
    spec.bokeh.spectrum(bands=bands, fig_cfg=fig_cfg, rest_frame=rest_frame, log_scale=log_scale,
                        show_comps=comps_scale, include_fits=default_show_fits, show_err=comps_err, in_fig=None,
                        show_cont=default_show_cont)

    if display_figure:
        streamlit_bokeh(spec.bokeh.fig, key='input_spec')

    return spec.bokeh.fig



def LyC_bokeh_spectrum(spec_key, bands=None, fig_cfg=None, default_show_fits=True, default_components=False,
                       default_show_cont=False, display_figure=True, reg_params=None):

    # Recover the spectrum AQUI ESTUVE
    spec = s_state[spec_key]

    # Columns for the widgets
    col0, col1, col2, col3, col4 = st.columns([0.15, 0.25, 0.2, 0.2, 0.2], gap="small",
                                              vertical_alignment='center', border=False)

    with col1:
        label = f"Rest frame (z = {spec.redshift:0.3f})"
        rest_frame = st.checkbox(label, value=False, key='rest_frame_check',
                                  help='Display the observation in the observer rest frame.')

    with col2:
        log_scale = st.checkbox("Log scale", value=False, key='log_scale_check',
                                help='Display the spectrum in logaritmic scale.')

    with col3:
        comps_scale = st.checkbox("Show Components", value=default_components, key='components_check',
                                help='Show spectrum components.')

    with col4:
        comps_err = st.checkbox("Show uncertainty", value=False, key='show_err_check',
                                help='Show spectrum flux uncertainty.')

    st.write("")
    fig_cfg = DEFAULT_FIG_CFG if fig_cfg is None else fig_cfg

    # Get the line labels and the bands labels for the lines
    spec.bokeh.spectrum(bands=bands, fig_cfg=fig_cfg, rest_frame=rest_frame, log_scale=log_scale,
                        show_comps=comps_scale, include_fits=default_show_fits, show_err=comps_err, in_fig=None,
                        show_cont=default_show_cont)

    # Reg profile
    if reg_params is not None:
        z_corr = (1 + spec.redshift) if rest_frame else 1
        spec.bokeh.fig.line(reg_params['wave_reg'] / z_corr, reg_params['flux_reg'] * z_corr, legend_label="Voigtfit .reg",
                       line_color=theme_lime.colors['cont'], line_dash="dashed", line_width=2)

    streamlit_bokeh(spec.bokeh.fig, key='input_spec')

    return


def bokeh_2D_spectrum(wave_array, flux_array, limits=None):

    # Create the image
    fig_cfg = {'width': 600, 'aspect_ratio': 3, 'tools': 'hover,fullscreen,pan,wheel_zoom,box_zoom,xzoom_in,yzoom_in,reset,save',
               'toolbar_location':"below", 'tooltips': [("x", "$x"), ("y", "$y")]}
    fig = figure(**fig_cfg)
    fig.x_range.range_padding = fig.y_range.range_padding = 0

    # Scale the flux for the visualization
    display_flux = Z_FUNC_CMAP(flux_array)
    im_cfg = {'image': [display_flux], 'x': wave_array[0], 'y': 0, 'dw': wave_array[-1]-wave_array[0],
              'dh': flux_array.shape[0], 'color_mapper':  LinearColorMapper(palette="Inferno256"), 'level': "image"}

    # Add data
    fig.image(**im_cfg)

    # Format axis
    fig.xaxis.axis_label = r"$$\mathrm{Wavelength\ (\mu m)}$$"
    fig.xaxis.axis_label_text_font_size = "16pt"
    fig.xaxis.major_label_text_font_size = "14pt"
    fig.yaxis.axis_label = r'$$\text{Spatial axis (pixels)}$$'
    fig.yaxis.axis_label_text_font_size = "16pt"
    fig.yaxis.major_label_text_font_size = "14pt"

    if limits is not None:
        fig.ray(x=wave_array[0], y=limits[0], length=wave_array[-1]-wave_array[0], angle=0, color='black', line_width=1, line_dash="dashed")
        fig.ray(x=wave_array[0], y=limits[1], length=wave_array[-1]-wave_array[0], angle=0, color='black', line_width=1, line_dash="dashed")

    streamlit_bokeh(fig, key='2D_fits_plot')

    return

def bokeh_extinction(cHbeta, cHbeta_err, log_extinc, rel_Hbeta):

    fig = extinction_gradient(cHbeta, cHbeta_err, log_extinc, rel_Hbeta=rel_Hbeta, return_fig=True, fig_cfg=DEFAULT_FIG_CFG)
    streamlit_bokeh(fig, key='extinction_plot')

    return


