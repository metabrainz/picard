# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
#
# Copyright (C) 2006-2008, 2011 Lukáš Lalinský
# Copyright (C) 2008-2009 Nikolai Prokoschenko
# Copyright (C) 2008-2009, 2018-2022, 2025 Philipp Wolfer
# Copyright (C) 2011 Pavan Chander
# Copyright (C) 2011-2012, 2019 Wieland Hoffmann
# Copyright (C) 2011-2013 Michael Wiencek
# Copyright (C) 2013, 2017-2024 Laurent Monin
# Copyright (C) 2014 Sophist-UK
# Copyright (C) 2016-2017 Sambhav Kothari
# Copyright (C) 2017 Suhas
# Copyright (C) 2018 Vishal Choudhary
# Copyright (C) 2021 Gabriel Ferreira
# Copyright (C) 2021-2023, 2025 Bob Swift
# Copyright (C) 2024 Giorgio Fontanive
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


from typing import TYPE_CHECKING

from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import (
    log,
    tagger_instance,
)
from picard.config import (
    Option,
    OptionError,
    get_config,
)
from picard.extension_points.options_pages import ext_point_options_pages
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.profile import (
    is_plugin_profile_key,
    profile_groups_group_from_page,
    profile_groups_order,
    setting_profile_key,
)
from picard.util import (
    get_url,
    restore_method,
)

from picard.ui import (
    HashableTreeWidgetItem,
    PicardDialog,
    SingletonDialog,
    modal_options,
)
from picard.ui.colors import interface_colors as _interface_colors
from picard.ui.forms.ui_options import Ui_OptionsDialog
from picard.ui.forms.ui_options_attached_profiles import (
    Ui_AttachedProfilesDialog,
)
from picard.ui.options import (  # noqa: F401 # pylint: disable=unused-import
    OptionsCheckError,
    OptionsPage,
    advanced,
    cdlookup,
    cover,
    cover_processing,
    fingerprinting,
    general,
    genres,
    interface,
    interface_colors,
    interface_cover_art_box,
    interface_quick_menu,
    interface_toolbar,
    interface_top_tags,
    maintenance,
    matching,
    metadata,
    network,
    player,
    plugins,
    profiles,
    ratings,
    releases,
    renaming,
    renaming_compat,
    scripting,
    sessions,
    startup,
    tags,
    tags_compatibility_aac,
    tags_compatibility_ac3,
    tags_compatibility_id3,
    tags_compatibility_wave,
)


if TYPE_CHECKING:
    from picard.ui.options.profiles import ProfilesOptionsPage


