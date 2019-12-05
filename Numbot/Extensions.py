from Logger import Logger, colors;
import Quotes;
from functools import wraps;
import math;
import inspect
import importlib;
import types;
import FieldNames;
import UserManagement;

#   self    accesslvl   sock    sqlite  sender  receiver    sendTo  msg
#   0       1           2       3       4       5           6       7

def accesslvl(accesslevel):
    def accesslevel_decorator(func):
        @wraps(func)
        def accesslevelwrapper(*args):
            if args[1] >= accesslevel:
                func(*args)
            else:
                args[0].chat(args[2], args[6], "You do not have access to that command, {}!".format(args[4]))
        accesslevelwrapper.__accesslevel__ = accesslevel
        return accesslevelwrapper
    return accesslevel_decorator

def prefix(pref):
    def prefix_decorator(func):
        @wraps(func)
        def prefixwrapper(*args):
            func(*args)
        prefixwrapper.__prefixed__ = pref
        return prefixwrapper
    return prefix_decorator

class Extensions:

    def __init__(self):
        for imp in Extensions.imports():
            importlib.reload(imp);
        return;

    def send(self, sock, message, log = True):
        msg = message;
        if msg.split()[0] == "PASS":
            msg = "PASS ********";
        if log == True:
            Logger.log(msg);
        try:
            sock.send("{0}\r\n".format(message).encode("utf-8"));
        except Exception:
            if log == False:
                Logger.Logger.log(msg);
            Logger.error("Exception on send!");
        return;

    def chat(self, sock, sendTo, message):
        if message != "":
            self.send(sock, "PRIVMSG {0} :{1}".format(sendTo, message));
        return;

    def imports():
        for name, val in globals().items():
            if isinstance(val, types.ModuleType):
                yield val;

    def getCommands():
        imps = list(Extensions.imports());
        commands = [];
        for a in Extensions.__dict__.keys():
            if hasattr(getattr(Extensions, a), "__accesslevel__") and not hasattr(getattr(Extensions, a), "__prefixed__"):
                commands.append((a, getattr(getattr(Extensions, a), "__accesslevel__")));
        for imp in imps:
            for cls in imp.__dict__:
                obj = getattr(imp, cls);
                if isinstance(obj, type) and obj.__module__ == imp.__name__:
                    for a in obj.__dict__.keys():
                        if hasattr(getattr(obj, a), "__accesslevel__") and not hasattr(getattr(obj, a), "__prefixed__"):
                            commands.append((a, getattr(getattr(obj, a), "__accesslevel__")));
        commands.sort(key = lambda x: x[0], reverse=False);
        commands.sort(key = lambda x: x[1], reverse=False);
        return commands;

    @accesslvl(0)
    def help(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Describes a specified command, or lists commands.

        Usage: !help [command | page number]
        """
        cmd = "!help";
        page = "";
        message = "";
        if len(msg) >= 1:
            cmd = msg[0].lower();
        try:
            page = int(cmd);
        except ValueError:
            page = "";
        if isinstance(page, int):
            cmds = []
            for i in Extensions.getCommands():
                if i[1] <= accesslvl:
                    cmds.append(i[0]);
            cmds.sort();
            if page > math.ceil(len(cmds) / 10):
                page = math.ceil(len(cmds) / 10);
            if page < 1:
                page = 1;
            message = "Commands, page {0} / {1}: ".format(page, math.ceil(len(cmds) / 10));
            commands = "";
            for i in range(10 * (page - 1), min(10 * page, len(cmds))):
                if commands != "":
                    commands = "{0}, ".format(commands);
                commands = "{0}{1}".format(commands, cmds[i]);
            message = "{0}{1}".format(message, commands);
        else:
            if len(cmd) > 1:
                if cmd[0] == "!":
                    cmd = cmd[1:];
            if hasattr(self, cmd):
                func = getattr(self, cmd);
                docString = func.__doc__;
                if docString == None:
                    docString = "No description found.";
                docString = docString.replace("\n", " ");
                docString = " ".join(docString.split());
                accesslevel = "";
                if hasattr(func, "__accesslevel__") and not hasattr(func, "__prefixed__"):
                    accesslevel = "Access level: {0}".format(func.__accesslevel__);
                    message = "!{0} - {1}. {2}".format(func.__name__, accesslevel, docString);
                else:
                    message = "{0} is not a command, {1}!".format(cmd, sender);
            else:
                found = False;
                for imp in Extensions.imports():
                    for clss in imp.__dict__:
                        obj = getattr(imp, clss);
                        if isinstance(obj, type) and obj.__module__ == imp.__name__:
                            if hasattr(obj, cmd):
                                if hasattr(getattr(obj, cmd), "__accesslevel__") and not hasattr(getattr(obj, cmd), "__prefixed__"):
                                    func = getattr(obj, cmd);
                                    docString = func.__doc__;
                                    if docString == None:
                                        docString = "No description found.";
                                    docString = docString.replace("\n", " ");
                                    docString = " ".join(docString.split());
                                    accesslevel = "";
                                    if hasattr(func, "__accesslevel__") and not hasattr(func, "__prefixed__"):
                                        found = True;
                                        accesslevel = "Access level: {0}".format(func.__accesslevel__);
                                        message = "!{0} - {1}. {2}".format(func.__name__, accesslevel, docString);
                if not found:
                    message = "{0} is not a command, {1}!".format(cmd, sender);
        if message != "":
            self.chat(sock, sendTo, message);
        return;

    def Action(self, sock, SQLite, sender, receiver, message):
        sendTo = receiver;
        if "#" not in sendTo:
            sendTo = sender;
        accessLevel = SQLite.GetAccessLevel(sender);
        msg = message.split();
        if len(msg) >= 1:
            if msg[0][0] == '!':
                command = msg[0][1:].lower();
                if hasattr(self, command):
                    if hasattr(getattr(self, command), "__accesslevel__") and not hasattr(getattr(self, command), "__prefixed__"):
                        getattr(self, command)(accessLevel, sock, SQLite, sender, receiver, sendTo, msg[1:]);
                for imp in Extensions.imports():
                    for clss in imp.__dict__:
                        obj = getattr(imp, clss);
                        if isinstance(obj, type) and obj.__module__ == imp.__name__:
                            if hasattr(obj, command):
                                if hasattr(getattr(obj, command), "__accesslevel__") and not hasattr(getattr(obj, command), "__prefixed__"):
                                    getattr(obj,command)(self, accessLevel, sock, SQLite, sender, receiver, sendTo, msg[1:]);
        return;