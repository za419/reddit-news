#!/usr/bin/env python3

import socket
import selectors
import sys
import time
import calendar
import os
import hashlib
import base64
import math
import traceback
import analysis
import string
import gzip
import bz2
import re
import lzma
import json
import cows
import client
import logging
import logging.handlers
from urllib import parse
from threading import Thread, current_thread
from configparser import ConfigParser

# Prep work
# Load in our configuration
# First, load in the defaults
# Use a line-ending agnostic hash to make sure default-config.ini hasn't been edited (lightly)
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default-config.ini'), 'r') as f:
    defaults = f.read()
    agnostic = defaults.translate(str.maketrans(dict.fromkeys(['\r','\n'])))
    hash = hashlib.sha256(agnostic.encode()).hexdigest()

    # This variable holds the 'canonical' hash of the default configuration file
    canonical = "f339a26041f836133e8ab324a1df48373b8801d8a878c33a8d9b9eb15b7d3975"

    # Now, the check.
    # Halt startup if the hashes don't match
    if hash!=canonical:
        sys.stderr.write("Default configuration hash mismatch!\n")
        sys.stderr.write("If you are developing the server code, please update the 'canonical' hash in the server code:\n")
        sys.stderr.write("canonical = '{0}'\n".format(hash))
        sys.exit(1)

defaultconfig = ConfigParser(interpolation=None)
defaultconfig.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'default-config.ini'))

# Now use those defaults to load in the overrides
config = ConfigParser(defaults=defaultconfig['DEFAULT'], interpolation=None)
config.read(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini'))
config = config['DEFAULT']

# Check whether we're supposed to handle uncaught exceptions
if config.getboolean("log_uncaught"):
    def logUncaught(type, value, tb):
        logger.critical("Uncaught exception:\n%s\n", ''.join(traceback.format_exception(type, value, tb)))

        # Check if we're supposed to keep crashing
        if config.getboolean("suppress_uncaught") and not issubclass(type, KeyboardInterrupt):
            # Recurse if we encounter more uncaught errors
            try:
                main()
            except:
                info=sys.exc_info()
                logUncaught(info[0], info[1], info[2])
        else:
            sys.exit(1)

    # Register the handler
    sys.excepthook=logUncaught

# Set whether the logging module will handle exceptions on its own
logging.raiseExceptions=config.getboolean("log_raise_exceptions")

# Configure a new logging level (VERBOSE)
logging.VERBOSE=5
logging.addLevelName(logging.VERBOSE, "VERBOSE")
def _verbose(self, message, *args, **kwargs):
    "Function for logging at a below-debug level"

    # if self.isEnabledFor(logging.VERBOSE):
    self._log(logging.VERBOSE, message, args, **kwargs)

logging.getLoggerClass().verbose=_verbose

# If set to do so, change the log milliseconds format
if config.getboolean('log_milliseconds_with_period'):
    logging.Formatter.default_msec_format='%s.%03d'

level = config['loglevel']
# Translate a log level (as configured) into a useful log level
leveldict = {
    "VERBOSE"  : logging.VERBOSE,
    "DEBUG"    : logging.DEBUG,
    "INFO"     : logging.INFO,
    "WARNING"  : logging.WARNING,
    "ERROR"    : logging.ERROR,
    "CRITICAL" : logging.CRITICAL
}

# Check if our log level is a valid name
if level in leveldict.keys():
    level = leveldict[level]
# If it isn't, try to convert it from an integer
else:
    try:
        level = int(level)
    except ValueError as ex:
        # We don't understand this level.
        # Raise a new exception with a somewhat more helpful error
        raise RuntimeError("Could not interpret \""+level+"\" as a valid logging level") from ex


#############################################################################################################
# Set verbose logging to a no-op if it's disabled                                                           #
# This is a performance enhancement, which breaks verbose logging if loglevel changes dynamically.          #
# If you encounter issues with this, remove this code.                                                      #
# When it works, this avoids a lot of unnecessary function calls (which are expensive in Python)            #
# Note that if you do remove this, you need to restore the check which is commented out in _verbose         #
# This check is removed, since _verbose can now only be called (through a logger) when VERBOSE is enabled.  #
#############################################################################################################
def noop(self, message, *args, **kwargs):
    "Does nothing, with arguments compatible to a logging function"
    pass

if level>logging.VERBOSE:
    logging.getLoggerClass().verbose=noop


# If logs directory does not exist, create it
logdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), config['logdirectory'])
logdir = os.path.realpath(logdir)
if not os.path.exists(logdir):
    os.makedirs(logdir)

# Prepare the handlers for our logger (using the data as configured)
handlers = []
if config.getboolean('log_to_console'):
    # Find the correct stream and add it
    if config['logstream']=="stdout":
        handlers.append(logging.StreamHandler(sys.stdout))
    elif config['logstream']=="stderr":
        handlers.append(logging.StreamHandler(sys.stderr))
    else:
        # No found handler. Warn the user and use stderr
        from warnings import warn
        warn("Could not parse "+config['logstream']+" as a console stream. Using stderr.")
        handlers.append(logging.StreamHandler(sys.stderr))
if config.getboolean('log_to_disk'):
    # Assemble and add the timed rotating file handler
    handlers.append(logging.handlers.TimedRotatingFileHandler(os.path.join(logdir, config['logfile']), config['log_rotation_interval'], int(config['log_rotation_period']), int(config['log_backup_count'])))

# If the handlers list is empty, reconfigure so that logging uses a StreamHandler, but has an unreasonably high logging level.
# That way, logging will be effectively disabled, without adding any code anywhere else
if len(handlers)==0:
    handlers.append(logging.StreamHandler(sys.stdout))
    level=math.pow(2, 64)

# Log both to the console and to a daily rotating file, storing no more than 30 days of logs
logging.basicConfig(level=level,
                    format=config['log_debugformat'] if config.getboolean('log_use_debugformat')
                                                     else config['logformat'],
                    handlers=handlers)
logger = logging.getLogger(config['logger'])
logger.setLevel(level)

port = int(sys.argv[1])
directory = os.path.realpath(sys.argv[2]).encode()

caching=0

# Check if we might have the -c flag
if len(sys.argv)>3 or config.getboolean('force_caching'):
    if config.getboolean('force_caching') or sys.argv[3].startswith("-c"):
        if len(sys.argv)>4:
            caching = int(sys.argv[4])
        else:
            caching = int(config['default_caching_duration'])
    else:
        logger.warning("Did not understand argument %s.", sys.argv[3])

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock.bind(("", port))
sock.listen(int(config['backlog']))

