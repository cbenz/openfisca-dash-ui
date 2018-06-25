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


def create_waterfall_figure(bars, include_sub_totals):
    def is_displayed(bar):
        return bar["code"] == "revenu_disponible" or include_sub_totals or bar["bar_type"] != "sub_total"

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

    layout = go.Layout(
        title=displayed_bars[-1]["name"],
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

    Tree leaves become "value" bars, and nodes become "sub_total" bars.
    """
    def process_node(node):
        nonlocal current_bases
        children = node.get('children')
        if children:
            # Sub-total bar
            new_children = pipe(children, map(process_node), filter(None), list)
            if new_children:
                return merge(node, {
                    'bar_type': 'sub_total',
                    'bases': new_children[0]["bases"],
                    'children': new_children,
                    'values': sum_lists(child["values"] for child in new_children),
                })
        else:
            # Value bar
            if current_bases is None:
                # Initialize current_bases according to the number of elements of the first processed leave of the tree.
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


def rename_key(old, new):
    def rename_key_(d):
        return dissoc(
            assoc(d, new, d[old]),
            old,
        )
    return rename_key_


def sum_lists(lists):
    """Return a `list` containing the sum of given `lists`, element by element.

    All the lists must be equal length.

    >>> sum_lists([])
    []
    >>> sum_lists([[0, 5], [1, 6]])
    [1, 11]
    """
    if not lists:
        return lists
    return reduce(lambda accu, l: list(map(operator.add, accu, l)), lists)
