from Logger import Logger, colors;
from functools import wraps;
import math;
import inspect

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

class Extensions:
    def __init__(self):
        self.commands = [];
        attr = Extensions.__dict__.keys();
        for a in attr:
            if hasattr(getattr(self, a), "__accesslevel__"):
                self.commands.append(a);
        self.commands = sorted(self.commands, key = lambda s: s.casefold());
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
        self.send(sock, "PRIVMSG {0} :{1}".format(sendTo, message));
        return;

    @accesslvl(6)
    def reload(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Reloads all extensions for the bot.

        Usage: !reload
        """
        return;

    @accesslvl(6)
    def raw(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Sends a raw message to IRC.

        Usage: !raw <message>
        """
        self.send(sock, " ".join(msg[0:]));
        return;

    @accesslvl(6)
    def sql(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Runs a SQLite query.

        Usage: !sql <query>
        """
        sqlite.Execute(" ".join(msg));
        response = sqlite.cur.fetchall();
        self.chat(sock, sendTo, response);

    @accesslvl(0)
    def quote(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Returns a selected or random quote.

        Usage: !quote [(# | search term [#<#>])]
        """
        Logger.debug(sqlite.GetQuoteCount());
        return;

    @accesslvl(1)
    def setaccesslevel(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Changes a selected user's access level. You cannot change your own or of people your level or higher, and you cannot set a user to your level or higher. Only works on registered users, and must be the registered account name.

        Usage: !setaccesslevel <user> <level>
        """
        message = "";
        if len(msg) != 2:
            message = "You must enter a username and an access level to set them to!";
        else:
            accesslevel = -1;
            try:
                accesslevel = int(msg[1]);
            except ValueError:
                message = "You must enter a valid number for access level!";
            if accesslevel <= 0:
                message = "Target access level must be greater than zero!";
            else:
                if accesslevel >= accesslvl:
                    message = "You cannot set an access level equal to or higher than your own!";
                else:
                    if sqlite.DoesUserExist(msg[0]) == False:
                        message = "That user does not exist!";
                    else:
                        if sqlite.GetAccessLevel(msg[0]) >= accesslvl:
                            message = "You cannot alter the access level of a user already at or above yours!";
                        else:
                            if sqlite.GetRegisteredName(sender).lower() == msg[0].lower():
                                message = "You cannot alter your own access level!";
                            else:
                                sqlite.SetAccessLevel(msg[0], accesslevel);
                                message = "User {0}'s access level successfully changed to {1}.".format(msg[0], accesslevel);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(0)
    def accesslevel(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Returns the target's access level.

        Usage: !accesslevel [target]
        """
        user = sender;
        if len(msg) >= 1:
            user = msg[0];
        self.chat(sock, sendTo, "{0} has an access level of {1}.".format(user, sqlite.GetAccessLevel(user)));

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
            if page > math.ceil(len(self.commands) / 10):
                page = math.ceil(len(self.commands) / 10);
            if page < 1:
                page = 1;
            message = "Commands, page {0} / {1}: ".format(page, math.ceil(len(self.commands) / 10));
            commands = "";
            if page == math.ceil(len(self.commands) / 10):
                commands = ", ".join(self.commands[10 * (page - 1):]);
            else:
                commands = ", ".join(self.commands[10 * (page - 1) : 10 * page - 1]);
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
                if hasattr(func, "__accesslevel__"):
                    accesslevel = "Access level: {0}".format(func.__accesslevel__);
                    message = "!{0} - {1}. {2}".format(func.__name__, accesslevel, docString);
                else:
                    message = "{0} is not a command, {1}!".format(cmd, sender);
            else:
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
                    if hasattr(getattr(self, command), "__accesslevel__"):
                        getattr(self, command)(accessLevel, sock, SQLite, sender, receiver, sendTo, msg[1:]);
        return;