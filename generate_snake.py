#!/usr/bin/env python3
import os
import requests
from pathlib import Path

GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_USER  = os.environ.get("GITHUB_USER", "DiyorKabolov")
OUTPUT_DIR   = Path("dist")

CELL  = 11
GAP   = 2
STEP  = CELL + GAP

SPEED = 0.045
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
        timeout=15,
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


def f(v):
    return f"{v:.5f}"


def generate_svg(weeks_data):
    num_weeks = len(weeks_data)

    # карта клеток
    cells = {}
    for w, week in enumerate(weeks_data):
        for d, day in enumerate(week["contributionDays"]):
            cells[(w, d)] = LEVEL_COLORS.get(
                day["contributionLevel"], LEVEL_COLORS["NONE"]
            )

    path = boustrophedon_path(num_weeks)
    step_of = {pos: i for i, pos in enumerate(path)}

    N = len(path)
    total = N * SPEED + PAUSE
    k_end = (total - 0.08) / total

    W = num_weeks * STEP + 20
    H = 7 * STEP + 20

    lines = []
    w = lines.append

    w(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    w(f'<rect width="{W}" height="{H}" fill="{BG_COLOR}" rx="8"/>')

    for (col, row), base_color in cells.items():
        x = col * STEP + 10
        y = row * STEP + 10

        i = step_of.get((col, row))
        if i is None:
            continue

        k_eat  = max(i * SPEED / total, 0.0001)
        k_next = min((i + 1) * SPEED / total, k_end - 0.0001)

        # ✅ ЕСЛИ НЕТ КОММИТА — просто рисуем, НЕ АНИМИРУЕМ
        if base_color == LEVEL_COLORS["NONE"]:
            w(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base_color}"/>')
            continue

        # ── клетка исчезает ТОЛЬКО если есть коммит ──
        w(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{base_color}">')
        w(f'<animate attributeName="opacity" calcMode="discrete" '
          f'values="1;0;0;1" '
          f'keyTimes="0;{f(k_eat)};{f(k_end)};1" '
          f'dur="{total:.3f}s" repeatCount="indefinite"/>')
        w('</rect>')

        # ── змейка (растёт корректно) ──
        w(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" fill="{HEAD_COLOR}" opacity="0">')

        w(f'<animate attributeName="opacity" calcMode="discrete" '
          f'values="0;1;1;0" '
          f'keyTimes="0;{f(k_eat)};{f(k_end)};1" '
          f'dur="{total:.3f}s" repeatCount="indefinite"/>')

        w(f'<animate attributeName="fill" calcMode="discrete" '
          f'values="{HEAD_COLOR};{HEAD_COLOR};{BODY_COLOR};{BODY_COLOR}" '
          f'keyTimes="0;{f(k_eat)};{f(k_next)};1" '
          f'dur="{total:.3f}s" repeatCount="indefinite"/>')

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
