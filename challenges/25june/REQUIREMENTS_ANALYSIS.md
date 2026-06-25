# Engineering Challenge Suite: Requirements Analysis & Implementation Plan

## Overview

Three independent console-based Python applications targeting entry-level engineers.
Each challenge exercises a distinct problem domain while sharing a common educational
thread: algorithmic thinking, data modeling, input validation, and clean code structure.

---

## Challenge 1: Smart Traffic Signal Controller

### Core Problem

Dynamically allocate green-light duration across four roads at a single intersection
based on real-time vehicle counts. The goal is proportional distribution, not fixed
rotation, to reduce congestion.

### Functional Requirements

| # | Requirement |
|---|-------------|
| 1 | Accept vehicle counts for North, South, East, West roads |
| 2 | Assign base green time of 10 seconds to each road |
| 3 | Distribute remaining 80 seconds proportionally by vehicle share |
| 4 | Total cycle time must equal exactly 120 seconds |
| 5 | Classify each road: LOW (<25), MODERATE (25-50), HIGH (>50) vehicles |
| 6 | Output a formatted traffic report with recommendations |

### Duration Calculation

```
Base time per road    = 10 sec
Total cycle time      = 120 sec
Remaining time        = 120 - (4 x 10) = 80 sec
Additional time       = (road_vehicles / total_vehicles) x 80
Final green time      = base + additional  (rounded to nearest integer)
```

### Ambiguities and Edge Cases

- **Zero vehicles on all roads**: Division by zero on total_vehicles. Must guard.
- **Zero vehicles on one road**: Road still receives base 10 seconds (spec implies this).
- **Rounding error**: After integer rounding, total may not sum to exactly 120. Need
  to assign residual seconds to the highest-traffic road to maintain the invariant.
- **Negative input**: Must reject; vehicle count is strictly non-negative.
- **Non-integer input**: Must reject gracefully.
- **Single road with all traffic**: Degenerate but valid; that road gets ~90 seconds.

### Bonus Features (from spec)

- Emergency vehicle detection (give priority override)
- Manual override option
- Log vehicle count and signal timings to file
- Console animation of traffic flow

### Missing Requirements

- Maximum vehicle count is not specified; assume practical upper bound of ~999.
- What happens when two roads have identical counts? Tie-breaking not specified;
  order of input (NSEW) is sufficient as implicit priority.

---

## Challenge 2: FIFA World Cup Team Power Score Generator

### Core Problem

Compute a composite "Power Score" for football teams based on match statistics,
rank teams, assign tier labels, and support bonus analytics.

### Power Score Formula

```
Match result:    Win=+30, Draw=+10, Loss=0
Goals scored:    +5 per goal
Clean sheet:     +15 (if goals_conceded == 0)
Possession:      +10 if >= 60%, +20 if >= 70%
Shots on target: +2 per shot
Yellow cards:    -2 per card
Red cards:       -10 per card
```

### Tier Classification

| Tier | Threshold |
|------|-----------|
| Title Contender | score >= 70 |
| Strong Team | score >= 60 |
| Average Team | score >= 50 |
| Weak Team | score < 50 |

(Thresholds inferred from the example output table.)

### Functional Requirements

| # | Requirement |
|---|-------------|
| 1 | Accept match data per team: goals_scored, goals_conceded, yellow_cards, red_cards, possession, shots_on_target, result |
| 2 | Compute power score using the formula above |
| 3 | Rank teams by descending power score |
| 4 | Assign tier category to each team |
| 5 | Display ranked table |
| 6 | Support multiple teams in a single session |

### Bonus Features (from spec)

- Update power score after each match automatically (cumulative multi-match support)
- World Cup winning probability (%) per team based on power score
- Momentum score: 3 consecutive wins = +20, 4 consecutive wins = +30
- Highlight most improved team across matches
- Export rankings to CSV or JSON

### Ambiguities and Edge Cases

- **Possession at exactly 70%**: Spec shows >= 70 gives +20; at exactly 60% gives +10.
  Verify boundary: 70% earns +20, not +10+20 simultaneously (it is a step function, not additive).
- **Possession below 60%**: No bonus (0 points).
- **Goals conceded > 0 but player also wants clean sheet**: Mutually exclusive by definition.
- **Negative stats**: Goals, shots, cards cannot be negative. Must validate.
- **Possession > 100% or < 0%**: Must reject.
- **Momentum bonus**: Requires match history per team; introduces statefulness.
- **Win probability**: No actuarial formula specified; a simple proportional share of
  total power score across all teams is the most defensible interpretation.
- **Tier thresholds**: Not stated explicitly in the spec. Inferred from the example
  table (Brazil=74 is Title Contender, Belgium=45 is Weak Team).

### Missing Requirements

- How to handle a team with no matches yet (zero score)?
- Is the system single-session or persistent across sessions? Bonus features imply persistence.
- Maximum number of teams not specified.

---

## Challenge 3: Digital Vault Security System

### Core Problem

