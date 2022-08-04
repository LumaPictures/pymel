"""
Wraps mypy.stubgen to improve signature generation with info from pymel caches.
"""
from __future__ import absolute_import, print_function

import textwrap
from typing import List, Optional, Tuple

import mypy.stubgen
import mypy.nodes
import mypy.types
import mypy.fastparse

from maintenance.buildutil import MelFunctionHelper, CORE_CMD_MODULES_MAP

BaseStubGenerator = mypy.stubgen.StubGenerator

# TODO: use flagInfo['modes'] to generate unique overload for query and edit mode
# TODO: return type.
#    if flagInfo['resultNeedsCasting'] and 'query' in modes:
#        returnType = flagInfo['args']
# TODO:


assert hasattr(BaseStubGenerator, 'get_func_args'), \
    "This version of mypy is not supported for stuben"

METACLASS_BASE_FIXES = {
    'pymel.core.nodetypes.DependNode': 'general.PyNode',
    'pymel.core.general.Attribute': 'PyNode',
    'pymel.core.general.AttributeSpec': 'PyNode',
    'pymel.core.general.Component': 'PyNode',
    'pymel.core.system.FileInfo': 'MutableMapping',
    'pymel.core.datatypes.Vector': 'VectorN',
    'pymel.core.datatypes.Matrix': 'MatrixN',
}


class PyMelStubGenerator(BaseStubGenerator):
    """
    Instantiated once for each module
    """

    def __init__(self, *args, **kwargs):
        super(PyMelStubGenerator, self).__init__(*args, **kwargs)
        self._decorator_sigs = {}

    def _import_as(self, module, as_name):
        self.import_tracker.add_import(module, as_name)
        self.import_tracker.required_names.add(as_name)

    def _import_from(self, module, names):
        self.import_tracker.add_import_from(
            module, [(x, None) for x in names])
        self.import_tracker.required_names.update(names)

    def visit_mypy_file(self, o) -> None:
        """
        Called before processing a file
        """
        super().visit_mypy_file(o)
        pyNodeName = CORE_CMD_MODULES_MAP.get(self.module)
        if pyNodeName:
            parts = pyNodeName.split('.', 1)
            if len(parts) == 2:
                self._import_as('pymel.core.general', parts[0])

        if self.module.startswith('pymel.core.'):
            # add typing imports
            self._import_from('typing', MelFunctionHelper.TYPING_TYPES)
            self._import_as('pymel.util', '_util')

    def get_base_types(self, cdef: mypy.nodes.ClassDef) -> List[str]:
        result = super(PyMelStubGenerator, self).get_base_types(cdef)
        # workaround stubgen failure to understand with_metaclass()
        if cdef.fullname in METACLASS_BASE_FIXES:
            assert result == [], result
            result.append(METACLASS_BASE_FIXES[cdef.fullname])
        return result

    def get_func_args(self, o: mypy.nodes.FuncDef, is_abstract: bool = False,
                      is_overload: bool = False) -> List[str]:
        deco_args = self._decorator_sigs.pop(o.fullname, None)
        if deco_args is not None:
            return deco_args

        module, name = o.fullname.rsplit('.', 1)
        return self._get_args(o, name, module, is_overload=is_overload)

    def _get_args(self, o: mypy.nodes.FuncDef, name: str, module=None,
                  is_overload: bool = False, skip=None) -> List[str]:
        if module:
            helper = MelFunctionHelper.get(name, module)
        else:
            helper = MelFunctionHelper(name)

        specifiedArgNames = []
        hasKwargs = False
        for arg in o.arguments:
            if arg.kind == mypy.nodes.ARG_STAR2:
                # stop when we reach **kwargs
                hasKwargs = True
                break
            specifiedArgNames.append(arg.variable.name)

        args = super(PyMelStubGenerator, self).get_func_args(o)
        if helper is None or not hasKwargs:
            return args
        else:
            if is_overload and args and args[0].startswith(('args:', 'self')):
                # in our code we start with this:
                #
                #   @overload
                #   def(args, foo=True,  **kwargs)
                #       # type: (Any, Literal[True], Any)
                #
                # then we generate something roughly like this:
                #
                #   def(args: Any, foo: Literal[True] = ..., **kwargs)
                #
                # and below we convert it to this:
                #
                #   def(*args, foo: Literal[True], **kwargs)
                #
                # notice we add the * and remove the default.
                # for overloads to work properly we want our func sigs to look
                # like the third form (with no default, so that mypy knows that
                # the overloaded arg must be provided)
                # but this is only valid in python3 and source code must remain
                # python2 compliant until several versions past 2022.
                # so we have a convention that overloads can specify their first
                # argument as `args` (without a *) and we'll add the star during
                # stub generation
                keep_default = [
                    (isinstance(arg.initializer, mypy.nodes.NameExpr) and
                     arg.initializer.name == 'Ellipsis')
                    for arg in o.arguments
                ]
                if args[0].startswith('args:'):
                    args[0] = '*' + args[0]
                args = [arg if keep else arg.replace(' = ...', '')
                        for arg, keep in zip(args, keep_default)]
            # use the annotations for the specified arguments
            otherArgs = helper.getArgs(skip=specifiedArgNames + (skip or []))
            return args[:len(specifiedArgNames)] + otherArgs

    def get_init(self, lvalue: str, rvalue: mypy.nodes.Expression,
                 annotation: Optional[mypy.types.Type] = None,
                 is_inside_func=False) -> Optional[str]:
        if lvalue == 'pathClass':
            return textwrap.dedent("""
                if LUMA:
                    import luma.filepath
                    pathClass = luma.filepath.Path
                else:
                    pathClass = _util.path
                """)
        if isinstance(rvalue, mypy.nodes.CallExpr) and rvalue.callee.name == 'getCmdFunc':
            # e.g. foo = _factories.getCmdFunc('foo')
            return self._indent + MelFunctionHelper(lvalue).getSignature()
        else:
            return super(PyMelStubGenerator, self).get_init(lvalue, rvalue, annotation,
                                                            is_inside_func=is_inside_func)

    def process_decorator(self, o: mypy.nodes.Decorator) -> Tuple[bool, bool]:
        is_abstract, is_overload = super(PyMelStubGenerator, self).process_decorator(o)
        for decorator in o.original_decorators:
            if (isinstance(decorator, mypy.nodes.CallExpr) and
                    decorator.callee.name == 'addMelDocs'):
                # FIXME: handle flag argument
                if len(decorator.args) >= 1 and isinstance(decorator.args[0], mypy.nodes.StrExpr):
                    cmdName = decorator.args[0].value
                    if len(decorator.args) == 1:
                        # e.g. @_factories.addMelDocs('listRelatives')
                        self._decorator_sigs[o.func.fullname] = self._get_args(
                            o.func, cmdName, is_overload=is_overload)
                    elif len(decorator.args) == 2 and decorator.arg_names[1] == 'excludeFlags':
                        # e.g. @_factories.addMelDocs('listRelatives', excludeFlags=['children'])
                        excludeExpr = decorator.args[1]
                        assert isinstance(excludeExpr, mypy.nodes.ListExpr)
                        exclude = [x.value for x in excludeExpr.items]
                        self._decorator_sigs[o.func.fullname] = self._get_args(
                            o.func, cmdName, is_overload=is_overload, skip=exclude)
        return is_abstract, is_overload


mypy.stubgen.StubGenerator = PyMelStubGenerator

mypy.stubgen.main()
