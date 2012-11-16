#!/usr/bin/env python2
import StringIO
import string
import zlib
import gzip
import urllib
import urllib2
import HTMLParser
import cookielib

FACEBOOK_EMAIL = "xxx"
FACEBOOK_PASSWORD = "xxx"

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

    def clear(self):
        self.inputs.clear()
        HTMLParser.HTMLParser.reset(self)

#     def close(self):
#         HTMLParser.HTMLParser.close(self)
#         for key in self.inputs.iterkeys():
#             print key, self.inputs[key]

def getResponseBody(response):
    """ Returns response.read(), but does gzip deflate if appropriate"""

    encoding = response.info().get("Content-Encoding")

    if encoding in ("gzip", "x-gzip", "deflate"):
        page = response.read()
        if encoding == "deflate":
            return zlib.decompress(page)
        else:
            fd = StringIO.StringIO(page)
            data = gzip.GzipFile(fileobj = fd)
            content = data.read()
            fd.close()
            data.close()
            return content
    else:
        return response.read()

class BingRewards:
    BING_URL = 'http://www.bing.com'
    BING_REQUEST_PERMISSIONS = "http://www.bing.com/fd/auth/signin?action=interactive&provider=facebook&return_url=http%3a%2f%2fwww.bing.com%2f&src=EXPLICIT&perms=read_stream%2cuser_photos%2cfriends_photos&sig="
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
        cookies = cookielib.CookieJar()
        self.opener = urllib2.build_opener(#urllib2.HTTPSHandler(debuglevel = 1),     # be verbose on HTTPS
                                      #urllib2.HTTPHandler(debuglevel = 1),      # be verbose on HTTP
                                      HTTPRefererHandler,                       # add Referer header on redirect
                                      urllib2.HTTPCookieProcessor(cookies))     # keep cookies

    def authenticate(self):
        """
        Authenticates a user on bing.com with his/her Facebook account.
        FACEBOOK_EMAIL and FACEBOOK_PASSWORD for this class must be set to appropriate values.

        throws HTMLParser.HTMLParseError
        throws urllib2.HTTPError if the server couldn't fulfill the request
        throws urllib2.URLError if failed to reach the server
        """
#        print "Requesting bing.com"

# request http://www.bing.com
        request = urllib2.Request(url = self.BING_URL, headers = self.HEADERS)
        response = self.opener.open(request)
        page = getResponseBody(response)
        response.close()

# get connection URL for provider Facebook
        s = string.index(page, '"Facebook":"')
        s += len('"Facebook":"')
        e = string.index(page, '"', s)
        url = page[s:e]
        s = string.index(url, 'sig=')
        s += len('sig=')
        e = string.find(url, '&', s)
        if e == -1:
            e = len(url)
        url = self.BING_REQUEST_PERMISSIONS + url[s:e]

#        print "Now requesting facebook authentication page"

# request FACEBOOK_CONNECT_ORIGINAL_URL
        request = urllib2.Request(url = url, headers = self.HEADERS)
        request.add_header("Referer", self.BING_URL)
        response = self.opener.open(request)
        referer = response.geturl()

# get Facebook authenctication form action url
        page = getResponseBody(response)
        response.close()
        s = string.index(page, '<form id="login_form"')
        s = string.index(page, 'action="', s)
        s += len('action="')
        e = string.index(page, '"', s)
        url = page[s:e]

# find all html elements which need to be sent to the server
        s = string.index(page, '>', s)
        s += 1
        e = string.index(page, '</form>')

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
        page = getResponseBody(response)
        response.close()

def main():
    try:
        bingRewards = BingRewards(FACEBOOK_EMAIL, FACEBOOK_PASSWORD)
        bingRewards.authenticate()

    except HTMLParser.HTMLParseError, e:
        print "HTMLParserError: %s" % e

    except urllib2.HTTPError, e:
        print "The server couldn't fulfill the request."
        print "Error code: ", e.code

    except urllib2.URLError, e:
        print "Failed to reach the server."
        print "Reason: ", e.reason

if __name__ == "__main__":
    main()
