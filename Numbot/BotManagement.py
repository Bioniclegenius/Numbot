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

class BotManagement:

    @accesslvl(0)
    def ping(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        self.chat(sock, sendTo, "Pong!");
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
        return;

    @accesslvl(6)
    def debug(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Debug command to get various bits of information.

        Usage: !debug [whatever parameters coded for at the moment]
        """
        message = "";
        for cmd in Extensions.getCommands():
            if message != "":
                message = "{}, ".format(message);
            message = "{}[{}] {}".format(message, cmd[1], cmd[0]);
        if message == "":
            message = "None";
        self.chat(sock, sendTo, message);
        return;
