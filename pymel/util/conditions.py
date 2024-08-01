from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
#------------------------------------------------------------------------------
# Condition objects - used for chaining together tests that yield True/False results
#------------------------------------------------------------------------------

from builtins import object

if False:
    from typing import *


class NO_DATA(Exception):
    pass


class Condition(object):

    """
    Used to chain together objects for conditional testing.
    """

    def __init__(self, value=None):
        # type: (Optional[Any]) -> None
        self.value = value

    def eval(self, data=NO_DATA):
        # type: (Any) -> bool
        return bool(self.value)

    def __or__(self, other):
        # type: (Condition) -> Or
        return Or(self, other)

    def __ror__(self, other):
        # type: (Condition) -> Or
        return Or(other, self)

    def __and__(self, other):
        # type: (Condition) -> And
        return And(self, other)

    def __rand__(self, other):
        # type: (Condition) -> And
        return And(other, self)

    def __invert__(self):
        # type: (Condition) -> Inverse
        return Inverse(self)

    def __bool__(self):
        # type: () -> bool
        return self.eval()

    def __str__(self):
        # type: () -> str
        return str(self.value)

Always = Condition(True)

Never = Condition(False)


class Inverse(Condition):

    def __init__(self, toInvert):
        # type: (Condition) -> None
        self.toInvert = toInvert

    def eval(self, data=NO_DATA):
        # type: (Any) -> bool
        return not self.toInvert.eval(data)

    def __str__(self):
        # type: () -> str
        return "not %s" % self.toInvert


class AndOrAbstract(Condition):
    _breakEarly = None  # type: bool
    _strJoiner = None  # type: str

    def __init__(self, *args):
        # type: (*Condition) -> None
        self.args = []
        for arg in args:
            if isinstance(arg, self.__class__):
                self.args.extend(arg.args)
            else:
                self.args.append(arg)

    def eval(self, data=NO_DATA):
        # type: (Any) -> bool
        for arg in self.args:
            if isinstance(arg, Condition):
                val = arg.eval(data)
            else:
                val = bool(arg)
            if val == self._breakEarly:
                return self._breakEarly
        return not self._breakEarly

    def __str__(self):
        # type: () -> str
        return "(%s)" % self._strJoiner.join([str(x) for x in self.args])


class And(AndOrAbstract):
    _breakEarly = False
    _strJoiner = ' and '


class Or(AndOrAbstract):
    _breakEarly = True
    _strJoiner = ' or '
