# MusicBrainz Picard Installation

## Quick Start

The easiest way to install Picard is from the [official downloads page](https://picard.musicbrainz.org/downloads/).

For development or building from source, follow the instructions below.

## Dependencies

### Required Dependencies

* [Python 3.10 or newer](https://www.python.org/downloads/)
* [PyQt 6.6.1 or newer](https://riverbankcomputing.com/software/pyqt/download)
* [Mutagen 1.45 or newer](https://mutagen.readthedocs.io/)
* [PyYAML 5.1 or newer](https://pyyaml.org/)
* [python-dateutil 2.7 or newer](https://dateutil.readthedocs.io/en/stable/) - For parsing date strings in metadata
* [charset-normalizer 3.3 or newer](https://pypi.org/project/charset-normalizer/) - For character encoding detection in CD ripping log files
* [pygit2](https://www.pygit2.org/) - For plugin system
* gettext (`msgfmt`):
  * **Windows:** Download from [gettext-iconv-windows](https://github.com/mlocati/gettext-iconv-windows/releases) and add to PATH
  * **Linux:** `sudo apt install gettext` (Ubuntu/Debian) or equivalent
  * **macOS:** Usually included with Xcode Command Line Tools, or `brew install gettext`
  > **Note:** On macOS, Homebrew installs gettext as keg-only. If you see `msgfmt` errors, you must link it manually:
  > ```bash
  > brew link gettext --force
  > export PATH="/opt/homebrew/opt/gettext/bin:$PATH"
  > ```
* A compiler (required for building C extensions):
  * **Windows:** [Visual Studio Community](https://aka.ms/vs/16/release/vs_community.exe)
  * **Linux:** `sudo apt install build-essential` (Ubuntu/Debian) or equivalent
  * **macOS:** Xcode Command Line Tools (`xcode-select --install`)

### Python Version-Specific Dependencies

* [tomli 2.3.0 or newer](https://pypi.org/project/tomli/) - Required for Python < 3.11 (Python 3.11+ has built-in TOML support)

### Optional Dependencies (Recommended)

* [discid 1.0 or newer](https://python-discid.readthedocs.org/) or [python-libdiscid](https://pypi.org/project/python-libdiscid/) - For CD lookups
* [Markdown 3.2 or newer](https://python-markdown.github.io/install/) - For enhanced internal documentation (scripting, plugins, etc.)
* [PyJWT 2.0 or newer](https://pyjwt.readthedocs.io/) - For "add cluster as release" functionality
* [chromaprint](https://acoustid.org/chromaprint) - For audio fingerprinting (AcoustID), allows identifying files by their actual audio content
* PyQt6 multimedia support - For embedded audio player (Linux: `python3-pyqt6.qtmultimedia libqt6multimedia6`)

## Installation Methods

### Method 1: Using uv (Recommended)

Quick setup with [uv](https://docs.astral.sh/uv/):

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# Set up and install Picard
uv venv
source .venv/bin/activate  # macOS/Linux (.venv\Scripts\activate.bat on Windows)
uv sync  # Automatically installs all dependencies from pyproject.toml
python setup.py build && python setup.py build_ext -i
uv pip install -e .

# Run Picard
picard
```

For development workflow, testing, code quality tools, and more details, see [CONTRIBUTING.md](CONTRIBUTING.md).

### Method 2: Using pip

After installing dependencies manually:

```bash
pip3 install .  # Installs Picard but not dependencies
```

To start Picard:

```bash
picard
```

To uninstall:

```bash
pip3 uninstall picard
```

### Method 3: Traditional pip setup

```bash
# Create virtual environment
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

# Install dependencies manually
pip install -r requirements.txt -r requirements-build.txt -r requirements-dev.txt

# Build and run
python3 setup.py build          # Compiles translations and prepares build files
python3 setup.py build_ext -i   # Builds C extensions in-place for development
python3 tagger.py
```

### Method 4: Legacy setup.py (Not Recommended)

```bash
sudo python3 setup.py install  # Installs Picard and attempts to install dependencies
```

## Platform-Specific Notes

### System Package Dependencies (Building from Source)

When building from source on Debian-based systems, you may need these system packages:

```bash
# Required for development tools and PyQt6 system libraries
apt install python3-venv python3-dev

# Optional: For discid support
apt install libdiscid0

# Optional: For multimedia player support
apt install libqt6multimedia6

# Alternative: Use system PyQt6 instead of pip/uv installation
apt install python3-pyqt6 python3-pyqt6.qtmultimedia
```

**Note:**
* Not needed for official binary installations
* When using uv/pip, you may still need some system libraries (like libqt6multimedia6)
* You can use system PyQt6 packages instead of installing via pip/uv

### Qt6 via pip Issues

If you get `libxcb` errors on startup when using Qt6 installed via pip:

```bash
sudo apt install libxcb-cursor0
```

## Packaging

To create and upload packages:

```bash
python3 setup.py sdist
twine upload dist/*
```

## Code Signatures

Official Picard packages are digitally signed. For packaging, use source archives from the [official file server](https://data.musicbrainz.org/pub/musicbrainz/picard/).

Verify signatures with:

```bash
gpg --verify picard-x.y.z.tar.gz.asc  # where x.y.z is the version number
```

| Certificate | Expiration | Fingerprint |
| ----------- | ---------- | ----------- |
| Windows Code Signing | 2024-10-25 | 4d0c868847e2a5e44ae734e1279a9c7007fd6d4c |
| Apple Code Signing | 2027-02-01 | deb351206f7dc9361e1cf3d864edce98a8d3302d |
| MBP Developers GPG | 2026-10-28 | [68990dd0b1edc129b856958167997e14d563da7c](https://keyserver.ubuntu.com/pks/lookup?op=vindex&search=0x67997e14d563da7c) |
