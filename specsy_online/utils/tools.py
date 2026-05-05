import streamlit as st


def dynamic_input_data_editor(data, key, **_kwargs):

    """
    Like streamlit's data_editor but allows re-initialization when `data` changes.
    Fixes issue where Streamlit does not update the editor on first run.
    """

    changed_key = f'{key}__changed'
    initial_data_key = f'{key}__initial_data'

    def on_data_editor_changed():
        if 'on_change' in _kwargs:
            args = _kwargs.get('args', ())
            kwargs_inner = _kwargs.get('kwargs', {})
            _kwargs['on_change'](*args, **kwargs_inner)
        st.session_state[changed_key] = True

    if changed_key in st.session_state and st.session_state[changed_key]:
        data = st.session_state[initial_data_key]
        st.session_state[changed_key] = False
    else:
        st.session_state[initial_data_key] = data

    __kwargs = _kwargs.copy()
    __kwargs.update({
        'data': data,
        'key': key,
        'on_change': on_data_editor_changed,
        'num_rows': 'dynamic',
        'hide_index': True,
    })

    return st.data_editor(**__kwargs)

