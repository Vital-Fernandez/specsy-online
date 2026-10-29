import tempfile
from pathlib import Path

import numpy as np
import streamlit as st
from streamlit import session_state as s_state

from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils import bokeh_server
from streamlit_bokeh import streamlit_bokeh


def update_spectrum(**retrieve_kwargs):

    # Button callback: replace the session spectrum and reload the plot keeping the current selection
    try:
        new_spec = s_state['spec'].retrieve.spectrum(**retrieve_kwargs)
    except Exception as e:
        s_state['mask_error'] = f'Could not update the spectrum: {e}'
        return

    s_state['spec'] = new_spec
    s_state['spec_hold'] = new_spec
    s_state['mask_launch'] = s_state.get('mask_launch', 0) + 1
    return

def apply_masks():

    # Read the file on click, so it includes the latest edits in the plot
    if not s_state['mask_file'].is_file():
        s_state['mask_error'] = 'No intervals selected: draw at least one span in the plot.'
        return

    masks = np.loadtxt(s_state['mask_file'], ndmin=2)[:, :2]
    update_spectrum(mask_intvls=masks)
    return


def remove_pixel_masks():
    update_spectrum(pixel_mask=np.zeros(s_state['spec'].wave.data.size, dtype=bool))
    return

# Sidebar information
sidebar_widgets()

# Introduction text
st.markdown(f'# Spectrum masking')

# Check if observation is available
spec = s_state.get('spec')
if spec is not None:

    st.write('Select the initial values for the masking function. Afterwards launch the interactive plot manually adjust '
             'the intervals.')

    # Per-session working folder and masks file (written live by the Bokeh editor)
    if 'mask_file' not in s_state:
        s_state['mask_dir'] = Path(tempfile.mkdtemp(prefix='specsy_masks_'))
        s_state['mask_file'] = s_state['mask_dir'] / 'masks.txt'
    mask_file = s_state['mask_file']

    # ------------------------------------------------ 1) Inputs (nothing reloads until the button is pressed)
    with st.form('mask_inputs', border=False):

        colA, colB = st.columns([0.5, 0.5], gap='large')

        with colA:
            in_lines = spec.retrieve.lines_frame().index.to_numpy()
            st.multiselect(label='Line list', options=in_lines, default=None, key='line_mask_selection',
                           placeholder='None', help='Lines labelled on the plot')
            intvls_upload = st.file_uploader('Initial intervals (optional)', type=['txt', 'dat'],
                                             help='Two columns: w_low w_high. Loaded each time the plot is '
                                                  'launched.')

        with colB:
            st.checkbox('Log scale', value=False, key='log_scale_check',
                        help='Display the spectrum in logarithmic scale.')
            st.checkbox('Rest frame', value=False, key='rest_frame_check',
                        help='Display the spectrum in the rest frame.')
            st.checkbox('Show uncertainty', value=False, key='show_err_check', help='Plot the 1σ flux band.')
            st.checkbox('Show masked pixels', value=True, key='show_masks_check')
            st.checkbox('Intervals in rest frame', value=True, key='match_obs_frame_check',
                        help='Store the intervals in the rest frame (match_obs_frame).')

        launch = st.form_submit_button('Launch interactive plot', type='primary', icon=':material/play_arrow:',
                                       help='Launching the plot resets the current selection.')

    # ------------------------------------------------ 2) Interactive plot
    st.write('***')
    if launch:

        # Every launch starts a new selection (from the uploaded intervals, if any)
        mask_file.unlink(missing_ok=True)

        intvls_path = None
        if intvls_upload is not None:
            intvls_path = s_state['mask_dir'] / f'input_{intvls_upload.name}'
            intvls_path.write_bytes(intvls_upload.getvalue())

        # Snapshot of the inputs used by the plot
        s_state['mask_kwargs'] = dict(intvls=intvls_path,
                                      line_list=list(s_state['line_mask_selection']) or None,
                                      log_scale=s_state['log_scale_check'],
                                      rest_frame=s_state['rest_frame_check'],
                                      show_err=s_state['show_err_check'],
                                      show_masks=s_state['show_masks_check'],
                                      match_obs_frame=s_state['match_obs_frame_check'])
        s_state['mask_launch'] = s_state.get('mask_launch', 0) + 1

    kwargs = s_state.get('mask_kwargs')
    if kwargs is not None:

        # Live editor (app launched with serve.py)
        if bokeh_server.BOKEH_MOUNTED:

            st.markdown("Mouse controls:\n")

            colA, colB = st.columns([0.5, 0.5])
            with colA:
                st.markdown("* Left-click and drag to create a span.\n"
                            "* Double-click on a span to delete it.\n"
                            "* Use the toolbar to pan/zoom, then re-select *Add mask region* to keep adding spans.")
            with colB:
                st.markdown("* Drag a span edge to resize it.\n"
                            "* Drag its interior to move it.\n")


            # Reloads (with a new selection) only when the button is pressed again
            # The iframe is sized to the figure, so the download button sits just below it
            fig_width, fig_height = 1000, 500
            bokeh_server.bokeh_live(lambda doc: spec.bokeh.masks(doc=doc, fname=mask_file,
                                                                 fig_cfg={'width': fig_width, 'height': fig_height},
                                                                 **kwargs),
                                    key='masks', reload_on=s_state['mask_launch'], height=fig_height + 30)

            # ------------------------------------------------ 3) Download / apply / remove masks
            def get_mask_files_data():
                return mask_file.read_bytes() if mask_file.is_file() else b'# w_low w_high\n'

            colA, colB, colC, _ = st.columns([0.2, 0.2, 0.25, 0.35])
            with colA:
                st.download_button('Download masks', data=get_mask_files_data, file_name='masks.txt',
                                   mime='text/plain', on_click='ignore', icon=':material/download:')
            with colB:
                st.button('Apply masks', on_click=apply_masks, icon=':material/filter_alt:',
                          help='Mask the selected intervals in the spectrum.')
            with colC:
                st.button('Remove pixel masks', on_click=remove_pixel_masks, icon=':material/filter_alt_off:',
                          help='Remove all the pixel masks from the spectrum.')

            # Errors from the button callbacks
            if 'mask_error' in s_state:
                st.error(s_state.pop('mask_error'))

        # Fallback (e.g. Streamlit Community Cloud)
        else:
            st.info('The interactive mask editor is only available in the local version of specsy-online '
                    '(`pip install specsy-online`, then run `specsy`). Here you can inspect the spectrum.',
                    icon=':material/info:')

            spec.bokeh.spectrum(line_list=kwargs['line_list'], log_scale=kwargs['log_scale'],
                                rest_frame=kwargs['rest_frame'], show_err=kwargs['show_err'], in_fig=None)
            streamlit_bokeh(spec.bokeh.fig, key='bokeh_masking_plot', use_container_width=True)

else:
    st.markdown(f'### No observation available')
    st.page_link("pages/1a_Load_spectrum.py", label='Please load an spectrum :yellow[**(link)**]', icon=":material/upload:")
    st.page_link("pages/1b_Load_collaboration.py", label='or get an observation from the virtual observatory page :yellow[**(link)**]', icon=":material/archive:")