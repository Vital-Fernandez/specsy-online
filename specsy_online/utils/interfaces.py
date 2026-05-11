import streamlit as st
from os import cpu_count
from streamlit import session_state as s_state,secrets
import streamlit_authenticator as stauth
from streamlit_gsheets import GSheetsConnection
from numpy import argsort, random, floor, ceil, intersect1d, sum, array, sort, searchsorted, min, max
from pyneb import RedCorr
from pandas import DataFrame
from lime.io import parse_lime_cfg
from lime.transitions import au, Line
from lime.retrieve.line_bands import get_spectrum_line_groups
from specsy import extinction_coeff_calc
from specsy.models.literature import TEM_FUNC_DICT, DEN_FUNC_DICT

from specsy_online.utils.input_output import (save_state, load_spectrum, parse_line_bands_df, get_text_spectrum, convert_for_download,
                                              widget_text_to_list, on_bands_edit, clear_obj_data, widget_save_state, parse_fit_cfg,
                                              save_objSample, get_instrument_cfg, on_toml_change)


from specsy_online.utils.tools import dynamic_input_data_editor
from specsy_online.utils.plots import bokeh_spectrum, bokeh_extinction, plot_bokeh_bands
from lime.archives.read_fits import SPECTRUM_FITS_PARAMS
from specsy_online.utils.formatting import REGION_TAGS_STYLE, REGION_LABELS, card_formating
import tomlkit

from specsy.plotting.bokeh_functions import bokeh_trace, bokeh_scatter_matrix, bokeh_flux_grid

FIT_CFG_PLACEHOLDER = ('[default_line_fitting]\n'
                       'H1_6563A_b="H1_6563A+N2_6583A+N2_6548A"\n'
                       'N2_6548A_amp="expr:N2_6584A_amp/2.94"\n'
                       'N2_6548A_kinem="N2_6584A"')

FIT_CFG_HELP = 'Please check LiMe documentation to read more on how to adjusts your fittings'

INSTRUMENT_LIST = ['sdss', 'osiris', 'isis', 'nirspec', 'cos', 'text']

SURVEY_LIST = ['CEERS', 'CAPERS', 'PID17515']

CODE_EXAMPLE_LOAD_SPECTRUM = None

def unit_conversion_inputs(column_wave, column_flux, label_wave, label_flux, default_wave_units=None, default_flux_units=None):

    message_help = 'These are the default units. Please use astropy string notation for the units.'

    # Read the units
    with column_wave:
        wave_units_str = st.text_input(label_wave, value=default_wave_units, placeholder='Angstrom', help=message_help)

    with column_flux:
        flux_units_str = st.text_input(label_flux, value=default_flux_units, placeholder='FLAM', help=message_help)

    # Review for empty cases
    wave_units_str = None if (wave_units_str is None) or (wave_units_str == "") else wave_units_str
    flux_units_str = None if (flux_units_str is None) or (flux_units_str == "") else flux_units_str

    # Confirm the units are astropy valid
    if wave_units_str is not None:
        try:
            au.Unit(wave_units_str)
        except:
            st.warning(f'Input wavelength units "{wave_units_str}" are not recognized please use astropy notation')
            wave_units_str = None

    if flux_units_str is not None:
        try:
            au.Unit(flux_units_str)
        except:
            st.warning(f'Input wavelength units "{flux_units_str}" are not recognized please use astropy notation')
            flux_units_str = None

    return wave_units_str, flux_units_str


def load_collaboration():

    # Title
    msg = f'## {s_state["username"].upper()} survey'
    st.write(msg)

    # Author block
    msg = (f'These observations belong to the CANDELS-Area Prism Epoch of Reionization Survey. Mark Dickinson at NOIRLab (AZ)'
           f' is the P.I. of this proposal with reference JWST-GO-6368. Please contact the P.I. before using this dataset.\n\n'
           f'This spreadsheet indexes the object characteristics and the observational files properties. Please check the '
           f'CAPERS README file for the columns parameters.\n\n'
           f'Use the widgets below to constrain the files selection.')
    st.write(msg)

    conn = st.connection("capers", type=GSheetsConnection)
    index_list = ['sample', 'id', 'file']
    df = conn.read(ttl=None, index_col=index_list, header=0)
    df.index.names = index_list

    # Sample indexing
    default_samples = df.index.get_level_values('sample').unique().to_numpy()
    sample_selection = st.multiselect('Sample selection:', default=default_samples, options=list(default_samples), key='sample_list')
                       #on_change=save_objSample, args=("sample_list",))
    idcs = df.index.get_level_values('sample').isin(sample_selection)

    # Redshift indexing
    label_text = 'Redshift range selection:'
    help_text = 'The observations list will be limited to the input redshift range'
    z_limits = floor(df.z_UNICORN.min()), ceil(df.z_UNICORN.max())
    z_range = st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
              key='z_range', value=z_limits, help=help_text)
    st.write(z_range)

    idcs = idcs & (df['z_UNICORN'] >= z_range[0]) & (df['z_UNICORN'] <= z_range[1])


    # Object indexing
    label_text = 'Comma-separated MSA IDs'
    help_text = 'The observations list will be limited to the input IDs'
    place_holder_text = '3,1027,80026'
    mpt_list = st.text_area(label=label_text, value=None, key='MPTUSERLIT', help=help_text, placeholder=place_holder_text)
                 #on_change=save_objSample, args=("MPTUSERLIT",),)

    mpt_array = widget_text_to_list(mpt_list)
    if mpt_array is not None:
        idcs_selection = df['MPT_number'].isin(mpt_array)
        mpt_found = df.loc[idcs_selection, 'MPT_number'].unique()
        mpt_common = intersect1d(mpt_found, mpt_array)
        if sum(mpt_common) > 0:
            st.info(f'Objects {", ".join(list(mpt_common.astype(str)))} were found the sample selection')
            idcs = idcs & idcs_selection
        else:
            st.warning('None of the objects in the input MPT list was found')



    msg = f'{idcs.sum()} files in selection'
    st.write(msg)
    st.dataframe(df.loc[idcs])

    return


