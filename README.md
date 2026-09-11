# Portfolio Env Health Checker

An "env variable validator," reskinned as a meta-tool: instead of
checking one project's `.env` file, it can scan an entire folder of
projects at once — built to sanity-check the `.env.example`/`.env` pairs
across my own 48+ repo portfolio, but it works on any directory tree.

```
$ python3 env_checker.py --portfolio fixtures
== broken_project ==
  MISSING: DATABASE_URL (required by .env.example, not set)
  EXTRA:   OLD_UNUSED_VAR (not in .env.example — leftover or typo?)
  TYPO?    expected 'SECRET_KEY', found 'SECRETKEY'
  EMPTY:   DEBUG_MODE is set but has no value
== good_project ==
  OK — .env matches .env.example

1/2 projects healthy.
```

## Features

- Compares `.env.example` (the contract a project expects) against the
  real `.env` and reports four distinct problems: variables that are
  **missing** entirely, **extra** variables not in the example, variables
  set but **empty**, and — the one most validators skip — likely **typos**
  (`SECRETKEY` instead of `SECRET_KEY`) caught with a similarity match so
  they're reported as a typo instead of one missing + one extra variable
- `--project` checks a single folder; `--portfolio` walks every
  subdirectory that has a `.env.example` and reports on all of them in one
  pass, with a final health tally
- Skips projects with no `.env.example` at all rather than falsely
  flagging every one of their `.env` variables as "extra"
- Verified against a deliberately broken fixture covering all four
  problem types at once, not just the easy missing-variable case

## Tech Stack

Python 3 · standard library only (`difflib`, `argparse`)

## Getting Started

```bash
git clone https://github.com/Kazenubis/portfolio-env-checker.git
cd portfolio-env-checker
python3 env_checker.py --project fixtures/broken_project
python3 env_checker.py --portfolio fixtures
```

Run the tests:

```bash
python3 -m unittest test_env_checker.py -v
```

## What I Learned

The typo detection is the part that made this more than a two-line diff.
Without it, a variable renamed from `SECRET_KEY` to `SECRETKEY` shows up
as one missing variable and one unrelated extra variable — technically
correct, but it hides the actual, single mistake behind two separate
lines. Pairing up close-match names with `difflib.get_close_matches`
before reporting missing/extra turns that into one clear "did you mean"
line, which is what a human reviewing the output actually wants to see.
