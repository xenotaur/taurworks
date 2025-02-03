import sys
import argparse
from datetime import datetime, timedelta
from collections import defaultdict
import pytz
from tzlocal import get_localzone  # For system timezone
from zoneinfo import ZoneInfo  # For Python's built-in timezone support (Python 3.9+)

def parse_timestamps(timestamp_lines, input_tz):
    events = []
    for line in timestamp_lines:
        try:
            naive_dt = datetime.strptime(line.strip(), "%Y%m%d:%H%M%S")
            localized_dt = naive_dt.replace(tzinfo=input_tz)  # Set the input timezone
            events.append(localized_dt)
        except ValueError:
            pass  # Ignore invalid lines
    return sorted(events)

def group_events(events):
    grouped = defaultdict(list)
    current_group = []

    for i, event in enumerate(events):
        if not current_group:
            current_group.append(event)
        else:
            # Check if within an hour of the last event in the group
            if (event - current_group[-1]).seconds <= 3600:
                current_group.append(event)
            else:
                grouped[current_group[0].date()].append(current_group)
                current_group = [event]
    
    # Add the final group
    if current_group:
        grouped[current_group[0].date()].append(current_group)
    return grouped

def format_group(group, output_tz, show_timestamps):
    start_time = group[0].astimezone(output_tz).strftime('%I:%M%p').lower()
    if len(group) == 1:
        group_desc = f"  - unknown duration: {start_time} (1 timestamp)"
    else:
        end_time = group[-1].astimezone(output_tz).strftime('%I:%M%p').lower()
        duration = (group[-1] - group[0]).seconds // 60
        group_desc = f"  - {duration} minutes: {start_time} to {end_time} ({len(group)} timestamps)"
    
    if show_timestamps:
        timestamp_list = [
            ts.astimezone(output_tz).strftime('%Y-%m-%d %H:%M:%S %Z') for ts in group
        ]
        group_desc += "\n    " + "\n    ".join(timestamp_list)
    
    return group_desc

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Group timestamps by date and time.")
    parser.add_argument('--input_timezone', help="Input timezone (e.g., UTC, EST). Defaults to system timezone.", default=None)
    parser.add_argument('--output_timezone', help="Output timezone (e.g., UTC, EST). Defaults to system timezone.", default=None)
    parser.add_argument('--show_timestamps', action='store_true', help="Explicitly list timestamps in each group.")
    args = parser.parse_args()
    
    # Determine timezones
    input_tz = ZoneInfo(args.input_timezone) if args.input_timezone else get_localzone()
    output_tz = ZoneInfo(args.output_timezone) if args.output_timezone else get_localzone()

    # Read timestamp lines from standard input
    timestamp_lines = sys.stdin.readlines()
    
    # Parse and group events
    events = parse_timestamps(timestamp_lines, input_tz)
    grouped = group_events(events)
    
    # Print formatted output
    for date, groups in grouped.items():
        date_str = date.strftime("%B %d, %Y")
        print(f"{date_str}:")
        for group in groups:
            print(format_group(group, output_tz, args.show_timestamps))

if __name__ == "__main__":
    main()

