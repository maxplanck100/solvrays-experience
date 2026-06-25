"""
Smart Traffic Signal Controller
Challenge 1

Dynamically allocates green-light duration across four intersection roads
based on vehicle counts using proportional distribution over a 120-second cycle.
"""

import json
import os
from datetime import datetime


ROADS = ["North", "East", "South", "West"]
BASE_GREEN_TIME = 10        # seconds guaranteed to each road
TOTAL_CYCLE_TIME = 120      # seconds
REMAINING_TIME = TOTAL_CYCLE_TIME - BASE_GREEN_TIME * len(ROADS)  # 80 seconds
CONGESTION_HIGH = 50
CONGESTION_MODERATE = 25
LOG_FILE = "traffic_log.json"


def get_vehicle_counts() -> dict[str, int]:
    """Prompt the user for vehicle counts on all four roads."""
    print("\nEnter the number of vehicles waiting at each road.")
    counts = {}
    for road in ROADS:
        while True:
            raw = input(f"  {road}: ").strip()
            if not raw.isdigit():
                print(f"    Invalid input. Enter a non-negative integer.")
                continue
            value = int(raw)
            if value > 9999:
                print(f"    Value too large. Maximum is 9999.")
                continue
            counts[road] = value
            break
    return counts


def compute_green_times(counts: dict[str, int]) -> dict[str, int]:
    """
    Compute integer green times ensuring the total equals exactly TOTAL_CYCLE_TIME.

    Uses floor allocation plus residual assignment to the highest-traffic road
    to absorb rounding error and preserve the 120-second invariant.
    """
    total_vehicles = sum(counts.values())

    if total_vehicles == 0:
        # All roads get equal time when no vehicles are present.
        equal_time = TOTAL_CYCLE_TIME // len(ROADS)
        return {road: equal_time for road in ROADS}

    raw_times = {
        road: BASE_GREEN_TIME + (counts[road] / total_vehicles) * REMAINING_TIME
        for road in ROADS
    }

    floored = {road: int(raw_times[road]) for road in ROADS}
    residual = TOTAL_CYCLE_TIME - sum(floored.values())

    # Assign residual seconds to the road with the largest fractional part.
    fractional_order = sorted(
        ROADS,
        key=lambda r: raw_times[r] - floored[r],
        reverse=True
    )
    for i in range(residual):
        floored[fractional_order[i % len(ROADS)]] += 1

    return floored


def classify_congestion(vehicle_count: int) -> str:
    if vehicle_count > CONGESTION_HIGH:
        return "HIGH"
    if vehicle_count >= CONGESTION_MODERATE:
        return "MODERATE"
    return "LOW"


def generate_report(counts: dict[str, int], green_times: dict[str, int]) -> None:
    """Print a formatted traffic report to the console."""
    total_vehicles = sum(counts.values())
    congestion_levels = {road: classify_congestion(counts[road]) for road in ROADS}

    highest_road = max(counts, key=lambda r: counts[r])
    overall_status = classify_congestion(counts[highest_road])

    print("\n" + "=" * 52)
    print(" SMART TRAFFIC SIGNAL CONTROLLER - REPORT")
    print("=" * 52)

    header = f"{'Road':<10} {'Vehicles':>9} {'Green Time (s)':>14} {'Congestion':>12}"
    print(header)
    print("-" * 52)

    for road in ROADS:
        congestion = congestion_levels[road]
        print(
            f"{road:<10} {counts[road]:>9} {green_times[road]:>14} {congestion:>12}"
        )

    print("-" * 52)
    print(f"{'TOTAL':<10} {total_vehicles:>9} {sum(green_times.values()):>14}")
    print("=" * 52)

    print(f"\nTotal Vehicles Detected : {total_vehicles}")
    print(f"Highest Congestion Road : {highest_road} ({ROADS.index(highest_road) and highest_road})")
    print(f"Overall Traffic Status  : {overall_status}")

    high_roads = [r for r in ROADS if congestion_levels[r] == "HIGH"]
    if high_roads:
        for road in high_roads:
            print(f"Recommendation          : Increase monitoring on {road} road.")
            print(f"                          Consider lane management or traffic police support.")
    else:
        print("Recommendation          : Traffic flow is within normal parameters.")

    print(f"Total Cycle Time        : {TOTAL_CYCLE_TIME} seconds")
    print("=" * 52)


def log_to_file(counts: dict[str, int], green_times: dict[str, int]) -> None:
    """Append the current session's data to a JSON log file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "vehicle_counts": counts,
        "green_times": green_times,
        "congestion": {road: classify_congestion(counts[road]) for road in ROADS},
    }
    records = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r") as f:
                records = json.load(f)
        except (json.JSONDecodeError, IOError):
            records = []

    records.append(entry)
    try:
        with open(LOG_FILE, "w") as f:
            json.dump(records, f, indent=2)
        print(f"\nSession logged to {LOG_FILE}")
    except IOError as e:
        print(f"\nWarning: Could not write log file: {e}")


def run_emergency_override(counts: dict[str, int]) -> dict[str, int]:
    """
    Emergency vehicle override: give maximum green time to a specified road
    by redistributing all remaining time to that road.
    """
    print(f"\nAvailable roads: {', '.join(ROADS)}")
    road = input("Enter road with emergency vehicle: ").strip().capitalize()
    if road not in ROADS:
        print("Invalid road. Cancelling override.")
        return compute_green_times(counts)

    times = {r: BASE_GREEN_TIME for r in ROADS}
    times[road] = TOTAL_CYCLE_TIME - BASE_GREEN_TIME * (len(ROADS) - 1)
    print(f"EMERGENCY OVERRIDE: {road} road given priority ({times[road]}s green time).")
    return times


def main() -> None:
    print("=" * 52)
    print("   SMART TRAFFIC SIGNAL CONTROLLER")
    print("=" * 52)

    while True:
        print("\nOptions:")
        print("  1. Run traffic analysis")
        print("  2. Emergency vehicle override")
        print("  3. View logs")
        print("  4. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            counts = get_vehicle_counts()
            green_times = compute_green_times(counts)
            generate_report(counts, green_times)
            save = input("\nSave log? (y/n): ").strip().lower()
            if save == "y":
                log_to_file(counts, green_times)

        elif choice == "2":
            counts = get_vehicle_counts()
            green_times = run_emergency_override(counts)
            generate_report(counts, green_times)

        elif choice == "3":
            if not os.path.exists(LOG_FILE):
                print("\nNo logs found.")
            else:
                try:
                    with open(LOG_FILE, "r") as f:
                        records = json.load(f)
                    print(f"\nFound {len(records)} log entries.")
                    for i, record in enumerate(records[-5:], 1):
                        print(f"\n[{i}] {record['timestamp']}")
                        for road in ROADS:
                            print(
                                f"  {road}: {record['vehicle_counts'][road]} vehicles, "
                                f"{record['green_times'][road]}s green"
                            )
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading log: {e}")

        elif choice == "4":
            print("Exiting.")
            break

        else:
            print("Invalid option. Please choose 1-4.")


if __name__ == "__main__":
    main()
