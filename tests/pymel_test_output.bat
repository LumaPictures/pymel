REM This is windows, so no tee for you - if you want to see results
REM as they come, open up a text editor and keep hitting refresh!
IF "%MAYA_PYTHON_VERSION%"=="2" (
    set MAYAPY=mayapy2
) ELSE (
    set MAYAPY=mayapy
)
%MAYAPY% pymel_test.py --gui-stdout %* >pymelTestOut.txt 2>&1