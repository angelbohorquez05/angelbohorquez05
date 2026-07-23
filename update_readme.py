# -*- coding: utf-8 -*-
"""Regenera README.md: ficha neofetch con datos en vivo.

Corre localmente (python update_readme.py) o via GitHub Actions (diario).
Regla: las stats con valor 0 o desconocido NO se muestran.
"""
import calendar
import json
import os
import time
import urllib.request
from datetime import date

USER = "angelbohorquez05"
BIRTHDAY = date(2002, 1, 13)
STAT_W = 52  # ancho de la columna de stats


def uptime():
    """Edad exacta en years, months, days."""
    today = date.today()
    years = today.year - BIRTHDAY.year
    months = today.month - BIRTHDAY.month
    days = today.day - BIRTHDAY.day
    if days < 0:
        months -= 1
        prev_month = today.month - 1 or 12
        prev_year = today.year if today.month > 1 else today.year - 1
        days += calendar.monthrange(prev_year, prev_month)[1]
    if months < 0:
        years -= 1
        months += 12
    return f"{years} years, {months} months, {days} days"


def api(url, retries=3):
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    for i in range(retries):
        with urllib.request.urlopen(req, timeout=15) as r:
            if r.status == 202:  # stats aun calculandose
                time.sleep(3)
                continue
            return json.load(r)
    return None


def github_stats():
    """Devuelve dict de stats; las que fallen quedan en None."""
    s = {"repos": None, "commits": None, "loc": None, "joined": None}
    try:
        u = api(f"https://api.github.com/users/{USER}")
        s["repos"] = u.get("public_repos")
        s["joined"] = u.get("created_at", "")[:4] or None
    except Exception as e:
        print(f"aviso: perfil no disponible ({e})")

    try:
        c = api(f"https://api.github.com/search/commits?q=author:{USER}")
        s["commits"] = c.get("total_count")
    except Exception as e:
        print(f"aviso: commits no disponibles ({e})")

    try:
        repos = api(f"https://api.github.com/users/{USER}/repos?per_page=100")
        own = [r["name"] for r in repos if not r.get("fork")]
        # lineas de codigo: sumas de additions - deletions del propio user
        added = deleted = 0
        for name in own:
            stats = api(
                f"https://api.github.com/repos/{USER}/{name}/stats/contributors")
            if not stats:
                continue
            for contrib in stats:
                if contrib.get("author", {}).get("login", "").lower() == USER:
                    for wk in contrib.get("weeks", []):
                        added += wk.get("a", 0)
                        deleted += wk.get("d", 0)
        if added:
            s["loc"] = f"{added - deleted:,} ( {added:,}++, {deleted:,}-- )"
    except Exception as e:
        print(f"aviso: repos/LOC no disponibles ({e})")
    return s


def dotline(label, value):
    base = f". {label}:"
    fill = STAT_W - len(base) - len(value) - 2
    return f"{base} {'.' * max(fill, 1)} {value}"


def cont_line(value):
    """Linea de continuacion (sin etiqueta), alineada a la derecha."""
    return "  " + "." * (STAT_W - len(value) - 3) + " " + value


def main():
    g = github_stats()

    stats = []
    header = "angel@bohorquez05 "
    stats.append(header + "-" * (STAT_W - len(header)))
    stats.append(dotline("OS", "Windows 11"))
    stats.append(dotline("Uptime", uptime()))
    stats.append(dotline("Host", "Milan, Italy"))
    stats.append(dotline("IDE", "VS Code"))
    stats.append("")
    stats.append(dotline("Languages.Programming", "Python"))
    stats.append(dotline("Languages.Computer", "HTML, JSON, LaTeX"))
    stats.append(dotline("Languages.Real", "Spanish, Italian"))
    stats.append(cont_line("English, Portuguese"))
    stats.append("")
    stats.append(dotline("Learning", "Machine Learning & AI"))
    stats.append(dotline("Hobbies", "Mountain hiking"))
    stats.append("")
    stats.append("- Contact " + "-" * (STAT_W - 10))
    stats.append(dotline("Email", "angelbohorquez.academic@gmail.com"))
    stats.append(dotline("LinkedIn", "in/angellbohorquez"))
    stats.append("")
    stats.append("- GitHub Stats " + "-" * (STAT_W - 15))
    if g["joined"]:
        stats.append(dotline("Member since", g["joined"]))
    if g["repos"]:
        stats.append(dotline("Repos", str(g["repos"])))
    if g["commits"]:
        stats.append(dotline("Commits", f"{g['commits']:,}"))
    if g["loc"]:
        stats.append(dotline("Lines of code", g["loc"]))

    body = "\n".join(line.rstrip() for line in stats)
    readme = "```text\n" + body + "\n```\n"
    with open("README.md", "w", encoding="utf-8", newline="\n") as f:
        f.write(readme)
    print("README.md regenerado")


if __name__ == "__main__":
    main()
