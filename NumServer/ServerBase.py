import socket;
import atexit;
from Numbot.Logger import Logger, colors;
import select;
from _thread import *;

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
            self.clients.append(conn);
            Logger.log("User connected at {0}.".format(addr));
            start_new_thread(self.clientThread, (self, conn, addr));
        return;

    def clientThread(self, sock, addr):
        while True:
            try:
                message = sock.recv(2048);
            except Exception:
                Logger.error();
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

    def removeClient(self, conn):
        if conn in self.clients:
            self.clients.remove(conn);
        return;

    def exit_handler(self):
        for conn in self.clients:
            conn.close();
        self.sock.close();
        return;