# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2007, 2011 Lukáš Lalinský
# Copyright (C) 2009 Carlin Mangar
# Copyright (C) 2009, 2018-2024 Philipp Wolfer
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2012 Chad Wilson
# Copyright (C) 2012-2014 Wieland Hoffmann
# Copyright (C) 2013-2014, 2017-2025 Laurent Monin
# Copyright (C) 2014 Francois Ferrand
# Copyright (C) 2015 Sophist-UK
# Copyright (C) 2016 Ville Skyttä
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Paul Roub
# Copyright (C) 2017-2019 Antonio Larrosa
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Louis Sautier
# Copyright (C) 2024 Giorgio Fontanive
# Copyright (C) 2024 ShubhamBhut
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
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


from unittest.mock import Mock, patch

import pytest

from picard.ui.coverartbox.coverart_handlers import _iter_file_parents, _set_coverart_dispatch
from picard.ui.coverartbox.coverartsetter import CoverArtSetter, CoverArtSetterMode


@pytest.fixture
def mock_image() -> Mock:
    """Create a mock cover art image."""
    return Mock()


@pytest.fixture
def mock_obj() -> Mock:
    """Create a basic mock object with metadata."""
    obj = Mock()
    obj.metadata = Mock()
    obj.metadata.images = Mock()
    obj.metadata_images_changed = Mock()
    return obj


@pytest.fixture
def context_manager_mock() -> Mock:
    """Create a proper context manager mock."""
    context_mock = Mock()
    context_mock.__enter__ = Mock(return_value=None)
    context_mock.__exit__ = Mock(return_value=None)
    return context_mock


@pytest.fixture
def mock_album(context_manager_mock: Mock) -> Mock:
    """Create a mock Album object."""
    from picard.album import Album

    album = Mock(spec=Album)
    album.tracks = []
    album.iterfiles.return_value = []
    album.suspend_metadata_images_update = context_manager_mock
    album.metadata = Mock()
    album.metadata.images = Mock()
    album.metadata_images_changed = Mock()
    album.update = Mock()
    return album


@pytest.fixture
def mock_file() -> Mock:
    """Create a mock File object."""
    from picard.file import File

    file = Mock(spec=File)
    file.metadata = Mock()
    file.metadata.images = Mock()
    file.metadata_images_changed = Mock()
    file.update = Mock()
    return file


@pytest.fixture
def mock_filelist(context_manager_mock: Mock) -> Mock:
    """Create a mock FileListItem object."""
    from picard.item import FileListItem

    filelist = Mock(spec=FileListItem)
    filelist.iterfiles.return_value = []
    filelist.suspend_metadata_images_update = context_manager_mock
    filelist.metadata = Mock()
    filelist.metadata.images = Mock()
    filelist.metadata_images_changed = Mock()
    filelist.update = Mock()
    return filelist


@pytest.fixture
def setter_append(mock_image: Mock, mock_obj: Mock) -> CoverArtSetter:
    """Create a CoverArtSetter in APPEND mode."""
    return CoverArtSetter(CoverArtSetterMode.APPEND, mock_image, mock_obj)


@pytest.fixture
def setter_replace(mock_image: Mock, mock_obj: Mock) -> CoverArtSetter:
    """Create a CoverArtSetter in REPLACE mode."""
    return CoverArtSetter(CoverArtSetterMode.REPLACE, mock_image, mock_obj)


class TestCoverArtSetter:
    """Test cases for the CoverArtSetter class using single dispatch pattern."""

    def test_init_with_proper_types(self, mock_image: Mock, mock_obj: Mock) -> None:
        """Test that CoverArtSetter initializes with proper type hints."""
        setter = CoverArtSetter(CoverArtSetterMode.APPEND, mock_image, mock_obj)

        assert setter.mode == CoverArtSetterMode.APPEND
        assert setter.coverartimage == mock_image
        assert setter.source_obj == mock_obj

    def test_set_coverart_calls_single_dispatch(self, setter_append: CoverArtSetter, mock_obj: Mock) -> None:
        """Test that set_coverart calls the single dispatch implementation."""
        with patch('picard.ui.coverartbox.coverartsetter._set_coverart_dispatch', return_value=True) as mock_impl:
            result = setter_append.set_coverart()

            mock_impl.assert_called_once_with(mock_obj, setter_append)
            assert result is True

    def test_default_implementation_returns_false(self, setter_append: CoverArtSetter, mock_obj: Mock) -> None:
        """Test that the default implementation returns False for unknown types."""
        result = _set_coverart_dispatch(mock_obj, setter_append)
        assert result is False

    @pytest.mark.parametrize(
        'mock_obj_fixture,expected_result',
        [
            ('mock_album', True),
            ('mock_file', True),
            ('mock_filelist', True),
        ],
    )
    def test_implementation_registered(
        self,
        request: pytest.FixtureRequest,
        mock_obj_fixture: str,
        expected_result: bool,
        setter_append: CoverArtSetter,
    ) -> None:
        """Test that implementations are properly registered for different object types."""
        mock_obj = request.getfixturevalue(mock_obj_fixture)

        result = _set_coverart_dispatch(mock_obj, setter_append)
        assert result is expected_result

    @pytest.mark.parametrize(
        'mode,should_strip',
        [
            (CoverArtSetterMode.REPLACE, True),
            (CoverArtSetterMode.APPEND, False),
        ],
    )
    def test_set_image_modes(
        self, mode: CoverArtSetterMode, should_strip: bool, mock_image: Mock, mock_obj: Mock
    ) -> None:
        """Test _set_image method in different modes."""
        setter = CoverArtSetter(mode, mock_image, mock_obj)
        setter._set_image(mock_obj)

        if should_strip:
            mock_obj.metadata.images.strip_front_images.assert_called_once()
        else:
            mock_obj.metadata.images.strip_front_images.assert_not_called()

        mock_obj.metadata.images.append.assert_called_once_with(mock_image)
        mock_obj.metadata_images_changed.emit.assert_called_once()

    @pytest.mark.parametrize(
        'parent_type,parent_attr,expected_parents',
        [
            ('track', 'album', ['track', 'album']),
            ('cluster', 'related_album', ['cluster', 'album']),
            (None, None, []),
        ],
    )
    def test_iter_file_parents(
        self, parent_type: str | None, parent_attr: str | None, expected_parents: list[str]
    ) -> None:
        """Test _iter_file_parents function with different parent types."""
        from picard.file import File

        mock_file = Mock(spec=File)

        if parent_type is None:
            mock_file.parent_item = None
            parents = list(_iter_file_parents(mock_file))
            assert parents == []
            return

        # Create parent mock
        if parent_type == 'track':
            from picard.track import Track

            parent = Mock(spec=Track)
            parent.album = Mock() if parent_attr else None
        elif parent_type == 'cluster':
            from picard.cluster import Cluster

            parent = Mock(spec=Cluster)
            parent.related_album = Mock() if parent_attr else None

        mock_file.parent_item = parent

        parents = list(_iter_file_parents(mock_file))

        # Convert expected_parents to actual mock objects
        expected = [parent]
        if parent_attr and getattr(parent, parent_attr):
            expected.append(getattr(parent, parent_attr))

        assert parents == expected
