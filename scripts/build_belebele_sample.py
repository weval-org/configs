#!/usr/bin/env python3
"""
Build per-language Belebele sample blueprints from the official dataset.

Belebele (Bandarkar et al., 2023) is a parallel multiple-choice reading
comprehension benchmark: the same 900 questions in 122 language variants.
Weval can't hold all 900 x 122, so this samples N questions once (seeded) and
writes the *same* questions in every chosen language, one blueprint per
language, so scores are comparable across languages.

Scoring is deterministic (answer letter), so no LLM judge is needed.

License: Belebele is CC BY-SA 4.0. Every generated file carries that license
and attribution in its header, which differs from this repo's CC0 default.

Usage:
  python3 scripts/build_belebele_sample.py
  python3 scripts/build_belebele_sample.py --n 40 --seed 20260929 --langs cat_Latn,spa_Latn

No external libraries beyond PyYAML; data comes from the Hugging Face
datasets-server rows API.
"""

import argparse
import hashlib
import json
import os
import random
import sys
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

ROWS_API = "https://datasets-server.huggingface.co/rows"
DATASET = "facebook/belebele"
TOTAL_ROWS = 900
PAGE = 100

# Chosen for the Current AI / MozFest (Barcelona) model-picker use case:
# Iberian languages (Belebele has no Galician), major European languages, the Southeast Asian languages
# SEA-LION targets, and a spread of widely spoken languages elsewhere.
DEFAULT_LANGS = {
    "eng_Latn": "English",
    "cat_Latn": "Catalan",
    "spa_Latn": "Spanish",
    "eus_Latn": "Basque",
    "por_Latn": "Portuguese",
    "fra_Latn": "French",
    "deu_Latn": "German",
    "ita_Latn": "Italian",
    "ind_Latn": "Indonesian",
    "zsm_Latn": "Malay",
    "vie_Latn": "Vietnamese",
    "tha_Thai": "Thai",
    "tgl_Latn": "Tagalog",
    "swh_Latn": "Swahili",
    "hin_Deva": "Hindi",
    "arb_Arab": "Arabic",
    "zho_Hans": "Chinese (Simplified)",
}

LETTERS = ["A", "B", "C", "D"]

SYSTEM_PROMPT = "Answer with only the letter (A, B, C, or D) of the correct answer."

PROMPT_TEMPLATE = (
    "Read the passage and answer the question.\n\n"
    "Passage: {passage}\n\n"
    "Question: {question}\n\n"
    "A. {a1}\nB. {a2}\nC. {a3}\nD. {a4}"
)


def answer_regex(letter: str) -> str:
    # Accepts "B", "B.", "(B)", "**B**", "Answer: B", "B. <option text>", "B\n\nexplanation".
    # Rejects other letters and words that merely start with the letter ("Based on...").
    return rf"^[^A-Za-z0-9]*(?:answer[^A-Za-z0-9]*)?{letter}(?:[^A-Za-z0-9][\s\S]*)?$"


def fetch_rows(config: str) -> list:
    rows = []
    for offset in range(0, TOTAL_ROWS, PAGE):
        qs = urlencode({"dataset": DATASET, "config": config, "split": "test", "offset": offset, "length": PAGE})
        for attempt in range(4):
            try:
                with urlopen(Request(f"{ROWS_API}?{qs}", headers={"User-Agent": "weval-configs"}), timeout=60) as resp:
                    data = json.load(resp)
                break
            except Exception as e:  # network hiccups / rate limits
                if attempt == 3:
                    raise
                time.sleep(2 ** (attempt + 1))
        rows.extend(r["row"] for r in data["rows"])
    if len(rows) != TOTAL_ROWS:
        raise RuntimeError(f"{config}: expected {TOTAL_ROWS} rows, got {len(rows)}")
    return rows


def row_key(row: dict) -> tuple:
    return (row["link"], str(row["question_number"]))


def prompt_id(row: dict) -> str:
    digest = hashlib.sha1(row["link"].encode("utf-8")).hexdigest()[:8]
    return f"bb-{digest}-q{row['question_number']}"


