#!/usr/bin/env python3
import os
import requests
from pathlib import Path

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USER  = os.environ.get("GITHUB_USER", "DiyorKabolov")
OUTPUT_DIR   = Path("dist")

CELL = 11
GAP  = 2
STEP = CELL + GAP

SPEED = 0.06
PAUSE = 2.0

HEAD_COLOR = "#7eb8f7"
BODY_COLOR = "#3c7dd9"
BG_COLOR   = "#0d1117"

LEVEL_COLORS = {
    "NONE": "#161b22",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353",
}


def fetch_contributions():
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
    r = requests.post(
        "https://api.github.com/graphql",
        json={"query": query, "variables": {"login": GITHUB_USER}},
        headers={"Authorization": f"bearer {GITHUB_TOKEN}"},
    )
    r.raise_for_status()
    return r.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]


def boustrophedon_path(num_weeks):
    path = []
    for w in range(num_weeks):
        col = range(7) if w % 2 == 0 else range(6, -1, -1)
        for d in col:
            path.append((w, d))
    return path


def generate_svg(weeks_data):
    num_weeks = len(weeks_data)

    cells = {}
    for w, week in enumerate(weeks_data):
        for d, day in enumerate(week["contributionDays"]):
            cells[(w, d)] = LEVEL_COLORS.get(
                day["contributionLevel"], LEVEL_COLORS["NONE"]
            )

    path = boustrophedon_path(num_weeks)

    # 🔥 только клетки с коммитами
    food = [pos for pos in path if pos in cells and cells[pos] != LEVEL_COLORS["NONE"]]
    food_set = set(food)

    W = num_weeks * STEP + 20
    H = 7 * STEP + 20

    total = len(food) * SPEED + PAUSE

    lines = []
    w = lines.append

    w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">')
    w(f'<rect width="{W}" height="{H}" fill="{BG_COLOR}" rx="8"/>')

    # ── фон ──
    for (col, row), color in cells.items():
        x = col * STEP + 10
        y = row * STEP + 10
        w(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')

    # ── тело змейки ──
    for i, (col, row) in enumerate(food):
        x = col * STEP + 10
        y = row * STEP + 10

        t = i / len(food)

        w(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{BODY_COLOR}" opacity="0">')
        w(f'''
        <animate attributeName="opacity"
            values="0;1;1"
            keyTimes="0;{t:.4f};1"
            dur="{total}s"
            calcMode="spline"
            keySplines="0.4 0 0.2 1;0 0 1 1"
            repeatCount="indefinite"/>
        ''')
        w('</rect>')

    # ── ПЛАВНАЯ ГОЛОВА ──
    path_x = []
    path_y = []

    for col, row in food:
        path_x.append(str(col * STEP + 10))
        path_y.append(str(row * STEP + 10))

    # зацикливание
    path_x.append(path_x[0])
    path_y.append(path_y[0])

    w(f'<rect width="{CELL}" height="{CELL}" rx="2" fill="{HEAD_COLOR}">')

    w(f'''
    <animate attributeName="x"
        values="{";".join(path_x)}"
        dur="{total}s"
        calcMode="spline"
        keySplines="0.4 0 0.2 1"
        repeatCount="indefinite"/>
    ''')

    w(f'''
    <animate attributeName="y"
        values="{";".join(path_y)}"
        dur="{total}s"
        calcMode="spline"
        keySplines="0.4 0 0.2 1"
        repeatCount="indefinite"/>
    ''')

    w('</rect>')

    w('</svg>')
    return "\n".join(lines)


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    weeks = fetch_contributions()
    svg = generate_svg(weeks)

    for name in (
        "github-contribution-grid-snake.svg",
        "github-contribution-grid-snake-dark.svg",
    ):
        (OUTPUT_DIR / name).write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
