#!/usr/bin/env python

# Copyright (c) 2009 Anthony Towns

# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# SOFTWARE IN THE PUBLIC INTEREST, INC. BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

class Type(object):
    def validate(self, val):
	return False

class Id(Type):
    default = None
    def validate(self, val):
	return True

class String(Type):
    default = ""
    def validate(self, val):
	return type(val) == str

class Integer(Type):
    default = 0
    def validate(self, val):
	return type(val) == int or type(val) == long

class Array(Type):
    default = []
    def __init__(self, value_type = String()):
	self.value_type = value_type
    def validate(self, val):
        return all( self.value_type.validate(i) for i in val )

class Dict(Type):
    default = {}
    def __init__(self, key_type = String(), value_type = String()):
	self.key_type = key_type
	self.value_type = value_type
    def validate(self, val):
        return all( self.key_type.validate(k)
			and self.value_type.validate(v)
				for k,v in val.iteritems() )

class Document(object):
    _id = Id()

    def __init__(self):
        self._key = None
        self._db = None
        for name, kind in self.defined_values():
	    setattr(self, name, kind.default)

    def defined_values(self):
        for name in dir(self.__class__):
	    if name[0] == "_": continue
	    v = getattr(self.__class__, name)
	    if not isinstance(v, Type): continue
	    yield name, v
	return

    def validate(self):
	return all(kind.validate(getattr(self, name))
			for name, kind in self.defined_values())
       
    def update(self):
        assert self._db is not None
        self._db.update(self)

    def __getattr__(self, name):
        if hasattr(self.__class__, name):
            v = getattr(self.__class__, name)
            if isinstance(v, Derived):
                value = v.derive(self)
                setattr(self, name, value)
            	return value
        return object.__getattr__(self, name)
 
    def __setattr__(self, name, value):
	if hasattr(self.__class__, name):
	    v = getattr(self.__class__, name)
	    if isinstance(v, Type) and not v.validate(value):
		raise TypeError("invalid type for member %s" % name)
        object.__setattr__(self, name, value)

class Relation(object):
    def __init__(self):
        for name in dir(self.__class__):
	    if name[0] == "_": continue
	    v = getattr(self.__class__, name)
	    if not isinstance(v, Type): continue
	    yield name, v
    
class Derivation(object):
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def derive(self, instance):
	instance._db.derive(instance, self.kwargs)

