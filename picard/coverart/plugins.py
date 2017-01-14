import json
from hashlib import md5
from uuid import uuid4
from PyQt4.QtCore import QMutex
from picard import config, log
from picard.plugin import PluginFunctions

FILE_ACTION = 0
DOWNLOAD_ACTION = 1
TAG_ACTION = 2

_coverart_downloaded_actions = PluginFunctions()
_coverart_tag_embed_actions = PluginFunctions()
_coverart_file_save_actions = PluginFunctions()

_process_cache = set()
_cache_mutex = QMutex(QMutex.Recursive)


def register_coverart_downloaded_action(action):
    _coverart_downloaded_actions.register(action.__module__, action)


def register_coverart_tag_embed_action(action):
    _coverart_tag_embed_actions.register(action.__module__, action)


def register_coverart_file_save_action(action):
    _coverart_file_save_actions.register(action.__module__, action)


def run_coverart_downloaded_action(coverartimage):
    _coverart_downloaded_actions.run(coverartimage)


def run_coverart_tag_embed_action(coverartimage):
    _coverart_tag_embed_actions.run(coverartimage)


def run_coverart_file_save_action(coverartimage):
    _coverart_file_save_actions.run(coverartimage)


_actions = [register_coverart_file_save_action,
            register_coverart_downloaded_action,
            register_coverart_tag_embed_action]


class CoverartPluginFunction(object):

    def __init__(self, action_type):
        self.id = uuid4()
        self.options = list()
        self.processor = None
        self.extra_settings = dict()
        _actions[action_type](self._run_processor)

    def _run_processor(self, coverartimage):
        if not is_cached(self.id, coverartimage, self.options, self.extra_settings):
            if self.processor:
                self.processor(coverartimage)
                log.debug('Running processor')
        else:
            log.debug('Processing cached, skipping')


def is_cached(action_id, coverartimage, options, extra_settings):
    _cache_mutex.lock()
    result = False
    try:
        m = md5()
        if not coverartimage.original_datahash:
            coverartimage.original_datahash = coverartimage.datahash
        m.update(coverartimage.original_data)
        for option in options:
            m.update("{}:{}".format(option.name, config.setting[option.name]))
        if extra_settings:
            m.update(json.dumps(extra_settings))
        m.update(action_id.hex)
        process_hash = m.hexdigest()
        if process_hash not in _process_cache:
            _process_cache.add(process_hash)
        else:
            result = True
    except Exception as e:
        print(e)
    finally:
        _cache_mutex.unlock()
        return result
