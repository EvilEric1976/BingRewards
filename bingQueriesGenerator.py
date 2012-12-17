#!/usr/bin/env python2
"""
Bing! queries generator

Usage:
    from bingQueriesGenerator import parseBingNews
    ...
    bool = parseBingNews(newsPage, numberOfQueries, maxQueryLen = MAX_QUERY_LEN)
"""

import re

BING_NEWS_URL = "http://www.bing.com/news?q=world+news"
MAX_QUERY_LEN = 50

class BingQueriesGenerator:
    def __init__(self):
        self.queries = set()
# will be set in self.parseBingNews()
        self.numberOfQueries = 0

    def __addQueriesFromString(self, inputString):
        """
        Adds all possible query compbinations which can be constructed from
        inputString to self.queries

        Returns False if len(self.queries) >= self.numberOfQueries
        meaning no more adding is necessary
        """
        e = len(inputString)
        while(e > 1):
            self.queries.add(inputString[:e])
            if len(self.queries) >= self.numberOfQueries:
                return False
            e -= 1
            while(inputString[-1] == ' '): e -= 1

        return True

    def __splitAndAdd(self, inputString, maxQueryLen):
        """
        Splits inputString into smaller parts each of around maxQueryLen in length
        and calls __addQueriesFromString on each of the smaller parst

        Returns False if len(self.queries) >= self.numberOfQueries
        meaning no more adding is necessary
        """
        s = 0
        resLen = len(inputString)
        e = resLen
        while True:
            while e - s > maxQueryLen:
                t = inputString.rfind(" ", s, e)
                if t == -1: break
                e = t

            if not self.__addQueriesFromString(inputString[s:e]):
                return False

            s = e + 1
            if s >= resLen:
                break
            e = resLen

        return True

    def __generateQueries(self, newsResultSet, maxQueryLen):
        """
        Generates up to self.numberOfQueries queries from newsResultSet

        Returns True if self.numberOfQueries queries were generated in
        self.queries set
        """
        snippetMarkerBegin = '<span class="sn_snip">'
        snippetMarkerBeginLen = len(snippetMarkerBegin)
        snippetMarkerEnd = '</span>'
        snippetMarkerEndLen = len(snippetMarkerEnd)

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
            inputString, numberOfSubsMade = htmlEntities.subn("", newsResultSet[s:e])
            inputString, numberOfSubsMade = trashChars.subn("", inputString)
            inputString = inputString.strip().replace("  ", " ")

            if not self.__splitAndAdd(inputString, maxQueryLen):
                return True

            s = e + 1 + snippetMarkerEndLen

        return False

    def parseBingNews(self, newsPage, numberOfQueries, maxQueryLen = MAX_QUERY_LEN):
        """
        parses Bing! news page and generates a set of unique queries to run on Bing!
        A query is considered to be unique if it distingueshes from any other query at
        least in a meaning letter. Where meaning letter is any ASCII charecter, but
        terminators (space, comma, colon, etc.)

        Url good enough to get Bing! news
        http://www.bing.com/news?q=world+news

        param newsPage a news page downloaded from Bing! news
        param numberOfQueries how many queries a user wants to perform
        param maxQueryLen the maximum query length

        returns a set of queries - self.queries
        """
        if newsPage is None: raise TypeError("newsPage is None")
        if newsPage.strip() == "": raise ValueError("newsPage is empty")
        if numberOfQueries <= 0:
            raise ValueError("numberOfQueries should be more than 0, but it is " + numberOfQueries)

        s = newsPage.index('<div class="NewsResultSet">')
        e = newsPage.index('<div class="news_gt">', s)

        self.numberOfQueries = numberOfQueries
        self.__generateQueries(newsPage[s:e], maxQueryLen)

        return self.queries
