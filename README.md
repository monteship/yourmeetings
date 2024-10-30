# `yourmeetings` is a simple [waybar](https://github.com/Alexays/Waybar) module that shows the next meeting in your Google Calendar.

## Inspired by [Chmouel Boudjnah](https://github.com/chmouel) [nextmeeting](https://github.com/chmouel/nextmeeting) 
A Bash script that checks Google Calendar for upcoming events and provides notifications, using `notify-send` for alerts and optionally opening Google Meet links. The script supports customizable calendar selection and notification display length.
In title shows only today's events, in the body shows the next event.
## Features
- **Waybar Integration**: Displays the next event in the Waybar status bar.
- **Event Notifications**: Notifies when an event is starting within the next 10 minutes.
- **Meeting URL Opening**: Automatically opens Google Meet URLs for upcoming events.
- **Agenda Display**: Lists events in a concise format with an option to specify text length.
- **Customization**: Options to select the calendar, specify notification length, and customize notification timing.

## Requirements

- **gcalcli**: A command-line interface for Google Calendar.
- **notify-send**: Used for desktop notifications (common on Linux systems).
- **jq**: Optional, for formatting output when generating JSON.
- **xdg-open**: Required for opening URLs in the default browser.

## Installation

1. Clone the repository or download the script directly.
2. Ensure that dependencies (`gcalcli`, `notify-send`, `jq`, and `xdg-open`) are installed on your system.
3. Calendar name can be obtained with `gcalcli list`
4. You need to install [gcalcli](https://github.com/insanum/gcalcli) and [setup
the google Oauth integration](https://github.com/insanum/gcalcli?tab=readme-ov-file#initial-setup) with google calendar.
5. Setup module in waybar config file.
```json
    "custom/agenda": {
        "format": "{}",
        "exec": "/bin/bash /event_notifier.sh --calendar Work --len 50",
        "on-click": "/bin/bash /event_notifier.sh --calendar Work --len 50 --open",
        "interval": 59,
        "return-type": "json",
        "tooltip": "true"
    },
```
### Optional
You can style some of the waybar item with the following CSS:

```css
#custom-agenda {
  color: #696969;
}
```

If you enable the option "--notify-min-before-events it will output a class
`soon` if the events is coming soon, you can style it with:

```css
#custom-agenda.soon {
  color: #eb4d4b;
}
```

## Copyright

[Apache-2.0](./LICENSE)

## Authors
- Misha Ship <https://github.com/monteship>
