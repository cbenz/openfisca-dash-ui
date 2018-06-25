#! /usr/bin/env python3

# openfisca-dash-ui -- User interface for OpenFisca
# By: Christophe Benz <christophe.benz@jailbreak.paris>
#
# Copyright (C) 2018 Christophe Benz
# https://github.com/cbenz/openfisca-dash-ui
#
# openfisca-dash-ui is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# openfisca-dash-ui is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.


import collections
import json
import logging
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from openfisca_core import decompositions, periods
from openfisca_france import FranceTaxBenefitSystem

from .waterfall import create_waterfall_figure, decomposition_to_waterfall, keep_index

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def count_to_step(min, max, count):
    """Examples:
    >> > count_to_step(0, 80, 5)
    20.0
    """
    return float(max - min) / (count - 1)


def value_to_index(min, step, value):
    """Examples:
    >> > value_to_index(0, 10, 0)
    0
    >> > value_to_index(0, 10, 40)
    4
    >> > value_to_index(3, 1, 6)
    3
    """
    return int((value / step) - min)


MIN = 0
MAX = 100000
COUNT = 100
STEP = count_to_step(MIN, MAX, COUNT)
INITIAL_VALUE = 0


def precalculate_decomposition_json(tbs):
    period = 2018

    scenario_params = {
        "period": period,
        "parent1": {
            "age": 30,
        },
        # "enfants": [
        #     {"age": 6},
        #     {"age": 8},
        #     {"age": 10}
        # ],
        "axes": [
            dict(
                count=COUNT,
                min=MIN,
                max=MAX,
                name='salaire_de_base',
            ),
        ],
    }

    scenario = tbs.new_scenario().init_single_entity(**scenario_params)
    simulation = scenario.new_simulation()

    decomposition_json = decompositions.get_decomposition_json(tbs)
    filled_decomposition_json = decompositions.calculate([simulation], decomposition_json)

    # def serialize(x):
    #     if isinstance(x, collections.Iterable):
    #         return list(x)
    #     return x
    # with Path("decomposition.json").open('w') as fd:
    #     json.dump(filled_decomposition_json, fd, indent=2, default=serialize)

    return filled_decomposition_json


decomposition_file_path = Path("decomposition.json")
if decomposition_file_path.is_file():
    print("Loading decomposition from file...")
    with decomposition_file_path.open() as fd:
        decomposition_json = json.load(fd)
else:
    print("Initializing France tax and benefit system...")
    tbs = FranceTaxBenefitSystem()
    print("Pre-calculating decomposition...")
    decomposition_json = precalculate_decomposition_json(tbs)

waterfall_columns = decomposition_to_waterfall(decomposition_json)

app = dash.Dash()
server = app.server  # Referenced by Procfile

app.layout = html.Div(children=[
    html.H1(children='OpenFisca'),

    html.P(children=[
        "Salaire de base : ",
        html.Span(id="salaire-de-base-value"),
        " € / an",
    ]),
    dcc.Slider(
        id="salaire-de-base",
        min=MIN,
        max=MAX,
        step=STEP,
        value=INITIAL_VALUE,
        updatemode='drag',
    ),

    dcc.Graph(id='waterfall'),
    dcc.Checklist(
        id='chart-options',
        options=[{'label': 'Display sub-totals', 'value': 'display-sub-totals'}],
        values=[]
    ),
])


@app.callback(Output('salaire-de-base-value', 'children'), [Input('salaire-de-base', 'value')])
def display_salaire_de_base(salaire_de_base):
    return salaire_de_base


@app.callback(Output('waterfall', 'figure'), [
    Input('salaire-de-base', 'value'),
    Input('chart-options', 'values'),
])
def update_waterfall(salaire_de_base, chart_options):
    index = value_to_index(MIN, STEP, salaire_de_base)
    return create_waterfall_figure(
        bars=keep_index(index, waterfall_columns),
        include_sub_totals='display-sub-totals' in chart_options,
    )
