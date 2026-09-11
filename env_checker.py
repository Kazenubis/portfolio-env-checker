"""
Portfolio Env Health Checker — a "env variable validator," reskinned as a
meta-tool for sanity-checking the .env.example / .env pairs across an
entire portfolio of repos (built to check Mahmoud's own 48+ project
folders, but it works on any directory tree).

    python3 env_checker.py --project /path/to/one/project
    python3 env_checker.py --portfolio /path/to/100-github-projects
"""

import argparse
import difflib
import os


def parse_env_file(path):
    """Parses a simple KEY=VALUE .env-style file. Ignores blank lines and
    lines starting with '#'. Returns {key: value} — value is not needed
    for the comparison logic below but is kept for completeness/testing."""
    variables = {}
    if not os.path.exists(path):
        return variables

    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            variables[key.strip()] = value.strip()
    return variables


def find_typos(missing_keys, extra_keys, cutoff=0.75):
    """Pairs up a missing key with an extra key when they're suspiciously
    similar (e.g. `API_KEY` vs `APIKEY`, or a case mismatch) — the case
    that's genuinely a typo rather than a real missing/extra variable."""
    typos = []
    remaining_extra = set(extra_keys)
    for missing in missing_keys:
        matches = difflib.get_close_matches(missing, remaining_extra, n=1, cutoff=cutoff)
        if matches:
            typos.append((missing, matches[0]))
            remaining_extra.discard(matches[0])
    return typos


def compare_env_files(example_path, actual_path):
    """Compares a `.env.example` (the contract) against a real `.env`
    (what's actually configured). Returns a report dict with:
      - missing: keys in .env.example but not in .env, and not a likely typo
      - extra: keys in .env but not in .env.example, and not a likely typo
      - typos: (expected_key, found_key) pairs that look like a mistyped
        version of an expected key
      - empty: keys present in .env but with an empty value
    """
    example_vars = parse_env_file(example_path)
    actual_vars = parse_env_file(actual_path)

    example_keys = set(example_vars.keys())
    actual_keys = set(actual_vars.keys())

    raw_missing = example_keys - actual_keys
    raw_extra = actual_keys - example_keys

    typos = find_typos(raw_missing, raw_extra)
    typo_missing = {m for m, _ in typos}
    typo_extra = {e for _, e in typos}

    missing = sorted(raw_missing - typo_missing)
    extra = sorted(raw_extra - typo_extra)
    empty = sorted(k for k in actual_keys & example_keys if actual_vars[k] == "")

    return {
        "missing": missing,
        "extra": extra,
        "typos": sorted(typos),
        "empty": empty,
    }


def is_healthy(report):
    return not (report["missing"] or report["extra"] or report["typos"] or report["empty"])


def scan_project(project_dir):
    """Compares <project_dir>/.env.example against <project_dir>/.env.
    Returns None if the project has no .env.example at all (nothing to
    check against) rather than reporting every .env var as "extra"."""
    example_path = os.path.join(project_dir, ".env.example")
    actual_path = os.path.join(project_dir, ".env")
    if not os.path.exists(example_path):
        return None
    return compare_env_files(example_path, actual_path)


def scan_portfolio(root_dir):
    """Walks every immediate subdirectory of `root_dir` that has a
    .env.example and reports on each — the "check my whole portfolio at
    once" use case."""
    results = {}
    for entry in sorted(os.listdir(root_dir)):
        project_dir = os.path.join(root_dir, entry)
        if not os.path.isdir(project_dir):
            continue
        report = scan_project(project_dir)
        if report is not None:
            results[entry] = report
    return results


def format_report(name, report):
    lines = [f"== {name} ==" if name else "== Report =="]
    if is_healthy(report):
        lines.append("  OK — .env matches .env.example")
        return "\n".join(lines)
    for missing in report["missing"]:
        lines.append(f"  MISSING: {missing} (required by .env.example, not set)")
    for extra in report["extra"]:
        lines.append(f"  EXTRA:   {extra} (not in .env.example — leftover or typo?)")
    for expected, found in report["typos"]:
        lines.append(f"  TYPO?    expected '{expected}', found '{found}'")
    for empty in report["empty"]:
        lines.append(f"  EMPTY:   {empty} is set but has no value")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Portfolio Env Health Checker")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--project", help="Path to a single project directory")
    group.add_argument("--portfolio", help="Path to a directory containing multiple project folders")
    args = parser.parse_args()

    if args.project:
        report = scan_project(args.project)
        if report is None:
            print(f"No .env.example found in {args.project} — nothing to check.")
        else:
            print(format_report(os.path.basename(os.path.abspath(args.project)), report))
    else:
        results = scan_portfolio(args.portfolio)
        if not results:
            print(f"No projects with a .env.example found under {args.portfolio}.")
            return
        healthy = 0
        for name, report in results.items():
            print(format_report(name, report))
            if is_healthy(report):
                healthy += 1
        print(f"\n{healthy}/{len(results)} projects healthy.")


if __name__ == "__main__":
    main()
