#!/usr/bin/env python2
import StringIO
import zlib
import gzip
import urllib
import urllib2
import HTMLParser
import cookielib
from bingFlyoutParser import BingFlyoutParser

ERROR_HTML = "error.html"
FACEBOOK_EMAIL = "ef_shade@mail.ru"
FACEBOOK_PASSWORD = "/b6R8iFvI8CkjQp{"
BING_URL = 'http://www.bing.com'

class AuthenticationError(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)

class HTTPRefererHandler(urllib2.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        if not "Referer" in req.headers:
#             if req.get_host() == "www.bing.com":
#                 req.headers["Referer"] = "http://www.bing.com/"
#             else:
                req.headers["Referer"] = req.get_full_url()
        return urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)

    http_error_301 = http_error_303 = http_error_307 = http_error_302

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

def getResponseBody(response):
    """ Returns response.read(), but does gzip deflate if appropriate"""

    encoding = response.info().get("Content-Encoding")

    if encoding in ("gzip", "x-gzip", "deflate"):
        page = response.read()
        if encoding == "deflate":
            return zlib.decompress(page)
        else:
            fd = StringIO.StringIO(page)
            try:
                data = gzip.GzipFile(fileobj = fd)
                try:     content = data.read()
                finally: data.close()
            finally:
                fd.close()
            return content
    else:
        return response.read()

class BingRewards:
    BING_REQUEST_PERMISSIONS = "http://www.bing.com/fd/auth/signin?action=interactive&provider=facebook&return_url=http%3a%2f%2fwww.bing.com%2f&src=EXPLICIT&perms=read_stream%2cuser_photos%2cfriends_photos&sig="
    BING_FLYOUT_PAGE = "http://www.bing.com/rewardsapp/flyoutpage?style=v2"
# common headers for all requests
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-us,en;q=0.5",
        "Accept-Charset": "utf-8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, facebook_email, facebook_password):
        self.facebook_email = facebook_email
        self.facebook_password = facebook_password
# bingMainUrl will be set in the end of self.authenticate() method
        self.bingMainUrl = None
        cookies = cookielib.CookieJar()
        self.opener = urllib2.build_opener(#urllib2.HTTPSHandler(debuglevel = 1),     # be verbose on HTTPS
                                           #urllib2.HTTPHandler(debuglevel = 1),      # be verbose on HTTP
                                           HTTPRefererHandler,                       # add Referer header on redirect
                                           urllib2.HTTPCookieProcessor(cookies))     # keep cookies

    def authenticate(self):
        """
        Authenticates a user on bing.com with his/her Facebook account.
        FACEBOOK_EMAIL and FACEBOOK_PASSWORD for this class must be set to appropriate values.

        throws AuthenticationError if authentication can not be passed
        throws HTMLParser.HTMLParseError
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
#        print "Requesting bing.com"

# request http://www.bing.com
        request = urllib2.Request(url = BING_URL, headers = self.HEADERS)
        response = self.opener.open(request)
        try:     page = getResponseBody(response)
        finally: response.close()

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
        url = self.BING_REQUEST_PERMISSIONS + url[s:e]

#        print "Now requesting facebook authentication page"

# request FACEBOOK_CONNECT_ORIGINAL_URL
        request = urllib2.Request(url = url, headers = self.HEADERS)
        request.add_header("Referer", BING_URL)
        response = self.opener.open(request)
        try:
            referer = response.geturl()

# get Facebook authenctication form action url
            page = getResponseBody(response)
        finally:
            response.close()
        s = page.index('<form id="login_form"')
        s = page.index('action="', s)
        s += len('action="')
        e = page.index('"', s)
        url = page[s:e]

# find all html elements which need to be sent to the server
        s = page.index('>', s)
        s += 1
        e = page.index('</form>')

        parser = HTMLFormInputsParser()
        parser.feed(page[s:e].decode("utf-8"))
        parser.close()
        parser.inputs["email"] = self.facebook_email
        parser.inputs["pass"] = self.facebook_password

#        print "Now passing facebook authentication"

# pass facebook authentication
        postFields = urllib.urlencode(parser.inputs)
        request = urllib2.Request(url, postFields, self.HEADERS)
        request.add_header("Referer", referer)
        response = self.opener.open(request)
        try:
            url = response.geturl()
# if that's not BING_URL => authentication wasn't pass => write the page to the file and report
            if url.find(BING_URL) == -1:
                del self.bingMainUrl
                self.bingMainUrl = None
                try:
                    with open(ERROR_HTML, "w") as fd:
                        fd.write(getResponseBody(response))
                        s = "check " + ERROR_HTML + " file for more information"
                except IOError:
                    s = "no further information could be provided - failed to write a file " + ERROR_HTML
                raise AuthenticationError("Authentication could not be passed:\n" + s)
            self.bingMainUrl = url
        finally:
            response.close()

    def requestFlyoutPage(self):
        """
        Returns bing.com flyout page
        This page shows what rewarding activity can be performed in
        order to earn Bing points
        throws AuthenticationError if self.bingMainUrl is not set
        """
        if self.bingMainUrl is None:
            raise AuthenticationError("bingMainUrl is not set, probably you haven't passed the authentication")

        url = self.BING_FLYOUT_PAGE
        request = urllib2.Request(url = url, headers = self.HEADERS)
        request.add_header("Referer", BING_URL)
        response = self.opener.open(request)
        try:     page = getResponseBody(response)
        finally: response.close()
        return page

    def getRewardsPoints(self):
        """
        Returns rewards points as int
        throws AuthenticationError if self.bingMainUrl is not set
        """

        if self.bingMainUrl is None:
            raise AuthenticationError("bingMainUrl is not set, probably you haven't passed the authentication")

# report activity
        postFields = urllib.urlencode( { "url" : self.bingMainUrl, "V" : "web" } )
        url = "http://www.bing.com/rewardsapp/reportActivity"
        request = urllib2.Request(url, postFields, self.HEADERS)
        request.add_header("Referer", BING_URL)
        response = self.opener.open(request)
        try:     page = getResponseBody(response)
        finally: response.close()

# parse activity page
        s = page.index("txt.innerHTML = '")
        s += len("txt.innerHTML = '")
        e = page.index("'", s)
        return int(page[s:e])

if __name__ == "__main__":
    try:
        bingRewards = BingRewards(FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
        bingRewards.authenticate()
        #print bingRewards.getRewardsPoints()
        bingFlyoutParser = BingFlyoutParser()
        bingFlyoutParser.parse(bingRewards.requestFlyoutPage(), BING_URL)
        bingFlyoutParser.printRewards()

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
