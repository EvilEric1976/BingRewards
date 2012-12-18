#!/usr/bin/env python2

from datetime import datetime

def __parseResultsArea(resultsArea):
    """
    Parses <div id="resultsArea">...</div> from Bing! history page
    Returns a list of queries (can be empty list)
    """
    startMarker = '<span class="query_t">'
    startMarkerLen = len(startMarker)

    history = []

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
        history.append(resultsArea[s:e])

        s = e + 4

    return history

def parse(page):
    """
    Parses Bing! history page and returns a set of queries for today
    Can be an empty set
    """
    if page is None: raise TypeError("page is None")
    if page.strip() == "": raise ValueError("page is empty")

    startMarker = '<div id="results_area">'
    endMarker   = '<div id="sidebar">'
    s = page.index(startMarker)
    s += len(startMarker)
    e = page.index(endMarker, s)

    return set(__parseResultsArea(page[s:e]))

def getBingHistoryTodayURL():
    """
    Returns URL to today's Bing! history
    i.e. "https://ssl.bing.com/profile/history?d=20121217"
    """
    BING_HISTORY_URL = "https://ssl.bing.com/profile/history?d="
    dtStr = datetime.now().strftime("%Y%m%d")
    return BING_HISTORY_URL + dtStr
