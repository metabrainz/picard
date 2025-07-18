#!/usr/bin/env python3
"""
Picard mit deutscher Lokalisierung starten
"""
import sys
import os
import logging

# Logging konfigurieren
logging.basicConfig(
    filename='debug.log',
    filemode='w',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s'
)

# Picard-Verzeichnis hinzufügen
picard_dir = '/home/tobber/tmp/picard_venv/musicbrainz-picard'
sys.path.insert(0, picard_dir)
os.environ['PYTHONPATH'] = picard_dir

# Deutsche Lokalisierung erzwingen
os.environ['LC_ALL'] = 'de_DE.UTF-8'
os.environ['LANG'] = 'de_DE.UTF-8'
os.environ['LANGUAGE'] = 'de'

logging.info("🇩🇪 Starting Picard with German localization...")
logging.info(f"📁 Picard Directory: {picard_dir}")
logging.info(f"🌍 Language: {os.environ.get('LANG')}")

try:
    # Picard importieren und starten
    import picard.tagger
    import picard.i18n

    # Deutsche Lokalisierung explizit setzen
    locale_dir = os.path.join(picard_dir, 'locale')
    logging.info(f"📂 Locale Directory: {locale_dir}")

    def log_and_print(msg):
        print(msg)
        logging.info(msg)

    if os.path.exists(locale_dir):
        log_and_print("✅ Locale directory found")
        # Gettext mit unserem locale-Verzeichnis initialisieren
        picard.i18n.setup_gettext(locale_dir, ui_language='de', logger=logging.info)
    else:
        log_and_print("❌ Locale directory not found")
        picard.i18n.setup_gettext(None, ui_language='de', logger=logging.info)

    # Picard GUI starten
    log_and_print("🚀 Starting Picard GUI...")
    from picard.tagger import main
    sys.exit(main())

except Exception as e:
    logging.error(f"❌ Error: {e}")
    print(f"❌ Error: {e}")
    import traceback
    logging.error(traceback.format_exc())
    traceback.print_exc()
