#!/bin/bash
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

DEFAULT_CALENDAR="monteship@gmail.com"
CALENDAR_URL="https://calendar.google.com/calendar/u/0/r"
UPCOMING_LENGTH=50
NOTIFY_PROGRAM=$(command -v notify-send)

function elipsis() {
    local string="$1"
    local length="$2"
    echo "$string" | sed -E 's/<[^>]*>//g' | awk -v len="$length" '{ if (length > len) print substr($0, 1, len-3) "…"; else print $0 }'
}

html_escape() {
    echo "$1" | sed \
        -e 's/&/\&amp;/g' \
        -e 's/</\&lt;/g' \
        -e 's/>/\&gt;/g' \
        -e 's/"/\&quot;/g' \
        -e "s/'/\&apos;/g"
}

function notify() {
    local title="$1"
    local start_date="$2"
    if [[ -n "$NOTIFY_PROGRAM" ]]; then
        "$NOTIFY_PROGRAM" -i /usr/share/icons/hicolor/scalable/apps/org.gnome.Calendar.svg "$title" "Start: $start_date" -t 60000
    fi
}

function open_meet_url() {
    local meet_url="$1"
    if [[ -n "$meet_url" ]]; then
        xdg-open "$meet_url"
    else
        echo "No meeting 🏖️"
    fi
}


function get_events() {
    gcalcli --nocolor --calendar="$DEFAULT_CALENDAR" agenda today --nodeclined --details=end --details=url --tsv |
        grep -E "https://.*" |
        while IFS=$'\t' read -r start_date start_hour end_date end_hour calendar_url meet_url title; do
            start_timestamp=$(date -d "$start_date $start_hour" +%s)
            end_timestamp=$(date -d "$end_date $end_hour" +%s)
            now=$(date +%s)
            title=$(html_escape "$title")
            if [[ $now -lt $end_timestamp ]]; then
                printf "%s\t%s\t%s\n" "$start_timestamp" "$meet_url" "$title"
            fi
        done
}

function show_today_upcoming() {
    get_events | while IFS=$'\t' read -r start_timestamp meet_url title; do
        start_date=$(date -d "@$start_timestamp" +"%H:%M")
        minutes_left=$(( (start_timestamp - $(date +%s)) / 60 ))
        if (( minutes_left > 0 )); then
            echo "$start_date - $title"
        fi

    done

}

function show_agenda() {
    get_events | while IFS=$'\t' read -r start_timestamp meet_url title; do
        start_date=$(date -d "@$start_timestamp" +"%a %H:%M")
        echo "$start_date - $title"
    done
}

function main() {
    local open_meet=false
    local url_to_open="$CALENDAR_URL"
    if [[ "$1" == "--open" ]]; then
        open_meet=true
    fi

    upcoming_event=$(get_events | head -n 1)
    if [[ -z "$upcoming_event" ]]; then
        text="No meeting \ud83c\udfd6\ufe0f"
    else
        start_timestamp=$(echo "$upcoming_event" | cut -f1)
        meet_date=$(date -d "@$start_timestamp" +"%Y-%m-%d")
        today_date=$(date +"%Y-%m-%d")
        minutes_left=$(( (start_timestamp - $(date +%s)) / 60 ))

        url_to_open=$(echo "$upcoming_event" | cut -f2)

        if [[ "$meet_date" != "$today_date" ]]; then
            text="No meeting \ud83c\udfd6\ufe0f"
        elif (( minutes_left < 10 )); then
            text=$(elipsis "$minutes_left min - $(echo "$upcoming_event" | cut -f3)" "$UPCOMING_LENGTH")
        else
            text=$(elipsis "$(date -d "@$start_timestamp" +"%H:%M") - $(echo "$upcoming_event" | cut -f3)" "$UPCOMING_LENGTH")
        fi
    fi

    start_timestamp=$(echo "$upcoming_event" | cut -f1)
    meet_url=$(echo "$upcoming_event" | cut -f2)
    start_date=$(date -d "@$start_timestamp" +"%H:%M")
    minutes_left=$(( (start_timestamp - $(date +%s)) / 60 ))

    if (( minutes_left < 10 )); then
        notify "$text" "$start_date"
    fi

    if $open_meet; then
        open_meet_url "$url_to_open"
        exit 0
    fi

    tooltip=$(show_agenda | jq -R -s '.')

    class="$([ $minutes_left -lt 10 ] && echo 'soon' || echo '')"

    python3 -c "import sys, json; print(json.dumps({'text': '$text', 'tooltip': $tooltip, 'class': '$class'}))"


}

main "$@"
