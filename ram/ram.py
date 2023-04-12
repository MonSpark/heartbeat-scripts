import psutil
import requests
import time
import argparse
import threading
from datetime import datetime
import signal

exit = threading.Event()


def quit(sig, _frame):
    print(f"Interrupted by {signal.Signals(sig).name}, shutting down")
    exit.set()


def collect_ram_usage(ram_usage: list[dict], ram_interval_seconds: int, verbose: bool = False):
    ram_interval_started_at = time.time()
    next_ram_usage_collection_at = ram_interval_started_at + ram_interval_seconds

    while not exit.is_set():
        # Set the start time of the loop
        loop_start_time = time.time()
        mem = psutil.virtual_memory()
        ram_percent = mem.percent

        usage = {'date': loop_start_time, 'ram_percent': ram_percent}
        ram_usage.append(usage)
        if verbose:
            # Print the RAM usage and date with milliseconds
            date = datetime.fromtimestamp(loop_start_time).strftime(
                '%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f'{date}: {ram_percent:.2f}%')

        # Clear the list of RAM usage data older than 15 minutes
        ago_15min = time.time() - 900
        # Filter in-place
        ram_usage[:] = [x for x in ram_usage if x['date'] > ago_15min]

        # Sleep for the remaining time
        now = time.time()
        wait_for = next_ram_usage_collection_at - now
        if wait_for > 0:
            exit.wait(wait_for)
        next_ram_usage_collection_at += ram_interval_seconds


def send_ram_usage(url: str, ram_usage_1min_avg: float, ram_usage_5min_avg: float, ram_usage_15min_avg: float, verbose: bool = False):
    # Print the RAM usage
    if verbose:
        print('Sending RAM usage to MonSpark Heartbeat Monitor')
        print(f'RAM usage (1 min avg): {ram_usage_1min_avg:.2f}%')
        print(f'RAM usage (5 min avg): {ram_usage_5min_avg:.2f}%')
        print(f'RAM usage (15 min avg): {ram_usage_15min_avg:.2f}%')
    # Retry sending the data 3 times
    for i in range(3):
        try:
            requests.post(url, json={
                'ram_usage_1min_avg': ram_usage_1min_avg,
                'ram_usage_5min_avg': ram_usage_5min_avg,
                'ram_usage_15min_avg': ram_usage_15min_avg,
            })
            if verbose:
                print('Data sent to MonSpark Heartbeat Monitor')
            break
        except Exception as e:
            print(e)
            if i == 2:
                print('Failed to send data to MonSpark Heartbeat Monitor')


def main(url: str, ram_interval_seconds: int, post_interval_seconds: int, verbose_level: int = 0):
    '''
    This function collects the RAM usage and sends it to the MonSpark Heartbeat Monitor

    ### Parameters
    1. `url`: The URL of the MonSpark Heartbeat Monitor
    2. `ram_interval_seconds`: The interval in seconds between each RAM usage collection
    3. `post_interval_seconds`: The interval in seconds between each data send to the MonSpark Heartbeat Monitor
    4. `verbose_level`: The level of verbosity of the script (0: only errors, 1: errors and posts, 2: all output) (default: 0)
    '''
    ram_usage = []
    post_interval_started_at = time.time()
    next_data_send_at = post_interval_started_at + post_interval_seconds
    # Start the RAM usage collection thread
    ram_usage_thread = threading.Thread(
        target=collect_ram_usage,
        args=(ram_usage, ram_interval_seconds, verbose_level > 1),
        daemon=True
    )
    ram_usage_thread.start()

    while not exit.is_set():
        # Wait for the post interval to pass
        now = time.time()
        wait_for = next_data_send_at - now
        if wait_for > 0:
            exit.wait(wait_for)
            if exit.is_set():
                break
        now = time.time()
        next_data_send_at += post_interval_seconds

        # Get the RAM usage for the last 1, 5 and 15 minutes

        # Get the RAM usage for the last 1 minute
        ago_1min = now - 60
        ram_usage_1min = [
            x['ram_percent'] for x in ram_usage if x['date'] > ago_1min
        ]
        ram_usage_1min_avg = sum(ram_usage_1min) / len(ram_usage_1min)

        # Get the RAM usage for the last 5 minutes
        ago_5min = now - 300
        ram_usage_5min = [
            x['ram_percent'] for x in ram_usage if x['date'] > ago_5min
        ]
        ram_usage_5min_avg = sum(ram_usage_5min) / len(ram_usage_5min)

        # Get the RAM usage for the last 15 minutes
        ago_15min = now - 900
        ram_usage_15min = [
            x['ram_percent'] for x in ram_usage if x['date'] > ago_15min
        ]
        ram_usage_15min_avg = sum(ram_usage_15min) / len(ram_usage_15min)

        # Send the RAM usage to the MonSpark Heartbeat Monitor
        send_ram_usage(
            url,
            ram_usage_1min_avg,
            ram_usage_5min_avg,
            ram_usage_15min_avg,
            verbose_level > 0
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='MonSpark Heartbeat Monitor - RAM',
        description='This script sends the RAM usage to the MonSpark Heartbeat Monitor',
    )
    parser.add_argument(
        '--url', '-u',
        type=str,
        required=True,
        help='The URL of the MonSpark Heartbeat Monitor',
    )
    parser.add_argument(
        '--collection-seconds', '-c',
        type=int,
        default=1,
        help='The interval in seconds between each RAM usage collection',
    )
    parser.add_argument(
        '--post-seconds', '-p',
        type=int,
        default=60,
        help='The interval in seconds between each data send to the MonSpark Heartbeat Monitor',
    )
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=1,
        help='The level of verbosity of the script (0: only errors, 1: errors and posts, 2: all output)',
    )
    args = parser.parse_args()

    import signal
    for sig in (signal.SIGTERM, signal.SIGHUP, signal.SIGINT):
        signal.signal(sig, quit)

    main(
        args.url,
        args.collection_seconds,
        args.post_seconds,
        args.verbose
    )
