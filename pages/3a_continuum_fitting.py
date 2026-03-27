import streamlit as st
from streamlit import session_state as s_state
from utils.sidebar import sidebar_widgets
from utils.plots import bokeh_spectrum
import lime

from numpy import array, ndarray


# def widget_text_to_list(str_list, id_types=int):
#
#     if str_list is not None:
#         output = str_list.replace('\n', '')
#         output = output.replace(' ', '')
#         output = array(output.split(',')).astype(id_types)
#     else:
#         output = None
#
#     return output

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
            return array([convert(p) for p in parts], dtype=dtype)
        except ValueError:
            bad = [p for p in parts if not _is_float(p)]
            st.error(err_msg if err_msg else f"❌ Could not convert to {dtype.__name__}. Invalid value(s): `{', '.join(bad)}`")
            st.stop()



# Run the sidebar
sidebar_widgets()

# Page structure
st.markdown(f'# Continuum fitting')

fname = '/home/vital/PycharmProjects/lime/examples/doc_notebooks/0_resources/spectra/sdss_dr18_0358-51818-0504.fits'
s_state['spec'] = lime.Spectrum.from_file(fname, instrument='sdss')

# Check file has been uploaded
if s_state['spec'] is not None:

    st.markdown(f'### The widgets below can be used to fit the spectrum continuum using a polynomial.')

    with st.form('aspect_form', border=False, enter_to_submit=False, clear_on_submit=False):

        spec = s_state['spec']


        col_list = st.columns([0.25, 0.25, 0.25, 0.25], gap='small')

        with col_list[0]:
            order_list = st.text_input('List polynomial orders', value='3, 4, 4', placeholder='3, 4, 4',
                                       help='')

        with col_list[1]:
            emis_threshold = st.text_input('Emission intensity threshold', value='5, 4, 3', placeholder='5, 4, 3',
                                           help='')

        with col_list[2]:
            abs_threshold = st.text_input('Absorption intensity threshold', value=None, placeholder='5, 4, 3',
                                          help='')

        with col_list[3]:
            smooth_scale = st.selectbox('Smooth scale', options=[0,1,2,3,4,5,6,7,8,9,10], index=0,
                                        help='')

        # Every form must have a submit button.
        submitted = st.form_submit_button("Run fit")

        # Load the dataframe
        if submitted:

            order_list = parse_str_list_to_arr(order_list, dtype=int)
            emis_threshold = parse_str_list_to_arr(emis_threshold, dtype=float)
            abs_threshold = parse_str_list_to_arr(abs_threshold, dtype=float, parse_none=True)
            smooth_scale = None if smooth_scale == 0 else smooth_scale

            st.write(order_list)
            st.write(emis_threshold)
            st.write(abs_threshold)
            st.write(smooth_scale)

            # Make sure entries have the right format
            spec.fit.continuum(degree_list=[3, 6, 6], emis_threshold=[3, 2, 1.5], smooth_scale=2)
            spec.plot.spectrum()
            # spec.infer.components(exclude_continuum=exclude_check)

        # Show the plot
    st.write('***')
    if spec.infer.pred_arr is not None:
        bokeh_spectrum('spec', default_components=True, default_show_fits=False)

else:

    st.markdown(f'### No observation available')

    st.page_link("pages/1a_Load_spectrum.py", label='Please load an spectrum :yellow[**(link)**]', icon=":material/upload:")
    st.page_link("pages/1a_Load_spectrum.py", label='or get an observation from the virtual observatory page :yellow[**(link)**]', icon=":material/archive:")