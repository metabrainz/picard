Translations
============

Picard translations are handled by [Weblate](https://translations.metabrainz.org/projects/picard/). For translation instructions please see [Picard, Picard Website and Picard User Guide Internationalization](https://wiki.musicbrainz.org/MusicBrainz_Picard/Internationalization).

The translation files are automatically synced between the Picard Github repository and Weblate. Translations can be done in Weblate or by updating the translation files directly.

Below is a technical description for managing the translations as a Picard maintainer or developer.

> **Note:** This document covers translating **Picard itself**. Translating a
> **plugin** works differently — see
> [Plugin Translation System](../docs/PLUGINSV3/TRANSLATIONS.md) for plugin UI
> and registry metadata translations.


Required tools
--------------

* [Weblate Client](https://docs.weblate.org/en/latest/wlc.html)
* [Babel](https://babel.pocoo.org/)


Getting the latest translations
-------------------------------

Weblate commits translations **directly to the GitHub repository** as
`Translated using Weblate (...)` commits, and the source strings
(`*.pot`/`*.po`) are synced back to Weblate automatically. Because of this
two-way sync, there is normally **no separate download step**: to get the
latest translations into your working tree, just pull from the repository:

```bash
git pull
```

After pulling, recompile the catalogs so the changes are visible when running
from source — see [Compiling translations for local use](#compiling-translations-for-local-use) below.

You do **not** need the Weblate Client (`wlc`) to get ordinary translation
updates — the two-way GitHub sync means `git pull` is enough. (`wlc` is used
only for the shared *attributes* and *countries* strings, which are pulled from
a separate Weblate project; see *Attributes and countries strings* below.)


Compiling translations for local use
------------------------------------

The `.po` files in this repository are the editable translation sources. At
runtime Picard loads the *compiled* binary catalogs (`.mo` files) from
`picard/locale/<locale>/LC_MESSAGES/`, one per translation domain (`picard`,
`picard-constants`, `picard-attributes`, `picard-countries`). The `.mo` files
are build artifacts and are not tracked in git, so they must be generated
before translated strings show up in the application.

To compile all `.po` files into `.mo` files **in the source tree**, run:

```bash
python setup.py build_locales
```

Run this whenever you pull new translations or edit a `.po` file, then restart
Picard (translations are loaded once at startup). This is the translation
equivalent of `python setup.py build_ui` and is required when running from
source with `python tagger.py`.

**Gotcha:** `python setup.py build` also triggers `build_locales`, but when run
as part of `build` the `.mo` files are written to the `build/` output directory
(`build/lib*/picard/locale/...`) for packaging/installation — **not** to the
source tree. Running from source loads `.mo` files from the source tree
(`picard/locale/...`), so a plain `python setup.py build` does **not** update
the catalogs used by `python tagger.py`. Use the standalone
`python setup.py build_locales` for that. (See the comment in the
`picard_build_locales` command in `setup.py` for the underlying reason: the
standalone invocation compiles in place because `build_lib` is unset.)


Testing a translation from source
---------------------------------

To see a translation in a running Picard built from source (for example to
review your own work before submitting it on Weblate):

1. Have a working source checkout that can run Picard. Setting this up
   (dependencies, building the Qt UI files and C extensions) is described in
   [INSTALL.md](../INSTALL.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).

2. Get the translation. Either pull the latest from the repository
   (`git pull`) or edit the relevant `po/*.po` file directly. If you edit a
   `.po` by hand, validate it before compiling:

   ```bash
   msgfmt --check po/fr.po -o /dev/null    # replace fr with your language code
   ```

3. Compile the catalogs into the source tree:

   ```bash
   python setup.py build_locales
   ```

4. Select the language (see below), then start Picard:

   ```bash
   python tagger.py
   ```

Repeat steps 2–4 (edit/pull → `build_locales` → restart) each time you change a
translation; the running application only loads translations at startup.


Selecting the interface language
---------------------------------

Picard determines its interface language in this order:

1. The **User interface language** option (Options → Interface). When set to
   anything other than *System default*, this value takes precedence. Changing
   it requires restarting Picard to take full effect.
2. Otherwise the **system locale**, taken from the `LANG`, `LC_ALL` and
   `LANGUAGE` environment variables.

To test a specific language without changing your Options, set the environment
variable when launching Picard (leave the interface-language option at
*System default*):

```bash
LANG=fr_FR.UTF-8 python tagger.py     # replace with your locale
```

Only languages that have a compiled `.mo` file in the source tree (see
*Compiling translations for local use* above) will display; otherwise Picard
falls back to English. Running with `-d`/`--debug` logs the resolved UI
language and the locale that was loaded, which is useful to confirm your
translation was picked up.


Picard source tree strings
--------------------------

Their translations are handled at <https://translations.metabrainz.org/projects/picard/app/>

One can update `picard.pot` using:

```bash
python setup.py regen_pot_file
```

Weblate will *automatically* sync the changed `picard.pot` and update the translation files (`*.po`) with msgmerge.


Constants strings
-----------------

Strings defined under `picard/const` (such as tag names and their
descriptions) are extracted separately from the rest of the source tree; the
main `regen_pot_file` command above ignores the `const` directory. Their
translations live in `po/constants/*.po` and are handled at
<https://translations.metabrainz.org/projects/picard/constants/>.

One can update `po/constants/constants.pot` using:

```bash
python setup.py regen_constants_pot_file
```

Weblate will *automatically* sync the changed `constants.pot` and update the
translation files (`po/constants/*.po`) with msgmerge.


AppStream metadata and XDG desktop file translations
----------------------------------------------------

Translations for the strings from `org.musicbrainz.Picard.appdata.xml.in` and `org.musicbrainz.Picard.desktop.in` are handled at <https://translations.metabrainz.org/projects/picard/appstream/>.

One can update `po/appstream/picard-appstream.pot` using:

```bash
python setup.py regen_appdata_pot_file
```

Weblate will *automatically* sync the changed `picard-appstream.pot` and update the translation files (`po/appstream/*.po`) with msgmerge.


Windows installer translations
------------------------------

The translations for the Windows installer are inside the JSON files in `installer/i18n/sources`.
Translation in Weblate is done at <https://translations.metabrainz.org/projects/picard/installer/>


Attributes and countries strings
--------------------------------

Their translations are handled at <https://translations.metabrainz.org/projects/musicbrainz/attributes/> and <https://translations.metabrainz.org/projects/musicbrainz/countries/>

`attributes.pot` and `countries.pot` are updated by [musicbrainz-server project](https://github.com/metabrainz/musicbrainz-server), outside the Picard project.

Unlike the other components, these are **not** translated within Picard: the
`po/attributes/*` and `po/countries/*` files are fetched from the MusicBrainz
Server project on Weblate rather than edited here.

Picard maintainers can regenerate `picard/const/attributes.py` and
`picard/const/countries.py`, which use `po/attributes/attributes.pot` and
`po/countries/countries.pot` as their base:

```bash
python setup.py update_constants --weblate-key={YOUR_WEBLATE_API_KEY}
```

By default this command first pulls the latest `attributes` and `countries`
translations from Weblate (via `scripts/tools/pull-shared-translations.py`,
which uses the Weblate Client) and then regenerates the two `.py` files. The
Weblate API key is required **only for this pull step**; it can be found in your
Weblate user settings under [API access](https://translations.metabrainz.org/accounts/profile/#api).

To regenerate the `.py` files from the `.pot` files already present in the tree
without contacting Weblate (no key needed), skip the pull step:

```bash
python setup.py update_constants --skip-pull
```

Instead of passing the Weblate API key each time you can also place a file `.weblate.ini` in the root of the repository with the following content:

```ini
[weblate]
url = https://translations.metabrainz.org/api/

[keys]
https://translations.metabrainz.org/api/ = YOUR_WEBLATE_API_KEY
```
