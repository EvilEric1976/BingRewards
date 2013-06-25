#!/usr/bin/env python

#
# developed by Sergey Markelov (2013)
#

from __future__ import with_statement

import cookielib
import random
import time
import urllib
import urllib2

import bingCommon
import bingFlyoutParser as bfp
import bingHistory
import helpers
from bingQueriesGenerator import BingQueriesGenerator, BING_NEWS_URL

# sleep that amound of seconds (can be float) + some random(0, SLEEP_BETWEEN_BING_QUERIES_SALT) milliseconds
SLEEP_BETWEEN_BING_QUERIES = 1.0
# this random number of milliseconds will be added to SLEEP_BETWEEN_BING_QUERIES to get the resulting sleep time
SLEEP_BETWEEN_BING_QUERIES_SALT = 3000

# extend urllib.addinfourl like it defines @contextmanager (to use with "with" keyword)
urllib.addinfourl.__enter__ = lambda self: self
urllib.addinfourl.__exit__  = lambda self, type, value, traceback: self.close()

class HTTPRefererHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        if not "Referer" in req.headers:
#             if req.get_host() == "www.bing.com":
#                 req.headers["Referer"] = "http://www.bing.com/"
#             else:
                req.headers["Referer"] = req.get_full_url()
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_302

class BingRewards:
    class RewardResult:
        def __init__(self, reward):
            if reward is None or not isinstance(reward, bfp.Reward):
                raise TypeError("reward is not of Reward type")

            self.o = reward
            self.isError = False
            self.message = ""
# action applied to the reward
            self.action  = bfp.Reward.Type.Action.WARN

    BING_FLYOUT_PAGE = "http://www.bing.com/rewardsapp/flyoutpage?style=v2"

    def __init__(self):
        cookies = cookielib.CookieJar()
        self.opener = urllib2.build_opener(#urllib2.HTTPSHandler(debuglevel = 1),     # be verbose on HTTPS
                                           #urllib2.HTTPHandler(debuglevel = 1),      # be verbose on HTTP
                                           HTTPRefererHandler,                       # add Referer header on redirect
                                           urllib2.HTTPCookieProcessor(cookies))     # keep cookies

    def requestFlyoutPage(self):
        """
        Returns bing.com flyout page
        This page shows what rewarding activity can be performed in
        order to earn Bing points
        """
        url = self.BING_FLYOUT_PAGE
        request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
        request.add_header("Referer", "http://www.bing.com/rewards/dashboard")
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        return page

    def getRewardsPoints(self):
        """
        Returns rewards points as int
        """
# report activity
        postFields = urllib.urlencode( { "url" : bingCommon.BING_URL, "V" : "web" } )
        url = "http://www.bing.com/rewardsapp/reportActivity"
        request = urllib2.Request(url, postFields, bingCommon.HEADERS)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        if len(page) == 0:
            raise Exception("Rewards points page is empty. That could mean you are not signed up for rewards with this account")

# parse activity page
        s = page.index("t.innerHTML='")
        s += len("t.innerHTML='")
        e = page.index("'", s)
        return int(page[s:e])

    def __processHit(self, reward):
        """Processes bfp.Reward.Type.Action.HIT and returns self.RewardResult"""
        res = self.RewardResult(reward)
        pointsEarned = self.getRewardsPoints()
        request = urllib2.Request(url = reward.url, headers = bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        pointsEarned = self.getRewardsPoints() - pointsEarned
# if HIT is against bfp.Reward.Type.RE_EARN_CREDITS - check if pointsEarned is the same to
# pointsExpected
        indCol = bfp.Reward.Type.Col.INDEX
        if reward.tp[indCol] == bfp.Reward.Type.RE_EARN_CREDITS[indCol]:
            matches = bfp.Reward.Type.RE_EARN_CREDITS[bfp.Reward.Type.Col.NAME].search(reward.name)
            pointsExpected = int(matches.group(1))
            if pointsExpected != pointsEarned:
                filename = helpers.dumpErrorPage(page)
                res.isError = True
                res.message = "Expected to earn " + str(pointsExpected) + " points, but earned " + \
                              str(pointsEarned) + " points. Check " + filename + " for further information"
        return res

    def __processSearch(self, reward):
        """Processes bfp.Reward.Type.Action.SEARCH and returns self.RewardResult"""

        BING_QUERY_URL = 'http://www.bing.com/search?q='
        BING_QUERY_SUCCESSFULL_RESULT_MARKER = '<div id="results_container">'

        res = self.RewardResult(reward)
        if reward.isAchieved():
            res.message = "This reward has been already achieved"
            return res

        indCol = bfp.Reward.Type.Col.INDEX
        if reward.tp[indCol] != bfp.Reward.Type.SEARCH_AND_EARN[indCol]:
            res.isError = True
            res.message = "Don't know how to process this search"
            return res

# get a set of queries from today's Bing! history
        url = bingHistory.getBingHistoryTodayURL()
        request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)
        history = bingHistory.parse(page)

