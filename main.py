#!/usr/bin/env python

#
# developed by Sergey Markelov (2013)
#

import HTMLParser
import getopt
import sys
import urllib2
import xml.etree.ElementTree as et

from bingAuth import BingAuth, AuthenticationError
from bingRewards import BingRewards
import bingCommon
import bingFlyoutParser as bfp
import helpers

verbose = False

def earnRewards(authType, login, password):
    """Earns Bing! reward points and returnes how many points has been earned"""
    try:
        if authType is None: raise ValueError("authType is None")
        if login is None: raise ValueError("login is None")
        if password is None: raise ValueError("password is None")

        bingRewards = BingRewards()
        bingAuth    = BingAuth(bingRewards.opener)
        bingAuth.authenticate(authType, login, password)
        points  = bingRewards.getRewardsPoints()
        rewards = bfp.parseFlyoutPage(bingRewards.requestFlyoutPage(), bingCommon.BING_URL)

        if verbose:
            bingRewards.printRewards(rewards)
        results = bingRewards.process(rewards)

        if verbose:
            print
            print "-" * 80
            print

        bingRewards.printResults(results, verbose)

        newPoints = bingRewards.getRewardsPoints()
        pointsEarned = newPoints - points
        print
        print "%s - %s" % (authType, login)
        print
        print "Points before: %d" % points
        print "Points after:  %d" % newPoints
        print "Points earned: %d" % pointsEarned

        print
        print "-" * 80

        return pointsEarned

    except AuthenticationError, e:
        print "AuthenticationError:\n%s" % e

    except HTMLParser.HTMLParseError, e:
        print "HTMLParserError: %s" % e

    except urllib2.HTTPError, e:
        print "The server couldn't fulfill the request."
        print "Error code: ", e.code

    except urllib2.URLError, e:
        print "Failed to reach the server."
        print "Reason: ", e.reason

def usage():
    print "Usage:"
    print "    -h, --help               show this help"
    print "    -f, --configFile=file    use specific config file. Default is config.xml"
    print "    -v, --verbose            print verbose output"

if __name__ == "__main__":
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hf:v", ["help", "configFile=", "verbose"])
    except getopt.GetoptError, e:
        print "getopt.GetoptError: %s" % e
        usage()
        sys.exit(1)

    configFile = "config.xml"
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-f", "--configFile"):
            configFile = a
        elif o in ("-v", "--verbose"):
            verbose = True
        else:
            raise NotImplementedError("option '" + o + "' is not implemented")

    print "%s - script started" % helpers.getLoggingTime()
    print "-" * 80
    print

    helpers.createResultsDir(__file__)

    try:
        tree = et.parse(configFile)
    except IOError, e:
        print "IOError: %s" % e
        sys.exit(2)

    totalPoints = 0
    root = tree.getroot()
    for accounts in root.findall("accounts"):
        for account in accounts.findall("account"):
            isDisabled = True if account.get("disabled", "false").lower() == "true" else False
            if isDisabled:
                continue
            accountType = account.get("type")
            login = account.find("login").text
            password = account.find("password").text
            totalPoints += earnRewards(accountType, login, password)

    print "Total points earned: %d" % totalPoints
    print
    print "%s - script ended" % helpers.getLoggingTime()
