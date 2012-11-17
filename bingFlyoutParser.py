import HTMLParser

#!/usr/bin/env python2
class Reward:
    def __init__(self):
        self.url = ""               # optional
        self.name = ""
        self.progressCurrent = 0    # optional
        self.progressMax = 0        # optional
        self.isDone = False         # optional - is set if progress is "Done"
        self.description = ""

    def isAchieved(self):
        """
        Returns True if the reward is achieved.
        Applicable only if self.progressMax is not 0
        """
        return (self.isDone or self.progressMax != 0 and self.progressCurrent == self.progressMax)

class BingFlyoutParser:
    """A class to work with Bing! flyout page"""
    class HTMLRewardsParser(HTMLParser.HTMLParser):
        """
        Gets Bing! flyout page starting from tag
        <div id="messageContainer"> to the tag
        <div id="bottomContainer">, excluding the last one
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

        def __init__(self):
            HTMLParser.HTMLParser.__init__(self)
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
                            self.reward.url = attr[1]
                elif self.step == self.ParsingStep.DIV_STATUS:
                    self.step = self.ParsingStep.A_GOALLINK

        def handle_endtag(self, tag):
            if tag == 'ul':
                self.rewards.append(self.reward)
                self.reward = Reward()

        def handle_data(self, data):
            if self.step == self.ParsingStep.SPAN_TITLE:
                if data.lower() == 'maintain gold':
                    if self.reward.name == "":
                        self.reward.name = data
            elif self.step == self.ParsingStep.A_REWARD_URL:
                if self.reward.name == "":
                    self.reward.name = data
            elif self.step == self.ParsingStep.SPAN_PROGRESS or \
                    self.step == self.ParsingStep.SPAN_PROGRESS_YG:
                if data.lower() == 'done':
                    self.reward.isDone = True
                else:
                    if self.reward.progressMax == 0 and not self.reward.isDone:
                        progress = data.split(' of ', 1)
                        self.reward.progressCurrent = int(progress[0])
                        self.reward.progressMax = int(progress[1])
            elif self.step == self.ParsingStep.DIV_MESSAGE:
# if '<a ' tag exists - that's probably the last tag - get rid of it
                if self.reward.description == "":
                    s = data.find("<a ")
                    self.reward.description = data[:s] if s != -1 else data
            elif self.step == self.ParsingStep.A_GOALLINK:
                if self.reward.name == "":
                    self.reward.name = data
            elif self.step == self.ParsingStep.DIV_TEXT_YG:
                if self.reward.description == "":
                    self.reward.description = data

        def close(self):
            HTMLParser.HTMLParser.close(self)
            if hasattr(self, "reward"):
                del self.reward

    def __init__(self):
        self.rewards = []           # will be set in self.parse()

    def parse(self, page):
        if page is None:
            raise TypeError("page is None")

        s = page.index('<div id="messageContainer">')
        e = page.index('<div id="bottomContainer">', s)
        parser = self.HTMLRewardsParser()
        parser.feed(page[s:e])
        parser.close()

        self.rewards = parser.rewards

    def printRewards(self):
        i = 1
        for r in self.rewards:
            print "Reward %d:" % i
            print "-----------"
            print "name        : %s" % r.name
            if r.url != "":
                print "url         : %s" % r.url
            if r.progressMax != 0:
                print "progressCur : %d" % r.progressCurrent
                print "progressMax : %d" % r.progressMax
                print "progress %%  : %0.2f%%" % (float(r.progressCurrent) / r.progressMax * 100)
            if r.isDone:
                print "is done     : true"
            print "description : %s" % r.description
            print
            i += 1
