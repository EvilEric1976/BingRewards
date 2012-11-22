#!/usr/bin/env python2
"""
Bing! flyout page parser

Usage:
    from bingFlyoutParser import Reward, parseFlyoutPage
    ...
    bingRewards = BingRewards(FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
    bingRewards.authenticate()
    parseFlyoutPage(bingRewards.requestFlyoutPage(), BING_URL)
"""

import HTMLParser
import re

class Reward:
    class Type:
        class Action:
            PASS   = 0
            INFORM = 1
            HIT    = 2
            SEARCH = 3
            WARN   = 4

            @staticmethod
            def toStr(action):
                actions = ("pass", "inform", "hit", "search", "warn")
                return (actions[action])

        class Col:
            INDEX  = 0
            NAME   = 1
            ISRE   = 2
            ACTION = 3

        SEARCH_AND_EARN_DESCR_RE = re.compile("Earn (\d)+ credits? per (\d)+ Bing search(es)? up to (\d+) credits? a day")

#       Alias                Index Reward.name                          isRe?  Action

        RE_EARN_CREDITS   = (1,    re.compile("Earn (\d+) credits?"),   True,  Action.HIT)
        SEARCH_AND_EARN   = (2,    "Search and Earn",                   False, Action.SEARCH)
        YOUR_GOAL         = (3,    "Your goal",                         False, Action.INFORM)
        MAINTAIN_GOLD     = (4,    "Maintain Gold",                     False, Action.INFORM)
        REFER_A_FRIEND    = (5,    "Refer-A-Friend",                    False, Action.PASS)
        SEND_A_TWEET      = (6,    "Send a Tweet",                      False, Action.PASS)
        RE_EARNED_CREDITS = (7,    re.compile("Earned \d+ credits?"),   True,  Action.PASS)
        COMPLETED         = (8,    "Completed",                         False, Action.PASS)

        ALL = (RE_EARN_CREDITS, SEARCH_AND_EARN, YOUR_GOAL, MAINTAIN_GOLD,
               REFER_A_FRIEND, SEND_A_TWEET, RE_EARNED_CREDITS, COMPLETED)

    """A class to represent a Bing! reward"""
    def __init__(self):
        self.url = ""               # optional
        self.name = ""
        self.progressCurrent = 0    # optional
        self.progressMax = 0        # optional
        self.isDone = False         # optional - is set if progress is "Done"
        self.description = ""
        self.tp = None              # is one of self.Type if set

    def isAchieved(self):
        """
        Returns True if the reward is achieved.
        Applicable only if self.progressMax is not 0
        """
        return (self.isDone or self.progressMax != 0 and self.progressCurrent == self.progressMax)

    def progressPercentage(self):
        if self.progressMax == 0:
            return 0
        else:
            return (float(self.progressCurrent) / self.progressMax * 100)

def parseFlyoutPage(page, bing_url):
    """
    Parses a bing flyout page
    returns a list of Reward objects

    page - bing flyout page - see the class __doc__ for further information
    bing_url - url of bing main page - generally http://www.bing.com which will be
                added to Reward.url as a prefix if appropriate
    """
    if page is None: raise TypeError("page is None")
    if page.strip() == "": raise ValueError("page is empty")

    s = page.index('<div id="messageContainer">')
    e = page.index('<div id="bottomContainer">', s)
    parser = _HTMLRewardsParser(bing_url)
    parser.feed(page[s:e])
    parser.close()

    return parser.rewards

