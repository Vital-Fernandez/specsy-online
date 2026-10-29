import streamlit as st
from os import cpu_count

try:
    import numpyro
    numpyro.set_host_device_count(cpu_count())
except:
    st.warning('Failed to set the device count on numpyro')

# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0a_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1a_Load_spectrum.py", title="Load spectrum"),
                                    st.Page("pages/1b_Load_collaboration.py", title="Virtual observatory")],

             "Tools": [st.Page("pages/3a_spectrum_masking.py", title="Spectrum masking"),
                       st.Page("pages/3b_continuum_fitting.py", title="Polynomial fitting")],

             "Aspect": [st.Page("pages/2a_Components_detection.py", title="Components detection")],


             "LiMe":    [st.Page("pages/4a_line_bands.py", title="Bands"),
                         st.Page("pages/4b_Line_fitting.py", title="Line fitting"), ],

             "PyNeb": [st.Page("pages/5a_Extinction.py", title="Gas extinction")],

             "SpecSy": [st.Page("pages/6a_Load_data_grids.py", title="Emissivity grids"),
                        st.Page("pages/6b_Direct_abundances.py", title="Direct method"),
                        st.Page("pages/6c_SSP.py", title="Stellar Population synthesis")],
             }

    pg = st.navigation(pages)
    pg.run()

    return

# Launch the app
run()