# campwatch

A simple laptop "application" to check reservecalifornia.com for campsite availability.

## What it does
- Checks ReserveCalifornia for availability based on your configured criteria
- Sends an email notification when availability is found
- Logs to /tmp when it runs regardless of if the campsite is available or not
- Runs automatically on macOS using a LaunchAgent (launchd)

## Requirements
- macOS
- Python 3
- A gmail account (though easily could be used with other providers)