def extinction_form(df_key):

    # Get the parameters for the calculation
    lines_df = s_state[df_key]
    lines_H1 = lines_df.loc[lines_df.particle == 'H1'].index.to_numpy()
    idx_column = lines_df.columns.get_loc('profile_flux') if 'profile_flux' in lines_df.columns else 0

    if lines_H1.size > 1:
        with ((st.form('extinction_form', border=True, enter_to_submit=False, clear_on_submit=False))):

            # Lines parameters
            st.write('Inputs/outputs:')
            colX, colY, colZ = st.columns([0.3, 0.3, 0.3])
            with colX:
                flux_column = st.selectbox('Flux column', lines_df.columns, index=idx_column)

            with colY:
                st.write("")
                st.write("")
                message = 'Recalculate the extinction coefficient to use the Balmer β wavelength as the relative value'
                Hbeta_conv_check = st.toggle(r'Convert to c(Hβ)', value='True', help=message)

            with colZ:
                st.write("")
                st.write("")
                message = 'Negative and NaN fluxes/uncertainties will be excluded from the calculation'
                non_phys_check = st.toggle(r'Exclude non-physical', value='True', help=message)

            # Lines parameters
            st.write("")
            st.write('Lines selection:')

            colA, colB, colC = st.columns([0.3, 0.3, 0.3])
            with colA:
                idx_default_norm = int(argsort(-lines_df.loc[lines_H1, lines_df.columns[idx_column]].to_numpy())[1])
                norm_line = st.selectbox('Normalization line', lines_H1, index=idx_default_norm)

            with colB:
                input_list = st.multiselect('Input lines', options=lines_H1, default=None, placeholder='All')
                input_list = None if len(input_list) == 0 else input_list

            with colC:
                exclude_list = st.multiselect('Exclude lines', options=lines_H1, default=None, placeholder='None')
                exclude_list = None if len(exclude_list) == 0 else exclude_list

            # Lines parameters
            st.write("")
            st.write('Physical model:')

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                reddening_laws = ["CCM89", "CCM89 Bal07", "CCM89 oD94", "S79 H83 CCM89","K76","SM79 Gal", "G03 LMC",
                                  "MCC99 FM90 LMC", "F99-like", "F99","F88 F99 LMC"]
                law = st.selectbox("Reddening Law", reddening_laws)

            with col2:
                R_V = st.number_input("Rᵥ", min_value=0.0, value=3.1, step=0.1)

            with col3:
                tem = st.number_input("Temperature (K)", min_value=500, value=10000, step=1000)

            with col4:
                den = st.number_input("Density (1/cm³)", min_value=1.0, value=100.0, step=100.0)

            st.write("")
            submitted = st.form_submit_button("Compute extinction")

            if submitted:

                st.write('***')
                st.write('## Results')
                st.write("")
                cHbeta, cHbeta_err, log_extinc = extinction_coeff_calc(lines_df, norm_line, R_V, law, tem, den, rel_Hbeta=Hbeta_conv_check,
                                                           flux_column=flux_column, line_list=input_list, exclude_list=exclude_list)

                red_cor = RedCorr(R_V=R_V, law=law, cHbeta=cHbeta)

                out1, out2, out3 = st.columns([0.27, 0.32, 0.25])
                with out1:
                    if Hbeta_conv_check:
                        coeff_label = r'c(H\beta)'
                    else:
                        coeff_label = Line(norm_line).latex_label[0]
                        coeff_label = f'c({coeff_label.replace("$", "")})'
                    st.markdown(rf"${coeff_label} = {cHbeta:.3f}\pm{cHbeta_err:.3f}$")

                with out2:
                    E_BV_err = cHbeta_err * 2.5 / red_cor.X(4861.25)
                    st.markdown(rf"$E(V - B) = {red_cor.E_BV:.3f}\pm{E_BV_err:.3f}$")

                with out3:
                    A_V_err = E_BV_err * R_V
                    st.markdown(rf"$A_{{V}} = {red_cor.AV:.3f}\pm{A_V_err:.3f}$")

                # Extinction plot
                bokeh_extinction(cHbeta, cHbeta_err, log_extinc, rel_Hbeta=Hbeta_conv_check)
    else:
        st.warning(f'No hydrogen lines')

    return


def load_spectrum_tab():

    st.markdown(f'#### File properties')
    col_A, col_B = st.columns([0.25, 0.75], gap='large')

    # Instrument
    with col_A:
        message_help = 'Please contact the author if your instrument is not supported with an example file.'
        instrument = st.selectbox('Instrument', INSTRUMENT_LIST, key='instr_selection', help=message_help)

    # File
    with col_B:
        message_help = 'The text file must follow the expect format'
        uploaded_file = st.file_uploader(label='Spectrum file browser', type=['.fits', '.txt', '.csv'],
                                         accept_multiple_files=False, key='spec_uploader', help=message_help)

        # Instrument configuration
        with st.expander("Default instrument file settings", icon=":material/satellite_alt:"):
            cfg = get_instrument_cfg()
            for label, df in cfg.items():
                st.caption(label)
                st.dataframe(df, hide_index=True, use_container_width=True)

        with st.expander(label='Text file properties', expanded=False, icon=":material/docs:"):
            col_A, col_B, col_C, col_D = st.columns([0.25, 0.25, 0.25, 0.25], gap='large')

            with col_A:
                message_help = 'Delimiter between columns'
                separator = st.text_input('Delimiter', value=None, placeholder='Whitespace', help=message_help)

            with col_B:
                message_help = 'Comments'
                comments = st.text_input('Comments', value='#', help=message_help)

            with col_C:
                message_help = 'Number of rows to skip'
                skiprows = st.number_input('Skip rows', value=0, help=message_help)

            with col_D:
                message_help = 'Columns to use in text file.'
                usecols = st.text_input('Use columns rows', value=None, placeholder="0,3,4", help=message_help)

    st.markdown(f'#### Observation properties')
    col_A, col_B, col_C, col_D = st.columns([0.25, 0.25, 0.25, 0.25], gap='large')

    # Redshift
    with col_A:
        message_help = 'Input observation redshift. The default value is 0. All measurements are reported on the observed frame.'
        z_string = st.text_input('Redshift', value=None, help=message_help)

    # Norm flux
    with col_B:
        message_help = 'Optional normalization for the input flux, LiMe will calculate one if necessary'
        norm_flux_string = st.text_input('Normalization flux', value=None, help=message_help)

    # Input wavelength and flux units
    wave_units_in, flux_units_in= unit_conversion_inputs(col_C, col_D, 'Wavelength units in', 'Flux units in',
                                                         SPECTRUM_FITS_PARAMS[instrument]['units_wave'],
                                                         SPECTRUM_FITS_PARAMS[instrument]['units_flux'])

    col_E, col_F, col_G, col_H = st.columns([0.25, 0.25, 0.25, 0.25], gap='large')

    # crop_waves
    with col_E:
        message_help = 'Minimum wavelength to crop the input spectrum. Leave empty to use the full range.'
        wave_min = st.number_input('Wave crop min', value=None, step=100, help=message_help)
    with col_F:
        message_help = 'Maximum wavelength to crop the input spectrum. Leave empty to use the full range.'
        wave_max = st.number_input('Wave crop max', value=None, step=100, help=message_help)

    # crop_flux
    with col_G:
        message_help = 'Minimum flux percentile to clip the flux array. Defaults to 0 percentile.'
        flux_min = st.number_input('Flux crop min percentile', min_value=0, max_value=100, step=1, value=None,
                                   help=message_help)
    with col_H:
        message_help = 'Maximum flux percentile to clip the flux array. Defaults to 100th percentile.'
        flux_max = st.number_input('Flux crop max percentile', min_value=0, max_value=100, step=1, value=None,
                                   help=message_help)

    # Pack into tuples, None if both ends are empty
    crop_waves = (wave_min, wave_max) if (wave_min is not None or wave_max is not None) else None
    if flux_min is not None or flux_max is not None:
        crop_flux = (flux_min if flux_min is not None else 0, flux_max if flux_max is not None else 100)
    else:
        crop_flux = None

    # Unit conversion
    st.markdown(f'#### Unit conversion')
    col_A, col_B, _, _ = st.columns([0.25, 0.25, 0.25, 0.25], gap='large')
    wave_units_out, flux_units_out= unit_conversion_inputs(col_A, col_B, 'Wavelength units out', 'Flux units out')


    st.space('xsmall')
    with st.form('load_spec_form', border=False, enter_to_submit=False, clear_on_submit=False):

        # submitted = st.button("Load observation")
        submitted = st.form_submit_button("Get spectrum")

        if submitted:

            if uploaded_file:

                try:

                    # Clear the previous state
                    clear_obj_data()

                    spec = load_spectrum(uploaded_file, instrument, z_string, norm_flux_string, wave_units_in, flux_units_in,
                                         crop_waves, crop_flux,
                                         uploaded_file.name, separator, comments, skiprows, usecols,
                                         wave_units_out, flux_units_out)

                    save_state('id', uploaded_file.name)
                    save_state('spec', spec)
                    save_state('obs_type', 'upload')

                except Exception as e:
                    st.error(f"An error occurred: {e}")

            else:
                st.warning('No spectrum file specified. Please provide one before proceeding.')

    return


