# -*- mode: python -*-

import glob
import os
import platform
import sys

# Get the version and build a CFBundleVersion compatible version
# of it according to Apple dev documentation
sys.path.insert(0, '.')
from picard import (
    PICARD_APP_ID,
    PICARD_APP_NAME,
    PICARD_DISPLAY_NAME,
    PICARD_ORG_NAME,
    PICARD_VERSION,
    __version__,
)


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
ab_extractor_name = 'streaming_extractor_music'
if os_name == 'Windows':
    fpcalc_name = 'fpcalc.exe'
    ab_extractor_name = 'streaming_extractor_music.exe'
    binaries += [('discid.dll', '.')]
    data_files.append((os.path.join('resources', 'win10', '*'), '.'))

if os_name == 'Darwin':
    binaries += [('libdiscid.0.dylib', '.')]

if os.path.isfile(fpcalc_name):
    binaries += [(fpcalc_name, '.')]

if os.path.isfile(ab_extractor_name):
    binaries += [(ab_extractor_name, '.')]

runtime_hooks = []
if os_name == 'Windows':
    runtime_hooks.append('scripts/pyinstaller/win-startup-hook.py')
elif os_name == 'Darwin':
    runtime_hooks.append('scripts/pyinstaller/macos-library-path-hook.py')
if '--onefile' in sys.argv:
    runtime_hooks.append('scripts/pyinstaller/portable-hook.py')


a = Analysis(['tagger.py'],
             pathex=['picard'],
             binaries=binaries,
             datas=data_files,
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=runtime_hooks,
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher)


pyz = PYZ(a.pure, a.zipped_data,
          cipher=block_cipher)


if '--onefile' in sys.argv:
    exe = EXE(pyz,
              a.scripts,
              a.binaries,
              a.zipfiles,
              a.datas,
              name='{}-{}-{}'.format(PICARD_ORG_NAME,
                                     PICARD_APP_NAME,
                                     __version__),
              debug=False,
              strip=False,
              upx=False,
              icon='picard.ico',
              version='win-version-info.txt',
              console=False)

else:
    exe = EXE(pyz,
              a.scripts,
              exclude_binaries=True,
              # Avoid name clash between picard executable and picard module folder
              name='picard' if os_name == 'Windows' else 'picard-run',
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

    if os_name == 'Darwin':
        info_plist = {
            'CFBundleName': PICARD_APP_NAME,
            'CFBundleDisplayName': PICARD_DISPLAY_NAME,
            'CFBundleIdentifier': PICARD_APP_ID,
            'CFBundleVersion': '%d.%d.%d' % PICARD_VERSION[:3],
            'CFBundleShortVersionString': PICARD_VERSION.to_string(short=True),
            'LSApplicationCategoryType': 'public.app-category.music',
            'LSMinimumSystemVersion': os.environ.get('MACOSX_DEPLOYMENT_TARGET', '10.12'),
            'NSHighResolutionCapable': True,
            'NSPrincipalClass': 'NSApplication',
            'NSRequiresAquaSystemAppearance': False,
            'CFBundleDocumentTypes': [{
                # Add UTIs understood by macOS
                'LSItemContentTypes': [
                    'com.apple.m4a-audio',
                    'com.apple.m4v-video',
                    'com.apple.protected-mpeg-4-audio',
                    'com.microsoft.advanced-systems-format',
                    'com.microsoft.waveform-audio',
                    'com.microsoft.windows-media-wm',
                    'com.microsoft.windows-media-wma',
                    'com.microsoft.windows-media-wmv',
                    'org.xiph.flac',
                    'public.aac-audio',
                    'public.ac3-audio',
                    'public.aifc-audio',
                    'public.aiff-audio',
                    'public.enhanced-ac3-audio',
                    'public.folder',
                    'public.midi-audio',
                    'public.mp3',
                    'public.mpeg-4',
                    'public.mpeg-4-audio',
                ],
                'CFBundleTypeRole': 'Editor',
            }],
        }

        # Add additional supported file types by extension
        from picard.formats import supported_formats
        for extensions, name in supported_formats():
            info_plist['CFBundleDocumentTypes'].append({
                'CFBundleTypeExtensions': [ext[1:] for ext in extensions],
                'CFBundleTypeRole': 'Editor',
            })

        app = BUNDLE(coll,
                     name='{} {}.app'.format(PICARD_ORG_NAME, PICARD_APP_NAME),
                     icon='picard.icns',
                     bundle_identifier=None,
                     info_plist=info_plist
                     )
