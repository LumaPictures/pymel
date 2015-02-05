
Building an Official PyMEL Release
==================================

1) Install Dependencies
-----------------------

  - git
  - graphviz: using an OS package manager like `yum`, `apt-get`, or `brew`, or on windows, from an [installer](http://www.graphviz.org/Download_windows.php)
  - python dependencies:
    ```
    sudo $MAYA_LOCATION/bin/mayapy get-pip.py
    sudo $MAYA_LOCATION/bin/mayapy -m pip install -r requirements.txt
    ```

2) Build caches
---------------
Before building the caches:

  - build caches from WINDOWS... reason being that we need to gather some
    information about plugin nodes, and windows has the "most complete" set of
    plugins (the only plugins that I know of that are in linux/osx but not in
    windows are IGES and stlImport... both of which are file translators only,
    with no nodes)

  - make sure environment is clean and that you have the default set of user prefs.  

  - delete existing cache for version you wish to rebuild

  - ensure that the CommandsPython, API, and Nodes doc subdirectories are installed.

To build the caches:

  - open a shell and set the environment variable `MAYA_NO_INITIAL_AUTOLOAD_MT=true`

  - in the script editor, run the following, substituting location of your dev
    version of pymel:

    ```python
    import sys
    pymelPath = r'C:\Dev\Projects\eclipse\workspace\pymelProject\pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import pymel.core as pm
    ```

  - repeat. building of api cache loads plugins, then building of cmd cache
    unloads them... unfortunately, some of the built-in plugins may not
    unload cleanly, resulting in an error; therefore, it may be necessary
    to run the above steps twice (once to build api cache, once for
    cmd cache)

3) Run Tests
------------

  - cd into tests directory, then on WINDOWS run:

        ./pymel_test.py

    OR, if on linux/mac:

        export PATH=$PATH:$MAYA_LOCATION/bin
        ./pymel_test_output.bash

4) Resolve Issues
-----------------

Common issues:

  - forgot to add `pymel.versions.v20XX`



5) Build Stubs
--------------

  - from a clean/default environment maya gui, run:

    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import maintenance.stubs
    reload(maintenance.stubs)
    maintenance.stubs.pymelstubs()
    ```

  - test the new stubs: from shell in the pymel directory, do::

    ```
    python -c "import maintenance.stubs;maintenance.stubs.stubstest('./extras/completion/py')"
    ```

    be sure to run the test using the same major version of python as maya (2.6, 2.7, etc), so that any references to functions and classes in the standard library are found.

6) Update the Changelog
-----------------------

  - run changelog script:

        ./maintenance/changelog $PREVIOUS_PYMEL_VERSION $CURRENT_REVISION

  - the args are git tags or commit hashes. for example:

        ./maintenance/changelog 1.0.4 HEAD

  - copy results from resulting `maintenance/CHANGELOG.temp` file to `CHANGELOG.rst`
  - edit as necessary


7) Build Docs
-------------

    **A NOTE ABOUT SPHINX:**
    Note that sphinx-1.1.3, 1.2.1, and the latest source stable commit in the
    repo, as of 2014-01-31, all seem to have problems.  1.1.3 seemed to have
    some sort of error when interfacing with graphviz (to generate the class
    graphs), and the later versions seem to currently have a bug that causes
    it to generate way-too-verbose summaries - for instance, the entry for
    animCurveEditor in docs\build\1.0\generated\pymel.core.windows.html had
    garbage from it's flag's in it's one-line summary.
    I found the problem, and will submit a bug fix, so hopefully future
    versions will be ok...

  - if you need to rebuild all the examples, delete `pymel/cache/mayaCmdsExamples.zip`. Be warned that the next step will cause your computer to freak out and possibly crash as it runs all of the examples from the Autodesk docs. Simply restart Maya and repeat until you get all the way through.

  - process new autodesk doc examples and add them to the examples cache:
    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    os.environ['PYMEL_INCLUDE_EXAMPLES'] = 'True'
    import pymel.internal.cmdcache as cmdcache
    cmdcache.fixCodeExamples()
    ```

  - finally, to build the docs, from a clean/default environment maya gui *without pymel imported*, run:

    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import maintenance.docs as docs
    docs.generate()
    docs.build(graphviz_dot=None)  #specify the location of dot executable if not on the PATH
    ```

8) Make Release
---------------

  - before releasing, make sure to tag the release (TODO: make this part of makerelease?):

        git tag -a 1.0.5rc1 -m "pymel release 1.0.5rc1"
        
  - then run the release script:

        ./maintenance/makerelease $PYMEL_VERSION

