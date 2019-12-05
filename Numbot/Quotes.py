from Logger import Logger, colors;
from functools import wraps;
import math;
import random;
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

def prefix(pref):
    def prefix_decorator(func):
        @wraps(func)
        def prefixwrapper(*args):
            func(*args)
        prefixwrapper.__prefixed__ = pref
        return prefixwrapper
    return prefix_decorator

class Quotes:

    @accesslvl(0)
    def quote(bot, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Returns a selected or random quote.

        Usage: !quote [(# | search term [#<#>])]
        """
        quoteCount = sqlite.GetQuoteCount();
        quoteNum = random.randint(1, quoteCount);
        quote = sqlite.GetQuoteByRow(quoteNum);
        if len(msg) >= 1:
            parseAsString = False;
            if len(msg) == 1:
                try:
                    tempQuoteNum = int(msg[0]);
                    if tempQuoteNum > 0 and tempQuoteNum <= quoteCount:
                        quoteNum = tempQuoteNum;
                except ValueError:
                    parseAsString = True;
            else:
                parseAsString = True;
            if parseAsString:
                searchString = " ".join(msg);
                searchCount = -1;
                if msg[-1][0] == '#':
                    searchString = " ".join(msg[:-1]);
                    try:
                        searchCount = int(msg[-1][1:]);
                    except ValueError:
                        searchCount = -1;
                quoteBuf = sqlite.GetQuoteBySearch(searchString, searchCount);
                if quoteBuf != "":
                    quote = quoteBuf;
                    quoteNum = sqlite.GetQuoteNumber(quote);
            else:
                quote = sqlite.GetQuoteByRow(quoteNum);
        message = "{}/{}: {}".format(quoteNum, quoteCount, quote);
        bot.chat(sock, sendTo, message);
        return;

    @accesslvl(2)
    def addquote(bot, accesslvl, sock, sqlite, sender, receiver, sendTo, msg):
        """
        Adds a quote to the database.

        Usage: !addquote [quote]
        """
        message = "";
        if len(msg) == 0:
            message = "You must enter a quote to add, {}!".format(sender);
        else:
            quote = " ".join(msg);
            quoteExists = sqlite.CheckQuoteExists(quote);
            if quoteExists:
                message = "That quote already exists, {}!".format(sender);
            else:
                sqlite.AddQuote(quote, sender);
                quoteCount = sqlite.GetQuoteCount();
                message = "Quote #{} successfully added.".format(quoteCount);
        bot.chat(sock, sendTo, message);
        return;