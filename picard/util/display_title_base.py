# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025-2026 Philipp Wolfer
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <https://www.gnu.org/licenses/>.


from picard.i18n import _


class HasDisplayTitle:
    TITLE: str | tuple[str, str, str]
    NAME: str

    """This class can be used as a mix-in by classes providing a static display title.

    This is usually be used by base classes that are supposed to be sub classes, where
    each sub class has it's own static title, but which should be translatable.
    Sub classes must define a TITLE attribute. As a fallback also a NAME attribute is
    being checked.

    Example defining such a base class:

        class GenreProvider(HasDisplayTitle):
            pass

    A sub class of this should define a TITLE class attribute. For Picard internal
    sub classes the title should be marked with N_() for translation:

        from picard.i18n import N_

        class MyGenreProvider(GenreProvider):

            TITLE = N_("My genres")

    Plugins should instead use the t_() function exposed by the plugin API:

        from picard.plugin3.api import t_

        class MyGenreProvider(GenreProvider):

            TITLE = t_("genre_provider.title", "My genres")
    """

    @classmethod
    def display_title(cls) -> str:
        """Returns the display title for this class.
        This will attempt to translate the title with the API translation system if
        available, otherwise use gettext.
        """
        title = getattr(cls, 'TITLE', getattr(cls, 'NAME', None)) or cls.__name__
        api = getattr(cls, 'api', None)
        if api:
            # In case the TITLE was created with t_() using a plural form
            if isinstance(title, tuple):
                return api.trn(*title, n=1)
            else:
                return api.tr(title)
        else:
            return _(title)


class HasMenuItems:
    """This class can be used as a mix-in by classes providing a static MENU tuple,
    such as the BaseAction class used for adding plugin actions to menus.

    A sub class of this should define a MENU class attribute, as a tuple defining the
    desired menu hierarchy. Each element is either a plain string or, for plugins, a
    string marked with the t_() function exposed by the plugin API (which may expand to
    a (key, singular, plural) tuple for plural forms).
    """

    MENU: tuple[str | tuple[str, str, str], ...]

    @classmethod
    def display_menu(cls) -> tuple[str, ...]:
        """Return the translated MENU path for this class.

        This attempts to translate each element with the API translation system if
        available, otherwise uses gettext. The class ``MENU`` attribute is left
        unchanged, so the method is safe to call repeatedly.
        """
        menu = getattr(cls, 'MENU', ())
        api = getattr(cls, 'api', None)
        translated: list[str] = []
        for item in menu:
            if api:
                # In case the item was created with t_() using a plural form
                if isinstance(item, tuple):
                    translated.append(api.trn(*item, n=1))
                else:
                    translated.append(api.tr(item))
            elif isinstance(item, tuple):
                translated.append(_(item[1]))
            else:
                translated.append(_(item))
        return tuple(translated)
