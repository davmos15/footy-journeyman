# Journeyman — Footy

Guess the mystery AFL player from their career, one season at a time. Daily puzzle + unlimited practice, normal/hard modes, share grid, stats. Single static site, no backend.

**Data coverage:** AFL seasons **2000–2026**, 1,534 players (794 can be the answer). Players who debuted before 2000 have their pre-2000 seasons truncated, so a career shown as starting in 2000 may actually be longer.

## Files

| File | What it is |
|---|---|
| `index.html` | The whole game. Loads `players.json` at runtime; falls back to an embedded ~60-player set if the fetch fails. |
| `players.json` | 1,534 players (794 can be the answer), season-by-season. ~670 KB. |
| `build_players.py` | Regenerates `players.json` from the source dataset. |
| `.github/workflows/refresh-data.yml` | Weekly auto-refresh of `players.json`. |
| `netlify.toml` | Static publish config. |

## Configure before launch

Near the top of the `<script>` in `index.html` there's a **SITE CONFIG** block:

```js
const COFFEE_URL = "https://www.buymeacoffee.com/davmos15";  // ← your Buy Me a Coffee URL
```

Set `COFFEE_URL` to your real Buy Me a Coffee link (it's currently a best-guess at your handle — **confirm it**). The ☕ button appears on the main screen and again on the result sheet after each game, plus a mention in the About panel. The year range and "via AFL Tables & fitzRoy" credit in the footer are filled in automatically from the data.

## Run locally

Because the game fetches `players.json`, open it through a server, not `file://`:

```bash
python3 -m http.server 8000   # then visit http://localhost:8000
```

(Opening `index.html` directly still works — it just uses the smaller embedded fallback set.)

## Go live on Netlify

1. Push this folder to a GitHub repo.
2. Netlify → Add new site → Import from GitHub → pick the repo.
3. Build command: *(blank)*. Publish directory: `.`. Deploy.

That's it — it's a static site. Every push auto-deploys.

## Keeping data fresh

`players.json` is built from **fitzRoy's redistributed AFL Tables dataset**, not scraped live from afltables.com (their robots.txt disallows automated access — respect it). fitzRoy publishes a cleaned copy on GitHub that updates through the season.

Manual rebuild:

```bash
pip install pyreadr pandas
curl -sL "https://raw.githubusercontent.com/jimmyday12/fitzRoy_data/main/data-raw/afl_tables_playerstats/afldata.rda" -o afldata.rda
python3 build_players.py afldata.rda players.json
```

The included GitHub Action does this every Monday and commits only if something changed, which triggers a Netlify redeploy. Enable it by allowing Actions write access: repo Settings → Actions → General → Workflow permissions → Read and write.

## Tuning the pool

Edit the constants at the top of `build_players.py`:

| Constant | Effect |
|---|---|
| `ANSWER_MIN_GAMES` / `ANSWER_MIN_LAST` | Who can be the mystery player. Raise games or recency to make answers more famous / easier. |
| `GUESS_MIN_GAMES` / `GUESS_MIN_LAST` | Who's selectable in autocomplete. |

## Known limitations

- **Position is inferred** from career stat profile (goals/disposals/hitouts) because the source has no position field. Buckets are deliberately coarse — RUCK / MID / FWD / MID/FWD / DEF — to avoid confident wrong labels. Override any player by hand-editing `players.json`.
- **No honours** (Brownlows, flags) in the source, so the game uses career games/goals as the late clue instead. If you want honours, they'd come from a second source (AFL API player details, or Wikipedia) keyed on player name.
- **Data starts 2000.** Change the `Season >= 2000` filter in `build_players.py` to go deeper.

## Attribution

Player statistics via [fitzRoy](https://github.com/jimmyday12/fitzRoy), sourced from [AFL Tables](https://afltables.com). Add a visible credit line before launch. No club logos, player photos, or league marks are used.
