#!/usr/bin/env python2
"""
Bing! queries generator

Generates a list of search strings long enough to query not lesser than
the passed number of times. A query is considered to be unique if it
distingueshes from any other query at least in a meaning letter. Where
meaning letter is any charecter, but terminators (space, comma, colon, etc.)

Usage:
    from bingQueriesGenerator import parseBingNews
    ...
    strings = parseBingNews(newsPage, numberOfQueries, maxQueryLen = MAX_QUERY_LEN)
"""

import re

BING_NEWS_URL = "http://www.bing.com/news?q=world+news"
MAX_QUERY_LEN = 50

def __appendResults(strings, res, maxQueryLen):
    s = 0
    resLen = len(res)
    e = resLen
    while True:
        while e - s > maxQueryLen:
            t = res.rfind(" ", s, e)
            if t == -1: break
            e = t

        strings.append(res[s:e])
        s = e + 1
        if s >= resLen:
            break
        e = resLen

def __getStrings(newsResultSet, numberOfQueries, maxQueryLen):
    snippetMarkerBegin = '<span class="sn_snip">'
    snippetMarkerBeginLen = len(snippetMarkerBegin)
    snippetMarkerEnd = '</span>'
    snippetMarkerEndLen = len(snippetMarkerEnd)

    strings = []

    htmlEntities = re.compile("&\w+;")
    trashChars = re.compile("[^\w\d ]")

    s = 0
    while True:
        s = newsResultSet.find(snippetMarkerBegin, s)
        if s == -1: break
        s += snippetMarkerBeginLen
        e = newsResultSet.index(snippetMarkerEnd, s)

# don't include the last "..." charecter
        e -= 1

# get rid of unrelated stuff
        res, numberOfSubsMade = htmlEntities.subn("", newsResultSet[s:e])
        res, numberOfSubsMade = trashChars.subn("", res)
        res = res.replace("  ", " ")

        __appendResults(strings, res, maxQueryLen)

        s = e + 1 + snippetMarkerEndLen

    return strings

def parseBingNews(newsPage, numberOfQueries, maxQueryLen = MAX_QUERY_LEN):
    """
    parses Bing! news page and returns a list of strings long enough to query not
    lesser than the passed number of times. A query is considered to be unique if it
    distingueshes from any other query at least in a meaning letter. Where meaning
    letter is any charecter, but terminators (space, comma, colon, etc.)

    Url good enough to get Bing! news
    http://www.bing.com/news?q=world+news

    param newsPage a news page downloaded from Bing! news
    param numberOfQueries how many queries a user wants to perform
    param maxQueryLen the maximum query length (to limit each string in the list of returning strings)

    returns a list of strings to query not lesser than numberOfQueries number of
    times
    """
    if newsPage is None: raise TypeError("newsPage is None")
    if newsPage.strip() == "": raise ValueError("newsPage is empty")
    if numberOfQueries <= 0:
        raise ValueError("numberOfQueries should be more than 0, but it is " + numberOfQueries)

    s = newsPage.index('<div class="NewsResultSet">')
    e = newsPage.index('<div class="news_gt">', s)

    strings = __getStrings(newsPage[s:e], numberOfQueries, maxQueryLen)
    i = 1
    for s in strings:
        print i, s
        i += 1

    raise RuntimeError("good")