def select_survey():

    st.title(f'Virtual observatory')
    st.space()
    st.write(
        "You may select a survey from the selection box below. Please note that some research projects may require "
        "authentication — please contact the project's Principal Investigator (P.I.) for access.")

    col_A, col_B = st.columns([0.25, 0.75], gap='large')

    with col_A:
        st.selectbox('Survey', SURVEY_LIST, key='survey_selection', help='Some surveys require authentification, '
                                                                         'please contact the project PI.')

    st.markdown("***")

    return


def add_kinematic_components():

    selected_lines = st.session_state.selected_lines
    if not selected_lines:
        st.warning("Please select at least one line (ki).")
        return

    cfg = st.session_state.bands_cfg
    section = cfg["default_line_fitting"]

    # Add kinematic entries
    for line in selected_lines:
        section[f"{line}_b"] = f"{line}+{line}_k-1"
        section[f"{line}_k-1_sigma"] = f"expr:>1.0*{line}_sigma"

    # Update grouped_lines deduplicating existing entries
    new_entries = [f"{line}_b" for line in selected_lines]
    existing = list(section.get("grouped_lines", []))
    section["grouped_lines"] = list(dict.fromkeys(existing + new_entries))

    st.session_state.bands_cfg = cfg
    st.session_state.toml_text = tomlkit.dumps(cfg)
    st.session_state.toml_area_key += 1


def add_vsigma_components():
    selected_lines = st.session_state.vsigma_lines
    velocity = st.session_state.vsigma_velocity

    if not selected_lines:
        st.warning("Please select at least one line.")
        return

    cfg = st.session_state.bands_cfg
    section = cfg["default_line_fitting"]

    for line in selected_lines:
        key = tomlkit.items.DottedKey([tomlkit.items.SingleKey("map_band_vsigma"),
                                       tomlkit.items.SingleKey(line)])
        section.append(key, velocity)

    st.session_state.bands_cfg = cfg
    st.session_state.toml_text = tomlkit.dumps(cfg)
    st.session_state.toml_area_key += 1


def prepare_default(wave_rest, bands):

    # Replace this with your actual function call
    external_cfg = get_spectrum_line_groups(wave_rest, bands)

    if external_cfg is None:
        st.warning("No configuration returned.")
        return

    cfg = st.session_state.bands_cfg
    section = cfg["default_line_fitting"]

    for key, value in external_cfg.items():
        section[key] = value

    if st.session_state.group_lines_toggle:
        new_entries = list(external_cfg.keys())
        existing = list(section.get("grouped_lines", []))
        section["grouped_lines"] = list(dict.fromkeys(existing + new_entries))

    fix_vsigma_formatting(section)

    st.session_state.bands_cfg = cfg
    st.session_state.toml_text = tomlkit.dumps(cfg)
    st.session_state.toml_area_key += 1


def fix_vsigma_formatting(section):
    """Rewrite any map_band_vsigma entries as proper dotted keys."""
    vsigma_entries = {k: v for k, v in section.items()
                      if isinstance(k, str) and k.startswith("map_band_vsigma.")}

    # Remove existing vsigma entries
    for k in vsigma_entries:
        del section[k]

    # Also remove the nested table version if it exists
    if "map_band_vsigma" in section:
        vsigma_dict = section["map_band_vsigma"]
        for line, value in vsigma_dict.items():
            vsigma_entries[f"map_band_vsigma.{line}"] = value
        del section["map_band_vsigma"]

    # Re-add as proper dotted keys
    for dotted_key, value in vsigma_entries.items():
        _, line = dotted_key.split(".", 1)
        key = tomlkit.items.DottedKey([tomlkit.items.SingleKey("map_band_vsigma"),
                                       tomlkit.items.SingleKey(line)])
        section.append(key, value)


