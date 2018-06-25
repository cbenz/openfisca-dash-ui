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

from openfisca_dash_ui import waterfall


def test_decomposition_to_waterfall():
    assert waterfall.decomposition_to_waterfall({
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
    }) == [
        {'code': 'V111', 'bar_type': 'value', 'bases': [0, 0, 0], 'values': [1, 2, 3]},
        {'code': 'V112', 'bar_type': 'value', 'bases': [1, 2, 3], 'values': [2, 3, 4]},
        {'code': 'N11', 'bar_type': 'sub_total', 'bases': [0, 0, 0], 'values': [3, 5, 7]},
        {'code': 'V121', 'bar_type': 'value', 'bases': [3, 5, 7], 'values': [-1, -1, -1]},
        {'code': 'N12', 'bar_type': 'sub_total', 'bases': [3, 5, 7], 'values': [-1, -1, -1]},
        {'code': 'V12', 'bar_type': 'value', 'bases': [2, 4, 6], 'values': [7, 8, 9]},
        {'code': 'N1', 'bar_type': 'sub_total', 'bases': [0, 0, 0], 'values': [9, 12, 15]},
    ]
