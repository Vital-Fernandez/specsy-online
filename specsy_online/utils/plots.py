from matplotlib import pyplot as plt
from bokeh.plotting import figure
from bokeh.models import LinearColorMapper

from lime.plotting.format import theme as theme_lime
from innate.plotting import theme as theme_innate
from specsy.plotting.plots import theme as theme_specsy
from specsy.plotting.plots import plot_corner_matrix, plot_flux_grid, extinction_gradient
from specsy.plotting.bokeh_functions import bokeh_trace, bokeh_scatter_matrix, bokeh_flux_grid
from specsy.plotting.arviz_functions import plot_fitted_fluxes, plot_traces, plot_fitted_params, plot_fitted_pairs, plot_prior_posterior
from .input_output import load_infer_data
import streamlit as st
from streamlit import session_state as s_state
from streamlit_bokeh import streamlit_bokeh
from astropy.visualization import ZScaleInterval
from arviz import summary
from bokeh.models import ColumnDataSource, BoxAnnotation

Z_FUNC_CMAP = ZScaleInterval()

theme_lime.set_style('dark')
theme_innate.set_style('dark')
theme_specsy.set_style('dark', library='bokeh')


DEFAULT_FIG_CFG = {'width':450, 'height':250, 'active_scroll': None,
                   "xaxis": {"axis_label_text_font_size": "16pt", "major_label_text_font_size":"14pt"},
                   "yaxis": {"axis_label_text_font_size": "16pt", "major_label_text_font_size":"14pt"}}

# Styled and documented headers for pymc symmary
PYMC_SUMMARY_COLUMN_CONFIG = {
    "_index": st.column_config.TextColumn(
        "Parameter",
        help="Model parameter from the MCMC sampling",
    ),
    "mean": st.column_config.NumberColumn(
        "Mean",
        help="Posterior mean of the parameter",
    ),
    "sd": st.column_config.NumberColumn(
        "Std. dev.",
        help="Posterior standard deviation",
    ),
    "eti89_lb": st.column_config.NumberColumn(
        "89% ETI (lower)",
        help="Lower bound of the 89% equal-tailed credible interval",
    ),
    "eti89_ub": st.column_config.NumberColumn(
        "89% ETI (upper)",
        help="Upper bound of the 89% equal-tailed credible interval",
    ),
    "ess_bulk": st.column_config.NumberColumn(
        "ESS (bulk)",
        help="Effective sample size: the number of independent samples the "
             "chain is equivalent to for estimating central quantities like "
             "the mean and median. MCMC samples are correlated, so this is "
             "smaller than the raw number of draws. Values above ~400 are "
             "generally considered reliable.",
    ),
    "ess_tail": st.column_config.NumberColumn(
        "ESS (tail)",
        help="Same idea as bulk ESS, but computed for the 5% and 95% "
             "quantiles. It tells you whether the extremes of the posterior "
             "are well sampled — a low value means the credible interval "
             "bounds are uncertain even if the mean is fine.",
    ),
    "r_hat": st.column_config.NumberColumn(
        "R̂",
        help="Gelman-Rubin convergence diagnostic; values ≤ 1.01 indicate "
             "the chains have converged",
        format="%.3f",
    ),
    "mcse_mean": st.column_config.NumberColumn(
        "MCSE (mean)",
        help="Monte Carlo standard error of the posterior mean",
    ),
    "mcse_sd": st.column_config.NumberColumn(
        "MCSE (sd)",
        help="Monte Carlo standard error of the posterior standard deviation",
    ),
}


def prioritized_default(options, priority_prefixes=('temp', 'den'), n_max=7):
    # Priority entries first, then the rest, capped at n_max
    priority = [opt for opt in options if opt.startswith(priority_prefixes)]
    others = [opt for opt in options if not opt.startswith(priority_prefixes)]
    return (priority + others)[:n_max]


def df_to_mathjax_html(df):
    headers = "".join(f"<th>{col}</th>" for col in df.columns)
    rows = ""
    for _, row in df.iterrows():
        cells = "".join(f"<td>{val}</td>" for val in row)
        rows += f"<tr>{cells}</tr>"
    return f"""
    <script src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
    <table border="1" style="border-collapse:collapse; width:100%">
      <thead><tr>{headers}</tr></thead>
      <tbody>{rows}</tbody>
    </table>
    """


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
        streamlit_bokeh(spec.bokeh.fig, key='input_spec', use_container_width=True)

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