def general_band_settings(def_linelist, default_particle_list, def_df):

    # Particle selection
    st.multiselect(label='Particles', options=default_particle_list, placeholder='All', default=None,
                   key='ion_list', help='Bands will be limited to these particles.')

    # Line selection
    in_lines = def_linelist if len(s_state['ion_list']) == 0 else def_df.loc[
        def_df.particle.isin(s_state['ion_list'])].index.sort_values().to_list()
    st.multiselect(label='Include lines', options=in_lines, default=None, key='lines_selected', placeholder='All',
                   label_visibility="visible", help='Select the transitions for the output lines table, by default '
                                                    'all lines will be considered.')
    # Rejected liens
    in_lines = def_linelist if len(s_state['ion_list']) == 0 else def_df.loc[def_df.particle.isin(s_state['ion_list'])].index.sort_values().to_list()
    st.multiselect(label='Exclude lines', options=in_lines, default=None, key='out_lines', placeholder='None',
                   label_visibility="visible", help='Excludes lines from the output lines table.')

    # Bands kinematics
    col0, col1, col2, col3, col4 = st.columns([0.2, 0.2, 0.2, 0.2, 0.2], gap='small')

    # Vacuum wavelengths
    with col0:
        st.space('xxsmall')
        st.space('xxsmall')
        st.toggle("Vacuum wavelengths", value=False, key='vacuum_check', help='Set all transition wavelengths '
                 'to vacuum values. The default behaviour is transitions within 2000Å < λ < 10000Å have air values.')

    # Central bandwidth correction
    with col1:
        st.space('xxsmall')
        st.space('xxsmall')
        st.toggle(label="Modify central band", value=True, key='adj_central', help='Adjust the central'
                  'band using the "bands kinematic" width and the  "sigma number"')

    # Band_vsigma
    with col2:
        st.space('xxsmall')
        st.space('xxsmall')
        st.toggle("Instrumental correction", value=True, key='instr_corr', disabled=not s_state['adj_central'],
                  help='Use an approximation for the observation resolving power to account for the instrument broadening', )

    # Instrument correction check
    with col3:
        st.number_input(label='Velocity width (km/s)', min_value=1, value=70, step=20,
                                      key='bands_velocity',
                                      disabled=not s_state['adj_central'], help='This is the bands with in Gaussian '
                                                                                'standard deviations. The default value is 70 km/s for emission line galaxies.')

    # number of sigmas
    with col4:
        msg = 'This is the number of Gaussian sigmas to compute the bands with.'
        st.number_input('Sigma number', min_value=1, value=4, step=1, key='n_sigma',
                                      help=msg, disabled=not s_state['adj_central'])

    return


def fitcfg_band_settings(def_linelist, default_particle_list, def_df, wave_rest):

    # Section to generate examples
    st.markdown(f'#### Configuration entries')

    # Add default settings
    st.markdown(f'Generate a list of line groups from the selected particles')
    in_df = def_df if len(s_state['ion_list']) == 0 else def_df.loc[def_df.particle.isin(s_state['ion_list'])]
    st.button(label="Predict merged|blended line groups", on_click=prepare_default, args=(wave_rest, in_df), use_container_width=True)

    # Kinematic components row
    st.markdown(f'Add a broad kinematic components configuration entries for the selected lines')
    in_lines = def_linelist if len(s_state['ion_list']) == 0 else def_df.loc[def_df.particle.isin(s_state['ion_list'])].index.sort_values().to_list()

    colA, colB = st.columns([0.5, 0.5])
    with colA:
        st.multiselect(label="Select lines", options=in_lines, placeholder="Select lines",
                       key="selected_lines", label_visibility="collapsed")
    with colB:
        st.button(label="Broad components", on_click=add_kinematic_components, use_container_width=True)


    colC, colD, colE = st.columns([0.4, 0.1, 0.5])
    with colC:
        st.markdown(f'Change the band velocity dispersion for certain lines')
        st.multiselect(label="Lines velocity width",  options=in_lines, placeholder="Select lines", default=None,
                       key="vsigma_lines", label_visibility="collapsed")
    with colD:
        st.markdown("Velocity (km/s)")
        st.number_input(label="Velocity (km/s)", min_value=1, value=200, step=20, key="vsigma_velocity",
                        label_visibility="collapsed")
    with colE:
        st.space(25)
        st.button(label="Bands velocity dispersion", on_click=add_vsigma_components, use_container_width=True)

    # Toggle to add groups generated to
    col_toggleA, col_toggleB, _ = st.columns([0.3, 0.3, 0.4])
    with col_toggleA:
        st.toggle(label='Add new entries to "grouped_lines" list', value=True, key="group_lines_toggle")
    with col_toggleB:
        st.toggle("Automatic group selection", value=False, key='auto_group',
                  help='Automatic selection of the group selected by the user')
    st.space('small')

    # Fitting configuration equivalent
    st.markdown(f'#### Fitting configuration')
    st.markdown(f'This section represents an [input toml file](https://toml.io/en/) for LiMe functions. Please check the '
                f'[documentation](https://lime-stable.readthedocs.io/en/latest/1_introduction/5_fitting_configuration.html#loading-the-fitting-configuration-from-a-text-file) '
                f'for more tips on how to adjust your fittings')
    st.text_area(label="Toml file", value=st.session_state.toml_text, label_visibility="collapsed",
                 height=300, key=f"toml_input_{st.session_state.toml_area_key}", on_change=on_toml_change)


    return