# find out how many searches need to be performed
        matches = bfp.Reward.Type.SEARCH_AND_EARN_DESCR_RE.search(reward.description)
        rewardsCount    = int(matches.group(1))
        rewardCost      = int(matches.group(2))
        maxRewardsCount = int(matches.group(4))
        searchesCount = maxRewardsCount * rewardCost / rewardsCount

# adjust to the current progress
        searchesCount -= reward.progressCurrent * rewardCost

        request = urllib2.Request(url = BING_NEWS_URL, headers = bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

# generate a set of queries to run
        bingQueriesGenerator = BingQueriesGenerator(searchesCount, history)
        queries = bingQueriesGenerator.parseBingNews(page)
        if len(queries) < searchesCount:
            print "Warning: not enough queries to run were generated !"
            print "Requested:", searchesCount
            print "Generated:", len(bingQueriesGenerator.queries)

        successfullQueries = 0
        i = 1
        totalQueries = len(queries)

        for query in queries:
            if i > 1:
# sleep some time between queries (don't worry Bing! ;) )
                t = SLEEP_BETWEEN_BING_QUERIES + (random.uniform(0, SLEEP_BETWEEN_BING_QUERIES_SALT) / 1000)
                time.sleep(t)

            url = BING_QUERY_URL + urllib.quote_plus(query)

            print "%s - %2d/%2d - Requesting: %s" % (helpers.getLoggingTime(), i, totalQueries, url)

            request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
            with self.opener.open(request) as response:
                page = helpers.getResponseBody(response)

# check for the successfull marker
            if page.find(BING_QUERY_SUCCESSFULL_RESULT_MARKER) == -1:
                filename = helpers.dumpErrorPage(page)
                print "Warning! Query:"
                print "\t" + query
                print "returned no results, check " + filename + " file for more information"

            else:
                successfullQueries += 1

            i += 1

        if successfullQueries < searchesCount:
            res.message = str(successfullQueries) + " out of " + str(searchesCount) + " requests were successfully processed"
        else:
            res.message = "All " + str(successfullQueries) + " requests were successfully processed"

        return res

    def process(self, rewards):
        """
        Runs an action for each of rewards as described in self.RewardType
        returns results list of self.RewardResult objects
        """
        if rewards is None or not isinstance(rewards, list):
            raise TypeError("rewards is not an instance of list")

        results = []

        for r in rewards:
            if r.tp is None:
                action = bfp.Reward.Type.Action.WARN
            else:
                action = r.tp[bfp.Reward.Type.Col.ACTION]

            if action == bfp.Reward.Type.Action.HIT:
                res = self.__processHit(r)
            elif action == bfp.Reward.Type.Action.SEARCH:
                res = self.__processSearch(r)
            else:
                res = self.RewardResult(r)

            res.action = action
            results.append(res)

        return results

    def __printReward(self, reward):
        """Prints a reward"""
        print "name        : %s" % reward.name
        if reward.url != "":
            print "url         : %s" % reward.url
        if reward.progressMax != 0:
            print "progressCur : %d" % reward.progressCurrent
            print "progressMax : %d" % reward.progressMax
            print "progress %%  : %0.2f%%" % reward.progressPercentage()
        if reward.isDone:
            print "is done     : true"
        print "description : %s" % reward.description

    def printRewards(self, rewards):
        """
        Prints out rewards list
        throws TypeError if rewards is None or not instance of list
        """
        if rewards is None or not isinstance(rewards, list):
            raise TypeError("rewards is not an instance of list")

        i = 0
        total = len(rewards)
        for r in rewards:
            i += 1
            print "Reward %d/%d:" % (i, total)
            print "-----------"
            self.__printReward(r)
            print

    def __printResult(self, result):
        """Prints a result"""
        self.__printReward(result.o)
        if result.isError:
            print "   Error    :   true"
        print "   Message  : " + result.message
        print "   Action   : " + bfp.Reward.Type.Action.toStr(result.action)


    def printResults(self, results):
        """
        Prints out results list
        throws TypeError if results is None or not instance of list
        """
        if results is None or not isinstance(results, list):
            raise TypeError("results is not an instance of list")

        i = 0
        total = len(results)
        for r in results:
            i += 1
            print "Result %d/%d:" % (i, total)
            print "-----------"
            self.__printResult(r)
            print
