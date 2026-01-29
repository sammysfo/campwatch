# campwatch

A simple laptop "application" to check Reserve California for campsite availability.

## What it does
- Checks Reserve California for availability based on your configured criteria
- Sends an email notification when availability is found
- Logs to /tmp when it runs regardless of if a campsite is available or not
- Runs automatically on macOS using a LaunchAgent (launchd) whenever your machine is connected to the internet

## Requirements
- macOS
- Python 3
- A gmail account (though easily could be used with other providers)

## Possible Nearterm TODO
- Support for multiple dates and `PlaceId`'s (watchlist)
- Daily digest emails
- iOS/macOS push notifications

## Install instructions
- TODO
