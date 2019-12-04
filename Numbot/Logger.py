import inspect;
import sys;
from enum import Enum;
import traceback;
from datetime import datetime;

#To enable CLI colors in Windows 10:
#Regedit -> HKEY_CURRENT_USER\Console
#"VirtualTerminalLevel" = dword:0000001
class colors(Enum):
    BLACK = "\x1b[1;30;40m";
    RED = "\x1b[1;31;40m";
    GREEN = "\x1b[1;32;40m";
    YELLOW = "\x1b[1;33;40m";
    BLUE = "\x1b[1;34;40m";
    MAGENTA = "\x1b[1;35;40m";
    CYAN = "\x1b[1;36;40m";
    WHITE = "\x1b[1;37;40m";
    DEFAULT = "\x1b[0m";

class Logger:
    def log(message = "", color = colors.DEFAULT):
        message = "{0}".format(message);
        while message[-1:] == "\n" or message[-1:] == "\r":
            message = message[:-1];
        print("{0}{1}{2}: {3}{4}{5}".format(colors.CYAN.value, datetime.now(), colors.DEFAULT.value, color.value, message, colors.DEFAULT.value));

    def debug(message = "", color = colors.YELLOW):
        caller = inspect.getframeinfo(inspect.stack()[1][0]);
        if message != "":
            message = "\t{0}".format(message);
        Logger.log("DEBUG: {0}\t{1}{2}".format(caller.filename[caller.filename.rindex("\\") + 1:], caller.lineno, message), color);

    def internal(message = "", color = colors.GREEN):
        Logger.log(message, color);

    def error(message = "", color = colors.RED):
        Logger.log("{0}\nEXCEPTION\n{1}".format(message, traceback.format_exc()), color);