def compute_bands():

    if "bands_cfg" not in st.session_state:
        default = {"default_line_fitting": {}}
        st.session_state.bands_cfg = tomlkit.loads(tomlkit.dumps(default))

    if "toml_text" not in st.session_state:
        st.session_state.toml_text = tomlkit.dumps(st.session_state.bands_cfg)

    if "toml_area_key" not in st.session_state:
        st.session_state.toml_area_key = 0

    tab_general, tab_fit_cfg, tab_upload = st.tabs(["Global settings", "Fit configuration settings", "Load from file"])

    # Input spectra definition
    spec = s_state['spec']
    def_df = spec.retrieve.lines_frame()
    def_linelist = def_df.index.sort_values().to_list()
    default_particle_list = list(def_df.particle.sort_values().unique())

    # Initial configuration values
    with tab_general:
        general_band_settings(def_linelist, default_particle_list, def_df)

    # Fit config mode
    with tab_fit_cfg:
        fitcfg_band_settings(def_linelist, default_particle_list, def_df, spec.wave_rest.data)

    # Load from file
    with tab_upload:
        st.markdown(f'### Frame file address')
        uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

    # Generate the bands
    st.space('small')
    if st.button("Generate bands"):

        # Delete previous bands df if present
        if s_state['bands_df'] is not None:
            save_state('bands_df', None)

        # ReInitialize counter for he bands editor
        if 'bands_editor_version' not in st.session_state:
            st.session_state['bands_editor_version'] = 0
        else:
            st.session_state['bands_editor_version'] += 1

        # Uploaded file always overwrite but warning is given
        if uploaded_file is None:
            spec = s_state['spec']
            input_cfg = parse_lime_cfg(tomlkit.loads(st.session_state.toml_text).unwrap())
        else:
            st.warning(f'Using uploaded bands')
            input_cfg = None

        if input_cfg is not None:
            bands = spec.retrieve.lines_frame(line_list=s_state['lines_selected'] or None,
                                              particle_list=s_state['ion_list'] or None,
                                              vacuum_waves=s_state['vacuum_check'],
                                              fit_cfg=input_cfg,
                                              automatic_grouping=s_state['auto_group'],
                                              rejected_lines=s_state['out_lines'] or None,
                                              adjust_central_band=s_state['adj_central'],
                                              band_vsigma=s_state['bands_velocity'],
                                              n_sigma=s_state['n_sigma'],
                                              instrumental_correction=s_state['instr_corr'],
                                              update_latex=False)
            save_state('bands_df', bands)

        else:
            try:
                save_state('bands_df', parse_line_bands_df(uploaded_file))
            except Exception as e:
                st.error(f"An error occurred loading the line bands file:\n{e}")

    return


def load_frame_tab():

    st.markdown(f'### Frame file address')
    uploaded_file = st.file_uploader("Choose a '.txt' file", type=['.txt'])

    # if st.form_submit_button("Upload lines frame"):
    if st.button("Upload lines frame"):

        # Load the measurements after clearing the old ones
        try:
            s_state['lines_df'] = None
            if s_state.get('spec') is not None:
                s_state['spec'].clear_data()
            save_state(param='lines_df', value=parse_line_bands_df(uploaded_file))
        except Exception as e:
            st.error(f"An error occurred loading the line measurements frame:\n{e}")

        # Assign the line measurements to the spectrum if available
        if s_state.get('spec') is not None:
            try:
                spec = s_state['spec']
                spec.load_frame(s_state['lines_df'])
                save_state(param='spec', value=spec)
            except Exception as e:
                st.warning(f"An error occurred trying to assign the uploaded lines measurements to the current observation:\n{e}")

    return


def declare_line_measuring():

    # Tabs for fitting lines and for loading measurements
    tab_fit, tab_upload = st.tabs(['Measure lines', 'Upload measurements'])

    with tab_fit:

        st.markdown(f'### Write the fitting configuration:')
        # st.text_area('Please follow .toml style', key='fit_cfg', height=300, placeholder=FIT_CFG_PLACEHOLDER,
        #              on_change=widget_save_state, help=FIT_CFG_HELP, args=("fit_cfg",))

        st.text_area(label="Bands configuration", value=st.session_state.toml_text, height=300,
                     help=FIT_CFG_HELP, key=f"toml_input_{st.session_state.toml_area_key}", on_change=on_toml_change)

        if s_state['spec'] is not None:

            # Show upload button if inputs are declared
            if (s_state['bands_df'] is not None) and (s_state['fit_cfg'] is not None):

                # Every form must have a submit button.
                submitted = st.button("Fit lines", key='button_bands')

                if submitted:

                    spec, bands = s_state['spec'], s_state['bands_df']
                    conf = parse_fit_cfg(s_state['fit_cfg'])

                    # Clear previous measurements
                    spec.frame = spec.frame.iloc[0:0]

                    # Measuring the lines
                    try:
                        my_bar = st.progress(int(spec.fit._i_line), text='Measuring the lines')
                        spec.fit.frame(bands, fit_cfg=conf)
                        my_bar.empty()
                    except Exception as e:
                        st.error(f"An error occurred: {e}")

                    # Save the dataframe which now contains the measurements
                    save_state('spec', spec)
                    save_state('lines_df', spec.frame.copy())

            else:
                st.write('Please declare the line bands')

        else:
            st.write('Please upload a spectrum')

    # Query surveys
    with tab_upload:
        with st.form('load_lines_form', border=False, enter_to_submit=False, clear_on_submit=False):
            load_frame_tab('lines_df')
            if s_state.lines_df is not None:
                st.success('Successful upload')
                st.dataframe(s_state.lines_df)

    return


def declare_spectrum_form():

    tab_load, tab_collabs, tab_query = st.tabs(["Load spectrum", "Collaborations", "Query survey"])

    # Load spectrum
    with tab_load:
        load_spectrum_tab()

    # Check from collaborations
    with tab_collabs:

        # Authenticate the user
        authenticator = stauth.Authenticate(secrets.collaborations.credentials.to_dict(), cookie_name=secrets.cookie.name,
                                            cookie_key=secrets.cookie.key, cookie_expiry_days=secrets.cookie.expiry_days)
        authenticator.login(location='main')

        if s_state.get('authentication_status'):
            st.write(s_state["username"])

            # Give the option to logout
            authenticator.logout(button_name='Collaboration logout')

    # Query surveys
    with tab_query:
        st.write('Not implemented')

    return


def handle_change():
    # Read the updated table from session_state
    st.session_state.bands_df = st.session_state["bands_df"]

    return


def band_slider(column, label, idcs, idx_central, wave_array, min_val, max_val, disabled=False):

    """
    Displays a Streamlit slider in a given column to adjust a wavelength band.

    Parameters:
    - column: st.column object
    - label: slider label
    - idcs: 2-element np.array of indices relative to wave_array
    - idx_central: central wavelength index
    - wave_array: numpy array of wavelength values
    - min_val, max_val: slider bounds
    - disabled: bool to disable the slider

    Returns:
    - 2-element array of updated wavelength values
    """

    with column:
        slider_val = st.slider(label=label, value=tuple(idcs - idx_central), min_value=min_val, max_value=max_val,
                               step=1, disabled=disabled)

        # Minimum number of pixels
        return slider_val[0] + idx_central, slider_val[1] + idx_central
        # return wave_array[slider_val[0] + idx_central], wave_array[slider_val[1] + idx_central]


