"""
Live Bokeh plots (Python callbacks) inside the specsy-online Streamlit pages.

``serve.py`` mounts ``bokeh_app`` at ``/bokeh`` and calls :func:`mark_mounted`. A page calls :func:`bokeh_live` with a
function that builds the plot into a Bokeh document, e.g. ``lambda doc: spec.bokeh.masks(doc=doc, ...)``. The function
is stored under a random per-session token, and the plot is shown in an iframe pointing at ``/bokeh/app?token=...``.

When the app is launched with ``streamlit run Welcome.py`` (e.g. Streamlit Community Cloud) there is no ``/bokeh``
route: ``BOKEH_MOUNTED`` is False and the pages should fall back to static plots.

Streamlit re-imports the project modules when their source changes. The shared state (mounted flag, plot registry and
the mounted Bokeh app) is therefore kept on the ``sys`` module, so it survives those reloads during development.
"""

import sys
import types
import uuid

import streamlit as st
from bokeh.models import Div
from bokeh.server.asgi import BokehASGI


def _shared_state():
    state = getattr(sys, '_specsy_bokeh_state', None)
    if state is None:
        state = types.SimpleNamespace(mounted=False, builders={}, app=None)
        sys._specsy_bokeh_state = state
    return state


_STATE = _shared_state()


def _url_argument(doc, name):
    request = getattr(doc.session_context, 'request', None)
    arguments = getattr(request, 'arguments', None) or {}
    values = arguments.get(name)
    return values[-1].decode() if values else None


def _document(doc):

    builder = _STATE.builders.get(_url_argument(doc, 'token'))
    if builder is None:
        doc.add_root(Div(text='<p>Plot not available. Reload the page.</p>'))
        return

    builder(doc)

    return


# Single Bokeh application for every live plot  ->  /bokeh/app?token=...  (created once per process)
if _STATE.app is None:
    _STATE.app = BokehASGI({'/app': _document})
bokeh_app = _STATE.app


def mark_mounted():
    """Called by serve.py once ``bokeh_app`` is mounted at /bokeh."""
    _STATE.mounted = True


def __getattr__(name):
    # Module attribute read from the shared state, so it survives Streamlit module reloads
    if name == 'BOKEH_MOUNTED':
        return _STATE.mounted
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def bokeh_live(builder, key, height=650, reload_on=None):
    """
    Display a live Bokeh plot in the current Streamlit page.

    Parameters
    ----------
    builder : callable
        Function receiving a ``bokeh.document.Document`` and adding the plot to it.
    key : str
        Unique name for this plot within the app (one token per browser session and key).
    height : int, optional
        Iframe height in pixels.
    reload_on : hashable, optional
        Inputs of the plot. The plot reloads in the browser when this value changes.
    """

    token_key = f'_bokeh_token_{key}'
    if token_key not in st.session_state:
        st.session_state[token_key] = uuid.uuid4().hex
    token = st.session_state[token_key]

    _STATE.builders[token] = builder

    st.iframe(f'/bokeh/app?token={token}&k={abs(hash(reload_on))}', height=height)

    return