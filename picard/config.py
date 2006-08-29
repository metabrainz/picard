# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
# Copyright (C) 2004 Robert Kaye
# Copyright (C) 2006 Lukáš Lalinský
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

from PyQt4 import QtCore

defaultConfig = {
    u"persist/viewCoverArt": True,
    u"persist/viewFileBrowser": False,
    u"persist/windowGeometry": QtCore.QRect(10, 10, 780, 680),
    u"persist/windowMaximized": False,
}

class ConfigError(Exception):
    pass

class ConfigGroup(object):
    
    def __init__(self, config, name):
        self.config = config
        self.name = name
        
    def get(self, name, default=QtCore.QVariant()):
        key = "%s/%s" % (self.name, name)
        if self.config.contains(key):
            return self.config.value(key)
        else:
            return default
        
    def getString(self, name, default=None):
        key = "%s/%s" % (self.name, name)
        if self.config.contains(key):
            return unicode(self.config.value(key).toString())
        else:
            return default
        
    def getInt(self, name, default=None):
        key = "%s/%s" % (self.name, name)
        if self.config.contains(key):
            value, ok = self.config.value(key).toInt()
            if ok:
                return value
        return default
        
    def getBool(self, name, default=None):
        key = "%s/%s" % (self.name, name)
        if self.config.contains(key):
            return self.config.value(key).toBool()
        else:
            return default
        
    def set(self, name, value):
        key = "%s/%s" % (self.name, name)
        self.config.setValue(key, QtCore.QVariant(value))

class Config(QtCore.QSettings):
    
    organization = u"MusicBrainz"
    application = u"MusicBrainz Picard 1.0"
    
    def __init__(self):
        """Initializes the configuration."""
        QtCore.QSettings.__init__(self, self.organization, self.application)
        self.setting = ConfigGroup(self, u"setting")
        self.persist = ConfigGroup(self, u"persist")
        self.profile = ConfigGroup(self, u"profile/default")

    def switchProfile(self, profileName):
        """Sets the current profile."""
        key = u"profile/%s" % (profileName,)
        if self.contains(key):
            self.profile.name = key
        else:
            raise ConfigError, "Unknown profile '%s'" % (profileName,) 
