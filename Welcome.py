import streamlit as st

import lime
import specsy


# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1_Load_spectrum.py", title="Load observation"),
                                    st.Page("pages/2_Load_collaboration.py", title="Collaborations"),
                                    st.Page("pages/3_Components_detection.py", title="Components detection")],

             "Line analysis":    [st.Page("pages/4_Load_line_bands.py", title="Line bands"),
                                  st.Page("pages/5_Line_fitting.py", title="Fitting configuration"), ],

             "Diagnostics":     [st.Page("pages/6_Extinction.py", title="Gas extinction")],

             "Chemical analysis": [st.Page("pages/7_Load_data_grids.py", title="Emissivity grids"),
                                   st.Page("pages/8_Direct_abundances.py", title="Direct method"),
                                   st.Page("pages/9_Photo-ionization_modelling.py", title="Photoionization models"), ], }

    pg = st.navigation(pages)
    pg.run()

    return


if __name__ == "__main__":

    run()

    # log = lime.load_frame('/home/vital/PycharmProjects/lime/tests/baseline/manga_lines_log.txt')
    #
    # st.dataframe(log)



    # # specsy.extinction_coeff_calc()

    # from bokeh.plotting import figure, show
    # from bokeh.models import ColumnDataSource, Whisker, HoverTool
    # import numpy as np
    # import pandas as pd
    #
    # # Sample synthetic data
    # x_arr = np.array([0.1, 0.4, 0.6, 0.9])
    # y_arr = np.array([0.05, 0.3, 0.6, 0.8])
    # y_err = np.array([0.02, 0.05, 0.04, 0.03])
    # idcs_valid = np.array([True, True, False, True])
    # line_labels = ['OIII', 'Hβ', 'Excluded', 'NII']
    # ref_label = "Hβ"
    # coeff_label = "Hβ"
    # cHbeta = 0.12
    # cHbeta_err = 0.02
    # m, n = 0.85, 0.01
    #
    # # Prepare unified data source
    # df = pd.DataFrame({
    #     'x': x_arr,
    #     'y': y_arr,
    #     'y_err': y_err,
    #     'label': line_labels,
    #     'valid': idcs_valid,
    #     'color': ['blue' if v else 'red' for v in idcs_valid]
    # })
    #
    # source = ColumnDataSource(df)
    #
    # # Linear fit line
    # fit_x = np.linspace(x_arr.min(), x_arr.max(), 100)
    # fit_y = m * fit_x + n
    #
    # # Bokeh figure
    # p = figure(title=f"c({coeff_label}) extinction calculation",
    #            x_axis_label=f"f_λ - f_{{{ref_label}}}",
    #            y_axis_label=f"log(I_λ / I_{{{ref_label}}})_theo - log(F_λ / F_{{{ref_label}}})_obs",
    #            width=700, height=400,
    #            tools="pan,wheel_zoom,box_zoom,reset")
    #
    # # Plot all points with color by validity
    # p.circle('x', 'y', size=8, color='color', source=source, legend_field='valid')
    #
    # # Error bars for all points
    # p.add_layout(Whisker(source=source, base='x', upper='y', lower='y',
    #                      upper_head=None, lower_head=None, line_width=2))
    #
    # # Hover tool for all points
    # hover_all = HoverTool(tooltips=[
    #     ("Line", "@label"),
    #     ("Valid", "@valid"),
    #     ("x", "@x{0.000}"),
    #     ("y", "@y{0.000}")
    # ])
    # p.add_tools(hover_all)
    #
    # # Linear fit
    # p.line(fit_x, fit_y, line_dash='dashed', line_width=2,
    #        legend_label=f"c({coeff_label}) = {cHbeta:.3f} ± {cHbeta_err:.3f}")
    #
    # p.legend.location = "bottom_center"
    # p.legend.orientation = "horizontal"
    #
    # show(p)
    #
    #
    #
