# Basic Picard 3 plugin example

from picard.plugin3.api import PluginApi


def enable(api: PluginApi) -> None:
    # api can be used to register plugin hooks and to access essential Picard APIs.
    pass


def disable() -> None:
    pass
