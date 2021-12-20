#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dash
import dash_bootstrap_components as dbc

external_stylesheets = [dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP]

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = "Entropy: quantum machine config"

server = app.server
app.config.suppress_callback_exceptions = True
