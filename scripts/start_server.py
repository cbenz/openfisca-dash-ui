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


from openfisca_dash_ui.app import app

if __name__ == '__main__':
    # The code reload starts the server twice. Use `use_reloader=False` or `debug=False` to disable it.
    app.run_server(debug=True, host="0.0.0.0", port=7777)
