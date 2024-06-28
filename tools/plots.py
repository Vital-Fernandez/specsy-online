from matplotlib import pyplot as plt
from bokeh.plotting import figure
import streamlit as st
from lime.plots import spectrum_figure_labels, theme as theme_lime
from specsy.plots import theme as theme_specsy, plot_traces, plot_corner_matrix, plot_flux_grid
from .io import load_infer_data
from innate.plotting import theme as theme_innate

theme_lime.set_style('dark')
theme_specsy.set_style('dark')
theme_innate.set_style('dark')

def plot_spectrum(spec):

    fig = figure(width=600, height=300, tools="pan,xwheel_pan,xzoom_in,xzoom_out,wheel_zoom,reset")

    fig.step(x=spec.wave_rest, y=spec.flux, mode="center")

    x_label, y_label = spectrum_figure_labels(spec.units_wave, spec.units_flux, spec.norm_flux)
    st.write(x_label)
    fig.xaxis.axis_label = r'{}'.format(x_label.replace("$", "$$")) #' ##r"$$\nu \:(10^{15} s^{-1})$$" #x_label
    fig.xaxis.axis_label_text_color = theme_lime.colors['fg']
    fig.yaxis.axis_label = y_label

    # Format figure
    fig.background_fill_color = theme_lime.colors['bg']  # Light grey color, you can use any hex color
    fig.border_fill_color = theme_lime.colors['bg']
    fig.xgrid.visible = False  # This hides all vertical grid lines
    fig.ygrid.visible = False

    fig.axis.axis_line_color = theme_lime.colors['fg']  # Changes the color of the axis lines

    # Customize axis labels
    fig.axis.axis_label_text_color = theme_lime.colors['fg']  # Changes the color of the axis labels

    # Customize major ticks
    fig.axis.major_label_text_color = theme_lime.colors['fg']  # Changes the color of the labels on the major ticks
    fig.axis.major_tick_line_color = theme_lime.colors['fg']  # Changes the color of the major ticks

    #  Customize minor ticks
    fig.axis.minor_tick_line_color = theme_lime.colors['fg']  # Changes the color of the minor ticks

    st.bokeh_chart(fig)
    st.markdown(f'You can click the +/- loop symbols to magnify along the X axis')

    return


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