set MAYA_APP_DIR=%HOMEDRIVE%%HOMEPATH%\maya_pymel_test
mkdir %MAYA_APP_DIR%
REM This is windows, so no tee for you - if you want to see results
REM as they come, open up a text editor and keep hitting refresh!
mayapy pymel_test.py --gui-stdout %* >pymelTestOut.txt 2>&1