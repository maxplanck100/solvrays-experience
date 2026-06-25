"""
FIFA World Cup Team Power Score Generator
Challenge 2

Computes composite power scores for football teams based on match statistics,
ranks them by score, assigns tier labels, and supports multi-match cumulative tracking.
"""

import csv
import json
import os
from typing import Optional


DATA_FILE = "worldcup_data.json"

RESULT_POINTS = {"win": 30, "draw": 10, "loss": 0}
GOALS_SCORED_POINTS = 5
CLEAN_SHEET_BONUS = 15
POSSESSION_HIGH_BONUS = 20      # >= 70%
POSSESSION_LOW_BONUS = 10       # >= 60% and < 70%
SHOTS_ON_TARGET_POINTS = 2
YELLOW_CARD_PENALTY = -2
RED_CARD_PENALTY = -10

TIER_THRESHOLDS = [
    (70, "Title Contender"),
    (60, "Strong Team"),
    (50, "Average Team"),
    (0,  "Weak Team"),
]

CONSECUTIVE_WIN_BONUSES = {3: 20, 4: 30}


def compute_match_score(
    result: str,
    goals_scored: int,
    goals_conceded: int,
    possession: float,
    shots_on_target: int,
    yellow_cards: int,
    red_cards: int,
) -> int:
    """
    Compute the power score for a single match.

    Possession bonus is a step function, not additive:
    >= 70% earns +20, >= 60% and < 70% earns +10, below 60% earns 0.
    """
    score = RESULT_POINTS.get(result.lower(), 0)
    score += goals_scored * GOALS_SCORED_POINTS
    if goals_conceded == 0:
        score += CLEAN_SHEET_BONUS
    if possession >= 70:
        score += POSSESSION_HIGH_BONUS
    elif possession >= 60:
        score += POSSESSION_LOW_BONUS
    score += shots_on_target * SHOTS_ON_TARGET_POINTS
    score += yellow_cards * YELLOW_CARD_PENALTY
    score += red_cards * RED_CARD_PENALTY
    return score


def compute_momentum_bonus(match_results: list[str]) -> int:
    """
    Scan the tail of match_results for consecutive wins and return the applicable bonus.

    Only the most recent consecutive streak from the end of the list is considered.
    Bonuses are not additive: the highest applicable bonus is returned.
    """
    streak = 0
    for result in reversed(match_results):
        if result.lower() == "win":
            streak += 1
        else:
            break

    for threshold in sorted(CONSECUTIVE_WIN_BONUSES.keys(), reverse=True):
        if streak >= threshold:
            return CONSECUTIVE_WIN_BONUSES[threshold]
    return 0


def assign_tier(total_score: int) -> str:
    for threshold, label in TIER_THRESHOLDS:
        if total_score >= threshold:
            return label
    return "Weak Team"


def compute_win_probability(teams: dict) -> dict[str, float]:
    """
    Compute win probability as each team's proportional share of total power score.

    Teams with negative total scores are clamped to zero for probability purposes.
    """
    floored = {name: max(0, data["total_score"]) for name, data in teams.items()}
    total = sum(floored.values())
    if total == 0:
        equal = round(100 / len(teams), 2) if teams else 0.0
        return {name: equal for name in teams}
    return {
        name: round((floored[name] / total) * 100, 2)
        for name in teams
    }


def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_data(teams: dict) -> None:
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(teams, f, indent=2)
    except IOError as e:
        print(f"Warning: Could not save data: {e}")


def get_int_input(prompt: str, min_val: int = 0, max_val: int = 999) -> int:
    while True:
        raw = input(prompt).strip()
        if not raw.lstrip("-").isdigit():
            print(f"  Enter an integer between {min_val} and {max_val}.")
            continue
        value = int(raw)
        if value < min_val or value > max_val:
            print(f"  Value must be between {min_val} and {max_val}.")
            continue
        return value


def get_float_input(prompt: str, min_val: float = 0.0, max_val: float = 100.0) -> float:
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
        except ValueError:
            print(f"  Enter a number between {min_val} and {max_val}.")
            continue
        if value < min_val or value > max_val:
            print(f"  Value must be between {min_val} and {max_val}.")
            continue
        return value


def get_result_input(prompt: str) -> str:
    while True:
        raw = input(prompt).strip().lower()
        if raw in ("win", "draw", "loss"):
            return raw
        print("  Enter 'win', 'draw', or 'loss'.")


