from datetime import datetime;
from Logger import Logger, colors;
import random;
import string;

class UserObject:
    def __init__(self):
        self.sock = None;
        self.addr = None;
        self.nick = "";
        self.channels = [];
        self.lastPinged = datetime.min;
        self.lastPingSuccess = datetime.min;
        self.ping = "";
        self.pingSuccess = False;
        return;

    def getAddress(self):
        try:
            return "{0}:{1}".format(self.addr[0], self.addr[1]);
        except Exception:
            return "?:?";
        return "?:?";

    def getNick(self):
        if self.nick != "":
            return self.nick;
        return self.getAddress();

    def close(self):
        if self.sock != None:
            self.sock.close();
        self.addr = None;
        self.nick = "";
        self.channels = [];
        self.lastPinged = datetime.min;
        return;

    def send(self, msgType, msg, log = False):
        try:
            msg = ":SERVER {0} {1} :{2}".format(msgType, self.getNick(), msg);
            if log:
                Logger.log(msg);
            self.sock.send("{0}\r\n".format(msg).encode("utf-8"));
        except Exception:
            Logger.error("Exception on send!");
        return;

    def sendPing(self):
        self.ping = "".join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(8));
        self.pingSuccess = False;
        self.lastPinged = datetime.now;
        try:
            self.sock.send("PING :{0}\r\n".format(self.ping).encode("utf-8"));
        except Exception:
            Logger.error("Exception on send (ping)!");
        return;

    def pinged(self):
        self.pingSuccess = True;
        self.lastPingSuccess = datetime.now;
        return;