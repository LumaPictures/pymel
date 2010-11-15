import pymel.all as pymel
import logging, logging.handlers
import sys
logger = logging.getLogger(__name__)

logLevelNames = [logging.getLevelName(n) for n in xrange(0,logging.CRITICAL+1,10)]
levelsDict = dict(zip(logLevelNames, range(0,logging.CRITICAL+1,10)))
levelsDict.update(dict(zip(range(0,logging.CRITICAL+1,10), logLevelNames)))

def refreshLoggerHierarchy():
    for v in logging.Logger.manager.loggerDict.values():
        try:
            del v.children
        except:pass

    for k, v in sorted(logging.Logger.manager.loggerDict.items()):
            if  not isinstance(v, logging.Logger):
                continue
            try:
                if v not in v.parent.children:
                    v.parent.children.append(v)
            except:
                v.parent.children = [v]

def initMenu():
    return LoggingMenu(parent=pymel.melGlobals["gMainWindow"])




class LoggingMenu(pymel.Menu):

    def refreshLoggingMenu(self):
        #pymel.Menu(self).deleteAllItems(1)
        self.buildSubMenu(self, logging.root)

    def changeLevel(self, item, level):
        logger.debug("Setting %s log level to %s" % (item, level))
        item.setLevel(levelsDict[level])

    def buildLevelMenu(self, parent, item):
        for level in logLevelNames:
            pymel.menuItem(p=parent, checkBox=levelsDict[item.level]==level, l=level, c=pymel.Callback(self.changeLevel, item, level))

    def buildSubMenu(self, parent, logger):
        #levelsMenu = pymel.menuItem(l="%s <%s>" % (logger.name, levelsDict[logger.level]),p=parent, sm=True)
        self.buildLevelMenu(parent, logger)
        pymel.menuItem(d=1,p=parent)
        try:
            if logger.children:
                pymel.menuItem(l="Child Loggers:",p=parent,en=0)
                for item in logger.children:
                    subMenu = pymel.menuItem(l=item.name, sm=True, p=parent, tearOff=True, aob=True, pmo=True)
                    subMenu.postMenuCommand(pymel.Callback(self.buildSubMenu, parent=subMenu, logger=item))
                    subMenu.setPostMenuCommandOnce(True)
        except: pass
        pymel.menuItem(d=1,p=parent)
        if logger.handlers:
            pymel.menuItem(l="Streams:",p=parent,en=0)
            for item in logger.handlers:
                levelsMenu = pymel.menuItem(l="%s <%s>" % (item.__class__.__name__, levelsDict[item.level]), p=parent, sm=True, aob=True)
                self.buildLevelMenu(levelsMenu, item)
                pymel.menuItem(d=1,p=levelsMenu)
                pymel.menuItem(l="Set Formatter", p=levelsMenu, c=pymel.Callback(self.setFormatter, item))
                pymel.menuItem(l="Remove", p=parent, ob=True, c=pymel.Callback(logger.removeHandler, item))
        pymel.menuItem(l="<New Stream...>", p=parent, c=lambda *x: self.addHandler(logger))

    def setFormatter(self, handler):
        tips = """
        name, levelno, levelname, pathname, filename, module, lineno, funcName, created,
        asctime, msecs, relativeCreated, thread, threadName, process, message
        """
        fmt = pymel.promptBox("Logging","Set Format:\n" + tips, "Set", "Cancel", tx=logging.BASIC_FORMAT)
        if fmt:
            handler.setFormatter(logging.Formatter(fmt))

    def addHandler(self, logger):
        mode = pymel.confirmBox("Logging","Handler Type:", "File", "Script Editor", "Console", "Log Server", "Cancel")
        if mode=="Cancel":
            return
        elif mode=="File":
            f = pymel.fileDialog(mode=1, dm="Log File: *.log")
            if not f:
                return
            handler = logging.FileHandler(f)
        elif mode=="Script Editor":
            handler = logging.StreamHandler()
        elif mode=="Console":
            handler = logging.StreamHandler(sys.__stderr__)
        elif mode=="Log Server":
            from logServer import SocketHandler, kHostName
            server = pymel.promptBox("Logging","Log Server Address:", "Connect", "Cancel", tx="%s:%s" % (kHostName, logging.handlers.DEFAULT_TCP_LOGGING_PORT))
            host, sep, port = server.partition(":")
            handler = SocketHandler(host, int(port))

        level = pymel.confirmBox("Logging","Log Level:", *logLevelNames)
        if not level:
            return
        handler.setLevel(levelsDict[level])
        handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logger.addHandler(handler)
        logger.info("Added %s-Handler to Logger '%s' at level %s" % (mode, logger.name, level))

    def __new__(cls, name="pymelLoggingControl", parent=None):
        if pymel.menu(name, ex=1):
            pymel.deleteUI(name)
        self = pymel.menu(name, l='Logging Control', aob=True, p=parent)
        return pymel.Menu.__new__(cls, self)

    def __init__(self, name=None, parent=None):
        self.postMenuCommand(self.refresh)

    def refresh(self, *args):
        refreshLoggerHierarchy()
        self.deleteAllItems(1)
#        if logging.root.handlers:
#            self.buildLevelMenu(self, logging.root.handlers[0])
        pymel.menuItem(l="Root Logger:",p=self,en=0)
        #pymel.menuItem(divider=1, p=self)
        #self.menuLoggerTree = pymel.menuItem(p=self, l="Logger Tree", sm=True, aob=True)
        self.refreshLoggingMenu()
        #self.menuLoggerTree.postMenuCommand(self.refreshLoggingMenu)

