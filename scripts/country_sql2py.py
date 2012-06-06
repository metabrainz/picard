#!/usr/bin/env python
# -*- coding: utf-8 -*-

def get_countries(dbuser="musicbrainz", dbname="musicbrainz_db_slave"):
  from subprocess import Popen, PIPE
  sql_command = "SELECT iso_code, name FROM country;"
  psql_command = ["psql", "--username="+dbuser, "--dbname="+dbname,
                          "--command="+sql_command,
                          "--no-align", "--tuples-only"]
  countries_sql = Popen(psql_command, stdout=PIPE).stdout.readlines()

  countries = []
  for country in countries_sql:
    countries += [country.strip().split("|", 1)]
  return countries

def countries_py_file(country_list, filename="countries.py"):
  countries_py = open(filename, 'w')
  countries_py.write("""# -*- coding: utf-8 -*-
# Automatically generated - don't edit.
# Use the "country_sql2py.py" script in the "scripts" folder and overwrite this
# file with the generated "countries.py" to update it.

from gettext import dgettext

RELEASE_COUNTRIES = {
""")
  for country in country_list:
    entry = 'u"'+country[0]+'": dgettext("picard-countries", u"'+country[1]+'"),'
    countries_py.write("    "+entry+"\n")
  countries_py.write("}")
  countries_py.close()

if __name__ == "__main__":
  countries_py_file(get_countries())