class ErrorOptionsPage(OptionsPage):
    def __init__(self, parent=None, errmsg='', from_cls: OptionsPage | None = None, dialog=None):
        # copy properties from failing page
        self.NAME = from_cls.NAME
        self.TITLE = from_cls.TITLE
        self.PARENT = from_cls.PARENT
        self._original_class = from_cls  # Track original class for duplicate detection
        self.SORT_ORDER = from_cls.SORT_ORDER
        self.ACTIVE = from_cls.ACTIVE
        self.HELP_URL = from_cls.HELP_URL

        super().__init__(parent=parent)

        self.error = _("This page failed to initialize")

        title_widget = QtWidgets.QLabel(_('Error while initializing option page "%s":') % _(from_cls.TITLE))

        error_widget = QtWidgets.QLabel()
        error_widget.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        error_widget.setText(errmsg)
        error_widget.setWordWrap(True)
        error_widget.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        error_widget.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        error_widget.setLineWidth(1)
        error_widget.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard | QtCore.Qt.TextInteractionFlag.TextSelectableByMouse
        )

        report_bug_widget = QtWidgets.QLabel(
            _('Please see <a href="%s">Troubleshooting documentation</a> and eventually report a bug.')
            % get_url('troubleshooting')
        )
        report_bug_widget.setOpenExternalLinks(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(title_widget)
        layout.addWidget(error_widget)
        layout.addWidget(report_bug_widget)
        layout.addStretch()
        self.ui = layout

        self.dialog = dialog


def _is_simple_value(value) -> bool:
    """Return True if the value is a simple scalar that can be reliably compared."""
    return isinstance(value, (str, int, float, bool))


class OptionsDialog(PicardDialog, SingletonDialog):
    suspend_signals = False

    def add_pages(self, parent_pagename, default_pagename, parent_item):
        pages = (p for p in self.pages if p.PARENT == parent_pagename)
        items = []
        for page in sorted(pages, key=lambda p: (p.SORT_ORDER, p.NAME)):
            # Check if this is a plugin option page and if the plugin is enabled
            page_active = page.ACTIVE
            api = getattr(type(page), 'api', None)
            if api is not None:  # This is a plugin option page
                try:
                    plugin_uuid = api._manifest.uuid if hasattr(api, '_manifest') and api._manifest else None
                    if plugin_uuid and getattr(self, 'plugin_manager', None):
                        # Only show page if plugin is enabled
                        is_enabled = plugin_uuid in self.plugin_manager._enabled_plugins
                        page_active = is_enabled
                    else:
                        # If we can't check plugin status, assume it's active if it has an API
                        page_active = True
                except AttributeError:
                    # Plugin manager not available, assume active
                    page_active = True

            # Skip disabled pages entirely
            if not page_active:
                continue

            item = HashableTreeWidgetItem(parent_item)
            if not page.initialized:
                title = _("%s (error)") % page.display_title()
            else:
                title = page.display_title()
            item.setText(0, title)
            if page_active:
                self.item_to_page[item] = page
                self.pagename_to_item[page.NAME] = item
                profile_groups_order(page.NAME)

                # If this is a plugin page and it matches the saved page, select it
                if (
                    api is not None
                    and not self.default_item
                    and page.NAME == get_config().persist['options_last_active_page']
                ):
                    log.debug("add_pages: Found saved plugin page '%s', setting as default_item", page.NAME)
                    self.default_item = item
            else:
                item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.add_pages(page.NAME, default_pagename, item)
            if page.NAME == default_pagename:
                log.debug("add_pages: Found matching page '%s', setting as default_item", page.NAME)
                self.default_item = item
            items.append(item)
        if not self.default_item and not parent_pagename:
            self.default_item = items[0] if items else None

    def __init__(self, default_page=None, parent=None):
        super().__init__(parent=parent)
        if modal_options():
            # On macOS: use WindowModal (blocks MainWindow, allows child windows
            # like Script Editor to be shown above). Add Window flag to prevent
            # sheet rendering.
            self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.Window)
        else:
            # On Linux/Windows: use NonModal + disabled MainWindow (set in
            # show_options). Use Tool type to stay above parent (MainWindow)
            # without staying on top of other applications.
            self.setWindowModality(QtCore.Qt.WindowModality.NonModal)
            self.setWindowFlags(
                QtCore.Qt.WindowType.Tool
                | QtCore.Qt.WindowType.WindowTitleHint
                | QtCore.Qt.WindowType.WindowSystemMenuHint
                | QtCore.Qt.WindowType.WindowCloseButtonHint
            )
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        self.ui = Ui_OptionsDialog()
        self.ui.setupUi(self)

        # Profile warning
        profile_layout = self.ui.profile_warning.layout()
        profile_warning_icon = QtWidgets.QLabel()
        profile_warning_icon.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Preferred)
        profile_warning_icon.setPixmap(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning).pixmap(20, 20)
        )
        profile_layout.addWidget(profile_warning_icon)

        self.profile_warning_text = QtWidgets.QLabel()
        self.profile_warning_text.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Preferred
        )
        profile_layout.addWidget(self.profile_warning_text)

        profile_help_button = QtWidgets.QToolButton()
        profile_help_button.setIcon(self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxQuestion))
        profile_help_button.setToolTip(_("Display help regarding option profiles"))
        profile_help_button.clicked.connect(self._show_profile_help)
        profile_layout.addWidget(profile_help_button)

        self.ui.reset_all_button = QtWidgets.QPushButton(_("&Restore all Defaults"))
        self.ui.reset_all_button.setToolTip(_("Reset all of Picard's settings"))
        self.ui.reset_button = QtWidgets.QPushButton(_("Restore &Defaults"))
        self.ui.reset_button.setToolTip(_("Reset all settings for current option page"))

        # Buttons
        ok = QtWidgets.QPushButton(_("Make It So!"))
        self.ui.buttonbox.addButton(ok, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        self.ui.buttonbox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Help)
        self.ui.buttonbox.addButton(self.ui.reset_all_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.ui.buttonbox.addButton(self.ui.reset_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)

        self.ui.buttonbox.accepted.connect(self.accept)
        self.ui.buttonbox.rejected.connect(self.reject)
        self.ui.reset_all_button.clicked.connect(self.confirm_reset_all)
        self.ui.reset_button.clicked.connect(self.confirm_reset)
        self.ui.buttonbox.helpRequested.connect(self.show_help)

        self.ui.attached_profiles_button = QtWidgets.QPushButton(_("Attached Profiles"))
        self.ui.attached_profiles_button.setToolTip(_("Show which profiles are attached to the options on this page"))
        self.ui.buttonbox.addButton(self.ui.attached_profiles_button, QtWidgets.QDialogButtonBox.ButtonRole.ActionRole)
        self.ui.attached_profiles_button.clicked.connect(self.show_attached_profiles_dialog)

        config = get_config()

        self.pages = []
        for Page in ext_point_options_pages:
            try:
                page = Page()
                page.set_dialog(self)
                page.initialized = True
            except Exception as e:
                log.exception("Failed initializing options page %r", Page)
                # create an empty page with the error message in place of the failing page
                # this approach still allows subpages of the failing page to load
                page = ErrorOptionsPage(from_cls=Page, errmsg=str(e), dialog=self)
            self.ui.pages_stack.addWidget(page)
            self.pages.append(page)

        self.item_to_page = {}
        self.pagename_to_item = {}
        self.default_item = None
        if not default_page:
            default_page = config.persist['options_last_active_page']
        self._default_page = default_page
        log.debug("OptionsDialog init: Trying to restore page '%s'", default_page)
        self.add_pages(None, default_page, self.ui.pages_tree)

        # work-around to set optimal option pane width
        self.ui.pages_tree.expandAll()
        max_page_name = self.ui.pages_tree.sizeHintForColumn(0) + 2 * self.ui.pages_tree.frameWidth()
        self.ui.dialog_splitter.setSizes([max_page_name, self.geometry().width() - max_page_name])

        self.ui.pages_tree.setHeaderLabels([""])
        self.ui.pages_tree.header().hide()

        self.restoreWindowState()
        self.finished.connect(self.saveWindowState)

        self.load_all_pages()

        maintenance_page = self.get_page('maintenance')
        if maintenance_page.loaded:
            maintenance_page.signal_reload.connect(self.load_all_pages)

        profile_page = self.get_page('profiles')
        if profile_page.loaded:
            profile_page.signal_refresh.connect(self.update_from_profile_changes)
            self.highlight_enabled_profile_options()

        self.ui.pages_tree.itemSelectionChanged.connect(self.switch_page)

        # Connect to plugin manager signals for dynamic updates
        tagger = tagger_instance()
        self.plugin_manager = tagger.get_plugin_manager()
        try:
            self.plugin_manager.plugin_ref_switched.connect(self.refresh_plugin_pages)
            # Connect to other plugin state changes
            self.plugin_manager.plugin_installed.connect(self.refresh_plugin_pages)
            self.plugin_manager.plugin_state_changed.connect(self.refresh_plugin_pages)
            self.plugin_manager.plugin_uninstalled.connect(self.refresh_plugin_pages)

            # Initial refresh to pick up any plugin option pages that were registered
            # since the last time the options dialog was opened
            self.refresh_plugin_pages()
        except AttributeError:
            # Plugin manager not available - this should not happen in normal operation
            pass

        # Set initial selection after plugin refresh
        if self.default_item:
            self.ui.pages_tree.setCurrentItem(self.default_item)  # this will call switch_page

    @property
    def initialized_pages(self):
        yield from (page for page in self.pages if page.initialized)

    @property
    def loaded_pages(self):
        yield from (page for page in self.pages if page.loaded)

    def load_all_pages(self):
        for page in self.initialized_pages:
            try:
                page.load()
                page.loaded = True
            except Exception:
                log.exception("Failed loading options page %r", page)
                self.disable_page(page.NAME)

    def show_attached_profiles_dialog(self):
        items = self.ui.pages_tree.selectedItems()
        if not items:
            return
        page = self.item_to_page[items[0]]
        option_group = profile_groups_group_from_page(page)
        if option_group:
            self.display_attached_profiles(option_group)
        else:
            self.display_simple_message_box(
                _("Profiles Attached to Options"),
                _("The options on this page are not currently available to be managed using profiles."),
            )

    def _show_profile_help(self):
        self.show_help('/usage/option_profiles.html')

    def display_simple_message_box(self, window_title, message):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Information)
        message_box.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        message_box.setWindowTitle(window_title)
        message_box.setText(message)
        message_box.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
        message_box.exec()

    def display_attached_profiles(self, option_group: dict) -> None:
        profile_page = self.get_page('profiles')
        profile_dialog = AttachedProfilesDialog(
            option_group,
            profile_page,
            parent=self,
        )
        profile_dialog.show_modal()

    def update_from_profile_changes(self):
        if not self.suspend_signals:
            self.highlight_enabled_profile_options(load_settings=True)

    def get_working_profile_data(self):
        profile_page = self.get_page('profiles')
        working_profiles = profile_page._clean_and_get_all_profiles()
        if working_profiles is None:
            working_profiles = []
        working_settings = profile_page.profile_settings
        return working_profiles, working_settings

    def highlight_enabled_profile_options(self, load_settings=False):
        working_profiles, working_settings = self.get_working_profile_data()
        bg_tracked = _interface_colors.get_color_css_rgba('profile_hl_bg', alpha=50)
        bg_override = _interface_colors.get_color_css_rgba('profile_hl_bg', alpha=120)

        for page in self.loaded_pages:
            option_group = profile_groups_group_from_page(page)
            if option_group:
                if load_settings:
                    page.load()
                seen_widgets = set()
                for opt in option_group['settings']:
                    for objname in opt.highlights:
                        try:
                            obj = getattr(page.ui, objname)
                        except AttributeError:
                            try:
                                obj = getattr(page, objname)
                            except AttributeError:
                                log.warning(
                                    "Option '%s' references widget '%s' not found on page '%s'",
                                    opt.name,
                                    objname,
                                    page.NAME,
                                )
                                continue
                        if not isinstance(obj, QtWidgets.QWidget):
                            log.warning(
                                "Option '%s' references widget '%s', expected QWidget, found '%s' on page '%s'",
                                opt.name,
                                objname,
                                obj.__class__.__name__,
                                page.NAME,
                            )
                            continue
                        # Skip list/tree views - stylesheets break checkable item rendering
                        if isinstance(obj, QtWidgets.QAbstractItemView):
                            continue
                        style_override = "#%s { background-color: %s; }" % (objname, bg_override)
                        style_tracked = "#%s { background-color: %s; }" % (objname, bg_tracked)
                        style_reset = "#%s { }" % (objname)
                        self._check_and_highlight_option(
                            obj,
                            setting_profile_key(opt.name, opt.section),
                            working_profiles,
                            working_settings,
                            style_override,
                            style_tracked,
                            style_reset,
                            seen_widgets,
                        )

    def _check_and_highlight_option(
        self,
        obj,
        option_name,
        working_profiles,
        working_settings,
        style_override,
        style_tracked,
        style_reset,
        seen_widgets,
    ):
        obj.setStyleSheet(style_reset)
        # Save original tooltip on first encounter, restore it on each pass
        if not hasattr(obj, '_original_tooltip'):
            obj._original_tooltip = obj.toolTip() or ''
        obj.setToolTip(obj._original_tooltip)
        config = get_config()
        for item in working_profiles:
            if not item['enabled']:
                continue
            profile_id = item['id']
            profile_title = item['title']
            profile_settings = working_settings.get(profile_id, {})
            if option_name not in profile_settings:
                continue
            profile_value = profile_settings[option_name]
            if profile_value is None:
                # Tracked but no value set yet
                tooltip_text = _("This option is tracked by profile: %s") % profile_title
                obj.setStyleSheet(style_tracked)
            else:
                # Check if value actually differs from base
                if is_plugin_profile_key(option_name):
                    section, name = option_name.split('/', 1)
                    opt = Option.get(section, name)
                    base_value = opt.default if opt else None
                else:
                    opt = Option.get('setting', option_name)
                    with config.setting.no_profile():
                        base_value = config.setting[option_name]
                # Convert profile value to same type for comparison
                if opt:
                    try:
                        profile_value = opt.convert(profile_value)
                    except (ValueError, TypeError):
                        pass
                if _is_simple_value(profile_value) and profile_value != base_value:
                    tooltip_text = _("This option is overridden by profile: %s") % profile_title
                    obj.setStyleSheet(style_override)
                else:
                    tooltip_text = _("This option is tracked by profile: %s") % profile_title
                    obj.setStyleSheet(style_tracked)
            # Append to existing tooltip if not already present
            if obj in seen_widgets:
                break
            seen_widgets.add(obj)
            # Fix combobox dropdown text color
            if isinstance(obj, QtWidgets.QComboBox):
                pal = obj.view().palette()
                pal.setColor(
                    pal.ColorRole.HighlightedText,
                    QtGui.QColor(_interface_colors.get_color('profile_hl_fg')),
                )
                obj.view().setPalette(pal)
            existing = obj.toolTip() or ''
            if existing:
                if QtCore.Qt.mightBeRichText(existing):
                    from html import escape

                    obj.setToolTip(existing + '<br>' + escape(tooltip_text))
                else:
                    obj.setToolTip(existing + '\n' + tooltip_text)
            else:
                obj.setToolTip(tooltip_text)
            break

    def get_page(self, pagename):
        return self.item_to_page[self.pagename_to_item[pagename]]

    def set_profiles_button_and_highlight(self, page):
        option_group = profile_groups_group_from_page(page)
        defined_profiles = self.get_page('profiles')._clean_and_get_all_profiles()
        # Only enable the dialog button if there are profiles defined and an option group on the page
        self.ui.attached_profiles_button.setEnabled(bool(option_group) and bool(defined_profiles))
        self.update_profile_save_warning(page)

    def update_profile_save_warning(self, page):
        working_profiles, working_settings = self.get_working_profile_data()
        profile_set = set()

        option_group = profile_groups_group_from_page(page)
        if option_group:
            for opt in option_group['settings']:
                for idx, item in enumerate(working_profiles):
                    if not item['enabled']:
                        continue
                    profile_id = item['id']
                    if profile_id not in working_settings:
                        continue
                    profile_settings = working_settings[profile_id]
                    if setting_profile_key(opt.name, opt.section) in profile_settings:
                        profile_set.add((idx, item['title']))

        if not profile_set:
            self.ui.profile_warning.setVisible(False)
            return

        sorted_profiles = sorted(profile_set)
        if len(sorted_profiles) <= 3:
            names = ', '.join([f'"{p[1]}"' for p in sorted_profiles])
        else:
            names = ', '.join([f'"{p[1]}"' for p in sorted_profiles[:3]]) + ', …'

        has_highlights = option_group and any(opt.highlights for opt in option_group['settings'])
        if has_highlights:
            msg = _('The highlighted settings on this page are overridden by %s') % names
        else:
            msg = _('Some settings on this page are overridden by %s') % names
        self.profile_warning_text.setText(msg)
        self.ui.profile_warning.setVisible(True)

    def switch_page(self):
        items = self.ui.pages_tree.selectedItems()
        if items:
            page = self.item_to_page[items[0]]
            self.set_profiles_button_and_highlight(page)
            self.ui.reset_button.setDisabled(not page.loaded)
            self.ui.pages_stack.setCurrentWidget(page)
            config = get_config()
            log.debug("switch_page: Saving page '%s' to options_last_active_page", page.NAME)
            config.persist['options_last_active_page'] = page.NAME

    def disable_page(self, pagename):
        item = self.pagename_to_item[pagename]
        item.setDisabled(True)

    def refresh_plugin_pages(self):
        """Refresh plugin option pages based on current plugin state."""
        log.debug("refresh_plugin_pages: Starting refresh")

        # Store current selection
        current_page = None
        selected_items = self.ui.pages_tree.selectedItems()
        if selected_items and selected_items[0] in self.item_to_page:
            current_page = self.item_to_page[selected_items[0]].NAME

        config = get_config()

        # Get currently active extension point pages
        active_page_classes = set(ext_point_options_pages)

        # Debug detailed extension point information (can be enabled for troubleshooting)
        if False:
            log.debug("refresh_plugin_pages: Active page classes: %s", [cls.__name__ for cls in active_page_classes])

            # Check what the extension point is actually yielding
            all_registered_pages = []
            for page_class in ext_point_options_pages._ExtensionPoint__dict.values():
                all_registered_pages.extend(page_class)
            log.debug("refresh_plugin_pages: All registered pages: %s", [cls.__name__ for cls in all_registered_pages])

            # Check enabled plugins and UUID mapping
            enabled_plugins = config.setting['plugins3_enabled_plugins']
            log.debug("refresh_plugin_pages: Enabled plugins: %s", enabled_plugins)

            # Check UUID mapping
            # Avoid circular import: ui.options.dialog → extension_points → ui
            from picard.extension_points import _plugin_uuid_to_module

            log.debug("refresh_plugin_pages: UUID to module mapping: %s", _plugin_uuid_to_module)

        # Remove pages from disabled plugins
        pages_to_remove = []
        for page in self.pages:
            page_class = type(page)
            # Check if this is a plugin page that's no longer active
            # For error pages, check the original class
            original_class = getattr(page, '_original_class', page_class)
            if hasattr(original_class, 'api') and original_class not in active_page_classes:
                pages_to_remove.append(page)
                log.debug("refresh_plugin_pages: Marking page for removal: %s", page_class.__name__)

        # Remove disabled plugin pages from UI stack and pages list
        for page in pages_to_remove:
            log.debug("refresh_plugin_pages: Removing page: %s", type(page).__name__)
            self.ui.pages_stack.removeWidget(page)
            self.pages.remove(page)
            page.deleteLater()  # Clean up the widget

        # Add new plugin pages
        existing_page_classes = {type(page) for page in self.pages}
        # Also track original classes for error pages to prevent duplicates
        existing_original_classes = {getattr(page, '_original_class', type(page)) for page in self.pages}

        for Page in active_page_classes:
            if Page not in existing_page_classes and Page not in existing_original_classes:
                log.debug("refresh_plugin_pages: Adding new page: %s", Page.__name__)
                try:
                    page = Page()
                    page.set_dialog(self)
                    page.initialized = True
                    self.ui.pages_stack.addWidget(page)
                    self.pages.append(page)
                    # Load the page if needed
                    try:
                        page.load()
                        page.loaded = True
                        log.debug("refresh_plugin_pages: Successfully loaded page: %s", Page.__name__)
                    except Exception:
                        log.exception("Failed loading options page %r", page)
                except Exception as e:
                    log.exception("Failed creating options page %r", Page)
                    # Create an error page in place of the failing page
                    page = ErrorOptionsPage(from_cls=Page, errmsg=str(e), dialog=self)
                    self.ui.pages_stack.addWidget(page)
                    self.pages.append(page)

        # Clear and rebuild the pages tree
        self.ui.pages_tree.clear()
        self.item_to_page.clear()
        self.pagename_to_item.clear()
        self.default_item = None  # Clear reference to deleted tree item

        # Rebuild pages tree
        default_page = current_page or self._default_page
        self.add_pages(None, default_page, self.ui.pages_tree)

        # Restore tree state
        self.ui.pages_tree.expandAll()

        # Restore selection if possible - prioritize current_page over default_page
        if current_page and current_page in self.pagename_to_item:
            self.ui.pages_tree.setCurrentItem(self.pagename_to_item[current_page])
        elif default_page and default_page in self.pagename_to_item:
            self.ui.pages_tree.setCurrentItem(self.pagename_to_item[default_page])
        elif self.default_item:
            self.ui.pages_tree.setCurrentItem(self.default_item)

        log.debug("refresh_plugin_pages: Refresh complete")

        # Rebuild the profile settings tree to reflect plugin option changes.
        # Use profile_selected() instead of load() to preserve unsaved
        # in-memory profile data (new profiles, settings changes).
        profile_page = self.get_page('profiles')
        if profile_page and profile_page.loaded:
            profile_page.profile_selected()
            profile_page.update_config_overrides()
            self.highlight_enabled_profile_options()

    def enable_page(self, pagename):
        """Enable a page in the options tree."""
        if pagename in self.pagename_to_item:
            item = self.pagename_to_item[pagename]
            item.setFlags(QtCore.Qt.ItemFlag.ItemIsSelectable | QtCore.Qt.ItemFlag.ItemIsEnabled)

    @property
    def help_url(self):
        current_page = self.ui.pages_stack.currentWidget()
        url = current_page.HELP_URL
        # If URL is empty, use the first non empty parent help URL.
        while current_page.PARENT and not url:
            current_page = self.get_page(current_page.PARENT)
            url = current_page.HELP_URL
        if not url:
            url = 'doc_options'  # key in PICARD_DOCS_URLS
        return url

    def accept(self):
        for page in self.loaded_pages:
            try:
                page.check()
            except OptionsCheckError as e:
                self._show_page_error(page, e)
                return
            except Exception as e:
                log.exception("Failed checking options page %r", page)
                self._show_page_error(page, e)
                return

        # Force the `profiles` page to always save first to avoid an error when
        # saving settings to a new profile that has been marked as enabled.
        profile_page = self.get_page('profiles')
        try:
            profile_page.save()
        except Exception as e:
            log.exception("Failed saving options page %r", profile_page)
            self._show_page_error(profile_page, e)
            return

        # Clear overrides so subsequent page saves use persisted profile state
        # rather than the dialog's working copy (which was already saved above)
        config = get_config()
        config.setting.set_profiles_override()
        config.setting.set_settings_override()

        for page in sorted(self.loaded_pages, key=lambda p: (p.SORT_ORDER, p.NAME)):
            if page.NAME == 'profiles':
                continue
            try:
                page.save()
            except Exception as e:
                log.exception("Failed saving options page %r", page)
                self._show_page_error(page, e)
                return
        super().accept()

    def _show_page_error(self, page, error):
        if not isinstance(error, OptionsCheckError):
            error = OptionsCheckError(_("Unexpected error"), str(error))
        self.ui.pages_tree.setCurrentItem(self.pagename_to_item[page.NAME])
        page.display_error(error)

    def saveWindowState(self):
        expanded_pages = []
        for pagename, item in self.pagename_to_item.items():
            index = self.ui.pages_tree.indexFromItem(item)
            is_expanded = self.ui.pages_tree.isExpanded(index)
            expanded_pages.append((pagename, is_expanded))
        config = get_config()
        config.persist['options_pages_tree_state'] = expanded_pages
        config.setting.set_profiles_override()
        config.setting.set_settings_override()

    @restore_method
    def restoreWindowState(self):
        config = get_config()
        pages_tree_state = config.persist['options_pages_tree_state']
        if not pages_tree_state:
            self.ui.pages_tree.expandAll()
        else:
            for pagename, is_expanded in pages_tree_state:
                try:
                    item = self.pagename_to_item[pagename]
                    item.setExpanded(is_expanded)
                except KeyError as e:
                    log.debug("Failed restoring expanded state: %s", e)

    def restore_all_defaults(self):
        self.suspend_signals = True
        for page in self.loaded_pages:
            try:
                page.restore_defaults()
            except Exception as e:
                log.error("Failed restoring all defaults for page %r: %s", page, e)
        self.highlight_enabled_profile_options(load_settings=False)
        self.suspend_signals = False

    def restore_page_defaults(self):
        current_page = self.ui.pages_stack.currentWidget()
        if current_page.loaded:
            current_page.restore_defaults()
            self.highlight_enabled_profile_options(load_settings=False)

    def confirm_reset(self):
        msg = _("You are about to reset your options for this page.")
        self._show_dialog(msg, self.restore_page_defaults)

    def confirm_reset_all(self):
        msg = _("Warning! This will reset all of your settings.")
        self._show_dialog(msg, self.restore_all_defaults)

    def _show_dialog(self, msg, function):
        message_box = QtWidgets.QMessageBox(self)
        message_box.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        message_box.setWindowModality(QtCore.Qt.WindowModality.WindowModal)
        message_box.setWindowTitle(_("Confirm Reset"))
        message_box.setText(_("Are you sure?") + "\n\n" + msg)
        message_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        if message_box.exec() == QtWidgets.QMessageBox.StandardButton.Yes:
            function()


