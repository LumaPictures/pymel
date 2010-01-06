.. PyMEL documentation master file, created by sphinx-quickstart on Thu Jan 29 22:10:49 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

===================================
PyMEL for Maya
===================================

PyMEL makes python scripting in Maya work the way it should. Maya's command module is a direct
translation of MEL commands into python functions. The result is a very awkward and unpythonic syntax which
does not take advantage of python's strengths -- particularly, a flexible, object-oriented design. PyMEL
builds on the cmds module by organizing many of its commands into a class hierarchy, and by
customizing them to operate in a more succinct and intuitive way.


Chapters:

.. toctree::
	:maxdepth: 1

	whats_new
	install
	why_pymel
	tutorial
	pynodes
	attributes
	non_existent_objs
	ui
	standalone
	advanced

Appendices:

.. toctree::
	:maxdepth: 1

	eclipse
	dev
	mel_to_python
	

.. autosummary::
	:nosignatures:
	:toctree: generated/
	
	pymel.versions
	pymel.mayautils
	pymel.internal
	pymel.core.animation
	pymel.core.effects
	pymel.core.general
	pymel.core.language
	pymel.core.modeling
	pymel.core.other
	pymel.core.rendering
	pymel.core.runtime
	pymel.core.system
	pymel.core.windows
	pymel.core.context
	pymel.core.datatypes
	pymel.core.nodetypes
	pymel.core.uitypes
	pymel.util
	pymel.util.arguments
	pymel.util.arrays
	pymel.util.common
	pymel.util.decoration
	pymel.util.enum
	pymel.util.mathutils
	pymel.util.namedtuple
	pymel.util.path
	pymel.util.trees
	pymel.util.utilitytypes


=======================================
    Special Thanks
=======================================

Special thanks to those studios with the foresight to support an open-source project of this nature:  Luma Pictures, 
Attitude Studio, and ImageMovers Digital.


