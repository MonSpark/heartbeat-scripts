# MonSpark Heartbeat Monitor Scripts

This repo is a collection of scripts that send data to the MonSpark Heartbeat Monitor

# What is a Heartbeat Monitor?

Heartbeat Monitor is used to check if a cronjob is running regularly.

After creating a heartbeat monitor, MonSpark provides a unique URL to the user, and the user's cronjob sends requests to this specific URL. If it misses a beat (or is known as a request), MonSpark will create an alert about it.

Users can also choose to get notifications if the cronjob send requests out of it’s schedule.

# Customizable Rules with JSON Path

With MonSpark's Cronjob/Heartbeat Monitor, users can create customized rules based on the request data using JSON paths. For instance, if the `cpu_usage` property is a numeric value and the it’s expected to be less than 80, MonSpark will flag this monitor as an anomaly (or down based on the rule configuration) and generate an alarm accordingly if the `cpu_usage` property is more than 80.

<img src="https://uploads-ssl.webflow.com/62ea25648685a927a480f200/64371557aa5693a8b66f3959_Screenshot%202023-04-12%20at%2023.32.14.png" width="600" />

This adaptable feature makes MonSpark's Cronjob/Heartbeat Monitor a versatile solution for monitoring various aspects of applications, such as daily database backups, CPU usage, disk usage, and more.

The possibilities for configuring rules on number, string, or boolean fields are endless, limited only by the user's imagination.

# Available Scripts


### [CPU](./cpu/)

This script sends the CPU usage to the MonSpark Heartbeat Monitor

### [RAM](./ram/)

This script sends the RAM usage to the MonSpark Heartbeat Monitor

### [DISK](./disk/)

This script sends the Disk usage to the MonSpark Heartbeat Monitor



