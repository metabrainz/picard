# -*- mode: python -*-

import glob
import os
import platform
import sys


# Get the version
# and build a CFBundleVersion compatible version of it according to Apple dev documentation
sys.path.append('.')
from picard import PICARD_VERSION
pv = [str(x) for x in PICARD_VERSION]
macos_picard_version = '.'.join(pv[:3])
macos_picard_short_version = macos_picard_version
if pv[3] != 'final':
	macos_picard_version += pv[3][0] + ''.join(pv[4:])


def _picard_get_locale_files():
    locales = []
    path_domain = {
        'po': 'picard',
        os.path.join('po', 'countries'): 'picard-countries',
        os.path.join('po', 'attributes'): 'picard-attributes',
    }
    for path, domain in path_domain.items():
        for filepath in glob.glob(os.path.join(path, '*.po')):
            filename = os.path.basename(filepath)
            locale = os.path.splitext(filename)[0]
            locales.append((domain, locale, filepath))
    return locales


def get_locale_messages():
    data_files = []
    for locale in _picard_get_locale_files():
        data_files.append(
            (os.path.join("build", "locale", locale[1], "LC_MESSAGES", locale[0] + ".mo"),
             os.path.join("locale", locale[1], "LC_MESSAGES")))
    return data_files


block_cipher = None
os_name = platform.system()
binaries = []

data_files = get_locale_messages()

fpcalc_name = 'fpcalc'
if os_name == 'Windows':
    fpcalc_name = 'fpcalc.exe'
    binaries += [
        ('discid.dll', '.'),
        ('ssleay32.dll', '.'),
        ('libeay32.dll', '.'),
    ]
    data_files.append((os.path.join('resources', 'win10', '*'), '.'))

if os_name == 'Darwin':
    binaries += [('libdiscid.0.dylib', '.')]

if os.path.isfile(fpcalc_name):
    binaries += [(fpcalc_name, '.')]


a = Analysis(['tagger.py'],
             pathex=['picard'],
             binaries=binaries,
             datas=data_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)


pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)


exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='picard',
          debug=False,
          strip=False,
          upx=False,
          icon='picard.ico',
          version='win-version-info.txt',
          console=False)


coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=False,
               name='picard')


if platform.system() == 'Darwin':
    info_plist = {
        'NSHighResolutionCapable': 'True',
        'NSPrincipalClass': 'NSApplication',
        'CFBundleName': 'Picard',
        'CFBundleDisplayName': 'MusicBrainz Picard',
        'CFBundleIdentifier': 'org.musicbrainz.picard',
        'CFBundleVersion': macos_picard_version,
        'CFBundleShortVersionString': macos_picard_short_version,
    }
    app = BUNDLE(coll,
                 name='MusicBrainz Picard.app',
                 icon='picard.icns',
                 bundle_identifier=None,
                 info_plist=info_plist
                 )
