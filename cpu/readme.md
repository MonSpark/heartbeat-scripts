# MonSpark Heartbeat Monitor - CPU Usage

This script sends the CPU usage to the MonSpark Heartbeat Monitor

## Prerequisites

- Python 3.6 or above

## Installation

1.  Clone this repo
2.  CD into the directory (e.g. `cd heartbeat-scripts/cpu`)
3.  Install the requirements

    ```bash
    pip3 install -r requirements.txt
    ```

# Usage

1.  Create a heartbeat monitor on MonSpark
2.  Copy the URL from the monitor
3.  Run the script with the URL as follows:

    ```bash
    python3 cpu.py -u <Heartbeat URL>
    ```

# Arguments

```bash
python3 cpu.py [-h] --url URL [-c CPU_SECONDS] [-p POST_SECONDS] [-v]
```

| Short | Long             | Default | Help                                                                                      |
| :---- | :--------------- | :------ | :---------------------------------------------------------------------------------------- |
| `-h`  | `--help`         |         | Show this help message and exit                                                           |
| `-u`  | `--url`          |         | The URL of the MonSpark Heartbeat Monitor                                                 |
| `-c`  | `--cpu-seconds`  | `1`     | The interval in seconds between each CPU usage collection                                 |
| `-p`  | `--post-seconds` | `60`    | The interval in seconds between each data send to the MonSpark Heartbeat Monitor          |
| `-v`  | `--verbose`      | `1`     | The level of verbosity of the script (0: only errors, 1: errors and posts, 2: all output) |