def enter_match_data(teams: dict) -> None:
    """Collect match statistics for a team and update its cumulative record."""
    print("\nEnter Match Data")
    print("-" * 30)

    team_name = input("Team name: ").strip()
    if not team_name:
        print("Team name cannot be empty.")
        return

    result = get_result_input("Result (win/draw/loss): ")
    goals_scored = get_int_input("Goals scored: ", 0, 99)
    goals_conceded = get_int_input("Goals conceded: ", 0, 99)
    possession = get_float_input("Possession (%): ", 0.0, 100.0)
    shots_on_target = get_int_input("Shots on target: ", 0, 99)
    yellow_cards = get_int_input("Yellow cards: ", 0, 20)
    red_cards = get_int_input("Red cards: ", 0, 11)

    match_score = compute_match_score(
        result, goals_scored, goals_conceded,
        possession, shots_on_target, yellow_cards, red_cards
    )

    if team_name not in teams:
        teams[team_name] = {
            "total_score": 0,
            "matches": [],
            "match_results": [],
        }

    team = teams[team_name]
    team["total_score"] += match_score
    team["match_results"].append(result)
    team["matches"].append({
        "result": result,
        "goals_scored": goals_scored,
        "goals_conceded": goals_conceded,
        "possession": possession,
        "shots_on_target": shots_on_target,
        "yellow_cards": yellow_cards,
        "red_cards": red_cards,
        "match_score": match_score,
    })

    momentum = compute_momentum_bonus(team["match_results"])
    effective_score = team["total_score"] + momentum

    print(f"\nMatch Score for {team_name}: {match_score}")
    if momentum > 0:
        print(f"Momentum Bonus: +{momentum} (consecutive win streak)")
    print(f"Cumulative Power Score: {effective_score}")
    print(f"Tier: {assign_tier(effective_score)}")

    save_data(teams)


def display_rankings(teams: dict) -> None:
    """Print a ranked table of all teams sorted by effective power score."""
    if not teams:
        print("\nNo teams registered yet.")
        return

    win_probs = compute_win_probability(teams)

    ranked = sorted(
        teams.items(),
        key=lambda item: item[1]["total_score"] + compute_momentum_bonus(item[1]["match_results"]),
        reverse=True,
    )

    print("\n" + "=" * 68)
    print(" WORLD CUP POWER RANKINGS")
    print("=" * 68)
    header = f"{'Rank':<6} {'Team':<15} {'Score':>7} {'Category':<20} {'Win Prob':>9}"
    print(header)
    print("-" * 68)

    for rank, (name, data) in enumerate(ranked, 1):
        momentum = compute_momentum_bonus(data["match_results"])
        effective = data["total_score"] + momentum
        tier = assign_tier(effective)
        prob = win_probs[name]
        print(f"{rank:<6} {name:<15} {effective:>7} {tier:<20} {prob:>8.1f}%")

    print("=" * 68)

    if len(ranked) >= 2:
        most_improved = find_most_improved(teams)
        if most_improved:
            print(f"\nMost Improved Team: {most_improved}")


def find_most_improved(teams: dict) -> Optional[str]:
    """
    Identify the team whose most recent match score was highest relative to
    their average match score across all prior matches.
    """
    best_team = None
    best_improvement = float("-inf")

    for name, data in teams.items():
        matches = data["matches"]
        if len(matches) < 2:
            continue
        prior_avg = sum(m["match_score"] for m in matches[:-1]) / (len(matches) - 1)
        last_score = matches[-1]["match_score"]
        improvement = last_score - prior_avg
        if improvement > best_improvement:
            best_improvement = improvement
            best_team = name

    return best_team


def export_rankings(teams: dict, fmt: str) -> None:
    """Export rankings to CSV or JSON."""
    win_probs = compute_win_probability(teams)
    ranked = sorted(
        teams.items(),
        key=lambda item: item[1]["total_score"] + compute_momentum_bonus(item[1]["match_results"]),
        reverse=True,
    )

    if fmt == "json":
        output = []
        for rank, (name, data) in enumerate(ranked, 1):
            momentum = compute_momentum_bonus(data["match_results"])
            effective = data["total_score"] + momentum
            output.append({
                "rank": rank,
                "team": name,
                "power_score": effective,
                "tier": assign_tier(effective),
                "win_probability": win_probs[name],
            })
        filename = "rankings_export.json"
        with open(filename, "w") as f:
            json.dump(output, f, indent=2)
        print(f"Rankings exported to {filename}")

    elif fmt == "csv":
        filename = "rankings_export.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Rank", "Team", "Power Score", "Tier", "Win Probability (%)"])
            for rank, (name, data) in enumerate(ranked, 1):
                momentum = compute_momentum_bonus(data["match_results"])
                effective = data["total_score"] + momentum
                writer.writerow([rank, name, effective, assign_tier(effective), win_probs[name]])
        print(f"Rankings exported to {filename}")


def main() -> None:
    teams = load_data()

    print("=" * 52)
    print("   FIFA WORLD CUP POWER SCORE GENERATOR")
    print("=" * 52)

    while True:
        print("\nMenu:")
        print("  1. Enter match data")
        print("  2. View rankings")
        print("  3. Export rankings (CSV)")
        print("  4. Export rankings (JSON)")
        print("  5. Reset all data")
        print("  6. Exit")
        choice = input("Choose: ").strip()

        if choice == "1":
            enter_match_data(teams)
        elif choice == "2":
            display_rankings(teams)
        elif choice == "3":
            export_rankings(teams, "csv")
        elif choice == "4":
            export_rankings(teams, "json")
        elif choice == "5":
            confirm = input("Reset all data? This cannot be undone. (yes/no): ").strip().lower()
            if confirm == "yes":
                teams.clear()
                if os.path.exists(DATA_FILE):
                    os.remove(DATA_FILE)
                print("All data cleared.")
        elif choice == "6":
            print("Exiting.")
            break
        else:
            print("Invalid option. Please choose 1-6.")


if __name__ == "__main__":
    main()
