from Logger import Logger, colors;
from functools import wraps;
import math;
import random;
import inspect
import FieldNames;

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

class UserManagement:

    @accesslvl(6)
    def setdata(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Sets a field of a user to the specified value.

        Usage: !setdata [username] [field name] [value]
        """
        message = "";
        if len(msg) < 3:
            message = "You must enter a username, field name, and value to set, {}!".format(sender);
        else:
            username = msg[0];
            fieldName = msg[1];
            value = msg[2];
            responseCode = sqlite.SetUserData(username, fieldName, value);
            if responseCode == -1:#Not a registered user
                message = "{} is not a registered user, {}!".format(username, sender);
            else:
                message = "Field '{}' for {} successfully set to {}.".format(fieldName, username, value);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(6)
    def getdata(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Gets the value of a field of a user.

        Usage: !getdata [username] [field name]
        """
        message = "";
        if len(msg) < 2:
            message = "You must enter a username and a field name, {}!".format(sender);
        else:
            username = msg[0];
            fieldName = msg[1];
            value = sqlite.GetUserData(username, fieldName);
            if value == -1:
                message = "{} is not a registered user, {}!".format(username, sender);
            elif value == None:
                message = "{} does not have a value for '{}', {}!".format(username, fieldName, sender);
            else:
                message = "'{}' for {} has a value of {}.".format(fieldName, username, value);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(6)
    def deletedata(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Deletes a field from a specified user.

        Usage: !deletedata [username] [field name]
        """
        message = "";
        if len(msg) < 2:
            message = "You must enter a username and a field name, {}!".format(sender);
        else:
            username = msg[0];
            fieldName = msg[1];
            value = sqlite.DeleteUserData(username, fieldName);
            if value == -1:
                message = "{} is not a registered user, {}!".format(username, sender);
            elif value == -2:
                message = "{} does not have a value for '{}', {}!".format(username, fieldName, sender);
            else:
                message = "'{}' for {} successfully deleted.".format(fieldName, username);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(4)
    def addpoints(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Adds points to a specified user. Users cannot go into negative points.

        Usage: !addpoints [username] [number of points]
        """
        message = "";
        if len(msg) < 2:
            message = "You must enter a username and a number of points to add, {}!".format(sender);
        else:
            username = msg[0];
            sendID = sqlite.GetUserID(sender);
            subjectID = sqlite.GetUserID(username);
            if sendID != subjectID:
                pointsToAdd = 0;
                validEntry = False;
                try:
                    pointsToAdd = int(msg[1]);
                    validEntry = True;
                except ValueError:
                    message = "The number of points must be an integer!";
                if validEntry:
                    curPoints = sqlite.GetUserData(username, FieldNames.General.Points);
                    if curPoints == -1:
                        message = "{} is not a registered user, {}!".format(username, sender);
                    elif curPoints == None:
                        curPoints = 0;
                    else:
                        curPoints = int(curPoints);
                    curPoints += pointsToAdd;
                    if curPoints < 0:
                        curPoints = 0;
                    sqlite.SetUserData(username, FieldNames.General.Points, str(curPoints));
                    message = "{} now has {} points.".format(username, curPoints);
            else:
                message = "You cannot give yourself points, {}!".format(sender);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(1)
    def points(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Gets the number of points for a given user, or yourself.

        Usage: !points <username>
        """
        message = "";
        username = sender;
        if len(msg) >= 1:
            username = msg[0];
        response = sqlite.GetUserData(username, FieldNames.General.Points);
        points = 0;
        if response == -1:
            message = "{} is not a registered user, {}!".format(username, sender);
        elif response == None:
            points = 0;
            sqlite.SetUserData(username, FieldNames.General.Points, str(points));
        else:
            points = int(response);
        if message == "":
            message = "{} has {} points.".format(username, points);
        self.chat(sock, sendTo, message);
        return;

    @accesslvl(1)
    def userid(self, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Gets the user ID for a given user, or yourself.

        Usage: !userid <username>
        """
        message = "";
        username = sender;
        if len(msg) >= 1:
            username = msg[0];
        response = sqlite.GetUserID(username);
        if response == -1:
            message = "{} is not a registered user, {}!".format(username, sender);
        else:
            message = "{} has a user ID of {}.".format(username, response);
        self.chat(sock, sendTo, message);
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
        return;