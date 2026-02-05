from io import TextIOWrapper
import datetime
import argparse
import re
from collections import namedtuple

LineTuple = namedtuple("LineTuple", ['time', 'host', 'status'])
class TimeRange(object):

    def __init__(self):
        self.start: LineTuple | None = None
        self.end: LineTuple | None = None

    def startIs(self, line: LineTuple):
        time = line.time
        assert (type(time) == datetime.datetime)
        if self.end is not None:
            assert (time <= self.end.time)
        self.start = line

    def endIs(self, line):
        time = line.time
        assert (type(time) == datetime.datetime)
        if self.start is not None:
            assert (time >= self.start.time)
        self.end = line

    def timeDelta(self):
        return self.end.time - self.start.time

    def __str__(self):
        startTime = self.start.time.strftime("%a %b %d %H:%M:%S")
        endTime = self.end.time.strftime("%a %b %d %H:%M:%S")

        return (f"Host: {self.start.host}" +
                f", time range: {self.timeDelta()}" +
                f", start time: {startTime}" + f", end time: {endTime}")

def parseLog(logFile: TextIOWrapper) -> list[ LineTuple ]:
    lineTuples = []
    for line in logFile.readlines():
        timestamp, host, status = line.rstrip().split('\t')

        timeObj = datetime.datetime.fromisoformat(timestamp)
        lineTuples.append(LineTuple(timeObj, host, status))
    return lineTuples

def getTimeRanges(lines: list[LineTuple], status: str) -> list[TimeRange]:
    result = []

    timeRange = TimeRange()
    currentTup = None
    nextTup = None
    for idx in range(len(lines) - 1):
        currentTup = lines[idx]
        nextTup = lines[idx + 1]

        if (currentTup.status not in ['OK', 'NOT CONNECTED']
                or nextTup.status not in ['OK', 'NOT CONNECTED']):
            raise Exception("Unrecognized log status")

        if currentTup.status == status:
            if nextTup.status == status:
                if timeRange.start is None:
                    timeRange.startIs(currentTup)
            else:
                if timeRange.start is None:
                    timeRange.startIs(currentTup)
                timeRange.endIs(currentTup)
                result.append(timeRange)
                timeRange = TimeRange()
    if timeRange.start is not None and timeRange.end is None:
        timeRange.end = nextTup
        result.append(timeRange)
    return result

def render(uptimeRanges: list[TimeRange], downtimeRanges: list[TimeRange],
           startDate: datetime.datetime | None = None) -> None:
    allTimeRanges = list(
        filter(
            # Ignore entry if end time is before the start date
            lambda r: r.end.time >= startDate,
            sorted(uptimeRanges + downtimeRanges, key=lambda r: r.start.time)
        )
    )
    print(
        f"Activity summary from {startDate.strftime("%Y/%m/%d")} to {allTimeRanges[-1].end.time.strftime("%Y/%m/%d")}")
    print(f"Total monitoring time: {allTimeRanges[ -1 ].end.time - allTimeRanges[ 0 ].start.time}")

    for timeRange in allTimeRanges:
        startTime = timeRange.start.time.strftime("%a %b %d %H:%M:%S")
        endTime = timeRange.end.time.strftime("%a %b %d %H:%M:%S")
        if timeRange.start.status == 'OK':
            print(f"[UP]:   {timeRange.timeDelta()}"
                  f", start: {startTime}"
                  f", end: {endTime}")
        else:
            print(f"[DOWN]: {timeRange.timeDelta()}"
                  f", start: {startTime}"
                  f", end: {endTime}")
    print('-' * 80)

    total = datetime.timedelta()
    print("Up times:")
    for uptimeRange in uptimeRanges:
        total += uptimeRange.timeDelta()
        print(uptimeRange)
    print(f"The connection was up {len(uptimeRanges)} times during the period")
    if uptimeRanges:
        print(f"The total up time was: {total}")
        print(f"Average up time was: {total / len(uptimeRanges)}")
    print('-' * 80)

    total = datetime.timedelta()
    print("Down times:")
    for downtimeRange in downtimeRanges:
        total += downtimeRange.timeDelta()
        print(downtimeRange)
    print(f"The connection was down {len(downtimeRanges)} times during the period")
    if downtimeRanges:
        print(f"The total down time was: {total}")
        print(f"Average down time was: {total / len(downtimeRanges)}")

def parseDate(dateStr: str) -> datetime.datetime:
    # Handle relative dates (e.g., "30d", "2w")
    match = re.match(r'^(\d+)([dwmy])$', dateStr.strip(), re.IGNORECASE)
    if match:
        value, unit = int(match.group(1)), match.group(2).lower()
        days = {'d': value, 'w': value * 7, 'm': value * 30, 'y': value * 365}
        return datetime.datetime.now() - datetime.timedelta(days=days[unit])

    # Try common formats
    for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d %H:%M:%S']:
        try:
            return datetime.datetime.strptime(dateStr, fmt)
        except ValueError:
            continue

    raise ValueError(f"Cannot parse: {dateStr}")

# Examples
def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor network connection")

    parser.add_argument('logFile', default="connection.log", type=str, help="Log file to parse", action="store")
    parser.add_argument('--date', default="30d", type=str,
                        help="Datetime string to specify start date in output. Default: 30d", action="store")
    return parser.parse_args()

def main():
    args = parseArgs()

    with open(args.logFile, "r") as f:
        lines = parseLog(f)
    uptimeRanges = getTimeRanges(lines, 'OK')
    downtimeRanges = getTimeRanges(lines, 'NOT CONNECTED')

    startDate = parseDate(args.date)
    render(uptimeRanges, downtimeRanges, startDate=startDate)

if __name__ == '__main__':
    main()