# Set sock as nonblocking
sock.setblocking(False)

# Helper functions
def waitingRequest(s, blocksize=4096):
    "Returns a string containing one complete HTTP request from s, loaded in chunks of blocksize"

    out = s.recv(blocksize)
    # Hopefully, our headers will be in the first blocksize.
    # But first, we know that if output is smaller than blocksize, we have everything that's ready for us
    if len(out)<blocksize:
        logger.debug("Downloaded request of size %d.", len(out))
        return out

    # While true, try to parse a content size out of our received data, and if we can't, fetch a block.
    contentSize = 0
    while True:
        block = s.recv(blocksize)
        out += block
        for line in block.split("\r\n"):
            if line.startswith("Content-Length: "):
                contentSize=int(line.split(": ")[1])
                break # Only use the first content-length header
    # "Worst" case scenario is that Content-Length is the last header.
    # In that case, we'll have four more bytes (CRLFCRLF), then the content bytes
    contentSize += 4
    # Load the content into out
    while contentSize>blocksize:
        out += s.recv(blocksize)
        contentSize -= blocksize
    if contentSize>0:
        out += s.recv(contentSize)

    logger.debug("Downloaded request of size %d.", len(out))

    # out should now contain all of our request
    return out

def mimeTypeOf (filename):
    "Attempts to find the appropriate MIME type for this file by extension (MIME types taken from https://www.freeformatter.com/mime-types-list.html)"

    parts = filename.decode().split(".")
    if len(parts)<2:
        # The file has no extension.
        # Default to application/octet-stream
        logger.debug("Assumed file %s was type %s (no extension).", filename.decode(), "application/octet-stream")
        return "application/octet-stream"

    # The extension is whatever is after the last '.' in the filename
    # Switch to lowercase for comparison
    extension = parts[-1].lower()
    logger.debug("Extension %s", extension)

    # Giant dictionary of extensions -> MIME types
    # In order to keep this whole thing from being recreated every time a request for a file is made,
    #   only allocate it the first time the function is called and store it as a local for other requests
    if not hasattr(mimeTypeOf, "dictionary"):
        logger.verbose("Configuring MIME type dictionary...")
        mimeTypeOf.dictionary = {
            "es": "application/ecmascript",
            "epub": "application/epub+zip",
            "jar": "application/java-archive",
            "class": "application/java-vm",
            "js": "application/javascript",
            "json": "application/json",
            "mathml": "application/mathml+xml",
            "mp4": "application/mp4",
            "doc": "application/msword",
            "bin": "application/octet-stream",
            "ogx": "application/ogg",
            "ogg": "application/ogg",
            "onetoc": "application/onenote",
            "pdf": "application/pdf",
            "ai": "application/postscript",
            "ps": "application/postscript",
            "rss": "application/rss+xml",
            "rtf": "application/rtf",
            "gram": "application/srgs",
            "sru": "application/sru+xml",
            "ssml": "application/ssml+xml",
            "tsd": "application/timestamped-data",
            "apk": "application/vnd.android.package-archive",
            "m3u8": "application/vnd.apple.mpegurl",
            "ppd": "application/vnd.cups-ppd",
            "gmx": "application/vnd.gmx",
            "xls": "application/vnd.ms.excel",
            "eot": "application/vnd.ms-fontobject",
            "chm": "application/vnd.ms-htmlhelp",
            "ppt": "application/vnd.ms-powerpoint",
            "mus": "application/vnd.musician",
            "odf": "application/vnd.oasis.opendocument.formula",
            "odg": "application/vnd.oasis.opendocument.graphics",
            "odi": "application/vnd.oasis.opendocument.image",
            "odp": "application/vnd.oasis.opendocument.presentation",
            "ods": "application/vnd.oasis.opendocument.spreadsheet",
            "odt": "application/vnd.oasis.opendocument.text",
            "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "rm": "application/vnd.rn-realmedia",
            "unityweb": "application/vnd.unity",
            "wpd": "application/vnd.wordperfect",
            "hlp": "application/winhlp",
            "7z": "application/x-7z-compressed",
            "dmg": "application/x-apple-diskimage",
            "bz": "application/x-bzip",
            "bz2": "application/x-bzip2",
            "vcd": "application/x-cdlink",
            "chat": "application/x-chat",
            "pgn": "application/x-chess-pgn",
            "csh": "application/x-csh",
            "deb": "application/x-debian-package",
            "wad": "application/x-doom",
            "dvi": "application/x-dvi",
            "otf": "application/x-font-otf",
            "pcf": "application/x-font-pcf",
            "ttf": "application/x-font-ttf",
            "pfa": "application/x-font-type1",
            "woff": "application/x-font-woff",
            "latex": "application/x-latex",
            "clp": "application/x-msclip",
            "exe": "application/x-msdownload",
            "pub": "application/x-mspublisher",
            "rar": "application/x-rar-compressed",
            "sh": "application/x-sh",
            "swf": "application/x-shockwave-flash",
            "xap": "application/x-silverlight-app",
            "tar": "application/x-tar",
            "tex": "application/x-tex",
            "texinfo": "application/x-texinfo",
            "xhtml": "application/xhtml+xml",
            "dtd": "application/xml+dtd",
            "zip": "application/zip",
            "mid": "audio/midi",
            "mp4a": "audio/mp4",
            "mpga": "audio/mpeg",
            "oga": "audio/ogg",
            "dts": "audio/vnd.dts",
            "dtshd": "audio/vnd.dts.hd",
            "weba": "audio/webm",
            "aac": "audio/x-aac",
            "m3u": "audio/x-mpegurl",
            "wma": "audio/x-ms-wma",
            "wav": "audio/x-wav",
            "bmp": "image/bmp",
            "gif": "image/gif",
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "pjpeg": "image/pjpeg",
            "png": "image/png",
            "svg": "image/svg+xml",
            "tiff": "image/tiff",
            "psd": "image/vnd.adobe.photoshop",
            "sub": "image/vnd.dvb.subtitle",
            "webp": "image/webp",
            "ico": "image/x-icon",
            "pbm": "image/x-portable-bitmap",
            "eml": "message/rfc822",
            "ics": "text/calendar",
            "css": "text/css",
            "csv": "text/csv",
            "html": "text/html",
            "txt": "text/plain",
            "rtx": "text/richtext",
            "sgml": "text/sgml",
            "tsv": "text/tab-separated-values",
            "ttl": "text/turtle",
            "uri": "text/uri-list",
            "curl": "text/vnd.curl",
            "scurl": "text/vnd.curl.scurl",
            "s": "text/x-asm",
            "c": "text/x-c",
            "f": "text/x-fortran",
            "java": "text/x-java-source,java",
            "vcs": "text/x-vcalendar",
            "vcf": "text/x-vcard",
            "yaml": "text/yaml",
            "3gp": "video/3gpp",
            "3g2": "video/3gpp2",
            "h264": "video/h264",
            "jpgv": "video/jpeg",
            "mp4": "video/mp4",
            "mpeg": "video/mpeg",
            "ogv": "video/ogg",
            "qt": "video/quicktime",
            "mxu": "video/vnd.mpegurl",
            "webm": "video/webm",
            "f4v": "video/x-f4v",
            "flv": "video/x-flv",
            "m4v": "video/x-m4v",
            "wmv": "video/x-ms-wmv",
            "avi": "video/x-msvideo",
        }
        logger.verbose("Done.")

    if not extension in mimeTypeOf.dictionary.keys():
        # We don't recognize this filetype
        # Default to application/octet-stream
        logger.debug("Assumed file %s was type %s (unknown extension).", filename.decode(), "application/octet-stream")
        return "application/octet-stream"

    # Recognized filetype. Return it.
    logger.debug("Guessed file %s was type %s.", filename.decode(), mimeTypeOf.dictionary[extension])
    return mimeTypeOf.dictionary[extension]

