import sys;
import sqlite3;
from Logger import Logger, colors;
import atexit;

class botsqlite:
    """
    Handles SQLite Database. Creates new db file if file not found.
    """

    def __init__(self, DBFileName = "Bot.db"):
        self.db = DBFileName;
        self.conn = sqlite3.connect(self.db);
        self.cur = self.conn.cursor();
        self.VerifyDBAndSetup();
        atexit.register(self.close);
        return;

    def VerifyDBAndSetup(self):
        tables = ["Config", "Channels", "Users", "UserData", "UserChannels", "Quotes"];
        for i in tables:
            if self.CheckTableExists(i) == False:
                Logger.internal("\t\tCreating {0} table...".format(i));
                if hasattr(self, "Create{0}Table".format(i)) == True:
                    getattr(self, "Create{0}Table".format(i))();
                else:
                    Logger.internal("\t\tCould not find Create{0}Table!".format(i),colors.RED);
        return;

    def CreateConfigTable(self):
        self.Execute('''
        CREATE TABLE Config (
            Lock char(1) NOT NULL DEFAULT 'X' PRIMARY KEY,
            IRCNetworkAddress TEXT NOT NULL,
            Port INTEGER NOT NULL,
            Username TEXT NOT NULL,
            Password TEXT,
            VerboseLogging INTEGER NOT NULL DEFAULT 0,
            constraint CK_T1_Locked CHECK (Lock = 'X')
        )
        ''');
        return;

    def CreateChannelsTable(self):
        self.Execute('''
        CREATE TABLE Channels (
            ChannelName TEXT NOT NULL PRIMARY KEY
        )
        ''');
        return;

    def CreateUsersTable(self):
        self.Execute('''
        CREATE TABLE Users (
            UserID INTEGER NOT NULL PRIMARY KEY,
            RegisteredName TEXT NOT NULL,
            AccessLevel INTEGER NOT NULL DEFAULT 1
        )
        ''');
        return;

    def CreateUserDataTable(self):
        self.Execute('''
        CREATE TABLE UserData (
            UserID INTEGER NOT NULL,
            FieldName TEXT NOT NULL,
            FieldValue TEXT,
            PRIMARY KEY (UserID, FieldName),
            FOREIGN KEY(UserID) REFERENCES Users(UserID)
        )
        ''');
        return;

    def CreateUserChannelsTable(self):
        self.Execute('''
        CREATE TABLE UserChannels (
            UserID INTEGER NOT NULL,
            DisplayName TEXT NOT NULL PRIMARY KEY,
            NumChannels INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(UserID) REFERENCES USERS(UserID)
        )
        ''');
        return;

    def CreateQuotesTable(self):
        self.Execute('''
        CREATE TABLE Quotes (
            ID INTEGER NOT NULL PRIMARY KEY,
            Quote TEXT NOT NULL,
            Timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UserID INTEGER NOT NULL,
            FOREIGN KEY(UserID) REFERENCES Users(UserID)
        )
        ''');
        return;

    def CheckTableExists(self, table):
        self.Execute("SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name = ?", (table));
        if self.cur.fetchone()[0] == 1:
            Logger.internal("\t{0} table exists.".format(table));
            return True;
        Logger.internal("\t{0} table does not exist.".format(table));
        return False;

    def GetConfigValues(self):
        self.Execute("SELECT IRCNetworkAddress, Port, Username, Password, VerboseLogging FROM CONFIG");
        configValues = self.cur.fetchone();
        return configValues;

    def GetChannels(self):
        self.Execute("SELECT ChannelName FROM Channels");
        channels = self.cur.fetchall();
        return channels;

    def ClearLastUsernames(self):
        self.Execute("DELETE FROM UserChannels");
        return;

    def ClearUsername(self, username):
        self.Execute("DELETE FROM UserChannels WHERE DisplayName = ?", (username));
        return;

    def AddUserEntry(self, username):
        username = username.lower();
        self.Execute("SELECT COUNT(*) FROM UserChannels WHERE DisplayName = ?", (username));
        usernameCount = self.cur.fetchone()[0];
        if usernameCount == 0:
            self.Execute("INSERT INTO UserChannels (UserID, DisplayName, NumChannels) VALUES (0, ?, 0)", (username));
        self.Execute("UPDATE UserChannels SET NumChannels = NumChannels + 1 WHERE DisplayName = ?", (username));
        return;

    def RemoveUserEntry(self, username):
        username = username.lower();
        self.Execute("SELECT COUNT(*) FROM UserChannels WHERE DisplayName = ?", (username));
        usernameCount = self.cur.fetchone()[0];
        if usernameCount > 0:
            self.Execute("UPDATE UserChannels SET NumChannels = NumChannels - 1 WHERE DisplayName = ?", (username));
            self.Execute("SELECT NumChannels FROM UserChannels WHERE DisplayName = ?", (username));
            channelCount = self.cur.fetchone()[0];
            if channelCount <= 0:
                self.Execute("DELETE FROM UserChannels WHERE DisplayName = ?", (username));
        return;

    def TieUserEntry(self, registeredName, username):
        registeredName = registeredName.lower();
        username = username.lower();
        self.AddUser(registeredName);
        self.Execute("SELECT UserID FROM Users WHERE RegisteredName = ?", (registeredName));
        userID = self.cur.fetchone()[0];
        self.Execute("SELECT COUNT(*) FROM UserChannels WHERE DisplayName = ?", (username));
        if self.cur.fetchone()[0] < 1:
            AddUserEntry(username);
        self.Execute("UPDATE UserChannels SET UserID = ? WHERE DisplayName = ?", (userID, username));
        return;

    def GetAccessLevel(self, username):
        username = username.lower();
        self.Execute("SELECT COUNT(*) FROM Users JOIN UserChannels ON Users.UserID = UserChannels.UserID WHERE UserChannels.DisplayName = ?", (username));
        if self.cur.fetchone()[0] >= 1:
            self.Execute("SELECT Users.AccessLevel FROM Users JOIN UserChannels ON Users.UserID = UserChannels.UserID WHERE UserChannels.DisplayName = ?", (username));
            accessLevel = self.cur.fetchone()[0];
            return accessLevel;
        return 0;

    def SetAccessLevel(self, username, accesslevel):
        username = username.lower();
        if self.DoesUserExist(username) == True:
            self.Execute("UPDATE Users SET AccessLevel = ? WHERE RegisteredName = ?", (accesslevel, username));
        return;

    def UpdateUsername(self, oldname, newname):
        oldname = oldname.lower();
        newname = newname.lower();
        self.Execute("UPDATE UserChannels SET DisplayName = ? WHERE DisplayName = ?", (newname, oldname));
        return;

    def AddUser(self, registeredName):
        registeredName = registeredName.lower();
        self.Execute("SELECT COUNT(*) FROM Users WHERE RegisteredName = ?", (registeredName));
        if self.cur.fetchone()[0] == 0:
            self.Execute("INSERT INTO Users (RegisteredName) VALUES (?)", (registeredName));
        return;

    def GetUserID(self, username):
        username = username.lower();
        self.Execute("SELECT COUNT(*) FROM Users JOIN UserChannels ON Users.UserID = UserChannels.UserID WHERE UserChannels.DisplayName = ?", (username));
        if self.cur.fetchone()[0] >= 1:
            self.Execute("SELECT Users.UserID FROM Users JOIN UserChannels ON Users.UserID = UserChannels.UserID WHERE UserChannels.DisplayName = ?", (username));
            userID = self.cur.fetchone()[0];
            return userID;
        else:
            self.Execute("SELECT COUNT(*) FROM Users WHERE RegisteredName = ?", (username));
            if self.cur.fetchone()[0] >= 1:
                self.Execute("SELECT UserID FROM Users WHERE RegisteredName = ?", (username));
                userID = self.cur.fetchone()[0];
                return userID;
        return -1;

    def GetQuoteCount(self):
        self.Execute("SELECT COUNT(*) FROM Quotes");
        return self.cur.fetchone()[0];

    def GetQuoteByRow(self, quoteNumber):
        self.Execute("SELECT Quote FROM (SELECT ROW_NUMBER() OVER (ORDER BY ID) RowNum, Quote, ID FROM Quotes) WHERE RowNum = ?", (quoteNumber));
        return self.cur.fetchone()[0];

    def GetQuoteBySearch(self, searchString, searchNumber):
        if searchNumber < 1:
            searchNumber = 1;
        searchString = "%{}%".format(searchString.upper());
        self.Execute("SELECT COUNT(*) FROM Quotes WHERE UPPER(Quote) LIKE ?", (searchString));
        count = self.cur.fetchone()[0];
        if searchNumber > count:
            searchNumber = count;
        if count > 0:
            self.Execute("SELECT Quote FROM (Select ROW_NUMBER() OVER (ORDER BY ID) RowNum, Quote, ID FROM Quotes WHERE UPPER(Quote) LIKE ?) WHERE RowNum = ?", (searchString, searchNumber));
            return self.cur.fetchone()[0];
        return "";

    def GetQuoteNumber(self, quote):
        self.Execute("SELECT RowNum FROM (SELECT ROW_NUMBER() OVER (ORDER BY ID) RowNum, Quote, ID FROM Quotes) WHERE Quote = ?", (quote));
        return self.cur.fetchone()[0];

    def CheckQuoteExists(self, quote):
        self.Execute("SELECT COUNT(*) FROM Quotes WHERE UPPER(Quote) = ?", (quote.upper()));
        count = self.cur.fetchone()[0];
        if count >= 1:
            return True;
        return False;

    def AddQuote(self, quote, username):
        userID = self.GetUserID(username);
        self.Execute("INSERT INTO Quotes (Quote, UserID) VALUES (?, ?)", (quote, userID));
        return;

    def DoesUserExist(self, username):
        username = username.lower();
        self.Execute("SELECT COUNT(*) FROM Users WHERE RegisteredName = ?", (username));
        count = self.cur.fetchone()[0];
        if count >= 1:
            return True;
        return False;

    def GetRegisteredName(self, username):
        username = username.lower();
        self.Execute("SELECT Users.RegisteredName FROM Users JOIN UserChannels ON Users.UserID = UserChannels.UserID WHERE UserChannels.DisplayName = ?", (username));
        return self.cur.fetchone()[0];

    def SetUserData(self, username, fieldName, value):
        username = username.lower();
        fieldName = fieldName.lower();#Case-insensitive
        value = str(value);#Ensure that all values are strings
        userID = self.GetUserID(username);
        if userID == -1:
            return -1;#Error: Not a registered user
        self.Execute("SELECT COUNT(*) FROM UserData WHERE UserID = ? AND lower(FieldName) = ?", (userID, fieldName));
        count = self.cur.fetchone()[0];
        if count >= 1:
            self.Execute("UPDATE UserData SET FieldValue = ? WHERE UserID = ? AND lower(FieldName) = ?", (value, userID, fieldName));
        else:
            self.Execute("INSERT INTO UserData (UserID, FieldName, FieldValue) VALUES (?, ?, ?)", (userID, fieldName, value));
        return 0;#Success

    def GetUserData(self, username, fieldName):
        username = username.lower();
        fieldName = fieldName.lower();#Case-insensitive
        userID = self.GetUserID(username);
        if userID == -1:
            return -1;#Error: Not a registered user;
        self.Execute("SELECT COUNT(*) FROM UserData WHERE UserID = ? AND lower(FieldName) = ?", (userID, fieldName));
        count = self.cur.fetchone()[0];
        if count == 0:
            return None;
        self.Execute("SELECT FieldValue FROM UserData WHERE UserID = ? AND lower(FieldName) = ?", (userID, fieldName));
        return self.cur.fetchone()[0];

    def DeleteUserData(self, username, fieldName):
        username = username.lower();
        fieldName = fieldName.lower();#Case-insensitive
        userID = self.GetUserID(username);
        if userID == -1:
            return -1;#Error: Not a registered user.
        self.Execute("SELECT COUNT(*) FROM UserData WHERE UserID = ? AND lower(FieldName) = ?", (userID, fieldName));
        count = self.cur.fetchone()[0];
        if count == 0:
            return -2;#Error: Field doesn't exist for user.
        self.Execute("DELETE FROM UserData WHERE UserID = ? AND lower(FieldName) = ?", (userID, fieldName));
        return 0;

    def Execute(self, command, params = ()):
        command = "{0}".format(command);
        if isinstance(params, tuple) == False:
            params = (params,);
        try:
            self.cur.execute(command, params);
            self.conn.commit();
        except Exception:
            Logger.error("Could not run SQLite command!");
        return;

    def close(self):
        self.conn.commit();
        self.conn.close();
        return;

