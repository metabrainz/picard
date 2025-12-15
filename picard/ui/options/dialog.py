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


from PyQt6 import (
    QtCore,
    QtGui,
    QtWidgets,
)

from picard import log
from picard.config import (
    Option,
    OptionError,
    SettingConfigSection,
    get_config,
)
from picard.const import PICARD_URLS
from picard.extension_points.options_pages import ext_point_options_pages
from picard.i18n import (
    N_,
    gettext as _,
)
from picard.profile import (
    profile_groups_group_from_page,
    profile_groups_order,
)
from picard.util import restore_method

from picard.ui import (
    HashableTreeWidgetItem,
    PicardDialog,
    SingletonDialog,
)
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
    plugins,
    plugins3,
    profiles,
    ratings,
    releases,
    renaming,
    renaming_compat,
    scripting,
    sessions,
    tags,
    tags_compatibility_aac,
    tags_compatibility_ac3,
    tags_compatibility_id3,
    tags_compatibility_wave,
)


class ErrorOptionsPage(OptionsPage):
    def __init__(self, parent=None, errmsg='', from_cls: OptionsPage = None, dialog=None):
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

        title_widget = QtWidgets.QLabel(_("Error while initializing option page '%s':") % _(from_cls.TITLE))

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
            % PICARD_URLS['troubleshooting']
        )
        report_bug_widget.setOpenExternalLinks(True)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(title_widget)
        layout.addWidget(error_widget)
        layout.addWidget(report_bug_widget)
        layout.addStretch()
        self.ui = layout

        self.dialog = dialog


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
                    if plugin_uuid and hasattr(self, 'plugin_manager') and self.plugin_manager:
                        # Only show page if plugin is enabled
                        is_enabled = plugin_uuid in self.plugin_manager._enabled_plugins
                        page_active = is_enabled
                    else:
                        # If we can't check plugin status, assume it's active if it has an API
                        page_active = True
                except AttributeError:
                    # Plugin manager not available, assume active
                    page_active = True

            # Skip disabled plugin pages entirely
            if api is not None and not page_active:
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
        self.setWindowModality(QtCore.Qt.WindowModality.ApplicationModal)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)

        from picard.ui.forms.ui_options import Ui_OptionsDialog

        self.ui = Ui_OptionsDialog()
        self.ui.setupUi(self)

        self.ui.profile_warning_icon.setPixmap(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxWarning).pixmap(20, 20)
        )
        self.ui.profile_help_button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.StandardPixmap.SP_MessageBoxQuestion)
        )
        self.ui.profile_help_button.setToolTip(_("Display help regarding option profiles"))
        self.ui.profile_help_button.clicked.connect(self._show_profile_help)

        self.ui.reset_all_button = QtWidgets.QPushButton(_("&Restore all Defaults"))
        self.ui.reset_all_button.setToolTip(_("Reset all of Picard's settings"))
        self.ui.reset_button = QtWidgets.QPushButton(_("Restore &Defaults"))
        self.ui.reset_button.setToolTip(_("Reset all settings for current option page"))

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
        self.first_enter = True
        self.installEventFilter(self)

        maintenance_page = self.get_page('maintenance')
        if maintenance_page.loaded:
            maintenance_page.signal_reload.connect(self.load_all_pages)

        profile_page = self.get_page('profiles')
        if profile_page.loaded:
            profile_page.signal_refresh.connect(self.update_from_profile_changes)
            self.highlight_enabled_profile_options()

        self.ui.pages_tree.itemSelectionChanged.connect(self.switch_page)

        # Connect to plugin manager signals for dynamic updates
        tagger = QtCore.QCoreApplication.instance()
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

    def display_attached_profiles(self, option_group):
        profile_page = self.get_page('profiles')
        override_profiles = profile_page._clean_and_get_all_profiles()
        override_settings = profile_page.profile_settings
        profile_dialog = AttachedProfilesDialog(
            option_group,
            parent=self,
            override_profiles=override_profiles,
            override_settings=override_settings,
        )
        profile_dialog.show()
        profile_dialog.raise_()
        profile_dialog.activateWindow()

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
        from picard.ui.colors import interface_colors as colors

        fg_color = colors.get_color('profile_hl_fg')
        bg_color = colors.get_color('profile_hl_bg')

        for page in self.loaded_pages:
            option_group = profile_groups_group_from_page(page)
            if option_group:
                if load_settings:
                    page.load()
                for opt in option_group['settings']:
                    for objname in opt.highlights:
                        try:
                            obj = getattr(page.ui, objname)
                        except AttributeError:
                            continue
                        style = "#%s { color: %s; background-color: %s; }" % (objname, fg_color, bg_color)
                        self._check_and_highlight_option(obj, opt.name, working_profiles, working_settings, style)

    def _check_and_highlight_option(self, obj, option_name, working_profiles, working_settings, style):
        obj.setStyleSheet(None)
        obj.setToolTip(None)
        for item in working_profiles:
            if item['enabled']:
                profile_id = item['id']
                profile_title = item['title']
                if profile_id in working_settings:
                    profile_settings = working_settings[profile_id]
                else:
                    profile_settings = {}
                if option_name in profile_settings:
                    tooltip = _("This option will be saved to profile: %s") % profile_title
                    try:
                        obj.setStyleSheet(style)
                        obj.setToolTip(tooltip)
                    except AttributeError:
                        pass
                    break

    def eventFilter(self, object, event):
        """Process selected events."""
        evtype = event.type()
        if evtype == QtCore.QEvent.Type.Enter:
            if self.first_enter:
                self.first_enter = False
                if self.tagger and self.tagger.window.script_editor_dialog is not None:
                    self.get_page('filerenaming').show_script_editing_page()
                    self.activateWindow()
        return False

    def get_page(self, pagename):
        return self.item_to_page[self.pagename_to_item[pagename]]

    def page_has_attached_profiles(self, page, enabled_profiles_only=False):
        if not page.loaded:
            return False
        profile_page = self.get_page('profiles')
        if not profile_page.loaded:
            return False
        option_group = profile_groups_group_from_page(page)
        if not option_group:
            return False
        working_profiles, working_settings = self.get_working_profile_data()
        for opt in option_group['settings']:
            for item in working_profiles:
                if enabled_profiles_only and not item['enabled']:
                    continue
                profile_id = item['id']
                if opt.name in working_settings[profile_id]:
                    return True
        return False

    def set_profiles_button_and_highlight(self, page):
        if self.page_has_attached_profiles(page):
            self.ui.attached_profiles_button.setDisabled(False)
        else:
            self.ui.attached_profiles_button.setDisabled(True)
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
                    if opt.name in profile_settings:
                        profile_set.add((idx, item['title']))
                        break

        if not profile_set:
            self.ui.profile_warning.setVisible(False)
            return

        if len(profile_set) == 1:
            text = _('profile "%s"') % profile_set.pop()[1]
        else:
            text = _('profiles %s') % ', '.join([f'"{p[1]}"' for p in sorted(profile_set)])
        self.ui.profile_warning_text.setText(_('The highlighted settings will be applied to %s') % text)
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
        default_page = current_page or config.persist['options_last_active_page']
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
            url = 'doc_options'  # key in PICARD_URLS
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
        pages = [
            self.get_page('profiles'),
        ]
        pages.extend(x for x in sorted(self.loaded_pages, key=lambda p: (p.SORT_ORDER, p.NAME)) if x.NAME != 'profiles')
        for page in pages:
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