def build_header(lang: str, name: str, n: int, seed: int) -> dict:
    return {
        "title": f"Belebele sample ({n} questions): {name}",
        "description": (
            f"Multiple-choice reading comprehension in **{name}** (`{lang}`), from the "
            "Belebele benchmark: a passage from FLORES-200, a question, and four answers.\n\n"
            f"This is a **sample of {n} of Belebele's 900 questions**, drawn once with seed {seed} "
            "and balanced so each answer letter is correct equally often. "
            "The same questions are used in every language in this set, so scores compare across "
            "languages. Scores are **not** directly comparable to full-benchmark Belebele results.\n\n"
            "**Scoring:** the model is asked to reply with only the letter of the answer; a response "
            "counts as correct when it starts with the right letter (an \"Answer:\" prefix, brackets "
            "or formatting are tolerated). A response that doesn't start with a letter is scored "
            "wrong, so format failures count against a model.\n\n"
            "**Source and license:** Belebele by Bandarkar et al. (Meta FAIR), released under "
            "[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). This file is a "
            "derivative and is shared under the same license, not CC0."
        ),
        "author": {"name": "Lucas Bandarkar et al. (Meta FAIR)", "url": "https://github.com/facebookresearch/belebele"},
        "references": [
            {"title": "The Belebele Benchmark: a Parallel Reading Comprehension Dataset in 122 Language Variants",
             "url": "https://arxiv.org/abs/2308.16884"},
            {"title": "facebook/belebele on Hugging Face", "url": "https://huggingface.co/datasets/facebook/belebele"},
        ],
        "tags": ["benchmark", "multilingual", "reading-comprehension", "multiple-choice", "belebele", name],
        "system": SYSTEM_PROMPT,
    }


def build_prompt(row: dict) -> dict:
    letter = LETTERS[int(row["correct_answer_num"]) - 1]
    return {
        "id": prompt_id(row),
        "prompt": PROMPT_TEMPLATE.format(
            passage=row["flores_passage"].strip(),
            question=row["question"].strip(),
            a1=row["mc_answer1"].strip(), a2=row["mc_answer2"].strip(),
            a3=row["mc_answer3"].strip(), a4=row["mc_answer4"].strip(),
        ),
        "ideal": letter,
        "should": [{"$imatches": answer_regex(letter)}],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=40, help="questions per language (default 40)")
    ap.add_argument("--seed", type=int, default=20260929)
    ap.add_argument("--langs", default=",".join(DEFAULT_LANGS), help="comma-separated Belebele config names")
    ap.add_argument("--out", default="blueprints/benchmarks/belebele")
    args = ap.parse_args()

    langs = [l.strip() for l in args.langs.split(",") if l.strip()]
    os.makedirs(args.out, exist_ok=True)

    # Sample once from English, then look the same questions up in every language.
    # Stratify by correct letter (n/4 each) so a model that favours one letter gains nothing.
    if args.n % len(LETTERS):
        ap.error(f"--n must be a multiple of {len(LETTERS)} so each answer letter is equally represented")
    english = fetch_rows("eng_Latn")
    rng = random.Random(args.seed)
    sample_rows = []
    for num in range(1, len(LETTERS) + 1):
        pool = [r for r in english if int(r["correct_answer_num"]) == num]
        sample_rows += rng.sample(pool, args.n // len(LETTERS))
    rng.shuffle(sample_rows)
    sample_keys = [row_key(r) for r in sample_rows]

    for lang in langs:
        name = DEFAULT_LANGS.get(lang, lang)
        rows = english if lang == "eng_Latn" else fetch_rows(lang)
        by_key = {row_key(r): r for r in rows}
        missing = [k for k in sample_keys if k not in by_key]
        if missing:
            raise RuntimeError(f"{lang}: {len(missing)} sampled questions not found")
        prompts = [build_prompt(by_key[k]) for k in sample_keys]

        header_comment = (
            f"# Belebele sample: {name} ({lang}). Generated by scripts/build_belebele_sample.py "
            f"--n {args.n} --seed {args.seed}; do not edit by hand.\n"
            "# License: CC BY-SA 4.0 (derivative of facebook/belebele), NOT the repo's CC0 default.\n"
        )
        body = (
            yaml.safe_dump(build_header(lang, name, args.n, args.seed), allow_unicode=True, sort_keys=False, width=100)
            + "---\n"
            + yaml.safe_dump(prompts, allow_unicode=True, sort_keys=False, width=100)
        )
        path = os.path.join(args.out, f"belebele-sample-{lang.lower().replace('_', '-')}.yml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(header_comment + body)
        print(f"wrote {path} ({len(prompts)} prompts)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