def trace_diagnostics_plots(trace):

    tabSummary, tabDistr, tabTraces, tabKDE, tabPriorPost = st.tabs(tabs=['Summary', 'Measurements distributions',
                                                                           'Traces', 'Scatter plot matrix',
                                                                           'Prior-Posterior comparison'],
                                                      on_change="rerun")
    summary_df = summary(trace)
    idcs_vars = ~summary_df.index.str.startswith('theo')
    summary_df = summary_df.loc[idcs_vars]

    # Trace plot
    with tabSummary:

        st.markdown(f'#### Measurements table:')
        st.dataframe(summary_df, column_config=PYMC_SUMMARY_COLUMN_CONFIG, width="content")

        st.space('small')
        st.markdown(f'#### Posterior flux distributions')
        st.markdown("These plots compare, for each emission line, the flux distribution predicted by the "
                    "model against the observed measurement: the vertical line marks the observed flux and "
                    "the shaded band its uncertainty, with the histograms colored by ion. In a successful "
                    "fit, the predicted distributions overlap the observed bands; lines whose distributions "
                    "fall clearly outside their band are poorly reproduced by the model and may point to "
                    "issues in the measurement or the fitted parameters.")

        fig_cfg = None
        fig = plot_fitted_fluxes(trace, backend='bokeh', in_fig=None, fig_cfg=fig_cfg, n_cols=5)
        streamlit_bokeh(fig)


    # Measurements distributions
    with tabDistr:
        st.markdown("These plots display the posterior distribution of each parameter, with the mean value "
                    "and its credible interval marked below. In a successful fit, the distributions are "
                    "smooth and single-peaked; broad, flat or multi-peaked distributions indicate poorly "
                    "constrained parameters. For synthetic tests, the vertical line marks the true "
                    "value, which should fall within the recovered distribution.")

        fig_cfg = {'width': 400, 'height': 200}
        fig = plot_fitted_params(trace, backend='bokeh', in_fig=None, fig_cfg=fig_cfg)
        streamlit_bokeh(fig)


    # Scatter plot matrix
    with tabTraces:
        st.markdown("These plots display the overlaid trace distributions (left) and their evolution "
                    "along the sampling (right). In a successful fit, all chains show a similar "
                    "distribution and their evolution resembles white noise, without drifts or jumps.")

        fig_cfg = {'width': 400, 'height': 200}
        fig = plot_traces(trace, backend='bokeh', in_fig=None, fig_cfg=fig_cfg)
        streamlit_bokeh(fig)

    # Flux grid
    with tabKDE:
        st.markdown("This figure displays the joint distributions for each pair of parameters, with the "
                    "marginal distribution of each parameter along the diagonal. A maximum of 6 parameters "
                    "can be displayed at a time. In a successful fit, the contours are compact and roughly "
                    "elliptical; elongated or curved shapes indicate correlated or degenerate parameters, "
                    "whose values cannot be constrained independently.")

        var_selection = st.multiselect('Parameters for the scatter matrix', options=summary_df.index.tolist(),
                                       default=prioritized_default(summary_df.index.tolist(), n_max=6), max_selections=6,
                                       help='Choose up to 6 parameters')

        fig_cfg = {'width': 200, 'height': 200}
        fig = plot_fitted_pairs(trace, var_names=var_selection, backend='bokeh', in_fig=None, fig_cfg=fig_cfg)
        streamlit_bokeh(fig)




    with tabPriorPost:
        st.markdown("These plots compare, for each parameter, the prior distribution (the assumed range "
                    "before the fit) against the posterior distribution (the values recovered from the "
                    "data). In a successful fit, the posterior is much narrower than the prior, showing "
                    "that the data, and not the initial assumptions, constrain the result. A posterior "
                    "that closely resembles the prior or piles up against its edges indicates the "
                    "parameter is not well constrained by the observations.")

        fig_cfg = {'width': 200, 'height': 200}
        fig = plot_prior_posterior(trace, var_names=var_selection, backend='bokeh', in_fig=None, fig_cfg=fig_cfg)
        streamlit_bokeh(fig)

    return


def plot_bokeh_bands(wave_plot, flux_plot, selected_line, bands_arr, log_check):

    y_axis_type = "log" if log_check else "linear"

    source = ColumnDataSource(dict(wave=wave_plot, flux=flux_plot))

    p = figure(width=800, height=350, title=selected_line, x_axis_label='Rest Wavelength', y_axis_label='Flux',
               y_axis_type=y_axis_type, tools="xpan,xwheel_zoom,reset,save")

    p.step('wave', 'flux', source=source, color=theme_specsy.colors['fg'], line_width=1)

    p.add_layout(BoxAnnotation(left=bands_arr[0], right=bands_arr[1],
                               fill_color=theme_specsy.colors['cont_band'], fill_alpha=0.2))
    p.add_layout(BoxAnnotation(left=bands_arr[2], right=bands_arr[3],
                               fill_color=theme_specsy.colors['line_band'], fill_alpha=0.2))
    p.add_layout(BoxAnnotation(left=bands_arr[4], right=bands_arr[5],
                               fill_color=theme_specsy.colors['cont_band'], fill_alpha=0.2))

    streamlit_bokeh(p, use_container_width=True)

    return