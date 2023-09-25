# Contributing to Picard

## Coding Style

As most of the other projects written in Python, we use the [PEP 8](https://www.python.org/dev/peps/pep-0008/). Though, we ignore some of the recommendations:

- E501 - Maximum line length (79 characters). The general limit we have is somewhere around 120-130.

*Recommended video: "[Beyond PEP 8 -- Best practices for beautiful intelligible code](https://www.youtube.com/watch?v=wf-BqAjZb8M)" by Raymond Hettinger at PyCon 2015, which talks about the famous P versus NP problem.*

The general idea is to make the code within a project consistent and easy to interpret (for humans).

Developers may install few extra tools using:

```bash
pip install -r requirements-dev.txt
```

To fix or preserve imports style, one can use `isort .` command (requires the [isort](https://github.com/PyCQA/isort) tool, see `.isort.cfg`).

It is recommended to add a pre-commit hook to check whether imports in changed code
follow the conventions. Add a file `.git/hooks/pre-commit` with the following content
and make it executable:

```bash
#!/usr/bin/env bash

PYFILES=$(git diff --cached --name-only | grep "\\.py$" | grep --invert-match \
  -e "^tagger\\.py$" \
  -e "^picard/resources\\.py$" \
  -e "^picard/\(coverart/providers\|formats\)/__init__\\.py$" \
  -e "^picard/const/\(__init__\|attributes\|countries\)\\.py$" \
  -e "^picard/ui/ui_.*\\.py$" \
  -e "^scripts/picard\\.in$")

if [ ! -z "$PYFILES" ]; then
  set -e
  isort --check-only --diff --quiet $PYFILES
  flake8 $PYFILES
fi
```


### Docstrings

Unless the function is easy to understand quickly, it should probably have a docstring describing what it does, how it does it, what the arguments are, and what the expected output is.

We recommend using ["Google-style" docstrings](https://google.github.io/styleguide/pyguide.html?showone=Comments#38-comments-and-docstrings) for writing docstrings.


### Picard specific code

Picard has some auto-generated `picard/ui/ui_*.py` PyQt UI related files. Please do not change them directly. To modify them, use Qt-Designer to edit the `ui/*.ui` and use the command `python setup.py build_ui` to generate the corresponding `ui_*.py` files.

We use snake-case to name all functions and variables except for the pre-generated PyQt functions/variables.

`gettext` and `gettext-noop` have been built-in the Picard code as `_` and `N_` respectively to provide support for internationalization/localization. You can use them without imports across all of Picard code. Make sure to mark all displayable strings for translation using `_` or `N_` as applicable. You can read more about python-gettext [here](https://docs.python.org/2/library/gettext.html).

### Strings quoting: single or double quotes?

As a general guideline, we tend to use double quotes for translatable strings and/or English phrases; or anything that may contain one or more single quotes.
We use single quotes for identifiers and keys (those are unlikely to contain a single quote; and usually no special character or space).
Of course, it all depends on context and those are just hints, rather than rules.

Examples:

```python
print("It is red")
```

Because changing it to `print("It's red")` would not require changing quotes.

```python
d = dict()
d['key'] = "It's red"

if 'key' in d:
    print(_("The value for 'key' is {key}.").format(**d))

```

In above example, 'key' is an identifier, usually using characters from `[a-z0-9_]` set.
But the printed string is translatable (English phrase).

```python
l1 = ['big', 'small']
l2 = ["It's a big city", "Small is the village"]
l3 = ["The city is big", "That's a small village"]

d = {
    'big': "The City",
    'small': "The Village",
}
print(d['small'])
```

In above example, `l1` contains identifiers (keys of dict `d`) while others are English words/phrases.
In the dict declaration, keys are single-quoted but values are double-quoted.

URIs (and paths used in URIs) should be, in general, enclosed in double quotes,
mainly because single quotes can appear in URI, unencoded, as sub-delimiters as specified
by [RFC3986](https://www.rfc-editor.org/rfc/rfc3986#section-2.2).

HTML/XML code often contains attributes that are enclosed by double quotes, so in this case,
better use single quotes, e.g. `html = '<a href="someurl">text</a>'`.

In doubt, choose whichever limit the number of escaped characters.
Typically single quote strings that are meant to contain double quotes (e.g. `'The file is "{file}"'`).


## Git Work-flow

We follow the "typical" GitHub workflow when contributing changes:

1. [Fork](https://help.github.com/articles/fork-a-repo/) a repository into your account.
2. Create a new branch and give it a meaningful name. For example, if you are going to fix issue PICARD-257, branch can be called `picard-257` or `preserve-artwork`.
3. Make your changes and commit them with a [good description](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html). Your commit subject should be written in **imperative voice** and **sentence case**. With regards to the contents of the message itself, you don't need to provide a lot of details, but make sure that people who look at the commit history afterwards can understand what you were changing and why.
4. [Create](https://help.github.com/articles/creating-a-pull-request/) a new pull request on GitHub. Make sure that the title of your pull request is descriptive and consistent with the rest. If you are fixing issue that exists in our bug tracker reference it like this: `PICARD-257: Allow preserving existing cover-art tags`. **Not** `[PICARD-257] - Allow preserving existing cover-art tags` or `Allow preserving existing cover-art tags (PICARD-257)` or simply `PICARD-257`.
5. Make sure to provide a bug tracker link to the issue that your pull request solves in the description.
6. Do not make one big pull request with a lot of unrelated changes. If you are solving more than one issue, unless they are closely related, split them into multiple pull requests. It makes it easier to review and merge the patches this way.
7. Try to avoid un-necessary commits after code reviews by making use of [git rebase](https://help.github.com/articles/about-git-rebase/) to fix merge conflicts, remove unwanted commits, rewording and editing previous commits or squashing multiple small related changes into one commit.

## Translations

See [po/README.md](./po/README.md) for information about translations.


## User Documentation

See the [Picard Documentation](https://github.com/metabrainz/picard-docs/blob/master/.github/CONTRIBUTING.md) project for information about contributing to the documentation for MusicBrainz Picard (aka the [Picard User Guide](https://picard-docs.musicbrainz.org)).


## Audio Metadata Specifications

The core functionality of Picard is the ability to read and write tags from / to files
with different tagging formats. When implementing support for new tags the goal is to
be compatible with existing software as good as possible. Below are links to relevant
metadata specifications and to the tag mapping tables used by various audio software.

### Format specs
- [ID3](https://github.com/id3/ID3v2.4)
- [VorbisComment](https://wiki.xiph.org/VorbisComment)
- [OggOpus](https://wiki.xiph.org/OggOpus#Comment_Header) (in addition to Vorbis Comment spec)
- [RFC 7845 - Ogg Encapsulation for the Opus Audio Codec](https://tools.ietf.org/html/rfc7845#section-5.2.1)
- [APE-Tags](http://wiki.hydrogenaud.io/index.php?title=APE_key)
- [Matroska \| Tag Specifications](https://www.matroska.org/technical/specs/tagging/index.html)
- [ASF / WMA](http://msdn.microsoft.com/en-us/library/ms867702.aspx)
- MP4: See iTunes Metadata Format Specification (was available at [Apple Developer website](https://developer.apple.com/), but does not seem to be available anymore)
- [RIFF Tags](https://exiftool.org/TagNames/RIFF.html) / [Resource Interchange File Format: INFO List Chunk](https://www.tactilemedia.com/info/MCI_Control_Info.html) / [Multimedia Programming Interface and Data Specifications 1.0](http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/Docs/riffmci.pdf)
- [Mutagen Spec Collection](https://mutagen-specs.readthedocs.io/en/latest/)


### Tag mapping tables
- [Picard](https://picard-docs.musicbrainz.org/en/appendices/tag_mapping.html)
- [JAudiotagger](http://www.jthink.net/jaudiotagger/tagmapping.html)
- [MP3Tag](https://help.mp3tag.de/main_tags.html)
- [Kid3](https://kid3.sourceforge.io/kid3_en.html#frame-list)
- [Yate Tag Mapping Table](https://2manyrobots.com/YateResources/InAppHelp/TagMappingTable.html)
- [MediaMonkey](https://www.mediamonkey.com/sw/webhelp/frame/index.html?abouttrackproperties.htm)
- [MusicBee](http://musicbee.wikia.com/wiki/Tag)
- [Kodi - Music Files & Tagging](https://kodi.wiki/view/Music_tagging#Tags_Kodi_reads)
- [Kodi - Video file tagging](https://kodi.wiki/view/Video_file_tagging#MP4_tag_options)
- [Quod Libet - Tag Formats & Spec Deviations](https://quodlibet.readthedocs.io/en/latest/development/formats.html)
- [Foobar2000:ID3 Tag Mapping - Hydrogenaudio Knowledgebase](https://wiki.hydrogenaud.io/index.php?title=Foobar2000:ID3_Tag_Mapping)
- [Tag Mapping - Hydrogenaudio Knowledgebase](https://wiki.hydrogenaud.io/index.php?title=Tag_Mapping)
- [Windows](https://docs.microsoft.com/en-US/windows/win32/wmformat/id3-tag-support)
- [SlimServerSupportedTags - SqueezeboxWiki](http://wiki.slimdevices.com/index.php/SlimServerSupportedTags)
- [Music Player Daemon 0.21.2 documentation](https://mpd.readthedocs.io/en/stable/protocol.html#tags)
- [Metadata Matrix – Pioneer DJ](https://forums.pioneerdj.com/hc/en-us/articles/360024701851-Metadata-Matrix)
- [DJ apps metadata matrix](https://docs.google.com/spreadsheets/d/1zhIJPOtYIueV72Gd81aVnbSa6dIA-azq9fnGC2rHUzo/edit?usp=sharing)

Also relevant:

- [Comparisson Picard / JAudiotagger](https://docs.google.com/spreadsheets/d/1afugW3R1FRDN-mwt5SQLY4R7aLAu3RqzjN3pR1497Ok/edit#gid=0)
- [Roon Knowledge Base - File Tag Best Practice](https://kb.roonlabs.com/File_Tag_Best_Practice)
- [Roon Knowledge Base - Roon Vs Tags](https://kb.roonlabs.com/Roon_Vs_Tags)


### Other specs

- [ReplayGain 2.0 specification](http://wiki.hydrogenaud.io/index.php?title=ReplayGain_2.0_specification)
