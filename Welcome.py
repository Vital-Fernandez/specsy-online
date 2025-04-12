import streamlit as st

# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1_Load_spectrum.py", title="Load observation"),
                              st.Page("pages/2_Load_collaboration.py", title="Collaborations")],

             "Line analysis":    [st.Page("pages/3_Load_line_bands.py", title="Line bands"),
                                  st.Page("pages/4_Line_fitting.py", title="Fitting configuration"), ],

             "Chemical analysis": [st.Page("pages/5_Load_data_grids.py", title="Emissivity grids"),
                                   st.Page("pages/6_Direct_abundances.py", title="Direct method"),
                                   st.Page("pages/7_Photo-ionization_modelling.py", title="Photoionization models"), ],}

    pg = st.navigation(pages)
    pg.run()

    return


if __name__ == "__main__":

    run()


