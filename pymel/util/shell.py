from __future__ import absolute_import
from __future__ import print_function
from __future__ import division
import os
import subprocess
from pymel.util.arguments import isIterable as _isIterable

__all__ = ['appendEnv', 'prependEnv', 'getEnv', 'getEnvs', 'putEnv',
           'refreshEnviron', 'executableOutput', 'shellOutput']


# TODO : expand environment variables when testing if it already exists in the list
def appendEnv(env, value):
    # type: (str, str) -> None
    """append the value to the environment variable list

    ( separated by ':' on osx and linux and ';' on windows). skips if it
    already exists in the list

    Parameters
    ----------
    env : str
    value : str
    """
    sep = os.path.pathsep
    if env not in os.environ:
        # print "adding", env, value
        os.environ[env] = value
    else:
        splitEnv = os.environ[env].split(sep)
        if value not in splitEnv:
            splitEnv.append(value)
            # print "adding", env, value
            os.environ[env] = sep.join(splitEnv)
    # i believe os.putenv is triggered by modifying os.environ, so this should not be necessary ?
    # if put :
    #    os.putenv(env, os.environ[env])


def prependEnv(env, value):
    # type: (str, str) -> None
    """prepend the value to the environment variable list

    (separated by ':' on osx and linux and ';' on windows). skips if it already
    exists in the list

    Parameters
    ----------
    env : str
    value : str
    """
    sep = os.path.pathsep
    if env not in os.environ:
        # print "adding", env, value
        os.environ[env] = value
    else:
        splitEnv = os.environ[env].split(sep)
        if value not in splitEnv:
            splitEnv.insert(0, value)
            # print "adding", env, value
            os.environ[env] = sep.join(splitEnv)


def getEnv(env, default=None):
    # type: (str, Any) -> None
    """get the value of an environment variable.

    returns default (None) if the variable has not been previously set.

    Parameters
    ----------
    env : str
    """
    return os.environ.get(env, default)


def getEnvs(env, default=None):
    # type: (str, Any) -> List[str]
    """
    get the value of an environment variable split into a list.

    returns default ([]) if the variable has not been previously set.

    Parameters
    ----------
    env : str

    Returns
    -------
    List[str]
    """
    try:
        return os.environ[env].split(os.path.pathsep)
    except KeyError:
        if default is None:
            return list()
        else:
            return default


def putEnv(env, value):
    # type: (str, str) -> None
    """set the value of an environment variable.

    overwrites any pre-existing value for this variable. If value is a
    non-string iterable (aka a list or tuple), it will be joined into a string
    with the separator appropriate for the current system.

    Parameters
    ----------
    env : str
    value : str
    """
    if _isIterable(value):
        value = os.path.pathsep.join(value)
    os.environ[env] = value


def refreshEnviron():
    """
    copy the shell environment into python's environment, as stored in os.environ
    """
    exclude = ['SHLVL']

    if os.name == 'posix':
        cmd = '/usr/bin/env'
    else:
        cmd = 'set'

    cmdOutput = shellOutput(cmd)
    # print "ENV", cmdOutput
    # use splitlines rather than split('\n') for better handling of different
    # newline characters on various os's
    for line in cmdOutput.splitlines():
        # need the check for '=' in line b/c on windows (and perhaps on other systems? orenouard?), an extra empty line may be appended
        if '=' in line:
            var, val = line.split('=', 1)  # split at most once, so that lines such as 'smiley==)' will work
            if not var.startswith('_') and var not in exclude:
                os.environ[var] = val


def executableOutput(exeAndArgs, convertNewlines=True, stripTrailingNewline=True,
                     returnCode=False, input=None, **kwargs):
    # type: (Any, bool, bool, bool, str, **Any) -> None
    """Will return the text output of running the given executable with the given arguments.

    This is just a convenience wrapper for subprocess.Popen, so the exeAndArgs argment
    should have the same format as the first argument to Popen: ie, either a single string
    giving the executable, or a list where the first element is the executable and the rest
    are arguments.

    Parameters
    ----------
    convertNewlines : bool
        if True, will replace os-specific newlines (ie, \\r\\n on Windows) with
        the standard \\n newline
    stripTrailingNewline : bool
        if True, and the output from the executable contains a final newline,
        it is removed from the return value
        Note: the newline that is stripped is the one given by os.linesep, not \\n
    returnCode : bool
        if True, the return will be a tuple, (output, returnCode)
    input : str
        if non-none, a string that will be sent to the stdin of the executable

    kwargs are passed onto subprocess.Popen

    Note that if the keyword arg 'stdout' is supplied (and is something other than subprocess.PIPE),
    then the return will be empty - you must check the file object supplied as the stdout yourself.

    Also, 'stderr' is given the default value of subprocess.STDOUT, so that the return will be
    the combined output of stdout and stderr.

    Finally, since maya's python build doesn't support universal_newlines, this is always set to False -
    however, set convertNewlines to True for an equivalent result.
    """

    kwargs.setdefault('stdout', subprocess.PIPE)
    kwargs.setdefault('stderr', subprocess.STDOUT)

    if input:
        kwargs.setdefault('stdin', subprocess.PIPE)

    cmdProcess = subprocess.Popen(exeAndArgs, **kwargs)
    cmdOutput = cmdProcess.communicate(input=input)[0]

    if stripTrailingNewline and cmdOutput.endswith(os.linesep):
        cmdOutput = cmdOutput[:-len(os.linesep)]

    if convertNewlines:
        cmdOutput = cmdOutput.replace(os.linesep, '\n')
    if returnCode:
        return cmdOutput, cmdProcess.returncode
    return cmdOutput


def shellOutput(shellCommand, convertNewlines=True, stripTrailingNewline=True,
                returnCode=False, input=None, **kwargs):
    # type: (Any, bool, bool, bool, str, **Any) -> None
    """Will return the text output of running a given shell command.

    Parameters
    ----------
    convertNewlines : bool
        if True, will replace os-specific newlines (ie, \\r\\n on Windows) with
        the standard \\n newline
    stripTrailingNewline : bool
        if True, and the output from the executable contains a final newline,
        it is removed from the return value
        Note: the newline that is stripped is the one given by os.linesep, not \\n
    returnCode: bool
        if True, the return will be a tuple, (output, returnCode)
    input : str
        if non-none, a string that will be sent to the stdin of the executable

    With default arguments, behaves like commands.getoutput(shellCommand),
    except it works on windows as well.

    kwargs are passed onto subprocess.Popen

    Note that if the keyword arg 'stdout' is supplied (and is something other than subprocess.PIPE),
    then the return will be empty - you must check the file object supplied as the stdout yourself.

    Also, 'stderr' is given the default value of subprocess.STDOUT, so that the return will be
    the combined output of stdout and stderr.

    Finally, since maya's python build doesn't support universal_newlines, this is always set to False -
    however, set convertNewlines to True for an equivalent result.
    """

    # commands module not supported on windows... use subprocess
    kwargs['shell'] = True
    kwargs['convertNewlines'] = convertNewlines
    kwargs['stripTrailingNewline'] = stripTrailingNewline
    kwargs['returnCode'] = returnCode
    kwargs['input'] = input

    return executableOutput(shellCommand, **kwargs)