def start_bounds(spec, output_bands,):
    s_state.idx_label = output_bands.index[output_bands["label"] == s_state.line_selected][0]
    s_state.idx_central = searchsorted(spec.wave_rest.data, output_bands.loc[s_state.idx_label, 'wavelength'])
    idcs_in = searchsorted(spec.wave_rest, output_bands.loc[s_state.idx_label, 'w1':'w6'].to_numpy()) - s_state.idx_central
    s_state.lower = tuple(idcs_in[0:2])
    s_state.central = tuple(idcs_in[2:4])
    s_state.upper = tuple(idcs_in[4:6])
    review_bounds()

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


def band_sliders(selected, wave_rest, wbands, idx_min, idx_max):
    labels = [("Blue continuum", "w1 - w2"), ("Line region", "w3 - w4"), ("Red continuum", "w5 - w6")]
    keys = ["left", "center", "right"]
    idxs = searchsorted(wave_rest, wbands).tolist()

    new_idxs = []
    for col, (title, label), key, (i, j) in zip(st.columns(3), labels, keys, zip(idxs[::2], idxs[1::2])):
        with col:
            st.markdown(f"**{title}**")
            s1, s2 = st.slider(label, min_value=idx_min, max_value=idx_max,
                               value=(int(i), int(j)), key=f"slider_{key}_{selected}")
            new_idxs.extend([s1, s2])

    return new_idxs


def tab_single_editor(edited_df, spec):

    if edited_df is not None and not edited_df.empty:
        selected = st.selectbox("Select band", options=edited_df.index)

        wave_rest = spec.wave_rest.data
        wbands = edited_df.loc[selected, ['w1', 'w2', 'w3', 'w4', 'w5', 'w6']].to_numpy()
        idx1, idx2, idx3, idx4, idx5, idx6 = searchsorted(wave_rest, wbands)
        idx_min = int(max((0, idx1 - 10)))
        idx_max = int(min((idx6 + 10, wave_rest.size - 1)))


        col_title, col_log, _ = st.columns([0.3, 0.3, 0.3])

        with col_title:
            st.markdown("##### Band edges (pixel index)")
        with col_log:
            log_check = st.toggle(label="Logarithmic scale", value=False, key='log_band_check')


        col_left, col_center, col_right = st.columns(3)

        with col_left:
            st.markdown("**Blue continuum**")
            s1, s2 = st.slider("w1 - w2", min_value=idx_min, max_value=idx_max,
                               value=(int(idx1), int(idx2)), key=f"slider_left_{selected}")
        with col_center:
            st.markdown("**Line region**")
            s3, s4 = st.slider("w3 - w4", min_value=idx_min, max_value=idx_max,
                               value=(int(idx3), int(idx4)), key=f"slider_center_{selected}")
        with col_right:
            st.markdown("**Red continuum**")
            s5, s6 = st.slider("w5 - w6", min_value=idx_min, max_value=idx_max,
                               value=(int(idx5), int(idx6)), key=f"slider_right_{selected}")

        limits_new = array([wave_rest[s1], wave_rest[s2], wave_rest[s3],
                            wave_rest[s4], wave_rest[s5], wave_rest[s6]])

        if any(limits_new != wbands):
            edited_df.at[selected, 'w1'] = wave_rest[s1]
            edited_df.at[selected, 'w2'] = wave_rest[s2]
            edited_df.at[selected, 'w3'] = wave_rest[s3]
            edited_df.at[selected, 'w4'] = wave_rest[s4]
            edited_df.at[selected, 'w5'] = wave_rest[s5]
            edited_df.at[selected, 'w6'] = wave_rest[s6]
            save_state('bands_df', edited_df)
            st.rerun()

        # Plot the selection
        plot_bokeh_bands(wave_rest[idx_min:idx_max], spec.flux.data[idx_min:idx_max], selected, limits_new, log_check)

    return edited_df


def bands_review():

    spec = st.session_state.spec

    edited_df = st.data_editor(st.session_state['bands_df'], num_rows='delete',
                               key=f"bands_editor_{st.session_state['bands_editor_version']}")

    # Tabs showing the full spectrum
    st.space('small')
    tabs_all, tab_single = st.tabs(['Full spectrum', 'Individual bands'])

    with tabs_all:
        bokeh_spectrum('spec', edited_df)

    with tab_single:
        tab_single_editor(edited_df, spec)

    return


def display_menu():

    # Check file has been uploaded
    if s_state['spec'] is not None:

        if s_state['obs_type'] == 'upload':

            # Show the spectrum
            st.markdown("***")
            st.markdown(f'## Input observation')

            # Plot spectrum
            bokeh_spectrum('spec')

            # Download
            rec_arr = get_text_spectrum('spec')
            csv = convert_for_download(rec_arr)
            st.download_button(label="Download as .txt", data=csv, file_name="spectrum.csv", mime="text/csv",
                               icon=":material/download:")

        elif s_state['obs_type'] == 'collaboration':
            if s_state["username"] == 'capers':
                st.write(f'Capers visualization is not implemented')

        elif s_state['obs_type'] == 'query':
            st.write(f'Query visualization is not implemented')

        else:
            return

    return


def samples_widgets_selection(input_df, sample_check=False, redshift_check=False, id_check=False, redshift_label="z_UNICORN",
                             id_label=None, example_ids=None):

    if sample_check or redshift_check:

        col1, col2 = st.columns(2, gap='large')

        # Sample selection
        with col1:
            if sample_check:
                default_samples = input_df.index.get_level_values('sample').unique().to_numpy()
                st.multiselect('**Sample selection:**', options=list(default_samples),
                                key='sample_list', on_change=save_objSample, args=("sample_list",))

        # Redshift range selection
        with col2:
            if redshift_check:
                label_text = '**Redshift range:**'
                help_text = f'The observations list will be limited to the input {redshift_label} range'
                z_limits = floor(input_df.z_UNICORN.min()), ceil(input_df.z_UNICORN.max())

                # Initial values for the range for first time
                if s_state.get('z_range') is None:
                    save_state('z_range', z_limits)

                st.slider(label_text, min_value=z_limits[0], max_value=z_limits[1], step=0.2,
                          key='z_range', help=help_text, on_change=save_objSample, args=("z_range",))


    # IDs selection
    if id_check:
        label_text = '**Object selection (comma separated)**'
        help_text = f'The observations list will be limited to the input "{id_label}"'
        st.text_area(label=label_text, value=None, key='mpt_list', help=help_text, placeholder=example_ids,
                     on_change=save_objSample, args=("mpt_list",),)

    return


