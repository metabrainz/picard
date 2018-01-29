# -*- mode: python -*-

import os
import glob


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
data_files = get_locale_messages()

a = Analysis(['tagger.py'],
             pathex=['picard'],
             binaries=[],
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
          upx=True,
          runtime_tmpdir=None,
          console=False,
          icon='picard.ico',
 )