def requestBody(request):
    "Returns only the body of a given HTTP request"

    return request.partition(b"\r\n\r\n")[2].decode()

def ETag(content):
    "Returns a standard ETag of content (base64 encoded sha256) for use anywhere ETags are used in the server. ETags are returned in the same form content was passed (string or bytes)"

    if isinstance(content, str):
        return base64.urlsafe_b64encode(hashlib.sha256(content.encode()).digest()).decode()
    else:
        return base64.urlsafe_b64encode(hashlib.sha256(content).digest())

def HTTP_time(at=None):
    "Returns a string formatted as an HTTP time, corresponding to the unix time specified by at (defaults to the present)"

    if at is None:
        at=time.time()

    return time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(at))

def parse_HTTP_time(at):
    "Returns a Unix timestamp from an HTTP timestamp"

    if isinstance(at, bytes):
        at=at.decode()

    return calendar.timegm(time.strptime(at, "%a, %d %b %Y %H:%M:%S GMT"))

def basicHeaders(status, contentType):
    "Constructs and returns a basic set of headers for a response (Does not end the header block)"

    # For performance, pre-create a format string for basic headers (we use this function a lot)
    if not hasattr(basicHeaders, "format"):
        logger.verbose("Assembling basic headers format...")
        basicHeaders.format =  "HTTP/1.1 {0}\r\n"
        basicHeaders.format += "Date: {1}\r\n"
        basicHeaders.format += "Connection: close\r\n"
        basicHeaders.format += "Vary: Accept-Encoding\r\n"

        # Advertise the configured state of our range request support
        if config.getboolean("enable_range_requests"):
            basicHeaders.format += "Accept-Ranges: bytes\r\n"
        else:
            basicHeaders.format += "Accept-Ranges: none\r\n"

        basicHeaders.format += "\r\n".join([s.strip() for s in config['additional_headers'].split(',')])+"\r\n"

        # Add cache-control header iff we have caching set
        if caching>0:
            basicHeaders.format += "Cache-Control: public, max-age="+str(caching)+"\r\n"

        basicHeaders.format += "Content-Type: {2}\r\n"

        logger.verbose("Done.")

    # Format in our arguments and return
    return basicHeaders.format.format(status, HTTP_time(), contentType).encode()

def constructResponse(unendedHeaders, content, contentType, allowEncodings=None, etag=None):
    "Attaches unendedHeaders and content into one HTTP response (adding content-length in the process), optionally overriding the etag. allowEncodings should be a list of strings of allowed encodings, or None."

    # Pre-compile our regex pattern
    if not hasattr(constructResponse, "compressPattern"):
        logger.verbose("Compiling compression regex...")
        constructResponse.compressPattern=re.compile(config['compress_type_regex'], re.IGNORECASE)
        logger.verbose("Done.")

    response =  unendedHeaders

    # Accept a str content
    if isinstance(content, str):
        content = content.encode()

    # Add ETag iff we have caching set
    if caching>0:
        # Either generate our own, or use the provided one
        if etag==None:
            response += b"ETag: \""+ETag(content)+b"\"\r\n"
        else:
            logger.verbose("Overrided ETag.")
            response += b"ETag: \""+etag+b"\"\r\n"

    # Process our encodings
    l=len(content)
    # Only attempt to find an encoding if:
    #   - We have some allowed encodings object to process
    #   - The size of our content is large enough that we're configured to compress it
    #   - The MIME type of our file is configured to be compressed.
    if allowEncodings!=None and l>int(config['minimum_compress_size']) and constructResponse.compressPattern.fullmatch(contentType)!=None:
        for encoding in allowEncodings:
            logger.debug("Permitted to use encoding %s.", encoding)
            if encoding=="identity" or encoding=="*":
                # We can silently use this encoding
                break
            elif encoding=="gzip":
                # Compress the content with gzip
                content=gzip.compress(content)
                logger.debug("Compressed content from %d bytes to %d bytes using gzip.", l, len(content))

                # Add an encoding header
                response += b"Content-Encoding: gzip\r\n"
                break
            elif encoding=="bzip2":
                # Compress the content with bzip2
                content=bz2.compress(content)
                logger.debug("Compressed content from %d bytes to %d bytes using bzip2.", l, len(content))

                # Add an encoding header
                response += b"Content-Encoding: bzip2\r\n"
                break
            elif encoding=="xz":
                # Compress the content with LZMA2 (as an XZ container)
                content=lzma.compress(content, lzma.FORMAT_XZ)
                logger.debug("Compressed content from %d bytes to %d bytes using LZMA2.", l, len(content))

                # Add an encoding header
                response += b"Content-Encoding: xz\r\n"
                break

    response += b"Content-Length: "+str(len(content)).encode()+b"\r\n\r\n"
    response += content
    return response

def queueResponse(sock, response):
    "Prepare the response to be sent on the socket sock. No work is done to response before send."

    # Either register the new writer, or modify the existing one.
    try:
        selector.register(Connection(sock, True, content=response), selectors.EVENT_WRITE)
    except KeyError:
        selector.modify(Connection(sock, True, content=response), selectors.EVENT_WRITE)

