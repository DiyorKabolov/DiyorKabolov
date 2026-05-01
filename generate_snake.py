#!/usr/bin/env python3
"""
Generates a growing snake SVG animation from GitHub contribution data.
The snake eats ONLY cells with contributions (not empty ones).
"""

import os
import requests
from pathlib import Path

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USER  = os.environ.get("GITHUB_USER", "DiyorKabolov")
OUTPUT_DIR   = Path("dist")

# Layout
CELL  = 11
GAP   = 2
STEP  = CELL + GAP

# Timing
SPEED = 0.045
PAUSE = 2.0

# Colors
HEAD_COLOR = "#7eb8f7"
BODY_COLOR = "#3c7dd9"
BG_COLOR   = "#0d1117"

LEVEL_COLORS = {
    "NONE":             "#161b22",
    "FIRST_QUARTILE":   "#0e4429",
    "SECOND_QUARTILE":  "#006d32",
    "THIRD_QUARTILE":   "#26a641",
    "FOURTH_QUARTILE":  "#39d353",
}


# ── GitHub API ─────────────────────────────────────────────────────────────

def fetch_contributions() -> list:
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    response = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"login": GITHUB_USER}},
        headers={"Authorization": f"bearer {GITHUB_TOKEN}"},
        timeout=15,
    )
    response.raise_for_status()
    data = response.json()
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


# ── Path ───────────────────────────────────────────────────────────────────

def boustrophedon_path(num_weeks: int, days: int = 7) -> list:
    path = []
    for w in range(num_weeks):
        col = range(days) if w % 2 == 0 else range(days - 1, -1, -1)
        for d in col:
            path.append((w, d))
    return path


# ── Utils ──────────────────────────────────────────────────────────────────

def f(v: float) -> str:
    return f"{v:.5f}"


# ── SVG ────────────────────────────────────────────────────────────────────

def generate_svg(weeks_data: list) -> str:
    num_weeks = len(weeks_data)

    # Карта клеток
    cells = {}
    for w, week in enumerate(weeks_data):
        for d, day in enumerate(week["contributionDays"]):
            cells[(w, d)] = LEVEL_COLORS.get(
                day["contributionLevel"], LEVEL_COLORS["NONE"]
            )

    # 🔥 ПОЛНЫЙ путь
    full_path = boustrophedon_path(num_weeks)

    # 🔥 ФИЛЬТР — только клетки с коммитами
    path = [pos for pos in full_path if cells[pos] != LEVEL_COLORS["NONE"]]

    N = len(path)
    total = N * SPEED + PAUSE

    k_end = (total - 0.08) / total

    W = num_weeks * STEP + 20
    H = 7 * STEP + 20

    # только для "съедаемых" клеток
    step_of = {(w, d): i for i, (w, d) in enumerate(path)}

    lines = []
    w_ = lines.append

    w_(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    w_(f'<rect width="{W}" height="{H}" fill="{BG_COLOR}" rx="8"/>')

    for (col, row), base_color in cells.items():
        x = col * STEP + 10
        y = row * STEP + 10

        # 🟩 ПУСТЫЕ клетки — просто рисуем
        if (col, row) not in step_of:
            w_(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base_color}"/>')
            continue

        i = step_of[(col, row)]

        k_eat  = max(i * SPEED / total, 0.0001)
        k_next = min((i + 1) * SPEED / total, k_end - 0.0001)

        # ── клетка исчезает когда съели ──
        w_(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base_color}">')
        w_(f'<animate attributeName="opacity" calcMode="discrete" '
           f'values="1;0;0;1" '
           f'keyTimes="0;{f(k_eat)};{f(k_end)};1" '
           f'dur="{total:.3f}s" repeatCount="indefinite"/>')
        w_('</rect>')

        # ── змейка ──
        w_(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{HEAD_COLOR}" opacity="0">')

        w_(f'<animate attributeName="opacity" calcMode="discrete" '
           f'values="0;1;1;0" '
           f'keyTimes="0;{f(k_eat)};{f(k_end)};1" '
           f'dur="{total:.3f}s" repeatCount="indefinite"/>')

        w_(f'<animate attributeName="fill" calcMode="discrete" '
           f'values="{HEAD_COLOR};{HEAD_COLOR};{BODY_COLOR};{BODY_COLOR}" '
           f'keyTimes="0;{f(k_eat)};{f(k_next)};1" '
           f'dur="{total:.3f}s" repeatCount="indefinite"/>')

        w_('</rect>')

    w_('</svg>')
    return '\n'.join(lines)


# ── MAIN ───────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Fetching contributions for @{GITHUB_USER} ...")
    weeks = fetch_contributions()
    print(f"Got {len(weeks)} weeks")

    svg = generate_svg(weeks)

    for name in (
        "github-contribution-grid-snake-dark.svg",
        "github-contribution-grid-snake.svg",
    ):
        (OUTPUT_DIR / name).write_text(svg, encoding="utf-8")
        print(f"OK dist/{name}")


if __name__ == "__main__":
    main()
