# -*- coding: utf-8 -*-

import collections
import json
import logging
import operator
from functools import reduce
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
import numpy as np
import plotly
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from openfisca_core import decompositions, periods
from openfisca_france import FranceTaxBenefitSystem
from toolz import assoc, concat, concatv, dissoc, get, merge, pipe, update_in
from toolz.curried import filter, map

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def sum_lists(lists):
    return reduce(lambda accu, l: list(map(operator.add, accu, l)), lists)


def rename_key(old, new):
    def rename_key_(d):
        return dissoc(
            assoc(d, new, d[old]),
            old,
        )
    return rename_key_


def count_to_step(min, max, count):
    """Examples:
    >>> count_to_step(0, 80, 5)
    20.0
    """
    return float(max - min) / (count - 1)


def value_to_index(min, step, value):
    """Examples:
    >>> value_to_index(0, 10, 0)
    0
    >>> value_to_index(0, 10, 40)
    4
    >>> value_to_index(3, 1, 6)
    3
    """
    return int((value / step) - min)


MIN = 0
MAX = 100000
COUNT = 100
STEP = count_to_step(MIN, MAX, COUNT)
INITIAL_VALUE = 0


def create_waterfall_figure(bars):
    x_data = [bar.get("short_name") or bar["name"] for bar in bars]
    base_data = [bar["base"] for bar in bars]
    checkpoints_data = [
        bar["value"]
        if bar["bar_type"] == "checkpoint"
        else 0
        for bar in bars
    ]
    red_data = [
        bar["value"]
        if bar["bar_type"] == "value" and bar["value"] < 0
        else 0
        for bar in bars
    ]
    green_data = [
        bar["value"]
        if bar["bar_type"] == "value" and bar["value"] >= 0
        else 0
        for bar in bars
    ]

    data = [
        # Base
        go.Bar(
            x=x_data,
            y=base_data,
            marker=dict(
                color='rgba(1,1,1, 0.0)',
                # color='gray',
            ),
            hoverinfo="none",
        ),

        # Checkpoints
        go.Bar(
            x=x_data,
            y=checkpoints_data,
            marker=dict(
                color='rgba(55, 128, 191, 0.7)',
                line=dict(
                    color='rgba(55, 128, 191, 1.0)',
                    width=2,
                ),
            ),
            # width=0.1,
            hoverinfo="none",
        ),

        # Red
        go.Bar(
            x=x_data,
            y=red_data,
            marker=dict(
                color='rgba(219, 64, 82, 0.7)',
                line=dict(
                    color='rgba(219, 64, 82, 1.0)',
                    width=2,
                )
            ),
            hoverinfo="none",
        ),

        # Green
        go.Bar(
            x=x_data,
            y=green_data,
            marker=dict(
                color='rgba(50, 171, 96, 0.7)',
                line=dict(
                    color='rgba(50, 171, 96, 1.0)',
                    width=2,
                )
            ),
            hoverinfo="none",
        ),

    ]

    layout = go.Layout(
        title=bars[-1]["name"],
        barmode='stack',
        paper_bgcolor='rgba(245, 246, 249, 1)',
        plot_bgcolor='rgba(245, 246, 249, 1)',
        showlegend=False
    )

    fig = go.Figure(data=data, layout=layout)
    return fig


