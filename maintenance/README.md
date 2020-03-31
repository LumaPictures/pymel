
Building an Official PyMEL Release
==================================

## 1) Install Dependencies


  - git
  - graphviz: using an OS package manager like `yum`, `apt-get`, or `brew`, or
    on windows, from an [installer](https://graphviz.gitlab.io/_pages/Download/Download_windows.html)
  - python dependencies:

    ```
    curl -O https://bootstrap.pypa.io/get-pip.py
    # if you have a globally accessible verison of pip it could conflict with the command below
    pip install -U pip
    # the extra args are to get around an insecure SSL in python < 2.7.9 - see:
    # https://urllib3.readthedocs.org/en/latest/security.<html id="insecureplatformwarning"></html>
    sudo chmod -R ugo+w $MAYA_LOCATION/
    $MAYA_LOCATION/bin/mayapy get-pip.py --index-url=http://pypi.python.org/simple/ --trusted-host pypi.python.org
    $MAYA_LOCATION/bin/mayapy -m pip install -r maintenance/requirements.txt --index-url=http://pypi.python.org/simple/ --trusted-host pypi.python.org
    ```

## 2) Build caches

### Before building the caches

  - build caches from WINDOWS... reason being that we need to gather some
    information about plugin nodes, and windows has the "most complete" set of
    plugins (the only plugins that I know of that are in linux/osx but not in
    windows are IGES and stlImport... both of which are file translators only,
    with no nodes)

  - make sure environment is clean and that you have the default set of user
    prefs.

  - delete existing cache for version you wish to rebuild

  - ensure that the CommandsPython, API, and Nodes doc subdirectories are
    installed. these go in `docs/Maya20XX/en_US/`

### To build the caches

#### Build the api cache

  - start maya

  - in the script editor, run the following, substituting location of your dev
    version of pymel:

    ```python
    import sys
    import os
    pymelPath = r'C:\Projects\Dev\pymel'   # ...or wherever YOUR pymel version is installed
    pymelInit = os.path.join(pymelPath, 'pymel', '__init__.py')
    if not os.path.isfile(pymelInit):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import pymel
    if not pymel.__file__.startswith(pymelInit):  # don't check equality, it may be a .pyc
        for mod in list(sys.modules):
            if mod.split('.')[0] == 'pymel':
                del sys.modules[mod]
    import pymel
    assert pymel.__file__.startswith(pymelInit)
    print(pymel.__file__)
    import pymel.internal.factories
    ```
  - importing pymel.internal.factories will automatically build the api cache,
    but not the command caches - which is good, because we need to make sure
    some plugins are NOT loaded before building the cmd caches (they can crash
    when unloaded, or are unable to be unloaded - unfortunately, we want these
    plugins loaded when building the API cache, but not when building the cmd
    caches.)

#### Build the cmd cache

  - In an open GUI maya, go the menu item "Window > Settings/Preferences>Plugin-in Manager"
  - Find the following plugins, and make sure they all have "Auto load"
    *UN*-checked:

    - bifrostGraph.mll (not strictly necessary, but maya will load much faster)
    - lookdevKit.mll
    - modelingToolkit.mll
    - mtoa.mll
    - renderSetup.mll
    - Type.mll
    - VectorRender.mll (will cause crash later when querying cmds.allNodeTypes)

  - Quit out of maya (which will save the plugin auto-load prefs)
  - set the environment variable `MAYA_NO_INITIAL_AUTOLOAD_MT=true` to prevent
    the modeling toolkit from being force loaded
  - start maya
  - in the script editor, run the following, substituting location of your dev
    version of pymel:

    ```python
    import sys
    import os
    pymelPath = r'C:\Projects\Dev\pymel'   # ...or wherever YOUR pymel version is installed
    pymelInit = os.path.join(pymelPath, 'pymel', '__init__.py')
    if not os.path.isfile(pymelInit):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import pymel
    if not pymel.__file__.startswith(pymelInit):  # don't check equality, it may be a .pyc
        for mod in list(sys.modules):
            if mod.split('.')[0] == 'pymel':
                del sys.modules[mod]
    import pymel
    assert pymel.__file__.startswith(pymelInit)
    print(pymel.__file__)

    # for some reason, renderSetup.mll is always force-loaded; further, if
    # unloaded automatically by pymel, it seems to trigger a crash - but if
    # explicitly unloaded first, it seems to be ok
    import maya.cmds as cmds
    cmds.unloadPlugin('renderSetup')

    import pymel.internal.factories

    # force loading + building of cmd caches
    pymel.internal.factories.loadCmdCache()
    ```

## 3) Generate core modules from templates


### To generate the modules

  - build from WINDOWS - important because there is a windows-only bug we need to test for
  
  - start gui maya

  - in the script editor, run the following, substituting location of your dev
    version of pymel:

    ```python
    import sys
    import os
    pymelPath = r'E:\Projects\Dev\_work\pymel'   # ...or wherever YOUR pymel version is installed
    pymelInit = os.path.join(pymelPath, 'pymel', '__init__.py')
    if not os.path.isfile(pymelInit):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import pymel
    if not pymel.__file__.startswith(pymelInit):  # don't check equality, it may be a .pyc
        for mod in list(sys.modules):
            if mod.split('.')[0] == 'pymel':
                del sys.modules[mod]
    import pymel
    assert pymel.__file__.startswith(pymelInit)
    import maintenance.build
    assert maintenance.build.__file__.startswith(pymelPath)
    maintenance.build.generateAll()
    ```


## 4) Run Tests

  - cd into tests directory, then
    
    - on WINDOWS run:

      ```
      pymel_test_output.bat --warnings-as-errors
      ```
       
      (note that since windows doesn't have tee, you'll see no output...
      look at the contents of pymelTestOut.txt in a text editor, and
    hit refresh to see changes!)

    - OR, if on linux/mac:

      ```
      export PATH=$PATH:$MAYA_LOCATION/bin
      ./pymel_test_output.bash --warnings-as-errors 2>&1 | tee pymelTestOut.txt
      ```
  - note that the "--warnings-as-errors" option (or it's short-form, "-W") is
    recommended for the first try, as it can alert you to pending deprecations
    or other problems you might otherwise miss - but if it's
    causing too many problems, you may omit it
  - then run the tests in a gui session of maya...
  
    - on windows:

      ```
      pymel_test_output.bat -W --gui
      ```
      
      again, look at the contents of pymelTestOut.txt in a text editor

    - OR, if on linux/mac:

      ```
      export PATH=$PATH:$MAYA_LOCATION/bin
      ./pymel_test_output.bash -W --gui  2>&1 | tee pymelTestOut.txt
      ```


## 5) Resolve Issues

### Version Constants

Should be indicated by an error in the tests.

run `cmds.about(api=True)` and assign the value to to `pymel.versions.v20XX`

### New MPx Classes

Indicated by this error:

    pymel : WARNING : found new MPx classes: MPxBlendShape. Run pymel.api.plugins._suggestNewMPxValues()

  - In `pymel.api.plugins` add a new `DependNode` sublcass for each missing type:

  ```python
  # new in 2016
  if hasattr(mpx, 'MPxBlendShape'):
      class BlendShape(DependNode, mpx.MPxBlendShape): pass
  ```

  The `DependNode` classes are required for the next step to work (which I
  would like to fix this eventually.)

  - Run `_suggestNewMPxValues()` which will print out dictionary names and new
    values to add to them.  You should verify these (Need input from Paul on how
    this should be done)


## 6) Build Stubs

  - from a clean/default environment maya gui, run:

    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    os.environ['PYMEL_DOCSTRINGS_MODE'] = 'stubs'
    import maintenance.pymelstubs
    reload(maintenance.pymelstubs)
    maintenance.pymelstubs.pymelstubs()
    ```

  - test the new stubs: from shell in the pymel base directory, do:

    ```
    python -m maintenance.stubs -o ./extras/completion --test
    ```

    be sure to run the test using the same major version of python as maya
    (2.6, 2.7, 3.7!? etc), so that any references to functions and classes in the
    standard library are found.


## 7) Update the Changelog

  - run changelog script:

        ./maintenance/changelog $PREVIOUS_PYMEL_VERSION $CURRENT_REVISION

  - the args are git tags or commit hashes. for example:

        ./maintenance/changelog 1.0.4 HEAD

  - copy results from resulting `maintenance/CHANGELOG.temp` file to `CHANGELOG.rst`
  - edit as necessary


## 8) Build Docs

### 8a) Build the processed examples

  - if you need to rebuild all the examples, delete `pymel/cache/mayaCmdsExamples.zip`.
  
  - We then want to create a new/default MAYA_APP_DIR, then lock it so it's
    perms can't be changed. To do this, first:
    
    - In windows:
    
      ```
      cd %USERPROFILE%\Documents
      mkdir maya_fixCodeExamples
      set MAYA_APP_DIR=%USERPROFILE%\Documents\maya_fixCodeExamples
      maya
      ```
    - In Linux/MacOS:
      ```bash
      cd ~
      mkdir maya_fixCodeExamples
      export MAYA_APP_DIR=~\maya_fixCodeExamples
      maya
      ```
      
  - When maya launches, and the "What's new" window pops up, uncheck the
    option to "Show this at startup" 
  - Once in maya, open a script editor, and paste the following, but DO NOT
    EXECUTE it yet (we are simply saving it to our script editor prefs) - also,
    be sure to edit the pymel path to your dev install of pymel:
    
    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    os.environ['PYMEL_DOCSTRINGS_MODE'] = 'html'
    import pymel
    assert pymel.__file__.startswith(pymelPath)
    import pymel.internal.cmdcache as cmdcache
    cmdcache.fixCodeExamples()
    ```
  - Change any other settings you might want saved, before we lock them
    - ie, I recommend in the script editor menus, turning on "History" >
    "Show stack trace" in case something goes wrong
  - Quit maya (which should cause it to save it's prefs)
  - Lock the perms of the prefs folder - running the examples can change a lot
    of stuff, and we want to make sure none of it is saved:
    - In windows:
      ```
      REM lock perms so it can't be written to - if you just deny "write",
      REM user can still delete, which some of the pref saving routines do!
      REM (ie, when saving scriptEditorTemp, it first deletes all entries,
      REM then tries to write!)
      icacls maya_fixCodeExamples /deny %USERNAME%:(OI)(CI)(DE,DC,WD,AD,WA,WEA)
      ```
      - if you want to restore write perms later, run this:
        ```
        icacls maya_fixCodeExamples /remove:d %USERNAME%
        ```
        
    - in Linux/MacOS:
      ```bash
      chmod -R u-w maya_fixCodeExamples
      ```
      - if you want to restore write perms later, run this:
        ```
        chmod -R u+w maya_fixCodeExamples
        ```

  - Be warned that the next step will cause your computer to freak out and
    possibly crash as it runs all of the examples from the Autodesk docs.
    Simply restart Maya and repeat until you get all the way through.

  - To process new autodesk doc examples and add them to the examples cache,
    relaunch maya and run the python script command you pasted in earlier.


### 8b) Build the docs

  - copy the list of internal commands provided by autodesk to `docs/internalCmds.txt`,
    or `docs/internalCommandList.txt`

  - turn off autoload for all plugins, so that pymel is not imported at startup
    (I haven't identified which plugins use pymel, but it includes mtoa and at
    least one other)

  - finally, to build the docs, from a clean/default environment maya gui
    *without pymel imported*, run:

    ```python
    import sys, os
    pymelPath = r'/Volumes/sv-dev01/devRepo/chad/pymel'   # ...or wherever YOUR pymel version is installed
    if not os.path.isfile(os.path.join(pymelPath, 'pymel', '__init__.py')):
        raise RuntimeError('invalid pymel path: %s' % pymelPath)
    if sys.path[0] != pymelPath:
        sys.path.insert(0, pymelPath)
    import maintenance.docs as docs
    assert docs.__file__.startswith(pymelPath)
    docs.build(graphviz_dot=None)  #specify the location of dot executable if not on the PATH
    ```

    The `generate()` function uses the sphinx autosummary extension to generate
    stub `.rst` source files for each module listed in `index.rst`. The stub
    files contain `autosummary`, `autofunction`, and `autoclass` directives
    that tell sphinx to inspect the specified objects.  These stub files are
    then read by sphinx when it is invoked the second time, by `build()`, at
    which point the `auto*` directives cause it to flesh out the documentation
    by inspecting live python objects, which it then writes out as html pages,
    one per `.rst`.

### Checking for Errors

While building the docs sphinx will spit out a wall of errors between reading
sources and writing html.

TODO: write something to capture sphinx errors and filter known acceptable
errors.

Known Acceptable errors:

  - "ERROR: Unexpected indentation." : this is due to the trailing `..` used to
    create visual whitespace in the mel command tables.  This might be better
    done using css...

### Rebuilding the Docs

A few notes on rebuilding:

  - You only need to run `generate` a second time if the pymel source changes.
  - If you edit static docstrings you need to restart Maya (or reload the
    module) before rebuilding


## 9) Make Release

  - before releasing, make sure to tag the release (TODO: make this part of
    makerelease?):

        git tag -a 1.0.5rc1 -m "pymel release 1.0.5rc1"
        
  - then run the release script:

        python maintenance/makerelease.py 1.0.5rc1

  - then make sure you push the tag!
  
        git push origin --tags
