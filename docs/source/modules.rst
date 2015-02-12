=======================================
Module Documentation
=======================================

---------------------------------------
  ``pymel.core``
---------------------------------------

The primary sub-package.

The following submodules are brought directly into the `pymel.core` namespace.  They contain all of the wrapped ``maya.cmds`` functions.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.core.animation
  pymel.core.effects
  pymel.core.general
  pymel.core.language
  pymel.core.modeling
  pymel.core.other
  pymel.core.rendering
  pymel.core.system
  pymel.core.windows
  pymel.core.context


---------------------------------------
  ``pymel.core.datatypes``
---------------------------------------

Data classes that are returned by functions within `pymel.core`.  Automatially imported into ``pymel.core`` as ``pymel.core.dt``.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.core.datatypes

---------------------------------------
  ``pymel.core.nodetypes``
---------------------------------------

Classes corresponding to each node type in Maya. Returned by functions within `pymel.core`.  Automatially imported into ``pymel.core`` as ``pymel.core.nt``.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.core.nodetypes

---------------------------------------
  ``pymel.core.uitypes``
---------------------------------------

Classes corresponding to each UI type in Maya. Returned by functions within `pymel.core`.  Automatially imported into ``pymel.core`` as ``pymel.core.ui``.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.core.uitypes
  
---------------------------------------
  ``pymel.core.runtime``
---------------------------------------

Runtime commands are kept in their own namespace to avoid conflicts with other functions and classes.

---------------------------------------
  ``pymel.util``
---------------------------------------

Utilities that are independent of Maya.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.util.arguments
  pymel.util.arrays
  pymel.util.common
  pymel.util.decoration
  pymel.util.enum
  pymel.util.mathutils
  pymel.util.namedtuple
  pymel.util.path
  pymel.util.utilitytypes

---------------------------------------
  ``pymel.versions``
---------------------------------------

Functions for getting and comparing versions of Maya. Can be safely imported without initializing ``maya.cmds``.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.versions

---------------------------------------
  ``pymel.mayautils``
---------------------------------------

Utilities for getting Maya resource directories, sourcing scripts, and executing deferred. Can be safely imported without initializing ``maya.cmds``.

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.mayautils

---------------------------------------
  ``pymel.tools``
---------------------------------------

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.tools.envparse
  pymel.tools.mel2py
  pymel.tools.py2mel
  pymel.tools.loggingControl


---------------------------------------
  ``pymel.api``
---------------------------------------

.. autosummary::
  :nosignatures:
  :toctree: generated/
  
  pymel.api.plugins
