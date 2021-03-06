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
from ruamel.yaml import YAML

from openfisca_core import periods
from openfisca_core.simulation_builder import SimulationBuilder
from openfisca_france import FranceTaxBenefitSystem

from .waterfall import create_waterfall_figure, decomposition_to_waterfall_bars, keep_index

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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


def calculate_decomposition(simulation, period, tree):
    """Mutate `tree` by computing the output variables represented by its notes."""
    for node in tree:
        array = simulation.calculate_add(node['code'], period)
        node['values'] = array.tolist()
        children = node.get("children")
        if children:
            calculate_decomposition(simulation, period, children)


def precalculate_decomposition(tax_benefit_system):
    period = 2018

    test_case = {
        "individus": {
            "Michel": {
                'date_naissance': {'ETERNITY': '1980-01-01'},
            },
        },
        "familles": {
            "famille_1": {
                "parents": ["Michel"]
            }
        },
        "foyers_fiscaux": {
            "foyer_fiscal_1": {
                "declarants": ["Michel"],
            },
        },
        "menages": {
            "menage_1": {
                "personne_de_reference": ["Michel"],
            }},
        "axes": [[
            {
                "name": 'salaire_de_base',
                "count": COUNT,
                "min": MIN,
                "max": MAX,
                "period": period,
            },
        ]],
    }

    simulation_builder = SimulationBuilder()
    simulation = simulation_builder.build_from_entities(tax_benefit_system, test_case)

    decomposition_path = Path('openfisca_dash_ui/decomposition.yaml')
    yaml = YAML(typ='safe')
    decomposition = yaml.load(decomposition_path)
    calculate_decomposition(simulation, period, decomposition)
    return decomposition


print("Initializing France tax and benefit system...")
tax_benefit_system = FranceTaxBenefitSystem()
print("Pre-calculating decomposition...")
decomposition_tree = precalculate_decomposition(tax_benefit_system)


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
        # updatemode='drag',
    ),

    dcc.Graph(id='waterfall'),
    dcc.Checklist(
        id='chart-options',
        options=[{'label': 'Display sub-totals', 'value': 'display-sub-totals'}],
        value=[]
    ),
])


@app.callback(Output('salaire-de-base-value', 'children'), [Input('salaire-de-base', 'value')])
def display_salaire_de_base(salaire_de_base):
    return salaire_de_base


@app.callback(Output('waterfall', 'figure'), [
    Input('salaire-de-base', 'value'),
    Input('chart-options', 'value'),
])
def update_waterfall(salaire_de_base, chart_options):
    index = value_to_index(MIN, STEP, salaire_de_base)
    return create_waterfall_figure(
        bars=decomposition_to_waterfall_bars(keep_index(index, decomposition_tree[0])),
        display_sub_totals='display-sub-totals' in chart_options,
    )