class _NoSelectionDelegate(QtWidgets.QStyledItemDelegate):
    """Delegate that paints items without selection highlight."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.state &= ~QtWidgets.QStyle.StateFlag.State_Selected


class AttachedProfilesDialog(PicardDialog):
    NAME = 'attachedprofiles'
    TITLE = N_("Attached Profiles")
    MARKER_ACTIVE = "★"
    MARKER_INACTIVE = "☆"

    def __init__(self, option_group: dict, profile_page: 'ProfilesOptionsPage', parent=None) -> None:
        super().__init__(parent=parent)
        self.option_group = option_group
        self.profile_page = profile_page
        self._building_tree: bool = False
        self._highlighted_item: QtWidgets.QTreeWidgetItem | None = None

        self.ui = Ui_AttachedProfilesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.ui.buttonBox.rejected.connect(self.close_window)
        self.ui.splitter.setStretchFactor(1, 1)

        self.setWindowTitle(_("Profiles Attached to Options in %s Section") % self.option_group['title'])

        # Show all profiles because even disabled profiles can be attached to options
        self._enabled_profiles = self.profile_page._clean_and_get_all_profiles()

        self._populate_profile_list()
        self.ui.profile_list.setIndentation(0)
        self.ui.profile_list.setItemDelegateForColumn(0, _NoSelectionDelegate(self.ui.profile_list))
        self.ui.profile_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.ui.settings_tree.itemChanged.connect(self._on_item_changed)
        self.ui.settings_tree.setMouseTracking(True)
        self.ui.settings_tree.setIndentation(0)
        self.ui.settings_tree.itemEntered.connect(self._on_item_hovered)

        # Hide left pane if only one enabled profile
        if len(self._enabled_profiles) <= 1:
            self.ui.profile_list.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.NoSelection)

        self._last_selection = []
        if len(self._enabled_profiles) > 1 and self.ui.profile_list.topLevelItemCount() > 0:
            self.ui.profile_list.topLevelItem(0).setSelected(True)
        elif len(self._enabled_profiles) == 1:
            self._populate_settings_tree()

    # --- Profile list ---

    def _populate_profile_list(self) -> None:
        self.ui.profile_list.clear()
        self.ui.profile_list.setToolTip(
            _(
                "Hover an option to see which profiles contain it.\n"
                "%s = option is in this profile, %s = option is not in this profile"
            )
            % (self.MARKER_ACTIVE, self.MARKER_INACTIVE)
        )
        fm = self.ui.profile_list.fontMetrics()
        marker_width = fm.horizontalAdvance(self.MARKER_ACTIVE) + 4
        marker_height = fm.boundingRect(self.MARKER_ACTIVE).height()
        marker_size = QtCore.QSize(marker_width, marker_height)
        for profile in self._enabled_profiles:
            # Identify profiles that are disabled but still attached to options with the "(disabled)" suffix,
            # but keep them selectable so users can manage their attached options from the page.
            item = QtWidgets.QTreeWidgetItem(
                [self.MARKER_INACTIVE, profile['title'] + (_(" (disabled)") if not profile['enabled'] else "")]
            )
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, profile['id'])
            item.setSizeHint(0, marker_size)
            self.ui.profile_list.addTopLevelItem(item)
        self.ui.profile_list.header().setMinimumSectionSize(marker_width)
        self.ui.profile_list.header().resizeSection(0, marker_width)
        self.ui.profile_list.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeMode.Fixed)

    def _selected_profile_ids(self) -> list[str]:
        ids = [item.data(0, QtCore.Qt.ItemDataRole.UserRole) for item in self.ui.profile_list.selectedItems()]
        if not ids:
            # No selection (single profile mode) — use all enabled profiles
            ids = [p['id'] for p in self._enabled_profiles]
        return ids

    def _on_selection_changed(self) -> None:
        if not self.ui.profile_list.selectedItems():
            # Never allow empty selection
            self.ui.profile_list.blockSignals(True)
            if len(self._last_selection) == 1:
                self._last_selection[0].setSelected(True)
            else:
                first = self.ui.profile_list.topLevelItem(0)
                first.setSelected(True)
                self._last_selection = [first]
            self.ui.profile_list.blockSignals(False)
            return
        self._last_selection = list(self.ui.profile_list.selectedItems())
        self._populate_settings_tree()

    # --- Settings tree ---

    def _populate_settings_tree(self) -> None:
        self._building_tree = True
        self._highlighted_item = None
        self._check_states = {}
        self.ui.settings_tree.clear()
        selected_ids = self._selected_profile_ids()
        for setting in self.option_group['settings']:
            try:
                title = Option.get_title(setting.section, setting.name)
            except OptionError as e:
                log.debug(e)
                continue
            if title is None:
                title = setting.name
            pkey = setting_profile_key(setting.name, setting.section)
            item = QtWidgets.QTreeWidgetItem([_(title)])
            item.setData(0, QtCore.Qt.ItemDataRole.UserRole, pkey)
            item.setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
            state = self._compute_check_state(pkey, selected_ids)
            self._check_states[pkey] = state
            item.setCheckState(0, state)
            item.setToolTip(0, self._build_tooltip(pkey))
            self.ui.settings_tree.addTopLevelItem(item)
        self._building_tree = False

    def _compute_check_state(self, pkey: str, selected_ids: list[str]) -> QtCore.Qt.CheckState:
        """Determine check state for an option given selected profiles."""
        if selected_ids:
            in_count = sum(1 for pid in selected_ids if pkey in self.profile_page.get_settings_for_profile(pid))
            if in_count == len(selected_ids):
                return QtCore.Qt.CheckState.Checked
            if in_count > 0:
                return QtCore.Qt.CheckState.PartiallyChecked
        return QtCore.Qt.CheckState.Unchecked

    def _build_tooltip(self, pkey: str) -> str:
        """Build tooltip explaining current state and what clicking will do."""
        selected_ids = self._selected_profile_ids()
        state = self._compute_check_state(pkey, selected_ids)
        if state == QtCore.Qt.CheckState.Checked:
            tooltip = _("This option is in the selected profile(s).\nClick to remove it from them.")
        elif state == QtCore.Qt.CheckState.PartiallyChecked:
            # Find which profile(s) have it
            profiles_with = []
            for profile in self._enabled_profiles:
                if pkey in self.profile_page.profile_settings.get(profile['id'], {}):
                    profiles_with.append(profile['title'])
            tooltip = _("This option is in: %s\nClick to add it to the selected profile(s).") % ", ".join(profiles_with)
        else:
            tooltip = _("This option is not in any profile.\nClick to add it to the selected profile(s).")
        return tooltip

    def _on_item_changed(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        if self._building_tree:
            return
        # Only react to actual check state changes
        pkey = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        new_state = item.checkState(0)
        if self._check_states.get(pkey) == new_state:
            return
        selected_ids = self._selected_profile_ids()
        if not selected_ids:
            return
        # User clicked: partial or unchecked → add to selected profiles
        # checked → remove from selected profiles
        if new_state != QtCore.Qt.CheckState.Unchecked:
            # Any click from partial/unchecked means "add"
            for pid in selected_ids:
                settings = self.profile_page.get_settings_for_profile(pid)
                if pkey not in settings:
                    settings[pkey] = None
        else:
            # Unchecked means "remove from selected profiles"
            for pid in selected_ids:
                settings = self.profile_page.get_settings_for_profile(pid)
                settings.pop(pkey, None)
        # Recompute correct state (may become partial if other profiles have it)
        correct_state = self._compute_check_state(pkey, selected_ids)
        self._check_states[pkey] = correct_state
        if item.checkState(0) != correct_state:
            self.ui.settings_tree.blockSignals(True)
            item.setCheckState(0, correct_state)
            self.ui.settings_tree.blockSignals(False)
        item.setToolTip(0, self._build_tooltip(pkey))
        self._update_profile_markers(pkey)
        self.profile_page.update_config_overrides()
        self.profile_page.profile_selected(update_settings=True)
        self.profile_page.reload_all_page_settings()

    def _on_item_hovered(self, item: QtWidgets.QTreeWidgetItem, column: int) -> None:
        """Show filled circle on profile list items that contain the hovered option."""
        if self._highlighted_item is item:
            return
        # Highlight the option row
        self._clear_option_highlight()
        bg = QtGui.QColor(_interface_colors.get_color('profile_hl_bg'))
        bg.setAlpha(80)
        item.setBackground(0, QtGui.QBrush(bg))
        self._highlighted_item = item
        # Update markers
        pkey = item.data(0, QtCore.Qt.ItemDataRole.UserRole)
        self._update_profile_markers(pkey)

    def _update_profile_markers(self, pkey: str) -> None:
        for i in range(self.ui.profile_list.topLevelItemCount()):
            list_item = self.ui.profile_list.topLevelItem(i)
            pid = list_item.data(0, QtCore.Qt.ItemDataRole.UserRole)
            psettings = self.profile_page.profile_settings.get(pid, {})
            marker = self.MARKER_ACTIVE if pkey in psettings else self.MARKER_INACTIVE
            if list_item.text(0) != marker:
                list_item.setText(0, marker)

    def _clear_profile_highlights(self) -> None:
        for i in range(self.ui.profile_list.topLevelItemCount()):
            list_item = self.ui.profile_list.topLevelItem(i)
            if list_item.text(0) != self.MARKER_INACTIVE:
                list_item.setText(0, self.MARKER_INACTIVE)
        self._clear_option_highlight()

    def _clear_option_highlight(self) -> None:
        if self._highlighted_item:
            self._highlighted_item.setBackground(0, QtGui.QBrush())
            self._highlighted_item = None

    def leaveEvent(self, event):
        self._clear_profile_highlights()
        super().leaveEvent(event)

    def close_window(self) -> None:
        self.close()
