# Contributing to Picard

Picard and associated plugins and documentation has been a colaborative effort by volunteer contributors from the very start,
and contributions continue to be welcome from anyone in the community, as:

* Code improvements in Picard itself (as PRs to this repo)
* Language translations for Picard (see the [Translations README](/metabrainz/picard/blob/master/po/README.md))
* New or modified plugins (as PRs on the [Picard-Plugins repo](/metabrainz/picard-plugins))
* Documentation improvements on the [Picard-Docs website](https://picard-docs.musicbrainz.org/en/about_picard/contributing.html)
* Answering user questions in the [Picard section of the Community discussion board](https://community.metabrainz.org/c/picard/13)

Please be aware that we try to maintain high quality standards in all these areas,
that there is a learning curve to being able to make high-quality contributions,
and we consider achieving this to be a team effort with other community members chipping in to help you achieve the quality needed. 
So please be prepared to welcome constructive criticism on your proposed contributions
and consider the effort  that is being expended by others to help you in the positive light it is given.

If you want to contribute to the Picard code, then please read-on for details on:

* [To-do list](#to-do-list)
* [Technical Setup](#technical-setup)
* [Development Workflow](#development-workflow)
* [Coding Standards](#coding-standards)
* [Git Workflow](#git-workflow)
* [Documentation](#documentation)
* [Audio Metadata Standards](#audio-metadata-standards) 

Before starting you might want to ask more experienced contributors for advice about how to get started, 
and the easiest way for this would be to ask in the MusicBrainz Picard Development chat room
on [Matrix](https://matrix.to/#/#musicbrainz-picard-dev:chatbrainz.org).

## To-Do List

In many cases, people make contributions because of their own experiences - 
they have had an issue or can see a way that Picard could be improved.

However if you simply would like to contribute and are looking for ideas, 
then a to-do list of outstanding issues are areas for improvement can be found on the 
[MusicBrainz Jira Tickets system - Picard project](https://tickets.metabrainz.org/projects/PICARD/issues/?filter=allopenissues).

If you want to pick one of these to work on, make sure that you start with something small 
as many of these are large-scale, long-term suggestions - 
if in doubt ask for advice in the chat room so that you don't spend time and effort on something that
is too complex or which won't get merged.

## Technical Setup

### 1. Install System Dependencies

**gettext (required for translations):**

- **Windows:** Download from [gettext-iconv-windows](https://github.com/mlocati/gettext-iconv-windows/releases) and add `C:\Program Files\gettext-iconv\bin` to PATH
- **Linux:** `sudo apt install gettext`
- **macOS:** `brew install gettext` (if not included with Xcode Command Line Tools)

### 2. Install uv (Recommended)

[uv](https://docs.astral.sh/uv/) is an extremely fast Python package manager:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 3. Set Up Development Environment

```bash
# Clone and enter the repository
git clone https://github.com/metabrainz/picard.git
cd picard

# Create virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate.bat  # Windows

# Install all dependencies (main, build, dev)
uv sync

# Build the project
python setup.py build          # Compiles translations and prepares build files
python setup.py build_ext -i   # Builds C extensions in-place for development

# Install in editable mode
uv pip install -e .
```

### 4. Run Picard

```bash
# After installing in editable mode (recommended)
picard

# Or run directly from source (without installation)
python ./tagger.py

# With debug mode
picard -d
# or
python ./tagger.py -d
```

### 5. Run Tests

```bash
# With activated virtual environment
pytest -n auto

# Or using uv (if not in activated venv)
uv run pytest -n auto
```

## Development Workflow

### Dependency Management

Dependencies are defined in `pyproject.toml` using modern Python packaging standards:

- **Main dependencies**: Runtime requirements for Picard
- **build**: Build tools (Babel, PyInstaller, pytest, setuptools)
- **dev**: Development tools (ruff, pre-commit, pylint, etc.)
- **plugins**: Optional plugin dependencies (aubio, opencc, zstandard)

**Important**: Never edit requirements files manually. They are auto-generated from `pyproject.toml`.

### Code Quality

Install pre-commit hooks for automatic code quality checks:

```bash
pre-commit install
```

This runs `ruff` for code style and updates requirements files automatically before each commit.

To manually update requirements after changing `pyproject.toml`:

```bash
pre-commit run pip-compile --all-files
```

### Alternative Setup (Traditional pip)

If you prefer not to use uv:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-build.txt
pip install -r requirements-dev.txt

# Build and install
python setup.py build          # Compiles translations and prepares build files
python setup.py build_ext -i   # Builds C extensions in-place for development
pip install -e .
```

### Switching Python Versions

**With uv (recommended):**

```bash
# uv automatically manages Python versions
uv venv --python 3.11
uv venv --python 3.12
source .venv/bin/activate
uv sync
```

**With system Python:**

```bash
# Create separate virtual environments
python3.11 -m venv .venv311
python3.12 -m venv .venv312

# Activate desired version
source .venv311/bin/activate  # or .venv312/bin/activate

# Install dependencies manually
pip install -r requirements.txt -r requirements-build.txt -r requirements-dev.txt
```

## Coding Standards

### Style Guidelines

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with these exceptions:
- **E501**: Line length limit is ~120-130 characters (not 79)

The goal is consistent, readable code within the project.

**Code formatting and linting:**

```bash
# Format code automatically
ruff format

# Check for style and lint issues
ruff check

# Auto-fix issues where possible
ruff check --fix
```

### Docstrings

Use ["Google-style" docstrings](https://google.github.io/styleguide/pyguide.html?showone=Comments#38-comments-and-docstrings) for functions that aren't immediately obvious.

### Picard-Specific Guidelines

- **UI Files**: Don't edit `picard/ui/ui_*.py` directly - these are auto-generated. Use Qt Designer to edit `ui/*.ui` files, then run `python setup.py build_ui` to regenerate the Python files
- **Naming**: Use snake_case for functions/variables (except pre-generated PyQt code)
- **Internationalization**: Use `_()` for translatable strings and `N_()` for gettext-noop

## Git Workflow

1. **Fork** the repository to your account
2. **Create a branch** with a meaningful name (e.g., `picard-257` or `preserve-artwork`)
3. **Make changes** with [good commit messages](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html):
   - Use **imperative voice** and **sentence case**
   - Be descriptive but concise
4. **Create a pull request** with format: `PICARD-257: Allow preserving existing cover-art tags`
5. **Reference the issue** in the PR description
6. **Keep PRs focused** - split unrelated changes into separate PRs
7. **Use git rebase** to clean up commits before merging

## Documentation

### User Documentation

See [Picard Documentation project](https://github.com/metabrainz/picard-docs/blob/master/.github/CONTRIBUTING.md) for contributing to the [Picard User Guide](https://picard-docs.musicbrainz.org).

### Translations

See [po/README.md](./po/README.md) for translation information.

## Audio Metadata Standards

When implementing tag support, aim for compatibility with existing software.

### Format Specifications

- [ID3](https://github.com/id3/ID3v2.4)
- [VorbisComment](https://wiki.xiph.org/VorbisComment)
- [OggOpus](https://wiki.xiph.org/OggOpus#Comment_Header) (in addition to Vorbis Comment spec)
- [RFC 7845 - Ogg Encapsulation for the Opus Audio Codec](https://tools.ietf.org/html/rfc7845#section-5.2.1)
- [APE-Tags](http://wiki.hydrogenaud.io/index.php?title=APE_key)
- [Matroska Tags](https://www.matroska.org/technical/specs/tagging/index.html)
- [ASF / WMA](http://msdn.microsoft.com/en-us/library/ms867702.aspx)
- MP4: See iTunes Metadata Format Specification (was available at [Apple Developer website](https://developer.apple.com/), but does not seem to be available anymore)
- [RIFF Tags](https://exiftool.org/TagNames/RIFF.html) / [Resource Interchange File Format: INFO List Chunk](https://www.tactilemedia.com/info/MCI_Control_Info.html) / [Multimedia Programming Interface and Data Specifications 1.0](http://www-mmsp.ece.mcgill.ca/Documents/AudioFormats/WAVE/Docs/riffmci.pdf)
- [Mutagen Spec Collection](https://mutagen-specs.readthedocs.io/en/latest/)

### Tag Mapping References

- [Picard Tag Mapping](https://picard-docs.musicbrainz.org/en/appendices/tag_mapping.html)
- [JAudiotagger](http://www.jthink.net/jaudiotagger/tagmapping.html)
- [MP3Tag](https://help.mp3tag.de/main_tags.html)
- [Kid3](https://kid3.sourceforge.io/kid3_en.html#frame-list)
- [Yate Tag Mapping Table](https://2manyrobots.com/YateResources/InAppHelp/TagMappingTable.html)
- [MediaMonkey](https://www.mediamonkey.com/sw/webhelp/frame/index.html?abouttrackproperties.htm)
- [MusicBee](http://musicbee.wikia.com/wiki/Tag)
- [Kodi - Music Files & Tagging](https://kodi.wiki/view/Music_tagging#Tags_Kodi_reads)
- [Kodi - Video file tagging](https://kodi.wiki/view/Video_file_tagging#MP4_tag_options)
- [Quod Libet - Tag Formats & Spec Deviations](https://quodlibet.readthedocs.io/en/latest/development/formats.html)
- [TagLib Mapping of Properties](https://taglib.org/api/p_propertymapping.html)
- [Foobar2000:ID3 Tag Mapping - Hydrogenaudio Knowledgebase](https://wiki.hydrogenaud.io/index.php?title=Foobar2000:ID3_Tag_Mapping)
- [Tag Mapping - Hydrogenaudio Knowledgebase](https://wiki.hydrogenaud.io/index.php?title=Tag_Mapping)
- [Windows](https://docs.microsoft.com/en-US/windows/win32/wmformat/id3-tag-support)
- [SlimServerSupportedTags - SqueezeboxWiki](http://wiki.slimdevices.com/index.php/SlimServerSupportedTags)
- [Music Player Daemon 0.21.2 documentation](https://mpd.readthedocs.io/en/stable/protocol.html#tags)
- [Metadata Matrix – Pioneer DJ](https://forums.pioneerdj.com/hc/en-us/articles/360024701851-Metadata-Matrix)
- [DJ apps metadata matrix](https://docs.google.com/spreadsheets/d/1zhIJPOtYIueV72Gd81aVnbSa6dIA-azq9fnGC2rHUzo/edit?usp=sharing)
- [Navidrome mappings.yaml](https://github.com/navidrome/navidrome/blob/master/resources/mappings.yaml)

### Additional References

- [Comparison Picard / JAudiotagger](https://docs.google.com/spreadsheets/d/1afugW3R1FRDN-mwt5SQLY4R7aLAu3RqzjN3pR1497Ok/edit#gid=0)
- [Roon Knowledge Base - File Tag Best Practice](https://kb.roonlabs.com/File_Tag_Best_Practice)
- [Roon Knowledge Base - Roon Vs Tags](https://kb.roonlabs.com/Roon_Vs_Tags)
- [ReplayGain 2.0 specification](http://wiki.hydrogenaud.io/index.php?title=ReplayGain_2.0_specification)