def indexing_sheets(input_df, sample_list=None, z_range=None, ref_redshift=None, mpt_list=None, ID_hdr=None, ID_types=int):

    # Sample indexing
    if sample_list is not None:
        idcs = input_df.index.get_level_values('sample').isin(s_state['sample_list'])
    else:
        idcs = input_df.index

    # Redshift range indexing
    if (z_range is not None) and (ref_redshift is not None):
        idcs = idcs & (input_df[ref_redshift] >= z_range[0]) & (input_df[ref_redshift] <= z_range[1])

    # Name selection
    if (mpt_list is not None) and (mpt_list != "") and (ID_hdr is not None):
        mpt_array = widget_text_to_list(mpt_list, ID_types)
        idcs_selection = input_df[ID_hdr].isin(mpt_array)
        mpt_found = input_df.loc[idcs_selection, ID_hdr].unique()
        idcs = idcs & idcs_selection

        if len(mpt_found) > 0:
            msg = f'The object {mpt_found} was found on the dataset' if len(mpt_found) == 1 else f'The objects {mpt_found} were found on the dataset'
            st.warning(msg)

    n_objs = idcs.shape[0]

    # No objects in selection
    if n_objs == 0:
        st.warning(f'There are not observations for the current selection')
    else:
        st.caption("")
        st.caption("Use the tools in the upper-right corner to expand the table, hide columns, or download it.")
        st.dataframe(input_df.loc[idcs])

    return idcs, n_objs


@st.cache_data
def load_demo_data() -> DataFrame:
    rng = random.default_rng(42)
    transitions = ["H1_4861A", "H1_6563A", "O2_3726A", "O2_3729A", "O3_4363A",
                    "O3_4959A", "O3_5007A", "S2_6717A", "S2_6731A", "S3_6312A",
                    "S3_9069A", "N2_6548A", "N2_6584A", "He1_5876A", "He2_4686A",
                    "Ar3_7136A", "Ar4_4711A", "Ar4_4740A", "Ne3_3869A", "Ne3_3968A",]
    particles = [t.split("_")[0] for t in transitions]
    fluxes    = rng.lognormal(mean=0.0, sigma=1.2, size=len(transitions)).round(4)
    return DataFrame({"particle": particles, "flux": fluxes}, index=transitions)

# Region cards
def get_taken_particles(region_labels, current_region_idx):
    taken = set()
    for i, lbl in enumerate(region_labels):
        if i == current_region_idx:
            continue
        key = f"region_{lbl}_particles"
        taken.update(st.session_state.get(key, []))
    return taken


def ionization_structure_interface(obs_df, TEM_DICT = {'eqT1': None, 'eqT2': None, 'eqT3': None, 'eqT4': None},
                                           DEN_DICT = {'eqNe1': None, 'eqNe2': None, 'eqNe3': None, 'eqNe4': None}):

    if obs_df is None:
        obs_df = load_demo_data()

    all_particles = sorted(obs_df["particle"].unique().tolist())

    # Formating for the labels
    st.markdown(REGION_TAGS_STYLE, unsafe_allow_html=True)

    col_reg, col_kinem, col_norm, _ = st.columns([0.25, 0.25, 0.25, 0.25], gap='medium')

    # Number of regions selectbox
    with col_reg:
        n_regions = st.selectbox(label="Number of regions", options=[1, 2, 3, 4], key="n_regions",
                                 help="Changing the number of regions clears all widget state.")

    with col_kinem:
        st.selectbox(label="Kinematic component", options=[0], key="kinem_order_specsy", help="Normalization label.")


    # ── Session-state reset when n_regions changes ────────────────────────────────
    _sentinel_key = f"__sentinel_{n_regions}__"
    if _sentinel_key not in st.session_state:
        for k in list(st.session_state.keys()):
            if k.startswith("region_"):
                del st.session_state[k]
        st.session_state[_sentinel_key] = True

    # st.markdown("<br>", unsafe_allow_html=True)

    region_labels = REGION_LABELS[n_regions]

    # Loop through the regions and produce the widgets
    cols = st.columns(n_regions, gap="medium")
    for idx, (col, region_name) in enumerate(zip(cols, region_labels)):

        with col:

            # Region label
            st.markdown(card_formating(region_name), unsafe_allow_html=True)

            # Particle selection
            taken = get_taken_particles(region_labels, idx)
            available_particles = [p for p in all_particles if p not in taken]
            sel_particles = st.multiselect(label="Species", options=available_particles,
                                           key=f"region_{region_name}_particles",
                                           help="Select the ionic species assigned to this region. Particles chosen here are"
                                                " removed from other regions.")

            # Line selection
            matching_lines = obs_df[obs_df["particle"].isin(sel_particles)].index.tolist() if sel_particles else []
            st.multiselect(label="Lines to exclude", options=matching_lines, default=[],
                           key=f"region_{region_name}_exclude",
                           help="Lines selected here will be excluded from the fit. By default all matching lines are included.")

            # Temperature - density modes
            c3, c4 = st.columns(2)
            select_box_msg = "Tied to region ->"

            with c3:
                temp_mode = st.selectbox(label="Temperature mode", options=["free", "tied"],
                                         key=f"region_{region_name}_temp_mode")
                if temp_mode == "tied":
                    options = REGION_LABELS[n_regions] + ['relation']
                    options.remove(region_name)
                    st.selectbox(label=select_box_msg, options=options, key=f"region_{region_name}_temp_tied_to")
                    st.selectbox(label="Temperature equation", options=['None'] + list(TEM_FUNC_DICT.keys()), key=f"region_{region_name}_temp_relation")

            with c4:
                den_mode = st.selectbox(label="Density mode", options=["free", "tied"],
                                        key=f"region_{region_name}_den_mode")
                if den_mode == "tied":
                    options = REGION_LABELS[n_regions] + ['relation']
                    options.remove(region_name)
                    st.selectbox(label=select_box_msg, options=options, key=f"region_{region_name}_den_tied_to")
                    st.selectbox(label="Relation", options=['None'] + list(DEN_FUNC_DICT.keys()), key=f"region_{region_name}_den_relation")

            st.markdown("</div>", unsafe_allow_html=True)

    return