A console-based secure note management application with user registration, authentication,
session management, account lockout, and data privacy between users.

### Functional Requirements

| # | Requirement |
|---|-------------|
| 1 | User registration with username and strong password |
| 2 | Login with correct credentials |
| 3 | Password strength validation (see rules below) |
| 4 | Add, view, delete secret notes per user |
| 5 | Lock account after 3 consecutive failed login attempts |
| 6 | Auto-logout after 2 minutes of inactivity |
| 7 | Users can only access their own notes |

### Password Strength Rules

- Minimum 8 characters
- At least 1 uppercase letter (A-Z)
- At least 1 lowercase letter (a-z)
- At least 1 digit (0-9)
- At least 1 special character from: `!@#$%` etc.

### Data Model

```python
User = {
    "username": str,
    "password": str,          # bcrypt/sha256 hashed
    "failed_attempts": int,   # 0-3
    "locked": bool,
    "last_active": float,     # Unix timestamp
    "notes": [
        {
            "title": str,
            "content": str,   # optionally encrypted
            "created_at": float
        }
    ]
}
```

### Security Rules

- Passwords are hashed before storing (never stored in plaintext)
- Account locks after 3 consecutive failed attempts
- Account unlocks after 5 minutes (spec says 5 minutes in security rules)
- Session timeout after 2 minutes of inactivity
- Users access only their own data
- All inputs validated

### Ambiguities and Edge Cases

- **Duplicate usernames**: Registration must check for existing username.
- **Empty username**: Must reject.
- **Account unlock timing**: Spec says "5 minutes" in security rules but the example
  output says "Try after some time" without a countdown. Show remaining lockout time.
- **Session timeout granularity**: Check on every menu action, not via background thread.
- **Note deletion by index vs title**: Spec shows deletion by index in the vault menu.
- **Note with duplicate title**: Not addressed; allow duplicates (simpler, user's responsibility).
- **Empty note title or content**: Should be rejected.
- **Hashing library**: `hashlib.sha256` is available in stdlib; no external dependency needed.
  `bcrypt` is stronger but adds a dependency. Use `hashlib` with salt for zero-dependency compliance.
- **Data persistence**: Spec mentions "export notes to file" as bonus, implying in-memory
  by default. For correctness and usability, persist to a JSON file on disk.

### Bonus Features (from spec)

- Encrypt note content before storing (AES or XOR cipher)
- Search notes by title
- Export notes to a file
- Dark mode terminal UI (color codes)
- Remember me / session persistence

### Missing Requirements

- Maximum note count per user not specified.
- Concurrent user sessions not addressed (single-user console, so N/A).
- Password change or account deletion flows not specified.

---

## Cross-Challenge Architecture Decisions

### Language: Python 3.10+

Justified by: stdlib completeness, readability, zero-build-step execution,
and alignment with intern/entry-level context.

### Dependencies: Zero external packages (stdlib only)

- `hashlib` for SHA-256 password hashing
- `hmac` for constant-time comparison
- `json` for persistence
- `time` / `datetime` for session and timestamps
- `re` for password validation
- `os` / `sys` for terminal control
- `getpass` for secure password input

### Persistence Strategy

All three challenges use in-memory data structures as primary state, with JSON file
persistence for Challenge 3 (which has explicit user accounts). Challenges 1 and 2
are stateless per run but support optional file logging as bonus.

### Input Validation Philosophy

Validate at the boundary. Never trust raw input. Convert and check type, range, and
format before passing into business logic. Fail loudly with clear error messages.

### Error Handling

Use explicit conditional checks over exceptions for predictable control flow.
Reserve try/except for genuinely exceptional conditions (file I/O, parse errors).

---

## Implementation Plan

### Phase 1: Core MVP (All Three Challenges)

1. Challenge 1: Traffic controller core algorithm + formatted output
2. Challenge 2: Power score calculator + ranking table
3. Challenge 3: Auth system + note CRUD + session management

### Phase 2: Robustness

- Input validation and edge case handling for all three
- Password hashing and security hardening for Challenge 3
- Rounding invariant enforcement for Challenge 1

### Phase 3: Bonus Features (Selected)

- Challenge 1: Log to file
- Challenge 2: CSV/JSON export + win probability
- Challenge 3: Note search + file persistence + note encryption

### Phase 4: Polish

- Consistent output formatting across all three
- Helpful error messages
- Code review pass: remove dead code, verify naming

---

## Engineering Tradeoffs

| Decision | Chosen | Alternative | Reason |
|----------|--------|-------------|--------|
| Hashing | SHA-256 + salt | bcrypt | No external dependency; sufficient for educational context |
| Persistence | JSON file | SQLite | Simpler, human-readable, no ORM overhead |
| Session timeout | Checked per action | Background thread | Threads add complexity and race conditions in console apps |
| Note encryption | XOR with key | AES-CBC | XOR is demonstrable without `cryptography` library |
| Green time rounding | Floor + residual to max | Round half-up | Guarantees exact 120-second invariant |
