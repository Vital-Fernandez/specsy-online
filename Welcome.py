import streamlit as st

# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1_Load_spectrum.py", title="Load observation"),
                                    st.Page("pages/2_Load_collaboration.py", title="Collaborations"),
                                    st.Page("pages/3_Components_detection.py", title="Components detection")],

             "Line analysis":    [st.Page("pages/4_Load_line_bands.py", title="Bands"),
                                  st.Page("pages/5_Line_fitting.py", title="Fitting"), ],

             "Diagnostics":     [st.Page("pages/6_Extinction.py", title="Gas extinction")],

             "Chemical analysis": [st.Page("pages/7_Load_data_grids.py", title="Emissivity grids"),
                                   st.Page("pages/8_Direct_abundances.py", title="Direct method"),
                                   st.Page("pages/9_Photo-ionization_modelling.py", title="Photoionization models"), ], }

    pg = st.navigation(pages)
    pg.run()

    return


def review_bounds():

    idx2, idx3 = st.session_state.central

    # Update lower limit
    idx0, idx1 = st.session_state.lower
    if idx1 > idx2:
        idx1 = idx2 - 2
        if idx0 > idx1:
            idx0 = idx1 - 2
        st.session_state.lower = (idx0, idx1)

    # Update upper
    idx4, idx5 = st.session_state.upper
    if idx3 > idx4:
        idx4 = idx3 + 2
        if idx4 > idx5:
            idx5 = idx4 + 2
        st.session_state.upper = (idx4, idx5)

    return

if __name__ == "__main__":

    run()