def sampler_cfg_widget():

    cores_max = cpu_count() or 1
    cores_recommended = max((1, cores_max - 4))
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.number_input("Draws", min_value=100, value=300, step=500, key='draws_pymc')

    with col2:
        st.number_input("Tune", min_value=100, value=300, step=200, key='tune_pymc')

    with col3:
        st.number_input(f"Chains (max = {cores_max})", min_value=1, max_value=cores_max,
                                 value=cores_recommended, step=1, key='chains_pymc')

    with col4:
        st.number_input(f"Cores (max = {cores_max})", min_value=1, max_value=cores_max,
                                value=cores_recommended, step=1, key='cores_pymc')

    with col5:
        st.selectbox("NUTS sampler", options=["numpyro", "nutpie", "pymc", "blackjax"], key='sampler_pymc')


    return


def make_sampling_callback():

    total_steps = s_state['draws_pymc'] * s_state['chains_pymc']  # callback only fires on draws, not tune
    chain_draws = {i: 0 for i in range(s_state['chains_pymc'])}

    progress_bar = st.progress(0, text=f"Sampling for {s_state['chains_pymc'] * s_state['draws_pymc']} steps...")

    def sampling_callback(trace, draw):
        if not draw.tuning:
            chain_draws[draw.chain] += 1
            completed = sum(chain_draws.values())
            progress = min(completed / total_steps, 1.0)
            progress_bar.progress(progress,
                                  text=f"Chain {draw.chain + 1}/{s_state['chains_pymc']} | draw {chain_draws[draw.chain]}/{s_state['draws_pymc']}")

    s_state['nebula'].infer.direct_method.run(draws=s_state['draws_pymc'], tune=s_state['tune_pymc'],
                                             target_accept=0.8, chains=s_state['chains_pymc'],
                                             cores=s_state['cores_pymc'], callback=sampling_callback,
                                             nuts_sampler=s_state['sampler_pymc'])


    progress_bar.progress(1.0, text="Sampling complete!")

    st.balloons()

    return


DISTRIBUTION_OPTIONS = ["Normal", "HalfNormal", "HalfCauchy", "Lognormal", "Uniform"]
PRIOR_COLUMNS = ["distribution", "center", "sigma", "factor", "shift"]
REGION_KEYS = ["low", "med", "high", "vhigh"]


def prior_configuration_widget(default_priors: dict, regions: list) -> dict:
    """
    Streamlit widget for configuring model priors.

    Parameters
    ----------
    default_priors : dict
        Default prior configuration mimicking the toml structure.
    regions : list
        List of region names to display temp/den priors for e.g. ["low", "high"]

    Returns
    -------
    dict
        Updated prior configuration in the same format as the input toml.
    """

    st.header("Prior Configuration")
    output = {}

    # --- helper to render one prior row ---
    def render_prior_row(key, defaults):
        dist, center, sigma, factor, shift = defaults
        cols = st.columns([2, 2, 2, 2, 2, 2])

        # small vertical space to align label with widgets
        cols[0].space(20)
        cols[0].markdown(f"**{key}**")

        new_dist = cols[1].selectbox(
            "Distribution", DISTRIBUTION_OPTIONS,
            index=DISTRIBUTION_OPTIONS.index(dist),
            key=f"{key}_dist"
        )

        # adapt parameter names and behavior based on distribution
        if new_dist == "Uniform":
            new_center = cols[2].number_input(
                "Lower limit", value=float(center),
                key=f"{key}_center"
            )
            new_sigma = cols[3].number_input(
                "Upper limit", value=float(sigma),
                key=f"{key}_sigma"
            )

        elif new_dist.startswith("Half"):
            # mean is always zero for half distributions, disabled
            new_center = cols[2].number_input(
                "Center", value=0.0,
                disabled=True,
                key=f"{key}_center"
            )
            new_sigma = cols[3].number_input(
                "Sigma", value=float(sigma), min_value=0.0,
                key=f"{key}_sigma"
            )

        else:
            new_center = cols[2].number_input(
                "Center", value=float(center),
                key=f"{key}_center"
            )
            new_sigma = cols[3].number_input(
                "Sigma", value=float(sigma), min_value=0.0,
                key=f"{key}_sigma"
            )

        new_factor = cols[4].number_input(
            "Factor", value=float(factor),
            key=f"{key}_factor"
        )
        new_shift = cols[5].number_input(
            "Shift", value=float(shift),
            key=f"{key}_shift"
        )

        return [new_dist, new_center, new_sigma, new_factor, new_shift]

    # --- temperatures ---
    st.subheader("Temperatures")
    header_cols = st.columns([2, 2, 2, 2, 2, 2])
    for col, label in zip(header_cols[1:], PRIOR_COLUMNS):
        col.markdown(f"*{label}*")

    for region in regions:
        key = f"temp_{region}"
        if key in default_priors:
            output[key] = render_prior_row(key, default_priors[key])

    # --- densities ---
    st.subheader("Densities")
    header_cols = st.columns([2, 2, 2, 2, 2, 2])
    for col, label in zip(header_cols[1:], PRIOR_COLUMNS):
        col.markdown(f"*{label}*")

    for region in regions:
        key = f"den_{region}"
        if key in default_priors:
            output[key] = render_prior_row(key, default_priors[key])

    # --- other priors (everything except temp/den) ---
    st.subheader("Other Priors")
    header_cols = st.columns([2, 2, 2, 2, 2, 2])
    for col, label in zip(header_cols[1:], PRIOR_COLUMNS):
        col.markdown(f"*{label}*")

    skip_keys = {f"temp_{r}" for r in REGION_KEYS} | {f"den_{r}" for r in REGION_KEYS}
    for key, defaults in default_priors.items():
        if key not in skip_keys:
            output[key] = render_prior_row(key, defaults)

    return output

def extinction_parameters_dm():

    st.markdown('The reddening law is calculated using [PyNeb](https://research.iac.es/proyecto/PyNeb/ext_law.html)')

    col1, col2, col3, col4 = st.columns(4, gap='large')

    with col1:
        st.selectbox('Normalization line', ['H1_4861A'], key='norm_line_dm')

    with col2:
        st.selectbox("Reddening Law", options=["CCM89", "CCM89 Bal07", "CCM89 oD94", "S79 H83 CCM89", "K76", "SM79 Gal", "G03 LMC",
                          "MCC99 FM90 LMC", "F99-like", "F99", "F88 F99 LMC"], key='rLaw_dm', help=f'Reddening laws using PyNeb notation')
    with col3:
        st.number_input("Rᵥ", min_value=0.0, value=3.1, step=0.1, key='Rv_dm')

    with col4:
        st.space('xxsmall')
        st.space('xxsmall')
        st.toggle(label="Normalize fluxes", value=True, key="norm_check", help="Divide the fluxes by H1_4861A")

    return