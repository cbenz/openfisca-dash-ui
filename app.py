# -*- coding: utf-8 -*-

import json
import logging
from functools import reduce
from pathlib import Path

import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.graph_objs as go
from dash.dependencies import Input, Output
from openfisca_core import decompositions, periods
from openfisca_france import FranceTaxBenefitSystem
from toolz import assoc, concat, concatv, dissoc, get, merge, pipe, update_in
from toolz.curried import filter, map

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


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


def columns_to_waterfall_bars(columns):
    def iter_bars():
        value = 0
        for column in columns:
            yield merge(column, {
                'base': value,
                'value': column['value'],
                'bar_type': 'green' if column['value'] > 0 else 'red'
            })
            value = value + column['value']
    bars = list(iter_bars())
    bars[-1].update({
        'bar_type': 'blue',
        'base': '0',
    })
    return bars


def create_waterfall_figure(columns):
    bars = columns_to_waterfall_bars(columns)

    x_data = [bar.get("short_name") or bar["name"] for bar in bars]
    base_data = [bar["base"] for bar in bars]
    blue_data = [
        bar["value"]
        if bar["bar_type"] == "blue"
        else 0
        for bar in bars
    ]
    red_data = [
        bar["value"]
        if bar["bar_type"] == "red"
        else 0
        for bar in bars
    ]
    green_data = [
        bar["value"]
        if bar["bar_type"] == "green"
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
            )
        ),

        # # Blue
        go.Bar(
            x=x_data,
            y=blue_data,
            marker=dict(
                color='rgba(55, 128, 191, 0.7)',
                line=dict(
                    color='rgba(55, 128, 191, 1.0)',
                    width=2,
                )
            )
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
            )
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
            )
        ),

    ]

    layout = go.Layout(
        title=columns[-1]["name"],
        barmode='stack',
        paper_bgcolor='rgba(245, 246, 249, 1)',
        plot_bgcolor='rgba(245, 246, 249, 1)',
        showlegend=False
    )

    fig = go.Figure(data=data, layout=layout)
    return fig


def decomposition_to_waterfall(decomposition_json):
    """Transform a decomposition tree to a list useful to render a waterfall chart.

    >>> decomposition_to_waterfall({
    ...     "code": "revdisp",
    ...     "values": [5],
    ...     "children": [
    ...         {
    ...             "code": "a",
    ...             "values": [2],
    ...             "children": [
    ...                 {"code": "c", "values": []}
    ...             ]
    ...         },
    ...         {
    ...             "code": "b",
    ...             "values": [3],
    ...         }
    ...     ]
    ... })
    [{'code': 'c', 'values': [], '@type': 'Value'}, {'code': 'a', 'values': [2], '@type': 'Node'}, {'code': 'b', 'values': [3], '@type': 'Value'}, {'code': 'revdisp', 'values': [5], '@type': 'Node'}]
    """
    def process_node(node):
        if node.get('children'):
            children = concat(
                process_node(child)
                for child in node['children']
            )
            node_without_children = pipe(
                node,
                lambda node: assoc(node, '@type', "Node"),
                lambda node: dissoc(node, 'children'),
                lambda node: update_in(node, ['values'], list),
            )
            return list(concatv(children, [node_without_children]))
        return [dict(assoc(node, '@type', "Value"))]

    return process_node(decomposition_json)


def keep_index(index, waterfall_columns):
    return pipe(
        waterfall_columns,
        map(lambda col: update_in(col, ['values'], lambda values: get(index, values, default=0))),
        map(rename_key('values', 'value')),
        filter(lambda node: node["value"] != 0),
        list,
    )


def precalculate_waterfall_columns(tbs):
    period = 2018

    scenario_params = {
        "period": period,
        "parent1": {
            "age": 30,
        },
        "enfants": [
            {"age": 6},
            {"age": 8},
            {"age": 10}
        ],
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

    return pipe(
        decompositions.get_decomposition_json(tbs),
        lambda decomposition_json: decompositions.calculate([simulation], decomposition_json),
        decomposition_to_waterfall,
    )


print("Initializing France tax and benefit system...")
tbs = FranceTaxBenefitSystem()

print("Pre-calculating waterfall data...")
waterfall_columns = precalculate_waterfall_columns(tbs)
# with Path("python/dash-ui/waterfall.json").open('w') as fd:
#     json.dump(waterfall_columns, fd)
# with Path("python/dash-ui/waterfall.json").open() as fd:
#     waterfall_columns = json.load(fd)


app = dash.Dash()

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
