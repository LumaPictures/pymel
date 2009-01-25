import pymel as pm
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
    m = LoggingMenu(parent=pm.getMelGlobal("string","gMainWindow"))


class LoggingMenu(pm.Menu):

    def refreshLoggingMenu(self):
        pm.Menu(self.menuLoggerTree).deleteAllItems(1)
        self.buildSubMenu(self.menuLoggerTree, logging.root)

    def changeLevel(self, item, level):
        logger.debug("Setting %s log level to %s" % (item, level))
        item.setLevel(levelsDict[level])

    def buildLevelMenu(self, parent, item):
        for level in logLevelNames:
            pm.menuItem(p=parent, l=(">%s<" if levelsDict[item.level]==level else "%s") % level, c=pm.Callback(self.changeLevel, item, level))

    def buildSubMenu(self, parent, logger):
        levelsMenu = pm.menuItem(l="%s <%s>" % (logger.name, levelsDict[logger.level]),p=parent, sm=True)
        self.buildLevelMenu(levelsMenu, logger)
        pm.menuItem(d=1,p=parent)
        try:
            if logger.children:
                pm.menuItem(l="Child-Loggers:",p=parent,en=0)
                for item in logger.children:
                    subMenu = pm.menuItem(l=item.name, sm=True, p=parent, tearOff=True, aob=True)
                    subMenu.postMenuCommand(pm.Callback(self.buildSubMenu, parent=subMenu, logger=item))
                    subMenu.setPostMenuCommandOnce(True)
        except: pass
        pm.menuItem(d=1,p=parent)
        if logger.handlers:
            pm.menuItem(l="Streams:",p=parent,en=0)
            for item in logger.handlers:
                levelsMenu = pm.menuItem(l="%s <%s>" % (item.__class__.__name__, levelsDict[item.level]), p=parent, sm=True, aob=True)
                self.buildLevelMenu(levelsMenu, item)
                pm.menuItem(d=1,p=levelsMenu)
                pm.menuItem(l="Set Formatter", p=levelsMenu, c=pm.Callback(self.setFormatter, item))
                pm.menuItem(l="Remove", p=parent, ob=True, c=pm.Callback(logger.removeHandler, item))
        pm.menuItem(l="<New Stream...>", p=parent, c=lambda *x: self.addHandler(logger))

    def setFormatter(self, handler):
        tips = """
        name, levelno, levelname, pathname, filename, module, lineno, funcName, created, 
        asctime, msecs, relativeCreated, thread, threadName, process, message
        """
        fmt = pm.promptBox("Logging","Set Format:\n" + tips, "Set", "Cancel", tx=logging.BASIC_FORMAT)
        if fmt:     
            handler.setFormatter(logging.Formatter(fmt))
        
    def addHandler(self, logger):
        mode = pm.confirmBox("Logging","Handler Type:", "File", "Script Editor", "Console", "Log Server", "Cancel")
        if mode=="Cancel":
            return
        elif mode=="File":
            f = pm.fileDialog(mode=1, dm="Log File: *.log")
            if not f:
                return
            handler = logging.FileHandler(f)
        elif mode=="Script Editor":
            handler = logging.StreamHandler()
        elif mode=="Console":
            handler = logging.StreamHandler(sys.__stderr__)
        elif mode=="Log Server":
            from logServer import SocketHandler, kHostName
            server = pm.promptBox("Logging","Log Server Address:", "Connect", "Cancel", tx="%s:%s" % (kHostName, logging.handlers.DEFAULT_TCP_LOGGING_PORT))
            host, sep, port = server.partition(":")
            handler = SocketHandler(host, int(port))
            
        level = pm.confirmBox("Logging","Log Level:", *logLevelNames)
        if not level:
            return
        handler.setLevel(levelsDict[level])
        handler.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logger.addHandler(handler)
        logger.info("Added %s-Handler to Logger '%s' at level %s" % (mode, logger.name, level))

    def __new__(cls, name="menuLogging", parent=None):
        if pm.menu(name, ex=1):
            pm.deleteUI(name)
        self = pm.menu("menuLogging", l='Logging Control', aob=True, p=parent)
        return pm.Menu.__new__(cls, self)

    def __init__(self, name=None, parent=None):
        self.postMenuCommand(self.refresh)

    def refresh(self):
        refreshLoggerHierarchy()
        self.deleteAllItems(1)
        if logging.root.handlers:
            self.buildLevelMenu(self, logging.root.handlers[0])
        pm.menuItem(d=1, p=self)
        self.menuLoggerTree = pm.menuItem(p=self, l="Logger Tree", sm=True, aob=True)
        self.menuLoggerTree.postMenuCommand(self.refreshLoggingMenu)
        