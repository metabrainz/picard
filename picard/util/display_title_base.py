# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2025 Philipp Wolfer
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
