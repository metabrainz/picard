Translations
============

Picard translations are handled by [Weblate](https://translations.metabrainz.org/projects/picard/). For translation instructions please see [Picard, Picard Website and Picard User Guide Internationalization](https://wiki.musicbrainz.org/MusicBrainz_Picard/Internationalization).

The translation files are automatically synced between the Picard Github repository and Weblate. Translations can be done in Weblate or by updating the translation files directly.

Below is a technical description for managing the translations as a Picard maintainer or developer.


Required tools
--------------

* [Weblate Client](https://docs.weblate.org/en/latest/wlc.html)
* [Babel](https://babel.pocoo.org/)


Picard source tree strings
--------------------------

Their translations are handled at <https://translations.metabrainz.org/projects/picard/app/>

One can update `picard.pot` using:

```bash
python setup.py regen_pot_file
```

Weblate will _automatically_ sync the changed `picard.pot` and update the translation files (`*.po`) with msgmerge.


AppStream metadata and XDG desktop file translations
----------------------------------------------------

Translations for the strings from `org.musicbrainz.Picard.appdata.xml.in` and `org.musicbrainz.Picard.desktop.in` are handled at <https://translations.metabrainz.org/projects/picard/appstream/>.

One can update `appstream/picard-appstream.pot` using:

```bash
python setup.py regen_appdata_pot_file
```

Weblate will _automatically_ sync the changed `picard-appstream.pot` and update the translation files (`appstream/*.po`) with msgmerge.


Windows installer translations
------------------------------

The translations for the Windows installer are inside the JSON files in `installer/i18n/sources`.
Translation in Weblate is done at <https://translations.metabrainz.org/projects/picard/installer/>


Attributes and countries strings
--------------------------------

Their translations are handled at <https://translations.metabrainz.org/projects/musicbrainz/attributes/> and <https://translations.metabrainz.org/projects/musicbrainz/countries/>

`attributes.pot` and `countries.pot` are updated by [musicbrainz-server project](https://github.com/metabrainz/musicbrainz-server), outside the Picard project.

Picard maintainers can regenerate `picard/const/attributes.py` and `picard/const/countries.py`, which are using `attributes.pot` and `countries.pot` as base. For this an Weblate API key is required, which can be found in your Weblate user settings under [API access](https://translations.metabrainz.org/accounts/profile/#api). The constants can then be updated with the following command:


```bash
python setup.py update_constants --weblate-key={YOUR_WEBLATE_API_KEY}
```

Instead of entering the Weblate API key each time you can also place a file `.weblate.ini` in the root of the repository with the following content:

```ini
[weblate]
url = https://translations.metabrainz.org/api/

[keys]
https://translations.metabrainz.org/api/ = YOUR_WEBLATE_API_KEY
```

It will retrieve and parse latest `attributes.pot` and `countries.pot` to rebuild `picard/const/attributes.py` and `picard/const/countries.py`.
