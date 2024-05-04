from matplotlib import pyplot as plt
from bokeh.plotting import figure, show

import streamlit as st
from lime.plots import spectrum_figure_labels, theme

theme.set_style('dark')


def plot_spectrum(spec):

    fig = figure(width=600, height=300, tools="pan,xwheel_pan,xzoom_in,xzoom_out,wheel_zoom,reset")

    fig.step(x=spec.wave_rest, y=spec.flux, mode="center")

    x_label, y_label = spectrum_figure_labels(spec.units_wave, spec.units_flux, spec.norm_flux)

    fig.xaxis.axis_label = x_label
    fig.yaxis.axis_label = y_label

    st.bokeh_chart(fig)
    st.markdown(f'You can click the +/- loop symbols to magnify along the X axis')

    return


def lime_spec_plotting(spec, plot_type='spectrum', **kwargs):

    fig = plt.figure()

    if plot_type == 'spectrum':
        spec.plot.spectrum(in_fig=fig, **kwargs)

    elif plot_type == 'grid':
        spec.plot.grid(in_fig=fig, **kwargs)

    else:
        st.write('Plot not recognized')

    st.pyplot(fig)

    return