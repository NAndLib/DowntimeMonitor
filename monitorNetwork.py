import os
import sys
import socket
import datetime
import argparse
from time import sleep
from urllib.parse import urlparse
import http.client as httplib

from typing import TextIO

DEFAULT_HOST = "8.8.8.8"
DEFAULT_PORT = 443
DEFAULT_TIMEOUT = 5
LOG_FMT = "{timestamp}\t{host}:{port}\t{status}\n"


def internet(host: str = DEFAULT_HOST,
             port: int = DEFAULT_PORT,
             timeout: int = DEFAULT_TIMEOUT,
             verbose: bool = False) -> bool:
    """
    Generates a small HEAD request to verify connectivity
    """
    if host.startswith('http'):
        host = urlparse(host).netloc
    conn = httplib.HTTPSConnection(host, port, timeout=timeout)
    try:
        if verbose:
            print(f"internet( host={host}, port={port}, timeout={timeout} )")
        conn.request("HEAD", "/")
        return True
    except socket.timeout:
        if verbose:
            print("Timed out")
        return False
    except socket.gaierror:
        if verbose:
            print("Resolution error")
        return False
    except KeyboardInterrupt:
        if verbose:
            print("Keyboard interrupt")
        raise
    except Exception as e:
        if verbose:
            print(f"Unknown Exception({e})")
        return False
    finally:
        conn.close()


def timestamp():
    """ Get Current timestamp string """
    return datetime.datetime.now().isoformat()


def parseArgs():
    parser = argparse.ArgumentParser(description="Monitor network connection")

    parser.add_argument(
        '--host',
        '-H',
        dest='host',
        default=DEFAULT_HOST,
        help=f"Monitor using the given host. Default: {DEFAULT_HOST}")
    parser.add_argument('--port',
                        '-p',
                        default=DEFAULT_PORT,
                        help=f"Use the given port. Default: {DEFAULT_PORT}")
    parser.add_argument(
        '--overwrite-log',
        '-O',
        dest='overwrite',
        action='store_true',
        help="Overwrite the log file if it exists instead of appending")
    parser.add_argument(
        '--logFile',
        '-l',
        default="connection.log",
        help="Name of log file to use. Default: connection log")
    parser.add_argument('--stdout',
                        action='store_true',
                        help="Use stdout instead of output file")
    parser.add_argument('--interval',
                        '-i',
                        metavar='SECONDS',
                        type=int,
                        default=5,
                        help="Time in seconds to wait before checking "
                        "the host again. Default: 5.")
    parser.add_argument(
        '--timeout',
        '-t',
        metavar='SECONDS',
        type=int,
        default=1,
        help="Timeout in seconds for connection check. Default: 1")
    parser.add_argument('--verbose',
                        '-v',
                        action='store_true',
                        help="Verbose output")
    parser.add_argument('--daemon',
                        '-d',
                        action='store_true',
                        help="Tells the script to run in daemon mode")

    return parser.parse_args()


def writeLog(file: TextIO, host: str, port: int, status: str):
    file.write(
        LOG_FMT.format(timestamp=timestamp(),
                       host=host,
                       port=port,
                       status=status))
    file.flush()


if __name__ == '__main__':
    args = parseArgs()
    if args.daemon:
        sys.stderr.write("Deamon mode currently unsupported")
        exit(1)

    logFile = args.logFile
    outFile = None
    if args.stdout:
        outFile = sys.stdout
    elif not os.path.isfile(logFile) or args.overwrite:
        outFile = open(logFile, 'w', encoding="UTF-8")
    else:
        outFile = open(logFile, 'a', encoding="UTF-8")

    host = args.host
    port = args.port
    print(f"Starting monitoring with {host} at {timestamp()}")
    startTime = datetime.datetime.now()
    try:
        while True:
            ok = internet(host,
                          port,
                          timeout=args.timeout,
                          verbose=args.verbose)
            if ok:
                writeLog(outFile, host, port, 'OK')
            else:
                writeLog(outFile, host, port, 'NOT CONNECTED')

            elapsed = datetime.datetime.now() - startTime
            if args.stdout or args.daemon:
                sys.stdout.write(
                    f"Elapsed time: {elapsed} "
                    f"[{'OK' if ok else 'NOT CONNECTED'}]{' ' * 20}\n")
            else:
                sys.stdout.write(
                    f"Elapsed time: {elapsed} "
                    f"[{'OK' if ok else 'NOT CONNECTED'}]{' ' * 20}\r")
            sys.stdout.flush()

            sleep(args.interval)
    except KeyboardInterrupt:
        print(f"\nStopping monitor at {timestamp()}")
    outFile.close()
