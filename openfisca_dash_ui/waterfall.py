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

import operator
from functools import reduce

import plotly.graph_objs as go
from toolz import assoc, concat, concatv, dissoc, get, merge, pipe, update_in
from toolz.curried import filter, map


def create_waterfall_figure(bars, display_sub_totals):
    def is_displayed(bar):
        return bar["code"] == "revenu_disponible" or display_sub_totals or bar["bar_type"] != "sub_total"

    displayed_bars = list(filter(is_displayed, bars))

    data = [
        go.Bar(
            x=[bar.get("short_name") or bar["name"] for bar in displayed_bars],
            y=[bar["value"] for bar in displayed_bars],
            base=[bar["base"] for bar in displayed_bars],
            marker=dict(
                color=[
                    'rgba(55, 128, 191, 0.7)'
                    if bar["bar_type"] == "sub_total"
                    else 'rgba(219, 64, 82, 0.7)'
                    if bar["value"] < 0
                    else 'rgba(50, 171, 96, 0.7)'
                    for bar in displayed_bars
                ],
                line=dict(
                    color=[
                        'rgba(55, 128, 191, 1.0)'
                        if bar["bar_type"] == "sub_total"
                        else 'rgba(219, 64, 82, 1.0)'
                        if bar["value"] < 0
                        else 'rgba(50, 171, 96, 1.0)'
                        for bar in displayed_bars
                    ],
                    width=2,
                )
            ),
        ),
    ]

    # shapes = [
    #     sub_total_rect(bar["start_child_index"], bar["end_child_index"])
    #     for bar in bars
    #     if bar["bar_type"] == "sub_total"
    # ]

    layout = go.Layout(
        title=displayed_bars[-1]["name"],
        barmode='stack',
        paper_bgcolor='rgba(245, 246, 249, 1)',
        plot_bgcolor='rgba(245, 246, 249, 1)',
        showlegend=True,
        # shapes=shapes,
    )

    fig = go.Figure(data=data, layout=layout)
    return fig


# def sub_total_rect(x0_bar_index, x1_bar_index):
#     return {
#         'type': 'rect',
#         'xref': 'x',
#         'yref': 'paper',
#         'x0': x0_bar_index - 0.45,
#         'y0': 0,
#         'x1': x1_bar_index + 0.45,
#         'y1': 1,
#         'fillcolor': 'gray',
#         'opacity': 0.2,
#         'line': {
#             'width': 0.5,
#         }
#     }


def decomposition_to_waterfall_bars(decomposition_tree):
    def process_node(node):
        nonlocal current_base
        children = node.get('children')
        if children:
            # Sub-total bar
            new_children = pipe(children, map(process_node), filter(None), list)
            if new_children:
                return merge(node, {
                    'bar_type': 'sub_total',
                    'base': new_children[0]["base"],
                    'children': new_children,
                    'value': sum(child["value"] for child in new_children),
                })
        elif node["value"]:
                # Value bar
                value_bar = merge(node, {
                    'bar_type': "value",
                    'base': current_base,
                })
                current_base = current_base + node["value"]
                return value_bar

        # Leaf node with value of 0, skip
        return None

    def to_bars(node):
        children = node.get('children')
        if not children:
            return [node]
        new_children = concat(to_bars(child) for child in children)
        bar = dissoc(node, 'children')
        return list(concatv(new_children, [bar]))

    current_base = 0

    return to_bars(process_node(decomposition_tree))


def keep_index(index, decomposition_tree):
    """Return a `decomposition_tree` with one value per node."""
    def process_node(node):
        children = node.get('children')
        if children:
            new_children = [process_node(child) for child in children]
            new_node = merge(node, {'children': new_children})
        else:
            new_node = merge(node, {'value': node['values'][index]})
        new_node = dissoc(new_node, 'values')
        return new_node

    return process_node(decomposition_tree)