def sendResponse(status, contentType, content, sock, headers=[], allowEncodings=None, etag=None):
    "Constructs and sends a response with the first three parameters via sock, optionally with additional headers, and optionally overriding the ETag. allowEncodings should be a list of strings of allowed encodings, or None."

    # Attempt to handle unencoded content
    # This occasionally throws TypeErrors, for no reason I can tell.
    # It complains that 'str' object is not callable... But the only thing I'm calling is type?
    try:
        if isinstance(content, str):
            content=content.encode()
    except:
        logger.debug("Strange error while attempting str/bytes detection.", exc_info=True)

        # At least keep from crashing.
        content=bytes(content)

    # If additional headers are specified, format them for HTTP
    # Else, send as normal
    if len(headers)>0:
        queueResponse(sock, constructResponse(basicHeaders(status, contentType)+("\r\n".join(headers)+"\r\n").encode(), content, contentType, allowEncodings, etag))
    else:
        queueResponse(sock, constructResponse(basicHeaders(status, contentType), content, contentType, allowEncodings, etag))

    logger.info("Queued response for socket %d.", sock.fileno())
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Response had %d additional headers: \"%s\".", len(headers), ", ".join(headers))

# Probably won't see much use for this... But need it at least for 400 bad request
def generateErrorPage(title, description):
    "Returns the HTML for an error page with title and description"

    # For performance, construct this once the first time an error page is generated
    if not hasattr(generateErrorPage, "format"):
        logger.verbose("Assembling error page generation format...")
        generateErrorPage.format =  "<!DOCTYPE html>\n"
        generateErrorPage.format += "<html lang='en'>\n"
        generateErrorPage.format += "  <head>\n"
        generateErrorPage.format += "    <meta charset='utf-8'>\n"
        generateErrorPage.format += "    <title>{0}</title>\n"
        generateErrorPage.format += "  </head>\n"
        generateErrorPage.format += "  <body>\n"
        generateErrorPage.format += "    <h1 style='text-align: center; width:100%'>{0}</h1>\n"
        generateErrorPage.format += "    <p>{1}</p>\n"
        generateErrorPage.format += "  </body>\n"
        generateErrorPage.format += "</html>\n"
        logger.verbose("Done.")

    # Use string formatting to insert the parameters into the page
    return generateErrorPage.format.format(title, description).encode()

# Class to store an open connection
class Connection:
    def __init__(self, conn, isWrite, isAccept=False, content=None, IP=None):
        self.conn = conn
        self.isWrite=isWrite
        self.isAccept = isAccept
        self.content = content
        self.IP=IP

    def __str__(self):
        return "{0} connection {1} from {2}, with content {3}".format("Write" if self.isWrite else "Read",
                                                                      self.fileno(),
                                                                      self.IP,
                                                                      self.content)

    def __repr__(self):
        return "Connection({!r}, {}, {}, {}, {})".format(self.conn, self.isWrite, self.isAccept, self.content, self.IP)

    # Follows configured behavior to attempt to get an IP out of request headers
    def setIPFrom(self, requestHeaders):
        try:
            header = config['client_identification_header']
            if header == "None":
                # Use the socket connection address and return
                self.IP=self.conn.getpeername()[0]
                return

            # Attempt to find that header in the request headers
            # requestHeaders can either be a list of headers, bytes, or a string representing the headers
            # Either way, make sure it ends up as a list of strings
            lines = []
            if type(requestHeaders) is list:
                if type(requestHeaders[0]) is bytes:
                    lines = [line.decode() for line in requestHeaders]
                else:
                    # Assume strings
                    lines = requestHeaders
            elif type(requestHeaders) is str:
                lines = requestHeaders.split("\r\n")
            elif type(requestHeaders) is bytes:
                lines = requestHeaders.decode().split("\r\n")
            else:
                # Assume it's some sort of collection
                lines = [line for line in requestHeaders]

            # Lines is now a list of strings, where each string is an HTTP header.
            for line in lines:
                if line.startswith(header):
                    # We've found our header.
                    vals = line.partition(": ")
                    value = vals[2]

                    # Handle standard headers which require more processing
                    if vals[0]=="X-Forwarded-For":
                        # X-Forwarded-For includes a list of forwarding proxies we don't care about.
                        value=value.partition(",")[0]
                    elif vals[0]=="Forwarded":
                        # Forwarded includes more data than just identifier
                        parts=[part.strip() for part in value.split(';')]

                        # Get the field that contains source data
                        for part in parts:
                            if part[:4].lower() == "for=":
                                # Part is our part.
                                value=part[4:]
                                break

                        # We're probably done, unless the address is IPv6.
                        # IPv6 records, for no apparent reason, must be in quotes and brackets. Strip both just in case
                        if value.startswith('\"'):
                            value=value.strip('[]\"')

                    # Set our IP to be that value
                    self.IP=value
                    return

            # We didn't find the header. Fall back to the socket connection address.
            self.IP=self.conn.getpeername()[0]
        except OSError:
            logger.exception("Exception while attempting to read client IP from socket %d.", self.conn.fileno(), exc_info=True)
            self.IP="Unknown (exception while processing IP address; See log for socket "+str(self.conn.fileno())+")."
            # Note, happily, that including the socket number in there at least provides some separation between connections.

    # For compatibility with select
    def fileno(self):
        return self.conn.fileno()

# Pre-create mimeTypeOf dictionary, basic headers, and error page data
mimeTypeOf(b"MimeType.precreate.file")
generateErrorPage("PRECREATION", "YOU SHOULD NEVER SEE THIS")
basicHeaders("599 Server Pre-create", "MimeType/precreate.file")

# Helpers for thread work
# This includes functions to create infinite sequences of thread names
def createThread(target, name, args):
    "Wrapper for the Thread constructor which takes positional arguments"

    logger.verbose("Creating thread %s.", name)

    return Thread(target=target, name=name, args=args)

def constantIterable(const):
    "A generator which always returns const"

    while True:
        yield const

def nameIterable(prefix):
    "A generator which generates an infinite sequence of strings, as prefix+id, for id in {0...infinity}"

    prefix=str(prefix)
    ID=0
    while True:
        logger.verbose("Advanced name \"%s\" to #%d.", prefix, ID)
        yield prefix+str(ID)
        ID+=1

