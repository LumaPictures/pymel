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

Appendices:

.. toctree::
	:maxdepth: 1

	eclipse
	dev
	design
	mel_to_python
	modules
