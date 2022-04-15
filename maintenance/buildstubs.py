from __future__ import absolute_import, print_function

from typing import Optional

import mypy.stubgen
import mypy.nodes
import mypy.types
import mypy.fastparse

from maintenance.buildutil import MelFunctionHelper

BaseStubGenerator = mypy.stubgen.StubGenerator

# TODO: use flagInfo['modes'] to generate unique overload for query and edit mode
# TODO: return type.
#    if flagInfo['resultNeedsCasting'] and 'query' in modes:
#        returnType = flagInfo['args']
# TODO:


assert hasattr(BaseStubGenerator, 'get_func_args'), \
    "This version of mypy is not supported for stuben"


class PyMelStubGenerator(BaseStubGenerator):

    def __init__(self, *args, **kwargs):
        super(PyMelStubGenerator, self).__init__(*args, **kwargs)
        # add typing imports
        self.import_tracker.add_import_from(
            'typing', [(x, None) for x in MelFunctionHelper.TYPING_TYPES])
        self.import_tracker.required_names.update(MelFunctionHelper.TYPING_TYPES)

    def get_func_args(self, o):
        module, name = o.fullname.rsplit('.', 1)
        helper = MelFunctionHelper.get(name, module)
        if helper is None:
            return super(PyMelStubGenerator, self).get_func_args(o)
        else:
            return helper.getArgs()

            # newArgs = [o.arguments[0]]
            # newObj = o.deserialize(o.serialize())

            # newObj.arguments = newArgs
            # # `unanalyzed_type` is None if if the function has no
            # # annotations.  we need to create it because this is the object
            # # that is used to find and print annotations.
            # newObj.unanalyzed_type = mypy.types.CallableType(
            #     arg_types=[arg.type_annotation for arg in newArgs],
            #     arg_names=[arg.variable.name for arg in newArgs],
            #     arg_kinds=[arg.kind for arg in newArgs],
            #     ret_type=None,  # this is not right
            #     fallback=None,  # this is not right
            # )
            # return super(PyMelStubGenerator, self).get_func_args(newObj)

    def get_init(self, lvalue: str, rvalue: mypy.nodes.Expression,
                 annotation: Optional[mypy.types.Type] = None) -> Optional[str]:
        if isinstance(rvalue, mypy.nodes.CallExpr) and rvalue.callee.name == 'getCmdFunc':
            return MelFunctionHelper(lvalue).getSignature()
        else:
            return super(PyMelStubGenerator, self).get_init(lvalue, rvalue, annotation)


mypy.stubgen.StubGenerator = PyMelStubGenerator

mypy.stubgen.main()