def processRequest(request, conn, encodings=None):
    "Process the Reddit processing request in request"

    body = requestBody(request)
    query = parse.parse_qs(body)

    # Log before we attempt to use the query
    logger.debug("Query body: %s", body)
    logger.debug("Parsed: %s", query)

    # Fetch information from Reddit
    target=query["target"][0]
    limit=int(query["limit"][0])
    comments2=(query["comments2"][0]=="true")
    if limit==0 and not comments2:
        limit=None
    results=None
    logger.debug("Fetching information for %s, limit %s, using %s.", target, limit, "comments2" if comments2 else "comments")
    if comments2:
        results=client.fetchall2(target, limit)
    else:
        results=client.fetchall(target)

    # Process comments into JSON-format (article should just be a string)
    article=json.dumps(results[0])
    comments=json.dumps(list(results[1]))

    # Return the results wrapped in a JSON object
    sendResponse("200 OK",
                 "application/json",
                 '{{"text": {0}, "comments": {1}}}'.format(article, comments),
                 conn,
                 allowEncodings=encodings)

    logger.info("Sent response.")

# Network operation helper functions
def readFrom(read, log=True):
    "Performs the operation of reading from the given Connection or set of Connections"

    # Set up our generators for post thread names
    if not hasattr(readFrom, "searcherName"):
        logger.verbose("Configuring post thread name generators...")
        readFrom.searcherName=nameIterable("Post searcher ")

        logger.verbose("Configuring connection blacklist...")
        blacklist = config['connection_blacklist']
        if blacklist==None:
            readFrom.blacklist=[]
        else:
            blacklist = blacklist.split(',')
            readFrom.blacklist = [addr.strip() for addr in blacklist]

        readFrom.blacklistResponse = config['blacklist_response']
        if readFrom.blacklistResponse=="None":
            readFrom.blacklistResponse=False

        logger.verbose("%d blacklisted addresses.", len(readFrom.blacklist))

        logger.verbose("Compiling cow easter egg regex...")
        readFrom.cowPattern=re.compile(config['moo_regex'], re.IGNORECASE)
        logger.verbose("Done.")

    # Log which thread we're on
    if log:
        logger.debug("Beginning read(s) on thread %s.", current_thread().name)

    # If this isn't a Connection, assume it's a collection of Connections and recurse
    if type(read) is not Connection:
        logger.verbose("Attempting iteration over passed collection...")
        for r in read:
            logger.verbose("Beginning read.")
            readFrom(r, False)
        logger.verbose("All reads complete.")
        return

    # Ignore erroneous sockets (those with negative file descriptors)
    if read.fileno() < 0:
        # Drop the connection from selector, close the error, and continue on our way
        # Ignore errors: What matters is that we don't do anything with the sockets
        logger.verbose("Noticed negative file descriptor %d.", read.fileno())
        try:
            selector.unregister(read)
            read.conn.close()
        except:
            pass
        return

    # For the accept socket, accept the connection and add it to the list
    if read.isAccept:
        # Accept as many connections as we can until none are immediately ready for accept
        try:
            while True:
                conn, address = read.conn.accept()
                address = address[0]

                # Check for blacklisting
                if address in readFrom.blacklist:
                    # This address is on the blacklist.
                    # Deny the connection.
                    logger.info("Denied incoming connection from %s (blacklisted IP address).", address)
                    if readFrom.blacklistResponse!=False:
                        conn.sendall(readfrom.blacklistResponse)
                    conn.close()
                    continue

                selector.register(Connection(conn, False, IP=address), selectors.EVENT_READ)
                logger.info("Accepting a new connection, attached socket %d.", conn.fileno())
                logger.debug("Connection is from %s.", address) # Not the client address per se, but informative in theory nonetheless.
        except socket.timeout:
            pass
        except BlockingIOError:
            pass
    else:
        logger.info("Processing request from socket %d.", read.fileno())
        # Fetch the HTTP request waiting on read
        request = waitingRequest(read.conn, int(config['HTTP_blocksize']))

        # If the request is zero-length, the client disconnected. Skip the work of figuring that out the hard way, and the unhelpful log message.
        # Log a better message, remove the connection from the list, skip the rest of the loop
        if len(request) == 0:
            logger.info("Empty request on socket %d.", read.fileno())
            sendResponse("400 Bad Request",
                         "text/html",
                         generateErrorPage("400 Bad Request",
                                           "Your browser send an empty request."),
                         read.conn)
            return

        # Set the IP on the connection
        logger.verbose("Attempting to parse IP from connection...")
        headers=request.partition(b"\r\n\r\n")[0]
        read.setIPFrom(headers)

        # Lines of the HTTP request (needed to read the header)
        lines = headers.split(b"\r\n")

        # See if we have an Accept-Encoding header
        logger.verbose("Attempting to grab list of allowed encodings...")
        encodings = []
        for header in lines:
            if header.decode().lower().startswith("accept-encoding: "):
                # Parse the values given by the header
                value = header.decode().partition(": ")[2]
                logger.debug("Allowed encodings: %s.", value)
                values = value.split(", ")
                encodings = [val.partition(";")[0] for val in values] # We don't care about quality values

                break

        # The first line tells us what we're doing
        # If it's GET, we return the file specified via commandline
        # If it's HEAD, we return the headers we'd return for that file
        # If it's something else, return 405 Method Not Allowed
        method = parse.unquote_to_bytes(lines[0])
        targ = method.partition(b" ")[2].rpartition(b" ")[0] # Target filename
        logger.debug("Method line %s, target %s.", method.decode(), targ.decode())
        if method.startswith(b"POST") and config.getboolean('enable_post'):
            logger.info("Received POST request to %s.", targ.decode())
            if targ==b"/process":
                processRequest(request, read.conn, encodings)
            else:
                # No other paths can receive a POST.
                # Tell the browser it can't do that, and inform it that it may only use GET or HEAD here.
                sendResponse("405 Method Not Allowed",
                             "text/html",
                             generateErrorPage("405 Method Not Allowed",
                                               "Your browser attempted to perform an action the server doesn't support at this location."),
                             read.conn,
                             ["Allow: GET, HEAD"],
                             encodings)

                # Log method not allowed
                logger.info("Issued method not allowed.")

            # No matter what, we've handled the request however we chose to.
            return
        elif not (method.startswith(b"GET") or method.startswith(b"HEAD")):
            # This server can't do anything with these methods.
            # So just tell the browser it's an invalid request
            sendResponse("501 Not Implemented",
                         "text/html",
                         generateErrorPage("501 Not Implemented",
                                           "Your browser sent a request to perform an action the server doesn't support."),
                         read.conn,
                         ["Allow: GET, HEAD"],
                         encodings)

            # Print note on error
            logger.info("Could not execute method %s.", method.decode())
            return

        # Parse the filename out of the request
        # Trim leading slashes to keep Python from thinking that the method refers to the root directory.
        filename = os.path.join(directory, targ.lstrip(b'/').split(b'?')[0])
        dir = False
        # If the filename is a directory, join it to "index.html"
        if os.path.isdir(filename):
            dir = True
            filename = os.path.join(filename, b"index.html")

        # Normalize the file path
        filename = os.path.realpath(filename)

        # Check if the relative path between the file and the service directory includes '..'
        # In other words, if one has to go 'up' in the directory structure to get to the target
        # If this is the case, return an error forbidding access to that file
        if b".." in os.path.relpath(filename, directory):
            # Detected attempt to access file outside allowed directory.
            # ACCESS DENIED
            sendResponse("403 Forbidden",
                         "text/html",
                         generateErrorPage("403 Forbidden",
                                           "You are not permitted to access \""+targ.decode()+"\" on this server."),
                         read.conn,
                         ["Warning: 299 Translate Access to files above the root directory of the served path is forbidden. This incident has been logged."],
                         encodings)

            # Log an error, pertaining to the fact that an attempt to access forbidden data has been thwarted.
            logger.error("Client at %s attempted to access forbidden file %s, but was denied access.", read.IP, filename.decode())

            return

        # Perform redirect of directories that don't end in a separator or slash
        targ = targ.decode()
        if dir and not (targ.endswith(os.path.sep) or targ.endswith('/')):
            sendResponse("301 Moved Permanently",
                         "text/html",
                         b"",
                         read.conn,
                         ["Location: "+targ+'/'])

            # Log redirect
            logger.info("Issued redirect from %s to %s/.", targ, targ)

            return

        # Guess the MIME type of the file.
        mimetype = mimeTypeOf(filename)

        # Read the file into memory
        logger.info("Attempting file read on file %s.", filename.decode())
        file = ""
        try:
            with open(filename, 'rb', 0) as f:
                file = f.read()
        except FileNotFoundError:
            # The file wasn't found.
            # Check for the 418 easter egg
            if targ.endswith("coffee") and config.getboolean('enable_418'):
                # Someone must be trying to get some coffee!
                # Too bad for them.
                # Image is, unsurprisingly, a teapot I rendered
                image = ""
                logger.verbose("Attempt to get coffee. Becoming a teapot. Attempting to access teapot image...")
                try:
                    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "teapot.png"), 'rb', 0) as f:
                        image = base64.b64encode(f.read()).decode()
                except:
                    logger.debug("Could not open teapot image.", exc_info=True)
                    pass
                logger.verbose("Done.")

                # If file load failed, just skip the image
                if len(image)==0:
                    logger.verbose("Sending imageless 418 easter egg page.")
                    sendResponse("418 I'm a teapot",
                                 "text/html",
                                 generateErrorPage("418 I'm a teapot",
                                                   "I'm sorry - I can't make coffee for you.<br>I'm a teapot."),
                                 read.conn,
                                 allowEncodings=encodings)
                else:
                    logger.verbose("Sending 418 easter egg page.")
                    sendResponse("418 I'm a teapot",
                                 "text/html",
                                 generateErrorPage("418 I'm a teapot",
                                                   "I'm sorry - I can't make coffee for you.</p>"+
                                                   "<img src=\"data:image/png;base64,"+image+"\" width=256 height=256><p>I'm a teapot."),
                                 read.conn,
                                 allowEncodings=encodings)

                # Log the teapot
                logger.warning("Became a teapot in response to request for unfound file %s.", filename.decode())

                file = ""

            # Not a teapot
            # Check for the cow easter egg
            if config.getboolean("enable_cows") and readFrom.cowPattern.fullmatch(method.split(b' ')[1].decode())!=None:
                cow=cows.getCow()
                 # Check if we're returning 200 OK or 404 Not Found
                status = "404 Not Found"
                if config.getboolean("cows_ok"):
                    status = "200 OK"
                # Send the response
                sendResponse(status,
                             "text/html",
                             generateErrorPage(status,
                                               """
                                               </p>
                                               <pre>
                                                 {0}
                                               </pre>
                                               <footer style="background-color: #DDD;
                                                              padding: 10px 10px 2px 10px;
                                                              margin: 0;
                                                              width: 100%;
                                                              bottom: 0;
                                                              left: 0;
                                                              position: fixed">
                                                  ASCii cow art is from <a href="https://www.asciiart.eu/animals/cows">The ASCii Art Archive</a>. The figures are property of their original creators, who are identified in the art if they chose to include identification in their work.
                                               </footer>
                                               """.format(cow)),
                             read.conn,
                             allowEncodings=encodings)
                 # Log the cow
                logger.warning("Became a cow in response to request for unfound file %s.", filename.decode())
                file = ""
            # Not a cow either
            else:
                # Return 404.
                sendResponse("404 Not Found",
                             "text/html",
                             generateErrorPage("404 Not Found",
                                               "The requested file \""+targ+
                                               "\" was not found on this server."),
                             read.conn,
                             allowEncodings=encodings)

                # Print note on error
                logger.warning("Could not find file %s.", filename.decode())
                file = ""
        except:
            # Some unknown error occurred. Return 500.
            # First, generate our error message
            exc_type, exc_value, exc_traceback = sys.exc_info()
            message = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))

            # Now send the error message.
            sendResponse("500 Internal Server Error",
                         "text/html",
                         generateErrorPage("500 Internal Server Error",
                                           "The server encountered an error while attempting to process your request.\n"+
                                           "<!-- Ok, since you know what you're doing, I'll confess.\n"+
                                           "I know what the error is. Python says:\n"+
                                           message+'\n'+" -->"),
                         read.conn,
                         allowEncodings=encodings)

            # Print note on error
            logger.exception("Could not open file %s.", filename.decode(), exc_info=True)
            file = ""

        if file=="":
            logger.debug("Breaking off connection attempt due to file open issue.")
            return

        # Serve the file back to the client.
        # First, handle caching
        if caching>0:
            logger.debug("Caching is enabled, checking for If-None-Match")
            Etag = ""
            for line in lines:
                if line.startswith(b"If-None-Match: "):
                    Etag = line.split(b"\"")[1]
                    logger.debug("Found header - ETag %s.", Etag.decode())

            # If there was no If-None-Match, check for a provided If-Modified-Since
            if Etag == "":
                logger.debug("Found no ETag, searching for last modified time.")
                mtime = float("nan")
                for line in lines:
                    if line.startswith(b"If-Modified-Since: "):
                        mt = line.partition(b": ")[2]
                        mtime = parse_HTTP_time(mt)
                        logger.debug("Found header - mtime %f, from timestamp %s.", mtime, mt.decode())

                if mtime>=math.floor(os.path.getmtime(filename)):
                    # Last modified time was given (all NaN comparisons return false), and the file has not since been modified.
                    # Return basic headers, plus ETag and mtime
                    queueResponse(read.conn, basicHeaders("304 Not Modified", mimetype)+b"ETag: \""+ETag(file)+b"\"\r\nLast-Modified: "+HTTP_time(os.path.getmtime(filename)).encode()+b"\r\n\r\n")
                    logger.info("Client already has this file (not modified since %f [which is %s]).", mtime, HTTP_time(mtime))

                    return
                else:
                    logger.info("Need to resend file (last modified too recently or no mtime passed).")

            # If we have an ETag and it matches our file, return 304 Not Modified
            elif Etag == ETag(file):
                # ETag matches. Return our basic headers, plus the ETag and mtime
                queueResponse(read.conn, basicHeaders("304 Not Modified", mimetype)+b"ETag: \""+Etag+b"\"\r\nLast-Modified: "+HTTP_time(os.path.getmtime(filename)).encode()+b"\r\n\r\n")
                logger.info("Client already has this file (matching hash %s) - Issued 304.", Etag.decode())

                return

        # Check if we're doing a byte reply
        done=False
        logger.verbose("Checking for range request...")
        for line in lines:
            # If we're not processing byte replies, break out of the loop
            # (this is here to reduce indentation on this really big loop)
            if not config.getboolean("enable_range_requests"):
                break

            if line.startswith(b"Range: "):
                # We have a byte-range-request
                logger.debug("Request on socket %d is a range request.", read.fileno())

                # Check for If-Range
                exit=False
                logger.verbose("Checking for If-Range....")
                for l in lines:
                    if l.startswith(b"If-Range: "):
                        # We found an If-Range
                        value=l.partition(b": ")[2]
                        logger.debug("Found If-Range: %s.", value)

                        # Check if the If-Range is a last-modified or an ETag
                        # Because our ETags are base64 encoded, we can check for the presence of a space to do this
                        if b' ' in value:
                            # Value is a last-modified
                            mtime=parse_HTTP_time(value)
                            logger.debug("Request is using mtime for If-Range.")

                            # Compare mtimes
                            if mtime<math.floor(os.path.getmtime(filename)):
                                # The file has been modified. We have to do a full-file.
                                exit=True
                                logger.debug("File modified since %d (mtime %d).", mtime, math.floor(os.path.getmtime(filename)))

                            # Either way, we're done. Break out.
                            break

                        else:
                            # Value is an ETag
                            value=value.strip(b"\"")
                            logger.debug("Request is using ETag for If-Range.")

                            # Compare ETags
                            etag=ETag(file)
                            if value!=etag:
                                # The file has been modified. We have to do a full-file.
                                exit=True
                                logger.debug("File modified. Client ETag \"%s\", server ETag \"%s\".", value, etag)

                            # Either way, we're done. Break out.
                            break

                # If the If-Range says not to perform a byte-range reply, break out of the loop early
                if exit:
                    break

                # Perform a byte-range reply
                range=line.partition(b": ")[2]
                logger.verbose("Parsing passed range \"%s\"...", range)
                # 'Range' should look like "bytes=x-y"
                # Clip out those first six characters
                range=range[6:]
                # Now, trim our file to match that range, saving the original length and ETag
                # Catch errors in the process and treat them as being ill-formed
                # This includes multipart requests, which are currently considered more trouble than they're worth.
                try:
                    points=[int(point) if len(point)!=0 else None for point in range.partition(b"-")[::2]]
                except:
                    points=[-1, -1]

                    # Log that there was an exception
                    logger.exception("Exception while processing range request for %s. If this is a multipart request, consider submitting an issue on github to add support for your use-case.", line.partition(b": ")[2].decode(), exc_info=True)

                length=len(file)
                # Handle empty points
                if points[0]==None:
                    points[0]=0
                if points[1]==None:
                    points[1]=length-1

                if points[0]<0 or points[1]>length or points[0]>points[1]:
                    # The request cannot be satisfied
                    # (The request doesn't ask for a valid part of the file)
                    # Issue a 416
                    sendResponse("416 Range Not Satisfiable",
                                 "text/html",
                                 generateErrorPage("416 Range Not Satisfiable",
                                                   "The server was unable to satisfy your request for bytes {0} to {1} of a {2} byte file.".format(points[0], points[1], length)),
                                 read.conn,
                                 ["Content-Range: */"+str(length)],
                                 encodings)

                    # Log the problem
                    logger.warning("Could not satisfy request from socket %d for bytes %d to %d of %d byte file %s.", read.fileno(), points[0], points[1], length, filename)

                    # Continue
                    done=True
                    break

                etag=ETag(file)
                file=file[points[0]:points[1]+1]
                # File now only contain the range that was requested.
                # Send it off, with a Content-Range header explaining how much we sent.
                # Respect both GET and HEAD
                # Pass the ETag we calculated
                if method.startswith(b"GET"):
                    sendResponse("206 Partial Content",
                                 mimetype,
                                 file,
                                 read.conn,
                                 ["Content-Range: bytes {0}-{1}/{2}".format(points[0], points[1], length),
                                  "Last-Modified: "+HTTP_time(os.path.getmtime(filename))],
                                 encodings,
                                 etag)
                else:
                    queueResponse(read.conn, constructResponse(basicHeaders("206 Partial Content",
                                                                            mimetype)+
                                                               b"Last-Modified: "+HTTP_time(os.path.getmtime(filename)).encode()+b"\r\n"+
                                                               "Content-Range: bytes {0}-{1}/{2}\r\n".format(points[0], points[1], length).encode(),
                                                               file,
                                                               mimetype,
                                                               encodings,
                                                               etag).partition(b"\r\n\r\n")[0]+b"\r\n\r\n")
                    logger.info("Sent headers for partial request to socket %d.", read.fileno())

                # Now, move on
                done=True
                break

        # Skip the normal full-file processing if we already sent a message
        if done:
            return

        # If we're here, we're not doing a byte range reply
        # If the method is GET, use sendResponse to send the file contents.
        logger.verbose("Performing regular request.")
        if method.startswith(b"GET"):
            sendResponse("200 OK", mimetype, file, read.conn, ["Last-Modified: "+HTTP_time(os.path.getmtime(filename))], encodings)
        # If the method is HEAD, generate the same response, but strip the body
        else:
            queueResponse(read.conn, constructResponse(basicHeaders("200 OK", mimetype)+b"Last-Modified: "+HTTP_time(os.path.getmtime(filename)).encode()+b"\r\n", file, mimetype, encodings).partition(b"\r\n\r\n")[0]+b"\r\n\r\n")
            logger.info("Sent headers to socket %d.", read.fileno())

