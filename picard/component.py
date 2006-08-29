# -*- coding: utf-8 -*-
#
# Picard, the next-generation MusicBrainz tagger
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
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -----------------------------------------------------------------------------
#
# Copyright (C) 2003-2006 Edgewall Software
# Copyright (C) 2003-2004 Jonas Borgström <jonas@edgewall.com>
# Copyright (C) 2004-2005 Christopher Lenz <cmlenz@gmx.de>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
# 3. The name of the author may not be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR `AS IS'' AND ANY EXPRESS
# OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
# GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Author: Jonas Borgström <jonas@edgewall.com>
#         Christopher Lenz <cmlenz@gmx.de>

__all__ = ['Component', 'ExtensionPoint', 'implements', 'Interface']

from PyQt4 import QtCore
import sip

import inspect, types, __builtin__

############## preliminary: two utility functions #####################

def skip_redundant(iterable, skipset=None):
    "Redundant items are repeated items or items in the original skipset."
    if skipset is None: skipset = set()
    for item in iterable:
        if item not in skipset:
            skipset.add(item)
            yield item


def remove_redundant(metaclasses):
    skipset = set([types.ClassType])
    for meta in metaclasses: # determines the metaclasses to be skipped
        skipset.update(inspect.getmro(meta)[1:])
    return tuple(skip_redundant(metaclasses, skipset))

##################################################################
## now the core of the module: two mutually recursive functions ##
##################################################################

memoized_metaclasses_map = {}

def get_noconflict_metaclass(bases, left_metas, right_metas):
     """Not intended to be used outside of this module, unless you know
     what you are doing."""
     # make tuple of needed metaclasses in specified priority order
     metas = left_metas + tuple(map(type, bases)) + right_metas
     needed_metas = remove_redundant(metas)

     # return existing confict-solving meta, if any
     if needed_metas in memoized_metaclasses_map:
       return memoized_metaclasses_map[needed_metas]
     # nope: compute, memoize and return needed conflict-solving meta
     elif not needed_metas:         # wee, a trivial case, happy us
         meta = type
     elif len(needed_metas) == 1: # another trivial case
        meta = needed_metas[0]
     # check for recursion, can happen i.e. for Zope ExtensionClasses
     elif needed_metas == bases: 
         raise TypeError("Incompatible root metatypes", needed_metas)
     else: # gotta work ...
         metaname = '_' + ''.join([m.__name__ for m in needed_metas])
         meta = classmaker()(metaname, needed_metas, {})
     memoized_metaclasses_map[needed_metas] = meta
     return meta

def classmaker(left_metas=(), right_metas=()):
    def make_class(name, bases, adict):
        metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
        return metaclass(name, bases, adict)
    return make_class

class Interface(object):
    """Marker base class for extension point interfaces."""


class ExtensionPoint(property):
    """Marker class for extension points in components."""

    def __init__(self, interface):
        """Create the extension point.
        
        @param interface: the `Interface` subclass that defines the protocol
            for the extension point
        """
        property.__init__(self, self.extensions)
        self.interface = interface
        self.__doc__ = 'List of components that implement `%s`' % \
                       self.interface.__name__

    def extensions(self, component):
        """Return a list of components that declare to implement the extension
        point interface."""
        extensions = ComponentMeta._registry.get(self.interface, [])
        return filter(None, [component.compmgr[cls] for cls in extensions])

    def __repr__(self):
        """Return a textual representation of the extension point."""
        return '<ExtensionPoint %s>' % self.interface.__name__


class ComponentMeta(type):
    """Meta class for components.
    
    Takes care of component and extension point registration.
    """
    _components = []
    _registry = {}

    def __new__(cls, name, bases, d):
        """Create the component class."""

        new_class = type.__new__(cls, name, bases, d)
        if name == 'Component':
            # Don't put the Component base class in the registry
            return new_class

        # Only override __init__ for Components not inheriting ComponentManager
        if True not in [issubclass(x, ComponentManager) for x in bases]:
            # Allow components to have a no-argument initializer so that
            # they don't need to worry about accepting the component manager
            # as argument and invoking the super-class initializer
            init = d.get('__init__')
            if not init:
                # Because we're replacing the initializer, we need to make sure
                # that any inherited initializers are also called.
                for init in [b.__init__._original for b in new_class.mro()
                             if issubclass(b, Component)
                             and '__init__' in b.__dict__]:
                    break
            def maybe_init(self, compmgr, init=init, cls=new_class):
                if cls not in compmgr.components:
                    compmgr.components[cls] = self
                    if init:
                        init(self)
            maybe_init._original = init
            new_class.__init__ = maybe_init

        if d.get('abstract'):
            # Don't put abstract component classes in the registry
            return new_class

        ComponentMeta._components.append(new_class)
        for interface in d.get('_implements', []):
            ComponentMeta._registry.setdefault(interface, []).append(new_class)
        for base in [base for base in bases if hasattr(base, '_implements')]:
            for interface in base._implements:
                ComponentMeta._registry.setdefault(interface, []).append(new_class)

        return new_class


class QComponentMeta(ComponentMeta, sip.wrappertype):
    """Wrapper metaclass to aviod metaclass conflict.
    """
    pass
        
def implements(*interfaces):
    """
    Can be used in the class definiton of `Component` subclasses to declare
    the extension points that are extended.
    """
    import sys

    frame = sys._getframe(1)
    locals = frame.f_locals

    # Some sanity checks
    assert locals is not frame.f_globals and '__module__' in frame.f_locals, \
           'implements() can only be used in a class definition'
    assert not '_implements' in locals, \
           'implements() can only be used once in a class definition'

    locals['_implements'] = interfaces


class Component(QtCore.QObject):
    """Base class for components.

    Every component can declare what extension points it provides, as well as
    what extension points of other components it extends.
    """
    __metaclass__ = QComponentMeta

    def __new__(cls, *args, **kwargs):
        """Return an existing instance of the component if it has already been
        activated, otherwise create a new instance.
        """
        # If this component is also the component manager, just invoke that
        if issubclass(cls, ComponentManager):
            self = super(Component, cls).__new__(cls)
            self.compmgr = self
            return self

        # The normal case where the component is not also the component manager
        compmgr = args[0]
        self = compmgr.components.get(cls)
        if self is None:
            self = super(Component, cls).__new__(cls)
            self.compmgr = compmgr
            compmgr.component_activated(self)
        return self
        

class ComponentManager(object):
    """The component manager keeps a pool of active components."""

    def __init__(self):
        """Initialize the component manager."""
        self.components = {}
        self.enabled = {}
        if isinstance(self, Component):
            self.components[self.__class__] = self

    def __contains__(self, cls):
        """Return wether the given class is in the list of active components."""
        return cls in self.components

    def __getitem__(self, cls):
        """Activate the component instance for the given class, or return the
        existing the instance if the component has already been activated."""
        if cls not in self.enabled:
            self.enabled[cls] = self.is_component_enabled(cls)
        if not self.enabled[cls]:
            return None
        component = self.components.get(cls)
        if not component:
            if cls not in ComponentMeta._components:
                raise TracError, 'Component "%s" not registered' % cls.__name__
            try:
                component = cls(self)
            except TypeError, e:
                raise TracError, 'Unable to instantiate component %r (%s)' \
                                 % (cls, e)
        return component

    def component_activated(self, component):
        """Can be overridden by sub-classes so that special initialization for
        components can be provided.
        """

    def is_component_enabled(self, cls):
        """Can be overridden by sub-classes to veto the activation of a
        component.

        If this method returns False, the component with the given class will
        not be available.
        """
        return True

