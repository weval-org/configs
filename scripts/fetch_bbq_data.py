#!/usr/bin/env python3
"""
Fetch the official BBQ dataset files from the nyu-mll/BBQ repository.

Defaults to downloading only the evaluation-ready JSONL files under `data/`.

Usage examples:
  python3 scripts/fetch_bbq_data.py
  python3 scripts/fetch_bbq_data.py --dest ./data/bbq
  python3 scripts/fetch_bbq_data.py --all --dest ./data/bbq_full
  python3 scripts/fetch_bbq_data.py --dirs data,templates --ref main

No external libraries are used; only Python standard library.
"""

import argparse
import json
import os
import sys
import time
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError


GITHUB_API_BASE = "https://api.github.com"
DEFAULT_REPO = "nyu-mll/BBQ"
DEFAULT_REF = "main"
DEFAULT_TOP_DIRS = ["data"]  # the JSONL files used for running evaluations


def eprint(*args):
    print(*args, file=sys.stderr)


def http_get_json(url, user_agent="civiceval-fetch-bbq/1.0"):
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        data = resp.read().decode(charset)
        return json.loads(data)


def http_download(url, dest_path, user_agent="civiceval-fetch-bbq/1.0"):
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    req = Request(url, headers={"User-Agent": user_agent})
    with urlopen(req) as resp, open(dest_path, "wb") as out:
        out.write(resp.read())


def list_directory(repo, path, ref):
    # GitHub API: GET /repos/{owner}/{repo}/contents/{path}?ref={ref}
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}?ref={ref}"
    return http_get_json(url)


def mirror_directory(repo, src_path, dest_root, ref, sleep_sec=0.0):
    """
    Recursively mirror a directory from GitHub repo contents API to local dest.
    Returns (num_files_downloaded, num_dirs_visited).
    """
    try:
        entries = list_directory(repo, src_path, ref)
    except HTTPError as e:
        eprint(f"HTTP error listing {repo}:{src_path}@{ref}: {e}")
        return 0, 0
    except URLError as e:
        eprint(f"Network error listing {repo}:{src_path}@{ref}: {e}")
        return 0, 0

    files_downloaded = 0
    dirs_visited = 1

    for entry in entries:
        entry_type = entry.get("type")
        entry_path = entry.get("path")  # full path in repo
        download_url = entry.get("download_url")

        if entry_type == "file" and download_url:
            rel_path = os.path.relpath(entry_path, start=src_path)
            dest_path = os.path.join(dest_root, src_path, rel_path)
            try:
                http_download(download_url, dest_path)
                files_downloaded += 1
                print(f"Downloaded: {entry_path} -> {dest_path}")
                if sleep_sec > 0:
                    time.sleep(sleep_sec)
            except HTTPError as e:
                eprint(f"HTTP error downloading {entry_path}: {e}")
            except URLError as e:
                eprint(f"Network error downloading {entry_path}: {e}")
        elif entry_type == "dir":
            sub_files, sub_dirs = mirror_directory(repo, entry_path, dest_root, ref, sleep_sec)
            files_downloaded += sub_files
            dirs_visited += sub_dirs
        else:
            # symlinks or submodules are ignored
            eprint(f"Skipping unsupported entry type '{entry_type}' at {entry_path}")

    return files_downloaded, dirs_visited


def parse_args():
    parser = argparse.ArgumentParser(description="Download BBQ dataset files from GitHub (nyu-mll/BBQ)")
    parser.add_argument("--repo", default=DEFAULT_REPO, help="GitHub repo in the form 'owner/name' (default: nyu-mll/BBQ)")
    parser.add_argument("--ref", default=DEFAULT_REF, help="Git ref/branch (default: main)")
    parser.add_argument(
        "--dirs",
        default=",".join(DEFAULT_TOP_DIRS),
        help="Comma-separated top-level directories to mirror (default: 'data')",
    )
    parser.add_argument("--all", action="store_true", help="Shortcut to include 'data,templates,supplemental'")
    parser.add_argument("--dest", default="./data/bbq", help="Destination root directory (default: ./data/bbq)")
    parser.add_argument("--sleep", type=float, default=0.0, help="Sleep seconds between file downloads (default: 0.0)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.all:
        top_dirs = ["data", "templates", "supplemental"]
    else:
        top_dirs = [d.strip() for d in args.dirs.split(",") if d.strip()]
        if not top_dirs:
            top_dirs = DEFAULT_TOP_DIRS

    dest_root = os.path.abspath(args.dest)
    os.makedirs(dest_root, exist_ok=True)

    print(f"Repo: {args.repo}")
    print(f"Ref: {args.ref}")
    print(f"Top-level dirs: {top_dirs}")
    print(f"Destination: {dest_root}")

    total_files = 0
    total_dirs = 0
    for top in top_dirs:
        print(f"\nMirroring '{top}' ...")
        files, dirs = mirror_directory(args.repo, top, dest_root, args.ref, args.sleep)
        print(f"Finished '{top}': {files} files, {dirs} directories traversed.")
        total_files += files
        total_dirs += dirs

    print(f"\nDone. Downloaded {total_files} files across {total_dirs} directories.")
    print("Commonly used evaluation files are in the 'data/' subdirectory you mirrored.")
    print("Examples include: Age.jsonl, Disability_status.jsonl, Gender_identity.jsonl, Nationality.jsonl,")
    print("  Physical_appearance.jsonl, Race_ethnicity.jsonl, Race_x_SES.jsonl, Race_x_gender.jsonl,")
    print("  Religion.jsonl, SES.jsonl, Sexual_orientation.jsonl")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        eprint("Interrupted.")
        sys.exit(130)


