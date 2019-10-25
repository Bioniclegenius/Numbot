import botsqlite;
import Logger;
import socket;
import Extensions;
import importlib;
import time;

class ircbot:
    """IRC Bot"""

    def __init__(self):
        Logger.Logger.internal("Starting bot...");
        self.loadSQLite();
        self.SQLite.ClearLastUsernames();
        Logger.Logger.internal("Getting config values...");
        self.configValues = self.SQLite.GetConfigValues();
        self.connect();
        Logger.Logger.internal("Loading extensions...");
        self.ext = Extensions.Extensions();
        return;

    def loadSQLite(self):
        Logger.Logger.internal("Initializing SQLite...");
        self.SQLite = botsqlite.botsqlite();
        Logger.Logger.internal("SQLite complete.");
        return;

    def connect(self):
        Logger.Logger.internal("Connecting to IRC...");
        self.sock = socket.socket();
        self.sock.settimeout(600);
        Logger.Logger.internal("\tIRC Network Address: {0}".format(self.configValues[0]));
        Logger.Logger.internal("\tPort: {0}".format(self.configValues[1]));
        Logger.Logger.internal("\tUsername: {0}".format(self.configValues[2]));
        self.sock.connect((self.configValues[0], self.configValues[1]));
        self.login();
        return;

    def run(self):
        oldRec = "";
        while True:
            rec = "{0}{1}".format(oldRec, self.receive());
            while "\r\n" in rec:
                rec2 = rec[:rec.index("\r\n")];
                if rec2 != "":
                    self.process(rec2);
                rec = rec[rec.index("\r\n") + 2:];
            oldRec = rec;
        return;

    def login(self):
        self.send("USER {0} {1} {2} :{3}".format(self.configValues[2], "Numbot", "*", "Numbot")); # Username, Host name, Server name, Real name
        self.send("NICK {0}".format(self.configValues[2]));
        self.send("PASS {0}".format(self.configValues[3]));
        return;

    def joinChannels(self, channels):
        for i in channels:
            self.send("JOIN #{0}".format(i[0]));
        return;

    def process(self, message):
        verbose = (self.configValues[4] == 1);
        msg = message.split();
        if len(msg) >= 1:
            if msg[0].lower() == "ping":
                if verbose:
                    Logger.Logger.log(" ".join(msg));
                self.send("PONG {0}".format(msg[1]), verbose);
                #Logger.internal("Pinged!", Logger.colors.BLUE);
            elif len(msg) >= 3:
                sender = msg[0];
                if "!" in sender:
                    sender = sender[:sender.index("!")];
                if sender[0] == ':':
                    sender = sender[1:];
                msgtype = msg[1].lower();
                receiver = msg[2];
                recMsg = "";
                if len(msg) >= 4:
                    recMsg = " ".join(msg[3:]);
                    recMsg = recMsg[1:];
                if msgtype == "privmsg":
                    accessLevel = self.GetAccessLevel(sender);
                    sendTo = receiver;
                    if "#" not in sendTo:
                        sendTo = sender;
                    if "#" not in receiver:
                        Logger.Logger.log("***WHISPER FROM {0}: {1}".format(sender, recMsg));
                    else:
                        Logger.Logger.log("{0} {1}: {2}".format(receiver, sender, recMsg));
                    if accessLevel >= 6:
                        if msg[3][1:].lower() == "!reload":
                            try:
                                importlib.reload(Extensions);
                                importlib.reload(botsqlite);
                                importlib.reload(Logger);
                                self.loadSQLite();
                                self.ext = Extensions.Extensions();
                                self.chat(sendTo, "Reloaded!");
                            except Exception:
                                self.chat(sendTo, "Error on reload!");
                                Logger.Logger.error("Exception!");
                    try:
                        self.ext.Action(self.sock, self.SQLite, sender, receiver, " ".join(msg[3:])[1:]);
                    except Exception:
                        self.chat(sendTo, "Exception! Check console for details!");
                        Logger.Logger.error("Exception!");
                elif msgtype == "396":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    channels = self.SQLite.GetChannels();
                    self.joinChannels(channels);
                    Logger.Logger.log(" ".join(msg));
                elif msgtype == "330" and len(msg) >= 5:
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    self.SQLite.TieUserEntry(msg[4], msg[3]);
                    Logger.Logger.log("{0} is logged in as {1}.".format(msg[4], msg[3]));
                elif msgtype == "nick":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    self.SQLite.UpdateUsername(sender, receiver);
                    Logger.Logger.log("{0} -> {1}".format(sender, receiver));
                elif msgtype == "quit":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    self.SQLite.ClearUsername(sender);
                    Logger.Logger.log("{0} quit: {1}".format(sender, " ".join(msg[2:])));
                elif msgtype == "part":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    self.LowerUser(sender);
                    Logger.Logger.log("{0} left {1}".format(sender, receiver));
                elif msgtype == "join":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    self.AddUser(sender);
                    Logger.Logger.log("{0} joined {1}".format(sender, receiver[1:]));
                elif msgtype == "353":
                    if verbose:
                        Logger.Logger.log(" ".join(msg));
                    Logger.Logger.internal("Checking users in {0} list: {1}".format(receiver, " ".join(msg[5:])[1:]));
                    if len(msg) >= 6:
                        for x in msg[5:]:
                            self.AddUser(x);
                elif msgtype in ["301", "311", "312", "313", "317", "318", "319", "366", "372", "375", "376", "378", "379", "671"] and not verbose:#Filter these from the log, no action required
                    #https://www.alien.net.au/irc/irc2numerics.html is a fantastic resource for these things
                    #301: WHOIS - Currently Away
                    #311: WHOIS - <nick> <user> <host> * :<real_name> (information about user)
                    #312: WOHIS - <nick> <server> :<server_info> (server info for user)
                    #313: WHOIS - Service account (user has IRC op priveleges)
                    #317: WHOIS - <nick> <seconds> :seconds idle
                    #318: WHOIS - End
                    #319: WHOIS - Channel list for user
                    #366: End of /NAMES list
                    #372: MOTD
                    #375: Start of MOTD
                    #376: End of MOTD
                    #378: WHOIS - Connecting from <username>@<ip/hostmask> - WHOIS Hostname
                    #379: WHOIS - Using modes <user modes>
                    #671: WHOIS - User is connected securely, like via SSLv2 or TLSv1 or other types
                    pass;
                else:
                    Logger.Logger.log(" ".join(msg));
            else:
                Logger.Logger.log(" ".join(msg));
        return;

    def ParseUsername(self, username):
        username = [x if x.isalnum() == True or x in "`|^_-{}[]\\" else "" for x in username]
        while len(username) >=1 and username[0] in "0123456789-":
            username = username[1:];
        username = "".join(username);
        return username;

    def AddUser(self, username):
        username = self.ParseUsername(username);
        self.SQLite.AddUserEntry(username);
        self.GetAccessLevel(username);
        return;

    def LowerUser(self, username):
        username = self.ParseUsername(username);
        self.SQLite.RemoveUserEntry(username);
        return;

    def GetAccessLevel(self, username):
        username = self.ParseUsername(username);
        accesslevel = self.SQLite.GetAccessLevel(username);
        if accesslevel == 0:
            self.send("WHOIS {0}".format(username), False);
        return accesslevel;

    def chat(self, sendTo, message):
        self.send("PRIVMSG {0} :{1}".format(sendTo, message));

    def receive(self):
        rec = "None";
        try:
            rec = self.sock.recv(1024).decode("utf-8");
        except Exception:
            Logger.Logger.error("Exception on receive!");
            self.connect();
        return rec;

    def send(self, message, log = True):
        msg = message;
        if msg.split()[0] == "PASS":
            msg = "PASS ********";
        if log == True:
            Logger.Logger.log(msg);
        try:
            self.sock.send("{0}\r\n".format(message).encode("utf-8"));
        except Exception:
            if log == False:
                Logger.Logger.log(msg);
            Logger.Logger.error("Exception on send!");
        return;