######################################################
# local classes & functions
######################################################
class _HTMLRewardsParser(HTMLParser.HTMLParser):
    """
    Gets Bing! flyout page starting from tag
    <div id="messageContainer"> to the tag
    <div id="bottomContainer">, excluding the last one

    Usage:
    parser = self.HTMLRewardsParser("http://www.bing.com")
    parser.feed(page[s:e])
    parser.close()

    then parser.rewards will contain a list of Reward objects
    """

    class ParsingStep:
        NONE             =   0    # not initialized
        LI_MAIN          =   1
        DIV_CONTENT      =   2
        DIV_STATUSBAR    =  20
        SPAN_TITLE       =  21    # if A_REWARD_URL doesn't exist, the data will be REWARD_NAME
        A_REWARD_URL     =  22    # optional, REWARD_NAME inside data if this tag exists
        SPAN_PROGRESS    =  23    # optional - contains REWARD_PROGRESS as 'CUR of MAX'
        DIV_MESSAGE      =  30    # REWARD_DESCRIPTION is in the data
        DIV_REDEEMGOAL   = 100    # exists only if REWARD_NAME is "Your goal"
        DIV_STATUS       = 110
        A_GOALLINK       = 111    # data is REWARD_NAME - "Your goal", then goes SPAN_PROGRESS
        SPAN_PROGRESS_YG = 112
        DIV_MESSAGE_YG   = 120    # if REWARD_NAME is "Your goal"
        DIV_TEXT_YG      = 121    # goes after DIV_MESSAGE_YG for REWARD_NAME "Your goal" and
                                    # data contains REWARD_DESCRIPTION

    def __init__(self, bing_url):
        """bing_url is the url of bing main page, generally - http://www.bing.com"""
        HTMLParser.HTMLParser.__init__(self)
        if bing_url is None or bing_url == "":
            raise TypeError("bing_url is empty")
        while bing_url.endswith("/"):
            bing_url = bing_url[:-1]
        self.bing_url = bing_url
        self.rewards = []
        self.step = self.ParsingStep.NONE

    def handle_starttag(self, tag, attrs):
        if tag == 'ul':
            self.reward = Reward()
        elif tag == 'li':
            for attr in attrs:
                if attr[0] == 'class' and attr[1] == 'main':
                    self.step = self.ParsingStep.LI_MAIN
        elif tag == 'div':
            for attr in attrs:
                if attr[0] == 'class':
                    if attr[1] == 'content':
                        if self.step == self.ParsingStep.LI_MAIN:
                            self.step = self.ParsingStep.DIV_CONTENT
                    elif attr[1] == 'statusbar':
                        if self.step == self.ParsingStep.DIV_CONTENT:
                            self.step = self.ParsingStep.DIV_STATUSBAR
                    elif attr[1] == 'message':
                        if self.step == self.ParsingStep.SPAN_PROGRESS or \
                            self.step == self.ParsingStep.A_REWARD_URL or \
                            self.step == self.ParsingStep.SPAN_TITLE:
                                self.step = self.ParsingStep.DIV_MESSAGE
                        elif self.step == self.ParsingStep.SPAN_PROGRESS_YG:
                            self.step = self.ParsingStep.DIV_MESSAGE_YG
                    elif attr[1] == 'redeemgoal':
                        if self.step == self.ParsingStep.DIV_CONTENT:
                            self.step = self.ParsingStep.DIV_REDEEMGOAL
                    elif attr[1] == 'status':
                        if self.step == self.ParsingStep.DIV_REDEEMGOAL:
                            self.step = self.ParsingStep.DIV_STATUS
                    elif attr[1] == 'text':
                        if self.step == self.ParsingStep.DIV_MESSAGE_YG:
                            self.step = self.ParsingStep.DIV_TEXT_YG
        elif tag == 'span':
            for attr in attrs:
                if attr[0] == 'class':
                    if attr[1] == 'title':
                        if self.step == self.ParsingStep.DIV_STATUSBAR:
                            self.step = self.ParsingStep.SPAN_TITLE
                    elif attr[1] == 'progress':
                        if self.step == self.ParsingStep.SPAN_TITLE or \
                            self.step == self.ParsingStep.A_REWARD_URL:
                                self.step = self.ParsingStep.SPAN_PROGRESS
                        elif self.step == self.ParsingStep.A_GOALLINK:
                            self.step = self.ParsingStep.SPAN_PROGRESS_YG
        elif tag == 'a':
            if self.step == self.ParsingStep.SPAN_TITLE:
                self.step = self.ParsingStep.A_REWARD_URL
                for attr in attrs:
                    if attr[0] == 'href':
                        self.reward.url = attr[1].strip()
            elif self.step == self.ParsingStep.DIV_STATUS:
                self.step = self.ParsingStep.A_GOALLINK

    def handle_endtag(self, tag):
        if tag == 'ul':
# add self.bing_url prefix to the reward's url if needed
            if self.reward.url != "":
                if self.reward.url.startswith("/"):
                    self.reward.url = self.bing_url + self.reward.url
            self.assignRewardType()
# append the reward to the list of rewards
            self.rewards.append(self.reward)
            self.reward = Reward()

    def handle_data(self, data):
        if self.step == self.ParsingStep.SPAN_TITLE:
            if data.lower() == 'maintain gold':
                if self.reward.name == "":
                    self.reward.name = data.strip()
        elif self.step == self.ParsingStep.A_REWARD_URL:
            if self.reward.name == "":
                self.reward.name = data.strip()
        elif self.step == self.ParsingStep.SPAN_PROGRESS or \
                self.step == self.ParsingStep.SPAN_PROGRESS_YG:
            if self.reward.progressMax == 0 and not self.reward.isDone:
                if data.lower() == 'done':
                    self.reward.isDone = True
                else:
                    progress = data.strip().split(' of ', 1)
                    self.reward.progressCurrent = int(progress[0])
                    self.reward.progressMax = int(progress[1])
        elif self.step == self.ParsingStep.DIV_MESSAGE:
# if '<a ' tag exists - that's probably the last tag - get rid of it
            if self.reward.description == "":
                s = data.find("<a ")
                self.reward.description = data[:s].strip() if s != -1 else data.strip()
        elif self.step == self.ParsingStep.A_GOALLINK:
            if self.reward.name == "":
                self.reward.name = data.strip()
        elif self.step == self.ParsingStep.DIV_TEXT_YG:
            if self.reward.description == "":
                self.reward.description = data.strip()

    def close(self):
        HTMLParser.HTMLParser.close(self)
        if hasattr(self, "reward"):
            del self.reward

    def assignRewardType(self):
        """Assigns a reward type to self.reward based on self.reward.name"""
        for t in Reward.Type.ALL:
            if t[Reward.Type.Col.ISRE]:         # regex
                if t[Reward.Type.Col.NAME].search(self.reward.name):
                    self.reward.tp = t
                    return
            elif t[Reward.Type.Col.NAME] == self.reward.name:
                self.reward.tp = t
                return
