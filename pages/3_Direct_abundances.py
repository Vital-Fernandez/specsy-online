import streamlit as st
import specsy
from streamlit import session_state as s_state
from tools.sidebar import sidebar_widgets
from tools.io import declare_line_measuring, parse_frame_normalization, load_emiss_grids
from tools.plots import lime_spec_plotting
from tools.operations import parce_direct_method

# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Direct abundances')

# Read the emissivities
emiss_db = load_emiss_grids('./resources/data/emissivity_db.nc')

# Read chemical fitting
results_file = './resources/data/SHOC579_results.txt'
df = parse_frame_normalization(results_file)

st.write(df)

# Generate the chemical model
dm_twoTemps = parce_direct_method(_emiss_grids=emiss_db, R_v=3.4, extinction_law="G03 LMC", temp_low_diag='Hagele_2006')

# Declare model
line_list = ['O2_3726A', 'O2_3729A', 'H1_4340A', 'O3_4363A', 'O3_4959A', 'O3_5007A', 'S3_6312A', 'H1_6563A', 'S2_6716A',
             'S2_6731A']
dm_twoTemps.fit.frame(df, lines_list=line_list, output_folder='./results/', results_label='SHOC579')

st.write(f'Finish')
