import sys;
sys.path.append("../Numbot");
import ServerBase

def main():
    server = ServerBase.ServerBase();
    server.run();
    return;

main();