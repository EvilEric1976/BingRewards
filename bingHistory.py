#!/usr/bin/env python2

#
# developed by Sergey Markelov (2013)
#

from datetime import datetime
from HTMLParser import HTMLParser
import helpers

def __parseResultsArea1(resultsArea):
    """
    Parses <div id="resultsArea">...</div> from Bing! history page
    Returns a list of queries (can be empty list)
    """
    startMarker = '<span class="query_t">'
    startMarkerLen = len(startMarker)

    history = []
    htmlParser = HTMLParser()

    s = 0
    while True:
        s = resultsArea.find(startMarker, s)
        if s == -1: break

# locate a query
        s += startMarkerLen
        s = resultsArea.index("<a ", s)
        s += 3
        s = resultsArea.index(">", s)
        s += 1
        e = resultsArea.index("</a>", s)

# resultsArea[s:e] now contains a query from history
        history.append(htmlParser.unescape(resultsArea[s:e]).strip())

        s = e + 4

    return history

def __isApproach(page, startMarker, endMarker):
    s = page.find(startMarker)
    if s == -1: return (False, 0, 0)
    s += len(startMarker)
    e = page.index(endMarker, s)
    return (True, s, e)

def __parseResultsArea2(resultsArea):
    """
    Parses results from Bing! history page
    Returns a list of queries (can be empty list)
    """
    startMarker = '<span class="sh_item_qu_query">'
    startMarkerLen = len(startMarker)

    history = []
    htmlParser = HTMLParser()

    s = 0
    while True:
        s = resultsArea.find(startMarker, s)
        if s == -1: break

# locate a query
        s += startMarkerLen
        e = resultsArea.index("</span>", s)

# resultsArea[s:e] now contains a query from history
        history.append(htmlParser.unescape(resultsArea[s:e]).strip())

        s = e + 7

    return history

def parse(page):
    """
    Parses Bing! history page and returns a set of queries for today
    Can be an empty set
    """
    if page is None: raise TypeError("page is None")
    if page.strip() == "":
        print "-------------------------------"
        print "Warning: Bing! history is empty"
        print "-------------------------------"
        print
        return set()

    (isIt, s, e) = __isApproach(page, '<div id="results_area">', '<div id="sidebar">')
    if isIt:
        return set(__parseResultsArea1(page[s:e]))

    (isIt, s, e) = __isApproach(page, '<ul class="sh_dayul">', '</ul>')
    if isIt:
        return set(__parseResultsArea2(page[s:e]))

    return set()

#    filename = helpers.dumpErrorPage(page)
#    raise NotImplementedError("No markers were found for the history. Check " + helpers.RESULTS_DIR + "/" + filename)

def getBingHistoryTodayURL():
    """
    Returns URL to today's Bing! history
    i.e. "https://ssl.bing.com/profile/history?d=20121217"
    """
    BING_HISTORY_URL = "https://ssl.bing.com/profile/history?d="
    dtStr = datetime.now().strftime("%Y%m%d")
    return BING_HISTORY_URL + dtStr
