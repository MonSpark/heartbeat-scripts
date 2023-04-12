import shutil
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


def collect_disk_usage(disk_path: str, disk_usage: list[dict], disk_interval_seconds: int, verbose: bool = False):
    disk_interval_started_at = time.time()
    next_disk_usage_collection_at = disk_interval_started_at + disk_interval_seconds

    while not exit.is_set():
        # Set the start time of the loop
        loop_start_time = time.time()
        disk = shutil.disk_usage(disk_path)
        disk_percent = 100 - (disk.free / disk.total) * 100

        usage = {'date': loop_start_time, 'disk_percent': disk_percent}
        disk_usage.append(usage)
        if verbose:
            # Print the disk usage and date with milliseconds
            date = datetime.fromtimestamp(loop_start_time).strftime(
                '%Y-%m-%d %H:%M:%S.%f')[:-3]
            print(f'{date}: {disk_percent:.2f}%')

        # Clear the list of disk usage data older than 15 minutes
        ago_15min = time.time() - 900
        # Filter in-place
        disk_usage[:] = [x for x in disk_usage if x['date'] > ago_15min]

        # Sleep for the remaining time
        now = time.time()
        wait_for = next_disk_usage_collection_at - now
        if wait_for > 0:
            exit.wait(wait_for)
        next_disk_usage_collection_at += disk_interval_seconds


def send_disk_usage(url: str, disk_usage_1min_avg: float, disk_usage_5min_avg: float, disk_usage_15min_avg: float, verbose: bool = False):
    # Print the disk usage
    if verbose:
        print('Sending disk usage to MonSpark Heartbeat Monitor')
        print(f'Disk usage (1 min avg): {disk_usage_1min_avg:.2f}%')
        print(f'Disk usage (5 min avg): {disk_usage_5min_avg:.2f}%')
        print(f'Disk usage (15 min avg): {disk_usage_15min_avg:.2f}%')
    # Retry sending the data 3 times
    for i in range(3):
        try:
            requests.post(url, json={
                'disk_usage_1min_avg': disk_usage_1min_avg,
                'disk_usage_5min_avg': disk_usage_5min_avg,
                'disk_usage_15min_avg': disk_usage_15min_avg,
            })
            if verbose:
                print('Data sent to MonSpark Heartbeat Monitor')
            break
        except Exception as e:
            print(e)
            if i == 2:
                print('Failed to send data to MonSpark Heartbeat Monitor')


def main(url: str, disk_path: str, disk_interval_seconds: int, post_interval_seconds: int, verbose_level: int = 0):
    '''
    This function collects the disk usage and sends it to the MonSpark Heartbeat Monitor

    ### Parameters
    1. `url`: The URL of the MonSpark Heartbeat Monitor
    2. `disk_interval_seconds`: The interval in seconds between each disk usage collection
    3. `post_interval_seconds`: The interval in seconds between each data send to the MonSpark Heartbeat Monitor
    4. `verbose_level`: The level of verbosity of the script (0: only errors, 1: errors and posts, 2: all output) (default:
    '''
    disk_usage = []
    post_interval_started_at = time.time()
    next_data_send_at = post_interval_started_at + post_interval_seconds

    # Start the disk usage collection thread
    disk_usage_thread = threading.Thread(
        target=collect_disk_usage,
        args=(disk_path, disk_usage, disk_interval_seconds, verbose_level > 1),
        daemon=True
    )
    disk_usage_thread.start()

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
        # Get the disk usage for the last 1, 5 and 15 minutes

        # Get the disk usage for the last 1 minute
        ago_1min = now - 60
        disk_usage_1min = [
            x['disk_percent'] for x in disk_usage if x['date'] > ago_1min
        ]
        disk_usage_1min_avg = sum(disk_usage_1min) / len(disk_usage_1min)

        # Get the disk usage for the last 5 minutes
        ago_5min = now - 300
        disk_usage_5min = [
            x['disk_percent'] for x in disk_usage if x['date'] > ago_5min
        ]
        disk_usage_5min_avg = sum(disk_usage_5min) / len(disk_usage_5min)

        # Get the disk usage for the last 15 minutes
        ago_15min = now - 900
        disk_usage_15min = [
            x['disk_percent'] for x in disk_usage if x['date'] > ago_15min
        ]
        disk_usage_15min_avg = sum(disk_usage_15min) / len(disk_usage_15min)

        # Send the disk usage to the MonSpark Heartbeat Monitor
        send_disk_usage(
            url,
            disk_usage_1min_avg,
            disk_usage_5min_avg,
            disk_usage_15min_avg,
            verbose_level > 0
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='MonSpark Heartbeat Monitor - Disk',
        description='This script sends the disk usage to the MonSpark Heartbeat Monitor',
    )
    parser.add_argument(
        '--url', '-u',
        type=str,
        required=True,
        help='The URL of the MonSpark Heartbeat Monitor',
    )
    parser.add_argument(
        '--disk-path', '-d',
        type=str,
        default='/',
        help='The path of the disk to monitor',
    )
    parser.add_argument(
        '--collection-seconds', '-c',
        type=int,
        default=1,
        help='The interval in seconds between each disk usage collection',
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
        args.disk_path,
        args.collection_seconds,
        args.post_seconds,
        args.verbose
    )