class AttachedProfilesDialog(PicardDialog):
    NAME = 'attachedprofiles'
    TITLE = N_("Attached Profiles")

    def __init__(self, option_group, parent=None, override_profiles=None, override_settings=None):
        super().__init__(parent=parent)
        self.option_group = option_group
        self.ui = Ui_AttachedProfilesDialog()
        self.ui.setupUi(self)
        self.ui.buttonBox.addButton(QtWidgets.QDialogButtonBox.StandardButton.Close)
        self.ui.buttonBox.rejected.connect(self.close_window)

        config = get_config()
        if override_profiles is None or override_settings is None:
            self.profiles = config.profiles[SettingConfigSection.PROFILES_KEY]
            self.settings = config.profiles[SettingConfigSection.SETTINGS_KEY]
        else:
            self.profiles = override_profiles
            self.settings = override_settings

        self.populate_table()

        self.ui.buttonBox.setFocus()
        self.setModal(True)

    def populate_table(self):
        model = QtGui.QStandardItemModel()
        model.setColumnCount(2)
        header_names = (_("Option"), _("Attached Profiles"))
        model.setHorizontalHeaderLabels(header_names)

        window_title = _("Profiles Attached to Options in %s Section") % self.option_group['title']
        self.setWindowTitle(window_title)

        for setting in self.option_group['settings']:
            try:
                title = Option.get_title('setting', setting.name)
            except OptionError as e:
                log.debug(e)
                continue
            option_item = QtGui.QStandardItem(_(title))
            option_item.setEditable(False)
            attached = []
            for profile in self.profiles:
                if setting.name in self.settings[profile['id']]:
                    attached.append(
                        "{0}{1}".format(
                            profile['title'],
                            _(" [Enabled]") if profile['enabled'] else "",
                        )
                    )
            attached_profiles = "\n".join(attached) or _("None")
            profile_item = QtGui.QStandardItem(attached_profiles)
            profile_item.setEditable(False)
            model.appendRow((option_item, profile_item))

        self.ui.options_list.setModel(model)
        self.ui.options_list.resizeColumnsToContents()
        self.ui.options_list.resizeRowsToContents()
        self.ui.options_list.horizontalHeader().setStretchLastSection(True)

    def close_window(self):
        """Close the script metadata editor window."""
        self.close()
