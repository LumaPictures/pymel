from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
#------------------------------------------------------------------------------
# Condition objects - used for chaining together tests that yield True/False results
#------------------------------------------------------------------------------


from builtins import object
class NO_DATA(Exception):
    pass


class Condition(object):

    """
    Used to chain together objects for conditional testing.
    """

    def __init__(self, value=None):
        self.value = value

    def eval(self, data=NO_DATA):
        return bool(self.value)

    def __or__(self, other):
        return Or(self, other)

    def __ror__(self, other):
        return Or(other, self)

    def __and__(self, other):
        return And(self, other)

    def __rand__(self, other):
        return And(other, self)

    def __invert__(self):
        return Inverse(self)

    def __bool__(self):
        return self.eval()

    def __str__(self):
        return str(self.value)

Always = Condition(True)

Never = Condition(False)


class Inverse(Condition):

    def __init__(self, toInvert):
        self.toInvert = toInvert

    def eval(self, data=NO_DATA):
        return not self.toInvert.eval(data)

    def __str__(self):
        return "not %s" % self.toInvert


class AndOrAbstract(Condition):

    def __init__(self, *args):
        self.args = []
        for arg in args:
            if isinstance(arg, self.__class__):
                self.args.extend(arg.args)
            else:
                self.args.append(arg)

    def eval(self, data=NO_DATA):
        for arg in self.args:
            if isinstance(arg, Condition):
                val = arg.eval(data)
            else:
                val = bool(arg)
            if val == self._breakEarly:
                return self._breakEarly
        return not self._breakEarly

    def __str__(self):
        return "(%s)" % self._strJoiner.join([str(x) for x in self.args])


class And(AndOrAbstract):
    _breakEarly = False
    _strJoiner = ' and '


class Or(AndOrAbstract):
    _breakEarly = True
    _strJoiner = ' or '
