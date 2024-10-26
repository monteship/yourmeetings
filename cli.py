#!/usr/bin/env python3
# Inspired by: Chmouel Boudjnah <chmouel@chmouel.com>
# Author: Misha Ship <monteship@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#

import argparse
import datetime
import html
import json
import os.path
import re
import shutil
import subprocess
import sys
import typing
import webbrowser
from dataclasses import dataclass

import dateutil.parser as dtparse
import dateutil.relativedelta as dtrel
import yaml

REG_TSV = re.compile(
    r"(?P<startdate>(\d{4})-(\d{2})-(\d{2}))\s*?(?P<starthour>(\d{2}:\d{2}))\s*(?P<enddate>(\d{4})-(\d{2})-(\d{"
    r"2}))\s*?(?P<endhour>(\d{2}:\d{2}))\s*(?P<calendar_url>(https://\S+))\s*(?P<meet_url>(https://\S*)?)\s*("
    r"?P<title>.*)$"
)
NOTIFY_PROGRAM: str = shutil.which("notify-send") or ""

# Load configuration from YAML file
with open("config.yml", "r") as ymlfile:
    config = yaml.safe_load(ymlfile)

DEFAULT_CALENDAR = config["calendar"]
NOTIFY_ICON = config["notify_icon"]
GOOGLE_CALENDAR_PUBLIC_URL = config["google_calendar_public_url"]
UPCOMING_LENGTH = config["upcoming_length"]


@dataclass
class Event:
    title: str
    start_date: datetime.datetime
    end_date: datetime.datetime
    meet_url: str

    @staticmethod
    def is_soon(event: "Event") -> bool:
        event_in = dtrel.relativedelta(event.start_date, datetime.datetime.now())
        return event_in.minutes < 10

    def __str__(self) -> str:
        event_in = dtrel.relativedelta(self.start_date, datetime.datetime.now())
        message = ""
        if event_in.days:
            message = f"{self.start_date:%a %H:%M}"
        elif event_in.hours or event_in.minutes > 10:
            message = f"{self.start_date:%H:%M}"
        elif event_in.minutes:
            message = f"{event_in.minutes} min"
            if event_in.minutes in [5, 1]:
                notify(self.title, self.start_date)

        return f"{message} - {self.title}"


class EventsManager:
    def __init__(self, events: list[Event]):
        self.events = events

    def upcoming_today(self) -> typing.Tuple[Event | str, bool]:
        today_events = [
            event
            for event in self.events
            if event.start_date.date() == datetime.datetime.now().date()
        ]

        today_events = sorted(today_events, key=lambda x: x.start_date)

        if not today_events:
            return "No meeting 🏖️", False

        return today_events[0], Event.is_soon(today_events[0])

    def agenda(self) -> list[Event]:
        events = sorted(self.events, key=lambda x: x.start_date)
        return events


def elipsis(string: str, length: int) -> str:
    # remove all html elements first from it
    hstring = re.sub(r"<[^>]*>", "", string)
    if len(hstring) > length:
        return string[: length - 3] + "..."
    return string


def gcalcli_output(args: argparse.Namespace) -> list[re.Match]:
    with subprocess.Popen(
        "gcalcli --nocolor --calendar={calendar} agenda today --nodeclined  --details=end --details=url --tsv ".format(
            calendar=args.calendar
        ),
        shell=True,
        stdout=subprocess.PIPE,
    ) as cmd:
        return process_file(cmd.stdout)


def process_file(fp) -> list[re.Match]:
    ret = []
    for _line in fp.readlines():  # type: ignore
        try:
            line = str(_line.strip(), "utf-8")
        except TypeError:
            line = _line.strip()
        match = REG_TSV.match(line)
        if not match:
            continue
        end_date = dtparse.parse(
            f"{match.group('enddate')} {match.group('endhour')}"  # type: ignore
        )
        if datetime.datetime.now() > end_date:
            continue

        if not match:
            continue
        ret.append(match)
    return ret


def retrieve_events(lines: list[re.Match]) -> EventsManager:
    events = []
    for match in lines:
        title = match.group("title")
        title = html.escape(title)
        start_date = dtparse.parse(
            f"{match.group('startdate')} {match.group('starthour')}"
        )
        meet_url = match.group("meet_url")
        event = Event(title, start_date, meet_url)
        events.append(event)
    return EventsManager(events)


def notify(
    title: str,
    start_date: datetime.datetime,
):
    if NOTIFY_PROGRAM == "":
        return
    other_args = []
    milliseconds = 1 * 60 * 1000
    other_args += ["-t", str(milliseconds)]
    subprocess.call(
        [
            NOTIFY_PROGRAM,
            "-i",
            os.path.expanduser(NOTIFY_ICON),
            title,
            f"Start: {start_date.strftime('%H:%M')}",
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--calendar",
        help="Specify the calendar to use",
        default=config["calendar"],
    )

    parser.add_argument(
        "--open-meet-url",
        action="store_true",
        help="click on invite url",
    )

    return parser.parse_args()


def open_meet_url(up_coming: Event | str):
    if isinstance(up_coming, str):
        print("No meeting 🏖️")
        return
    webbrowser.open_new_tab(up_coming.meet_url)
    sys.exit(0)


def main():
    args = parse_args()
    matches = gcalcli_output(args)
    events_manager = retrieve_events(matches)
    up_coming, soon = events_manager.upcoming_today()

    if args.open_meet_url:
        open_meet_url(up_coming)
        return

    json.dump(
        {
            "text": elipsis(up_coming, UPCOMING_LENGTH),
            "tooltip": "\n".join([str(event) for event in events_manager.agenda()]),
            "class": "soon" if soon else None,
        },
        sys.stdout,
    )


if __name__ == "__main__":
    main()
