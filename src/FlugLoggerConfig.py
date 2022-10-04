#
# This file handles setting up logging.
#
import logging
import logging.handlers
import sys

FLUG_LOGGER_DEFAULT_FMT = "[@ %(asctime)s]--[%(levelname)8s]--[%(funcName)20s()] %(message)s"

class FlugLoggerConfig:
    @staticmethod
    def init(logLevel: str = "DEBUG", logFmt: str = FLUG_LOGGER_DEFAULT_FMT, logStdout: bool = True,
             logFile: str = None, logFileSize: int = 1e7, logFileNum: int = 5):
        """
        Configure the logging module/setup handlers (...).
        
        `logLevel` Sets the log level. This can be one of `"INFO"`, `"WARN"`, `"DEBUG"`, `"ERROR"` or `"CRITICAL"`.  (`str`)
        
        `logFmt` Sets the format for the logger. If not set, a default format will be used. (`str`)
        
        `logStdout` Enables (`True`)/Disables (`False`) Logging to `stdout` (Standard Output). (`bool`)
        
        `logFile` Sets the file to log to. If set to `None`, `FlugLogger` won't log into a separate file. (`str`)
        
        `logFileSize` Maximum amount of bytes a log file is allowed to grow to before being rotated out. (`int`)
        
        `logFileNum` Maximum amount of log files to be created before deleting old ones.
        """
        logLevel = logLevel
        logFmt = logFmt
        logStdout = logStdout
        logFile = logFile
        logFileSize = logFileSize
        logFileNum = logFileNum

        # formatter
        fmt = logging.Formatter(logFmt)

        # temporary list of handlers
        handlers = []

        # add a stream handler for stdout if enabled
        if logStdout == True:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            handlers.append(sh)

        # add a file handler for the log file if enabled
        if logFile != None:
            fh = logging.handlers.RotatingFileHandler(logFile, maxBytes=logFileSize, backupCount=logFileNum)
            fh.setFormatter(fmt)
            handlers.append(fh)

        # initialize and configure the logger
        logging.basicConfig(level = logLevel, format=logFmt, handlers=handlers)
        log = logging.getLogger("FlugLog")
        log.setLevel(logLevel)
