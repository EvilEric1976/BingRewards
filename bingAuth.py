#
# developed by Sergey Markelov (2013)
#

import HTMLParser
import random
import urllib
import urllib2

import bingCommon
import helpers

class AuthenticationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class HTMLFormInputsParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.inputs = {}

    def handle_starttag(self, tag, attrs):
        if tag == 'input':
            name = value = ''
            for attr in attrs:
                if attr[0] == 'name':
                    name = attr[1]
                elif attr[0] == 'value':
                    value = attr[1]
            if name != '' and value != '':
                self.inputs[name] = value.encode("utf-8")

class BingAuth:
    def __init__(self, opener):
        """
        @param opener is an instance of urllib2.OpenerDirector
        """
        if opener is None or not isinstance(opener, urllib2.OpenerDirector):
            raise TypeError("opener is not an instance of urllib2.OpenerDirector")

        self.opener = opener

    def __authenticateFacebook(self, login, password):
        """
        Authenticates a user on bing.com with his/her Facebook account.

        throws AuthenticationError if authentication can not be passed
        throws HTMLParser.HTMLParseError
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
        BING_REQUEST_PERMISSIONS = "http://www.bing.com/fd/auth/signin?action=interactive&provider=facebook&return_url=http%3a%2f%2fwww.bing.com%2f&src=EXPLICIT&perms=read_stream%2cuser_photos%2cfriends_photos&sig="
#        print "Requesting bing.com"

# request http://www.bing.com
        request = urllib2.Request(url = bingCommon.BING_URL, headers = bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

# get connection URL for provider Facebook
        s = page.index('"Facebook":"')
        s += len('"Facebook":"')
        e = page.index('"', s)
        url = page[s:e]
        s = url.index('sig=')
        s += len('sig=')
        e = url.find('&', s)
        if e == -1:
            e = len(url)
        url = BING_REQUEST_PERMISSIONS + url[s:e]

#        print "Now requesting facebook authentication page"

# request FACEBOOK_CONNECT_ORIGINAL_URL
        request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            referer = response.geturl()
# get Facebook authenctication form action url
            page = helpers.getResponseBody(response)

        s = page.index('<form id="login_form"')
        s = page.index('action="', s)
        s += len('action="')
        e = page.index('"', s)
        url = page[s:e]

# relative url? add url from the previous response
        if url[0:1] == "/":
            url = referer + url

# find all html elements which need to be sent to the server
        s = page.index('>', s)
        s += 1
        e = page.index('</form>')

        parser = HTMLFormInputsParser()
        parser.feed(page[s:e].decode("utf-8"))
        parser.close()
        parser.inputs["email"] = login
        parser.inputs["pass"] = password

#        print "Now passing facebook authentication"

# pass facebook authentication
        postFields = urllib.urlencode(parser.inputs)
        request = urllib2.Request(url, postFields, bingCommon.HEADERS)
        request.add_header("Referer", referer)
        with self.opener.open(request) as response:
            url = response.geturl()
# if that's not bingCommon.BING_URL => authentication wasn't pass => write the page to the file and report
            if url.find(bingCommon.BING_URL) == -1:
                try:
                    filename = helpers.dumpErrorPage(helpers.getResponseBody(response))
                    s = "check " + filename + " file for more information"
                except IOError:
                    s = "no further information could be provided - failed to write a file into " + \
                        helpers.RESULTS_DIR + " subfolder"
                raise AuthenticationError("Authentication has not been passed:\n" + s)

    def __authenticateLive(self, login, password):
        """
        Authenticates a user on bing.com with his/her Live account.

        throws AuthenticationError if authentication can not be passed
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
#        print "Requesting bing.com"

