from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

from builtins import zip
from builtins import object
import string
import sys
import textwrap
import inspect
import pymel.util as util


def indent(s, margin):
    return '\n'.join((margin + line) if line else line
                     for line in s.split('\n'))


class DocstringBuilder(object):
    DOC_WIDTH = 120

    def __init__(self, cmdName, indentation='    '):
        import pymel.internal.factories as factories
        factories.loadCmdCache()
        factories.loadCmdDocCache()
        self.cmdName = cmdName
        try:
            self.cmdInfo = factories.cmdlist[cmdName]
        except KeyError:
            raise factories.MelCommandMissingError(cmdName)
        self.indentation = indentation

    def startFlagSection(self):
        raise NotImplementedError

    def indent(self, lines):
        return indent(lines, self.indentation)

    def _addFlag(self, flag, docs):
        # flag type
        try:
            argInfo = docs['args']
        except KeyError:
            raise KeyError("Error retrieving doc args for: "
                           "%r, %r" % (self.cmdName, flag))

        typ = self.getTypeIdentifier(argInfo)

        # flag docstring
        descr = docs.get('docstring', '')

        # flag modes
        tmpmodes = docs.get('modes', [])
        modes = []
        if 'create' in tmpmodes:
            modes.append('create')
        if 'query' in tmpmodes:
            modes.append('query')
        if 'edit' in tmpmodes:
            modes.append('edit')

        return self.addFlag(flag, typ, docs['shortname'], descr, modes)

    def addFlag(self, flag, typ, shortname, descr, modes):
        "Generate docs for a single flag"
        raise NotImplementedError

    def addFooter(self):
        return '\nDerived from mel command `maya.cmds.%s`\n' % (self.cmdName)

    def getTypeIdentifier(self, typ):
        if isinstance(typ, list):
            try:
                typ = [x.__name__ for x in typ]
            except:
                typ = [str(x) for x in typ]
            typ = ', '.join(typ)
        else:
            try:
                typ = typ.__name__
            except:
                pass
        return typ

    def build(self, docstring):
        # type: (str) -> str
        """
        Add the generated docstrings to the existing docstring

        Parameters
        ----------
        docstring : str
            original docstring

        Returns
        -------
        str
        """
        if docstring:
            docstring = inspect.cleandoc(docstring)
            docstring = self.indent(docstring) + '\n\n'

        # insert the description before the existing docstring
        description = '\n'.join(
            textwrap.wrap(self.cmdInfo['description'], width=self.DOC_WIDTH))

        docstring = self.indent(description) + '\n\n' + docstring

        flagsInfo = self.cmdInfo['flags']

        if flagsInfo and not set(flagsInfo.keys()).issubset(['edit', 'query']):

            docstring += self.indent(self.startFlagSection())

            for flag in sorted(flagsInfo.keys()):
                if flag in ['edit', 'query']:
                    continue

                docstring += self.indent(self._addFlag(flag, flagsInfo[flag]))

        docstring += self.indent(self.addFooter())
        return '\n' + docstring


class RstDocstringBuilder(DocstringBuilder):

    """
    Docstring builder that outputs reStructuredText for building HTML docs
    """
    widths = [3, 100, 32, 32]
    altwidths = [widths[0] + widths[1]] + widths[2:]
    rowsep = '+' + '+'.join(['-' * (w - 1) for w in widths]) + '+\n'
    headersep = '+' + '+'.join(['=' * (w - 1) for w in widths]) + '+\n'

    @staticmethod
    def section(title):
        return '.. rubric:: %s:\n' % title

    @staticmethod
    def makerow(items, widths):
        return '|' + '|'.join(
            ' ' + i.ljust(w - 2) for i, w in zip(items, widths)) + '|\n'

    def startFlagSection(self):
        s = self.section('Flags')
        s += '\n' + self.rowsep
        s += self.makerow(
            ['Long Name / Short Name', 'Argument Types', 'Properties'],
            self.altwidths)
        s += self.headersep
        return s

    def addFlag(self, flag, typ, shortname, descr, modes):
        s = ''
        for data in util.izip_longest(
                ['``%s`` / ``%s``' % (flag, shortname)],
                textwrap.wrap('*%s*' % typ, self.widths[2] - 2),
                ['.. image:: /images/%s.gif' % m for m in modes],
                fillvalue=''):
            s += self.makerow(data, self.altwidths)

        # docstring += makerow( ['**%s (%s)**' % (flag, docs['shortname']),
        # '*%s*' % typ, ''], altwidths )
        # for m in modes:
        #    docstring += makerow( ['', '', '.. image:: /images/%s.gif' % m], altwidths )

        s += self.rowsep

        descr_widths = [self.widths[0], sum(self.widths[1:])]
        if descr:
            for line in textwrap.wrap(descr.strip('|'), sum(self.widths[1:]) - 2):
                s += self.makerow(['', line], descr_widths)
                # add some filler at the bottom
                # docstring += makerow(['', '  ..'], descr_widths)
        else:
            s += self.makerow(['', ''], descr_widths)

        # empty row for spacing
        # docstring += rowsep
        # docstring += makerow( ['']*len(widths), widths )
        # closing separator
        s += self.rowsep
        return s

    def addFooter(self):
        footer = super(RstDocstringBuilder, self).addFooter()

        if self.cmdInfo.get('example', None):
            # docstring = ".. |create| image:: /images/create.gif\n.. |edit| image::
            # /images/edit.gif\n.. |query| image:: /images/query.gif\n\n" + docstring
            footer += ('\n\n' + self.section('Example') + '\n::\n' +
                       self.cmdInfo['example'])
        return footer


class NumpyDocstringBuilder(DocstringBuilder):
    DOC_WIDTH = 80

    @staticmethod
    def section(title):
        return title + '\n' + ('-' * len(title)) + '\n'

    def startFlagSection(self):
        return self.section('Parameters')

    def getTypeIdentifier(self, typ):
        if isinstance(typ, list):
            try:
                typ = [x.__name__ for x in typ]
            except:
                typ = [str(x) for x in typ]
            typ = 'Tuple[%s]' % ', '.join(typ)
        else:
            try:
                typ = typ.__name__
            except:
                pass
        return typ

    def addFlag(self, flag, typ, shortname, descr, modes):
        extra = '- modes: %s\n' % ', '.join(modes)
        if shortname:
            extra += '- shortname: %s\n' % shortname
        extra = self.indent(extra)

        descr = '\n'.join(
            ['    ' + x for x in textwrap.wrap(descr, self.DOC_WIDTH)])
        # add trailing newline
        descr = descr + '\n' if descr else ''

        docstring = '%s : %s\n%s%s' % (flag, typ, descr, extra)
        return docstring


class PyDocstringBuilder(DocstringBuilder):

    """
    Docstring builder that generates human-readable docstrings for use with
    the python help() function.
    """
    DOC_WIDTH = 80

    @staticmethod
    def section(title):
        return title + ':\n'

    def startFlagSection(self):
        return self.section('Flags')

    def addFlag(self, flag, typ, shortname, descr, modes):
        descr = '\n'.join(
            ['    ' + x for x in textwrap.wrap(descr, self.DOC_WIDTH)])
        # add trailing newline
        descr = descr + '\n' if descr else ''
        return '- %s %s [%s]\n%s\n' % (
            (flag + ' : ' + shortname).ljust(30),
            ('(' + typ + ')').ljust(15),
            ','.join(modes),
            descr)
