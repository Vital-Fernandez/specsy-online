"""
specsy-online entry point: Streamlit (Welcome.py) + live Bokeh plots mounted at /bokeh.

Installed as the "specsy" command (pyproject: specsy = "specsy_online.serve:main"), or run directly:

    python specsy_online/serve.py [--port 8501] [--host localhost] [--no-browser]

Requires Streamlit >= 1.57 and Bokeh >= 3.10.
"""

import argparse
import threading
import webbrowser
from pathlib import Path

import streamlit as st
from starlette.routing import Mount

from specsy_online.utils import bokeh_server

# Absolute path, so it does not depend on the working directory
WELCOME = Path(__file__).parent / 'Welcome.py'

# Tell the pages the live plots are available
bokeh_server.mark_mounted()

# The Bokeh core starts by itself on the first /bokeh request
app = st.App(WELCOME, routes=[Mount('/bokeh', app=bokeh_server.bokeh_app)])


def main(argv=None):

    import uvicorn

    parser = argparse.ArgumentParser(prog='specsy', description='Launch specsy-online')
    parser.add_argument('--port', type=int, default=8501)
    parser.add_argument('--host', default='localhost')
    parser.add_argument('--no-browser', action='store_true', help='Do not open the browser')
    args = parser.parse_args(argv)

    url = f'http://{args.host}:{args.port}'
    print(f'\n  specsy-online running at {url}  (Ctrl+C to stop)\n')

    if not args.no_browser:
        threading.Timer(1.5, webbrowser.open, args=(url,)).start()

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == '__main__':
    main()