def writeTo(write, log=True):
    "Performs the operation of writing to the given Connection or set of Connections"

    # Log which thread we're on
    if log:
        logger.debug("Beginning write(s) on thread %s.", current_thread().name)

    # If write isn't a Connection, assume it's a collection of Connections
    if type(write) is not Connection:
        logger.verbose("Attempting iteration over passed collection...")
        for w in write:
            logger.verbose("Beginning write.")
            writeTo(w, False)
        return

    # Handling writes is a lot easier than reads, because the read logic has made all the decisions.
    # Send data unless we encounter an exception
    try:
        while len(write.content)>0:
            logger.verbose("Sending %d bytes...", len(write.content))
            sent=write.conn.send(write.content)
            logger.verbose("Sent %d bytes.", sent)
            write.content=write.content[sent:]

        logger.info("Sent response to socket %d.", write.fileno())
    except:
        logger.exception("Write interrupted on socket %d. %d bytes remaining.", write.fileno(), len(write.content), exc_info=True)

    # Close the connection
    write.conn.close()

def splitInto(arr, n):
    "Splits arr into n roughly equally sized pieces."

    # See how we can divide the length of the array into n pieces
    quotient, remainder=divmod(len(arr), n)
    # Use some neat math and our divisions to split the array in a generator statement
    return (arr[i*quotient+min(i, remainder) : (i+1)*quotient+min(i+1, remainder)] for i in range(n))

