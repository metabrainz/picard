Translations
============

Picard translations are handled by [Transifex](https://www.transifex.com).

_Please do not manually edit the PO files._

Required tools
--------------

* [Transifex client](http://support.transifex.com/customer/portal/topics/440187-transifex-client/articles)
* [Babel](http://babel.pocoo.org/)


Picard source tree strings
--------------------------

Their translations are handled at https://www.transifex.com/projects/p/musicbrainz/resource/picard/

One can update `picard.pot` using:
```bash
$ python setup.py regen_pot_file
```

Transifex will _automatically_ pick `picard.pot` from [Picard git repository master branch](https://github.com/metabrainz/picard/tree/master) once per day.


Attributes and countries strings
--------------------------------

Their translations are handled at https://www.transifex.com/projects/p/musicbrainz/resource/attributes/ and https://www.transifex.com/projects/p/musicbrainz/resource/countries/

`attributes.pot` and `countries.pot` are updated by [musicbrainz-server project](https://bitbucket.org/metabrainz/musicbrainz-server/), outside the Picard project.

Picard maintainers can regenerate `picard/const/attributes.py` and `picard/const/countries.py`, which are using `attributes.pot` and `countries.pot` as base, using the command:
```bash
$ python setup.py update_constants
```
It will retrieve and parse latest `attributes.pot` and `countries.pot` to rebuild `picard/const/attributes.py` and `picard/const/countries.py`.


To fetch latest translations from Transifex
-------------------------------------------

Use the following command:

```bash
$ python setup.py get_po_files
```

It will fetch all po files from Transifex, but the most incomplete ones.

The minimum acceptable percentage of a translation in order to download it can be seen using:
```bash
$ python setup.py get_po_files --help
```
The percentage value is passed to the `tx pull` command.
