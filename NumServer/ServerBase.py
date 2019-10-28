import socket;
import atexit;
from Logger import Logger, colors;
import select;
from _thread import *;
from UserObject import UserObject;
from datetime import datetime;

class ServerBase:
    '''A pseudo-IRC server for testing local IRC stuff'''

    def __init__(self):
        Logger.log("Initializing server...");
        Logger.log("\tRegistering exit handler...");
        atexit.register(self.exit_handler);
        Logger.log("\tSetting up initial IRC parameters...");
        self.host = "";
        Logger.log("\t\tHost: \"{0}\"".format(self.host));
        self.port = 6667;#Standard IRC port
        Logger.log("\t\tPort: {0}".format(self.port));
        Logger.log("\tInitializing socket list...");
        self.maxConn = 100;
        Logger.log("\t\tMax connections: {0}".format(self.maxConn));
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1);
        self.sock.bind((self.host, self.port));
        self.sock.listen(self.maxConn);
        self.clients = [];
        return;

    def run(self):
        Logger.log("Starting main server loop.");
        Logger.log("Now accepting incoming connections...");
        while True:
            conn, addr = self.sock.accept();
            usr = UserObject();
            usr.sock = conn;
            usr.addr = addr;
            usr.sendPing();
            self.clients.append(usr);
            Logger.log("User connected at {0}.".format(self.clients[-1].getAddress()));
            start_new_thread(self.clientThread, (self.clients[-1],));
        return;

    def clientThread(self, usr):
        oldMessage = "";
        while True:
            try:
                message = "{0}{1}".format(oldMessage, usr.sock.recv(1024).decode("utf-8"));
                while "\r\n" in message:
                    msg = message[:message.index("\r\n")];
                    if msg != "":
                        msg2 = msg;
                        if msg.split()[0] == "PASS":
                            msg = "PASS ********";
                        Logger.log("{0}: {1}".format(usr.getNick(), msg));
                        self.process(usr, msg2);
                    message = message[message.index("\r\n") + 2:];
                oldMessage = message;
            except ConnectionResetError:
                self.removeClient(usr);
                break;
            except Exception:
                Logger.error();
                break;
        return;

    def process(self, usr, msg):
        msg = msg.split();
        if msg[0].lower() == "nick" and len(msg) >= 2:
            usr.nick = msg[1];
        if msg[0].lower() == "pong" and len(msg) >= 2:
            if msg[1][0] == ':':
                msg[1] = msg[1][1:];
            if msg[1] == usr.ping:
                if usr.lastPingSuccess == datetime.min:
                    usr.send("396", "Ping confirmed.", True);
                usr.pinged();
        return;

    def broadcast(self, message, conn):
        '''
        Broadcast message to all except the original sender
        '''
        for client in self.clients:
            if client != conn:
                try:
                    client.send(message);
                except Exception:
                    client.close();
                    self.removeClient(client);
                    Logger.error("Client failed to receive message.");
        return;

    def removeClient(self, usr):
        if usr in self.clients:
            self.clients.remove(usr);
            Logger.log("{0} disconnected.".format(usr.getNick()));
        return;

    def exit_handler(self):
        for usr in self.clients:
            usr.close();
        self.sock.close();
        return;