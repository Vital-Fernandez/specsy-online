import streamlit as st

# Welcome screen
def run():

    # Menu pages
    pages = {"Welcome": [st.Page("pages/0a_introduction.py", title="Introduction")],

             "Spectroscopic data": [st.Page("pages/1a_Load_spectrum.py", title="Load spectrum"),
                                    st.Page("pages/1b_Load_collaboration.py", title="Virtual observatory")],

             "Aspect": [st.Page("pages/2a_Components_detection.py", title="Components detection")],

             "Continuum": [st.Page("pages/3a_continuum_fitting.py", title="Polynomial fitting")],

             "LiMe":    [st.Page("pages/4a_line_bands.py", title="Bands"),
                         st.Page("pages/4b_Line_fitting.py", title="Fitting"), ],

             "Diagnostics": [st.Page("pages/5a_Extinction.py", title="Gas extinction")],

             "SpecSy": [st.Page("pages/6a_Load_data_grids.py", title="Emissivity grids"),
                        st.Page("pages/6b_Direct_abundances.py", title="Direct method"),
                        ], }

    pg = st.navigation(pages)
    pg.run()


    return


if __name__ == "__main__":

    run()

# '''
#
# conda create -c conda-forge -n specsy_online python=3.12 "pymc>=5" numpyro blackjax
# conda activate specsy_online
#
# pip install pyneb
# pip install bokeh
# pip install streamlit
# pip install streamlit-bokeh
# pip install streamlit-authenticator
# pip install st-gsheets-connection
# pip install google-api-python-client
#
# pip install pyneb bokeh streamlit streamlit-bokeh streamlit-authenticator st-gsheets-connection google-api-python-client
#
# conda deactivate
# conda remove -n specsy_online --all
#
# spesy_online_v1
# pip install numpy matplotlib pandas astropy lmfit mplcursors scipy pyneb
# pip install joblib scikit-learn
# pip install pymc
# pip install bokeh streamlit streamlit-bokeh
# pip install st-gsheets-connection
#
# /home/vital/anaconda3/envs/specsy_online_v1/bin/streamlit run specsy_online/Welcome.py
#
# pip install st-gsheets-connection
#
# '''