# Selector for open connections
selector = selectors.DefaultSelector()

maxThreads=int(config['max_threads'])
timeout=None if config['select_timeout']=="None" else float(config['select_timeout'])
# Generators for thread creation maps
reader = constantIterable(readFrom)
writer = constantIterable(writeTo)
readname = nameIterable("reader")
writename = nameIterable("writer")

# Main function
def main():
    "Infinite loop for connection service"

    # Declare globals
    global reader
    global writer
    global readname
    global writename

    while True:
        # Make sure the accept socket is in the select list
        try:
            selector.register(Connection(sock, False, True), selectors.EVENT_READ)
            logger.verbose("Accept socket was not already in the selection queue.")
        except KeyError:
            pass
        except:
            logger.exception("Problem with accept socket.", exc_info=True)
            raise

        # Select sockets to process
        logger.verbose("Selection...")
        ready = selector.select(timeout)

        # Pull socket lists from the list of ready tuples
        readable=[r[0].fileobj for r in ready if r[1]&selectors.EVENT_READ and r[0].fileobj.fileno()>0]
        writeable=[w[0].fileobj for w in ready if w[1]&selectors.EVENT_WRITE and w[0].fileobj.fileno()>0]

        # Attempt to unregister objects with negative FDs.
        erroneous=[e[0].fileobj for e in ready if e[0].fileobj.fileno()<=0]
        logger.verbose("Selected %d sockets with negative descriptors.", len(erroneous))
        for err in erroneous:
            try:
                selector.unregister(err)
            except:
                logger.verbose("Unable to unregister FD %d.", err.fileno(), exc_info=True)

        # If we're in single-thread mode
        if maxThreads==0:
            # Read from the readable sockets
            logger.verbose("Selected %d readable sockets.", len(readable))
            for read in readable:
                selector.unregister(read)
                readFrom(read)

            # Now, handle the writeable sockets
            logger.verbose("Selected %d writeable sockets.", len(writeable))
            for write in writeable:
                selector.unregister(write)
                writeTo(write)

        # We're performing operations on multiple threads
        # If the maximum number of threads is one, skip over the logic for splitting up the socket arrays
        elif maxThreads==1:
            # Read from the readable sockets in a read thread
            logger.verbose("Selected %d readable sockets.", len(readable))
            reader = None
            if len(readable)!=0:
                reader = createThread(readFrom, next(readname), (readable,))
                reader.start()

            # Make sure we don't double process sockets when we go on to selection
            # The only thing we need is to remove the sockets from the selector list.
            # We do that before waiting for any thread joins.
            list(map(selector.unregister, readable+writeable)) # Faster than a for loop, but arguably a bit hacky

            # Now, handle the writeable sockets in a write thread
            logger.verbose("Selected %d writeable sockets.", len(writeable))
            if len(writable)!=0:
                writer = createThread(writeTo, next(writename), (writeable,))
                writer.start()

            if len(readable)!=0 and config.getboolean('block_on_read'):
                # Wait for the reader to finish
                reader.join()

        # We have to use multiple threads per operation
        else:
            logger.verbose("Selected %d readable sockets.", len(readable))
            # Split up the readable sockets and read from them
            readers=[]
            # Our work pools start as one socket to one thread
            rpools=readable

            # If we don't have enough threads for that, split the work up into maxThreads pools
            if maxThreads<len(readable):
                rpools=splitInto(readable, maxThreads)

            # Create a list of threads to run reads on
            if len(readable)>0:
                readers=list(map(createThread, reader, readname, ((read,) for read in rpools)))
            # ...and start all of those threads
            for thread in readers:
                thread.start()

            logger.verbose("Selected %d writeable sockets.", len(writeable))
            # Split up the writeable sockets and write to them
            writers=[]
            # Our work pools start as one socket to one thread
            wpools=writeable

            # If we don't have enough threads for that, split the work up into maxThreads pools
            if maxThreads<len(writeable):
                wpools=splitInto(writeable, maxThreads)

            # Make sure we don't double process sockets when we go on to selection
            # The only thing we need is to remove the sockets from the selector list.
            # We do that before waiting for any thread joins.
            list(map(selector.unregister, readable+writeable)) # Faster than a for loop, but arguably a bit hacky

            # Create a list of threads to run writes on
            if len(writeable)>0:
                writers=list(map(createThread, writer, writename, ((write,) for write in wpools)))
            # ...and start all of those threads
            for thread in writers:
                thread.start()

            # By here, all of our readers and writers are running.
            # If configured to do so, wait for the readers to finish before returning to select
            if config.getboolean('block_on_read'):
                for r in readers:
                    r.join()

# Run the main code
if __name__ == "__main__":
    main()
