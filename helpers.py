#!/usr/bin/env python2

import StringIO
import zlib
import gzip
import os
import errno
from datetime import datetime

RESULTS_DIR = "results/"

def createResultsDir(f):
    """
    Creates results dir where all output will go based on
    __file__ object which is passed through f

    Note: results dir is created with 755 mode

    RESULTS_DIR global variable will be updated
    """
    global RESULTS_DIR
    scriptDir = os.path.dirname(os.path.realpath(f))
    resultsDir = scriptDir + "/" + RESULTS_DIR
    try:
        os.makedirs(resultsDir, 0o755)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise
    RESULTS_DIR = resultsDir


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

def dumpErrorPage(page):
    """
    Dumps page into a file. The resulting file is placed into RESULTS_DIR subfolder
    with error_dtStr.html name, where dtStr is current date and time with
    microseconds precision
    """
    if page is None: raise TypeError("page is None")

    dtStr = datetime.now().strftime("%Y%m%d-%H%M%S.%f")
    filename = "error_" + dtStr + ".html"
    with open(RESULTS_DIR + filename, "w") as fd:
        fd.write(page)

    return filename
