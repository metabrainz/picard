#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2006 Lukáš Lalinský
# Copyright (C) 2012 Frederik "Freso" S. Olesen
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

def get_countries(dbuser="musicbrainz", dbname="musicbrainz_db_slave"):
    from subprocess import Popen, PIPE
    sql_command = "SELECT iso_code, name FROM country;"
    psql_command = ["psql", "--username="+dbuser, "--dbname="+dbname,
                            "--command="+sql_command,
                            "--no-align", "--tuples-only"]
    countries_sql = Popen(psql_command, stdout=PIPE).stdout.readlines()

    return [country.strip().split("|", 1) for country in countries_sql]

def countries_py_file(country_list, filename="countries.py"):
    countries_py = open(filename, 'w')
    countries_py.write("""# -*- coding: utf-8 -*-
# Automatically generated - don't edit.
# Use the "country_sql2py.py" script in the "scripts" folder and
# overwrite this file with the generated "countries.py" to update it.

RELEASE_COUNTRIES = {
""")
    country_line = '    u"{0}": u"{1}",\n'
    for country in country_list:
        countries_py.write(country_line.format(country[0], country[1]))
    countries_py.write("}")
    countries_py.close()

if __name__ == "__main__":
    countries_py_file(get_countries())
