import streamlit as st
from streamlit import session_state as s_state
from specsy_online.utils.sidebar import sidebar_widgets
from specsy_online.utils.plots import bokeh_spectrum
from numpy import savetxt, column_stack
from io import StringIO
from numpy import ndarray


def _is_float(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False

def _to_int(s: str) -> int:
    f = float(s)  # handles "2", "2.0", "2.1" etc.
    if not f.is_integer():
        raise ValueError(f"{s!r} is not a whole number")
    return int(f)


def parse_str_list_to_arr(text: str, dtype, parse_none=True, err_msg=None, empty_error_msg=None,
                          converters = {int: _to_int, float: float}, ) -> ndarray:

    # Return None
    if text is None or text == 'none':
        if parse_none:
            return None
        else:
            st.error(empty_error_msg if empty_error_msg else 'Missing user widget input.')
            st.stop()

    # Return the entries
    else:
        parts = text.replace('\n', '')
        parts = text.replace(' ', '')
        parts = text.split(",")
        convert = converters[dtype]
        try:
            return [convert(p) for p in parts]
        except ValueError:
            bad = [p for p in parts if not _is_float(p)]
            st.error(err_msg if err_msg else f"❌ Could not convert to {dtype.__name__}. Invalid value(s): `{', '.join(bad)}`")
            st.stop()



# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Continuum fitting')

# fname = '/home/vital/PycharmProjects/lime/examples/doc_notebooks/0_resources/spectra/sdss_dr18_0358-51818-0504.fits'
# s_state['spec'] = lime.Spectrum.from_file(fname, instrument='sdss')
spec = s_state.get('spec')

# Check file has been uploaded
if spec is not None:

    st.markdown(f'### The widgets below can be used to fit the spectrum continuum using a polynomial.')

    with st.form('cont_fut', border=False, enter_to_submit=False, clear_on_submit=False):

        # First set of parameters
        col_listA = st.columns([0.25, 0.25, 0.25, 0.25], gap='small')

        with col_listA[0]:
            order_list = st.text_input('List polynomial orders', value='3, 4, 4', placeholder='3, 4, 4',
                                       help='')

        with col_listA[1]:
            emis_threshold = st.text_input('Emission intensity threshold', value='5, 4, 3', placeholder='5, 4, 3',
                                           help='')

        with col_listA[2]:
            abs_threshold = st.text_input('Absorption intensity threshold', value=None, placeholder='5, 4, 3',
                                          help='')

        with col_listA[3]:
            smooth_scale = st.selectbox('Smooth scale', options=[0,1,2,3,4,5,6,7,8,9,10], index=0,
                                        help='')

        # Second set of parameters
        col_listB = st.columns([0.75, 0.25], gap='small')

        with col_listB[0]:
            example_msg = '[[5700, 5800], [7100, 7200]]'
            help_msg = ''
            masked_intervals = st.text_input('Masked intervals', value=None, placeholder=example_msg, help=help_msg)

        with col_listB[1]:
            st.space("xxsmall")
            st.space("xxsmall")
            rest_intvls = st.checkbox("Rest frame", help='The masked intervals are declared in the rest frame')

        # Every form must have a submit button.
        st.space('small')
        submitted = st.form_submit_button("Run fit")

        # Load the dataframe
        if submitted:
            order_list = parse_str_list_to_arr(order_list, dtype=int)
            emis_threshold = parse_str_list_to_arr(emis_threshold, dtype=float)
            abs_threshold = parse_str_list_to_arr(abs_threshold, dtype=float, parse_none=True)
            smooth_scale = None if smooth_scale == 0 else smooth_scale

            # Make sure entries have the right format
            spec.fit.continuum(degree_list=order_list, emis_threshold=emis_threshold, smooth_scale=smooth_scale)

    # Display the spectrum
    if spec.cont is not None:
        bokeh_spectrum(spec_key='spec', default_components=False, default_show_fits=False,
                       default_show_cont=True if spec.cont is not None else False)


        def arrays_to_txt(wave_arr, flux_arr):
            buffer = StringIO()
            savetxt(buffer, column_stack([wave_arr, flux_arr]), header="wavelength,flux", comments="", delimiter=",")
            return buffer.getvalue()


        st.download_button(label="Download continuum", data=arrays_to_txt(spec.wave.data, spec.cont),
                           file_name="continuum_fit.txt", mime="text/plain", icon=":material/download:")

else:
    st.markdown(f'### No observation available')
    st.page_link("pages/1a_Load_spectrum.py", label='Please load an spectrum :yellow[**(link)**]', icon=":material/upload:")
    st.page_link("pages/1a_Load_spectrum.py", label='or get an observation from the virtual observatory page :yellow[**(link)**]', icon=":material/archive:")