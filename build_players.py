#!/usr/bin/env python3
"""
Journeyman — dataset builder
----------------------------
Turns fitzRoy's redistributed AFL Tables match data (afldata.rda, sourced from
github.com/jimmyday12/fitzRoy_data — NOT scraped live from afltables.com) into
the season-aggregated players.json the game consumes.

Run:  python3 build_players.py afldata.rda players.json

Answer pool  = players who can be the mystery player (well-known, recent).
Guess pool   = everyone selectable in autocomplete (broader).
Both live in one array; guess-only players omit `seasons` to keep the file small.

Position is HEURISTIC (derived from career stat profile) since the source has no
position field. It only drives a late clue, so occasional noise is acceptable;
override in players.json by hand for any player you care about.
Honours are NOT in the source; the game degrades gracefully without them.
"""
import sys, json, pandas as pd, pyreadr

SRC = sys.argv[1] if len(sys.argv) > 1 else "afldata.rda"
OUT = sys.argv[2] if len(sys.argv) > 2 else "players.json"

# Tunables -------------------------------------------------------------
ANSWER_MIN_GAMES   = 100   # to be a possible answer
ANSWER_MIN_LAST    = 2010  # must have played this recently
GUESS_MIN_GAMES    = 30    # to appear in autocomplete
GUESS_MIN_LAST     = 2006
CLUB_CANON = {  # afltables names -> game display names
    "Footscray":"Western Bulldogs", "Kangaroos":"North Melbourne",
    "Brisbane Lions":"Brisbane", "Brisbane Bears":"Brisbane",
    "Greater Western Sydney":"GWS", "Gold Coast":"Gold Coast",
    "West Coast":"West Coast", "Port Adelaide":"Port Adelaide",
    "St Kilda":"St Kilda", "North Melbourne":"North Melbourne",
}
def club(name): return CLUB_CANON.get(name, name)

def infer_pos(gpg, dpg, hpg):
    """Coarse, robust buckets. gpg=goals/gm, dpg=disposals/gm, hpg=hitouts/gm.
    Deliberately avoids KEY vs SMALL forward — that needs height, which the
    source lacks, so it was mislabelling Franklin/Betts. FWD covers both."""
    if hpg >= 6:                     return "RUCK"
    if dpg >= 21:                    return "MID"
    if gpg >= 1.0 and dpg < 15:      return "FWD"
    if gpg >= 0.5 and dpg >= 14:     return "MID/FWD"
    if dpg >= 14:                    return "MID"
    return "DEF"

print("Loading", SRC, "…")
df = pyreadr.read_r(SRC)["afldata"]

# numeric coercion
for c in ["Season","Disposals","Goals","Hit.Outs"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")
df = df[df["Season"] >= 2000].copy()          # modern era only
df["Goals"] = df["Goals"].fillna(0)
df["Disposals"] = df["Disposals"].fillna(0)
df["Hit.Outs"] = df["Hit.Outs"].fillna(0)
df["Playing.for"] = df["Playing.for"].map(club)

# stable display name; disambiguate collisions later via ID+debut
df["disp"] = df["Player"].astype(str).str.strip()

players = []
name_counts = {}

for pid, g in df.groupby("ID"):
    name = g["disp"].mode().iloc[0]
    seasons = []
    for yr, s in g.groupby("Season"):
        # club = team with most games that season
        cl = s["Playing.for"].mode().iloc[0]
        seasons.append({
            "y": int(yr),
            "club": cl,
            "g": int(len(s)),
            "gl": int(s["Goals"].sum()),
            "d": round(float(s["Disposals"].mean()), 1),
        })
    seasons.sort(key=lambda r: r["y"])
    total_g = sum(s["g"] for s in seasons)
    last    = seasons[-1]["y"]
    first   = seasons[0]["y"]
    tot_goals = sum(s["gl"] for s in seasons)
    tot_disp  = sum(s["d"]*s["g"] for s in seasons)
    hp = float(g["Hit.Outs"].sum()) / max(total_g,1)
    pos = infer_pos(tot_goals/max(total_g,1), tot_disp/max(total_g,1), hp)
    clubs = []
    for s in seasons:
        if s["club"] not in clubs: clubs.append(s["club"])

    answerable = total_g >= ANSWER_MIN_GAMES and last >= ANSWER_MIN_LAST
    guessable  = total_g >= GUESS_MIN_GAMES  and last >= GUESS_MIN_LAST
    if not (answerable or guessable):
        continue

    rec = {"name":name, "pos":pos, "first":first, "last":last,
           "clubs":clubs, "games":total_g, "goals":tot_goals,
           "answer":answerable}
    if answerable:
        rec["seasons"] = seasons
    players.append(rec)
    name_counts[name] = name_counts.get(name, 0) + 1

# disambiguate duplicate display names (e.g. two Josh Kennedys)
for p in players:
    if name_counts[p["name"]] > 1:
        p["name"] = f'{p["name"]} ({p["clubs"][0]}, {p["first"]})'

players.sort(key=lambda p: (-p["games"]))
answers = [p for p in players if p["answer"]]
print(f"{len(players)} guessable, {len(answers)} answerable")
json.dump(players, open(OUT,"w"), separators=(",",":"))
import os
print(f"wrote {OUT} ({os.path.getsize(OUT)//1024} KB)")