def decomposition_to_waterfall(decomposition_json):
    """Transform a decomposition tree to a list useful to render a waterfall chart.

    Compute sub-totals for tree nodes.

    Tree leaves become "value" bars, and nodes become "checkpoint" bars.

    >>> decomposition_to_waterfall({
    ...     "code": "N1",
    ...     "children": [
    ...         {
    ...             "code": "N11",
    ...             "children": [
    ...                 {"code": "V111", "values": [1, 2, 3]},
    ...                 {"code": "V112", "values": [2, 3, 4]},
    ...                 {"code": "V113", "values": [0, 0, 0]}
    ...             ]
    ...         },
    ...         {
    ...             "code": "N12",
    ...             "children": [
    ...                 {"code": "V121", "values": [-1, -1, -1]}
    ...             ]
    ...         },
    ...         {
    ...             "code": "N13",
    ...             "children": [
    ...                 {"code": "V131", "values": [0, 0, 0]}
    ...             ]
    ...         },
    ...         {"code": "V12", "values": [7, 8, 9]}
    ...     ]
    ... })
    [{'code': 'V111', 'values': [1, 2, 3], 'bar_type': 'value', 'bases': [0, 0, 0]}, {'code': 'V112', 'values': [2, 3, 4], 'bar_type': 'value', 'bases': [1, 2, 3]}, {'code': 'N11', 'bar_type': 'checkpoint', 'bases': [0, 0, 0], 'values': [3, 5, 7]}, {'code': 'V121', 'values': [-1, -1, -1], 'bar_type': 'value', 'bases': [3, 5, 7]}, {'code': 'N12', 'bar_type': 'checkpoint', 'bases': [0, 0, 0], 'values': [2, 4, 6]}, {'code': 'V12', 'values': [7, 8, 9], 'bar_type': 'value', 'bases': [2, 4, 6]}, {'code': 'N1', 'bar_type': 'checkpoint', 'bases': [0, 0, 0], 'values': [9, 12, 15]}]
    """
    def process_node(node):
        nonlocal current_bases
        children = node.get('children')
        if children:
            # Sub-total bar
            new_children = pipe(children, map(process_node), filter(None), list)
            if new_children and any(sum_lists(child['values'] for child in new_children)):
                values = sum_lists([new_children[-1]["bases"], new_children[-1]["values"]])
                return merge(node, {
                    'bar_type': 'checkpoint',
                    'bases': [0] * len(values),
                    'children': new_children,
                    'values': values,
                })
        else:
            # Value bar
            if current_bases is None:
                # Initialize current_bases according to the number of elements of a leave of the tree.
                current_bases = [0] * len(node["values"])
            if any(node["values"]):
                value_bar = merge(node, {
                    'bar_type': "value",
                    'bases': current_bases,
                })
                current_bases = sum_lists([current_bases, node["values"]])
                return value_bar

        return None

    def to_bars(node):
        children = node.get('children')
        if not children:
            return [node]
        new_children = concat(to_bars(child) for child in children)
        bar = dissoc(node, 'children')
        return list(concatv(new_children, [bar]))

    current_bases = None

    return to_bars(process_node(decomposition_json))


def keep_index(index, waterfall_columns):
    return pipe(
        waterfall_columns,
        map(lambda col: update_in(col, ['bases'], lambda bases: get(index, bases, default=0))),
        map(lambda col: update_in(col, ['values'], lambda values: get(index, values, default=0))),
        map(rename_key('bases', 'base')),
        map(rename_key('values', 'value')),
        filter(lambda node: node["value"] != 0),
        list,
    )


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


print("Initializing France tax and benefit system...")
tbs = FranceTaxBenefitSystem()
print("Pre-calculating waterfall data...")
decomposition_json = precalculate_decomposition_json(tbs)

# with Path("decomposition.json").open() as fd:
#     decomposition_json = json.load(fd)

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

    dcc.Graph(
        id='waterfall',
        figure=create_waterfall_figure(keep_index(value_to_index(MIN, STEP, INITIAL_VALUE), waterfall_columns))
    ),
])


@app.callback(Output('salaire-de-base-value', 'children'), [Input('salaire-de-base', 'value')])
def display_salaire_de_base(salaire_de_base):
    return salaire_de_base


@app.callback(Output('waterfall', 'figure'), [Input('salaire-de-base', 'value')])
def update_waterfall(salaire_de_base):
    index = value_to_index(MIN, STEP, salaire_de_base)
    return create_waterfall_figure(keep_index(index, waterfall_columns))


if __name__ == '__main__':
    app.run_server(debug=True, port=7777)