# request http://www.bing.com
        request = urllib2.Request(url = bingCommon.BING_URL, headers = bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

# get connection URL for provider Live
        s = page.index('"WindowsLiveId":"')
        s += len('"WindowsLiveId":"')
        e = page.index('"', s)
        url = page[s:e]

        request = urllib2.Request(url = url, headers = bingCommon.HEADERS)
        request.add_header("Referer", bingCommon.BING_URL)
        with self.opener.open(request) as response:
            referer = response.geturl()
# get Facebook authenctication form action url
            page = helpers.getResponseBody(response)

# get PPFT parameter
        s = page.index("sFTTag")
        s = page.index('value="', s)
        s += len('value="')
        e = page.index('"', s)
        PPFT = page[s:e]

# get PPSX parameter
        s = page.index(",g:'")
        s += len(",g:'")
        e = page.index("'", s)
        PPSX = page[s:e]

# get sso parameter
        s = page.index(",W:")
        s += len(",W:")
        e = page.index(",", s)
        sso = int(page[s:e])

# generate ClientLoginTime
        clt = 20000 + int(random.uniform(0, 1000))

# generate RenderCompleteTime
        renderTime = 130 + int(random.uniform(0, 100))

# generate ResourcesCompleteTime
        resourcesTime = renderTime + int(random.uniform(2, 5))

# generate ResourcesCompleteTime
        PLT = 870 + int(random.uniform(0, 250))

# get url to post data to
        s = page.index(",urlPost:'")
        s += len(",urlPost:'")
        e = page.index("'", s)
        url = page[s:e]

        postFields = urllib.urlencode({
            "login"         : login,
            "passwd"        : password,
            "SI"            : "Sign in",
            "type"          : "11",
            "PPFT"          : PPFT,
            "PPSX"          : PPSX,
            "idsbho"        : "1",
            "LoginOptions"  : "3",
            "sso"           : str(sso),
            "NewUser"       : "1",
            "i1"            : "0",                  # ClientUserSaved
            "i2"            : "1",                  # ClientMode
            "i3"            : str(clt),             # ClientLoginTime
            "i4"            : "0",                  # ClientExplore
            "i7"            : "0",                  # ClientOTPRequest
            "i12"           : "1",                  # LoginUsedSSL
            "i13"           : "0",                  # ClientUsedKMSI
            "i14"           : str(renderTime),      # RenderCompleteTime
            "i15"           : str(resourcesTime),   # RenderCompleteTime
            "i16"           : str(PLT),             # PLT
            "i17"           : "0",                  # SRSFailed
            "i18"           : "__Login_Strings|1,__Login_Core|1," # SRSSuccess
        })

        # get Passport page

        request = urllib2.Request(url, postFields, bingCommon.HEADERS)
        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        s = page.index("<form ")
        e = page.index("</form>", s)
        e += len("</form>")

        parser = HTMLFormInputsParser()
        parser.feed(page[s:e].decode("utf-8"))
        parser.close()
        postFields = urllib.urlencode(parser.inputs)

        # finish passing authentication

        url = "http://www.bing.com/Passport.aspx?requrl=http%3a%2f%2fwww.bing.com%2f&wa=wsignin1.0"
        request = urllib2.Request(url, postFields, bingCommon.HEADERS)
        request.add_header("Origin", "https://login.live.com")

        with self.opener.open(request) as response:
            page = helpers.getResponseBody(response)

        url = bingCommon.BING_URL
        request = urllib2.Request(url, postFields, bingCommon.HEADERS)
        request.add_header("Referer", "http://www.bing.com/Passport.aspx?requrl=http%3a%2f%2fwww.bing.com%2f&wa=wsignin1.0")
        with self.opener.open(request) as response:
            url = response.geturl()

# if that's not bingCommon.BING_URL => authentication wasn't pass => write the page to the file and report
            if url.find(bingCommon.BING_URL) == -1:
                try:
                    filename = helpers.dumpErrorPage(helpers.getResponseBody(response))
                    s = "check " + filename + " file for more information"
                except IOError:
                    s = "no further information could be provided - failed to write a file into " + \
                        helpers.RESULTS_DIR + " subfolder"
                raise AuthenticationError("Authentication has not been passed:\n" + s)

    def authenticate(self, authType, login, password):
        """
        throws ValueError if login or password is None
        throws AuthenticationError
        """
        if login is None: raise ValueError("login is None")
        if password is None: raise ValueError("password is None")

        try:
            authMethod = getattr(self, "_" + self.__class__.__name__ + "__authenticate" + authType)
            authMethod(login, password)
        except AttributeError:
            raise AuthenticationError("Configuration Error: authentication type " + authType + " is not supported")
