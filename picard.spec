# -*- mode: python -*-

import os
import glob
import platform


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
            (os.path.join("build", "locale", locale[1], "LC_MESSAGES" , locale[0] + ".mo"),
             os.path.join("locale", locale[1], "LC_MESSAGES")))
    return data_files


block_cipher = None
os_name = platform.system()
binaries = []

data_files = get_locale_messages()

fpcalc_name = 'fpcalc'
if os_name == 'Windows':
    fpcalc_name = 'fpcalc.exe'
    binaries += [('discid.dll', '')]

if os_name == 'Darwin':
    binaries += [('libdiscid.0.dylib', '')]

if os.path.isfile(fpcalc_name):
    binaries += [(fpcalc_name, '')]


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
          a.binaries,
          a.zipfiles,
          a.datas,
          name='picard',
          debug=False,
          strip=False,
          runtime_tmpdir=None,
          console=True,
          icon='picard.ico',
 )
if platform.system() == 'Darwin':
    info_plist = {'NSHighResolutionCapable': 'True', 'NSPrincipalClass': 'NSApplication'}
    app = BUNDLE(exe,
                 name='MusicBrainz Picard.app',
                 icon='picard.icns',
                 bundle_identifier=None,
                 info_plist=info_plist
                )
