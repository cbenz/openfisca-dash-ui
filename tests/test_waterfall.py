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

from pathlib import Path
from ruamel.yaml import YAML

from openfisca_france import FranceTaxBenefitSystem
from openfisca_dash_ui import waterfall


def test_decomposition_variables():
    tbs = FranceTaxBenefitSystem()
    path = Path('openfisca_dash_ui/decomposition.yaml')
    yaml = YAML(typ='safe')
    decomposition = yaml.load(path)
    def check(tree):
        for node in tree:
            assert node['code'] in tbs.variables
            check(node['children'])


def test_decomposition_to_waterfall_bars():
    assert waterfall.decomposition_to_waterfall_bars({
        "code": "N1",
        "children": [
            {
                "code": "N11",
                "children": [
                    {"code": "V111", "value": 1},
                    {"code": "V112", "value": 2},
                    {"code": "V113", "value": 0}
                ]
            },
            {
                "code": "N12",
                "children": [
                    {"code": "V121", "value": -1}
                ]
            },
            {
                "code": "N13",
                "children": [
                    {"code": "V131", "value": 0}
                ]
            },
            {"code": "V12", "value": 7}
        ]
    }) == [
        {'code': 'V111', 'bar_type': 'value', 'base': 0, 'value': 1},
        {'code': 'V112', 'bar_type': 'value', 'base': 1, 'value': 2},
        {'code': 'N11', 'bar_type': 'sub_total', 'base': 0, 'value': 3},
        {'code': 'V121', 'bar_type': 'value', 'base': 3, 'value': -1},
        {'code': 'N12', 'bar_type': 'sub_total', 'base': 3, 'value': -1},
        {'code': 'V12', 'bar_type': 'value', 'base': 2, 'value': 7},
        {'code': 'N1', 'bar_type': 'sub_total', 'base': 0, 'value': 9},
    ]


def test_keep_index():
    assert waterfall.keep_index(0, {
        "code": "N1",
        "children": [
            {
                "code": "N11",
                "children": [
                    {"code": "V111", "values": [1, 2, 3]},
                    {"code": "V112", "values": [2, 3, 4]},
                    {"code": "V113", "values": [0, 0, 0]}
                ]
            },
            {
                "code": "N12",
                "children": [
                    {"code": "V121", "values": [-1, -1, -1]}
                ]
            },
            {
                "code": "N13",
                "children": [
                    {"code": "V131", "values": [0, 0, 0]}
                ]
            },
            {"code": "V12", "values": [7, 8, 9]}
        ]
    }) == {
        "code": "N1",
        "children": [
            {
                "code": "N11",
                "children": [
                    {"code": "V111", "value": 1},
                    {"code": "V112", "value": 2},
                    {"code": "V113", "value": 0}
                ]
            },
            {
                "code": "N12",
                "children": [
                    {"code": "V121", "value": -1}
                ]
            },
            {
                "code": "N13",
                "children": [
                    {"code": "V131", "value": 0}
                ]
            },
            {"code": "V12", "value": 7}
        ]
    }
