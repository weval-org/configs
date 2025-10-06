#!/usr/bin/env python3
"""
Generate Weval YAML blueprints to evaluate model sensitivity to table/data formats.

This script creates one YAML blueprint per selected format. Each blueprint embeds a
seeded synthetic dataset of employee records in the prompt and asks a set of
deterministic numeric lookup questions (exact-match scoring).

Outputs are written under blueprints/table-format-sensitivity/ by default.

Usage example:
  python3 scripts/generate_table_format_eval.py \
    --formats markdown_kv,csv,jsonl,markdown_table,yaml \
    --num-records 150 --num-questions 150

The dataset/question design mirrors common format evaluations (11 formats) and
uses fixed seeds for reproducibility.

Inspired by [Which Table Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-input-data-format-for-llms).
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import string
from io import StringIO
from textwrap import dedent
from typing import Dict, List, NamedTuple, Sequence, TypedDict, Callable


# Defaults chosen for fast local runs. You can scale these up as desired.
DEFAULT_NUM_RECORDS = 150
DEFAULT_NUM_QUESTIONS = 150
RECORD_SEED = 202310
QUESTION_SEED = 424242


FIRST_NAMES = [
    "Alice", "Benjamin", "Charlotte", "Diana", "Elliot", "Fiona", "Grace", "Henry",
    "Isla", "Jack", "Liam", "Maya", "Noah", "Olivia", "Paige", "Quinn", "Riley",
    "Sophia", "Theo", "Uma", "Violet", "Wyatt", "Xavier", "Yara", "Zane",
]

CITIES = [
    "London", "New York", "San Francisco", "Berlin", "Paris", "Sydney", "Toronto",
    "Singapore", "Tokyo", "Dublin", "Chicago", "Austin", "Madrid", "Amsterdam",
    "Dubai", "Stockholm", "Zurich", "Hong Kong", "Vancouver", "Seoul",
]

DEPARTMENTS = [
    "Engineering", "Product", "Design", "Operations", "Finance", "Marketing",
    "Sales", "Support", "Customer Success", "Data",
]


class EmployeeRecord(TypedDict):
    id: int
    name: str
    age: int
    city: str
    department: str
    salary: int
    years_experience: int
    project_count: int


class QAEntry(TypedDict):
    record_id: int
    field: str
    question: str
    answer: str


class FormatSpec(NamedTuple):
    key: str
    label: str
    formatter: Callable[[Sequence[EmployeeRecord]], str]


NUMERIC_FIELDS: Dict[str, str] = {
    "salary": "What is {name}'s salary? (Return just the number, e.g. '85200'.)",
    "years_experience": "How many years of experience does {name} have? (Return just the number, e.g. '12'.)",
    "age": "How old is {name}? (Return just the number, e.g. '42'.)",
    "project_count": "How many projects has {name} completed? (Return just the number, e.g. '15'.)",
}

DEA_SYSTEM_PROMPT = (
    "You are a data extraction assistant. You will be given a collection of employee records and a question about those records.\n"
    "Return only the exact numeric value requested. Use digits without commas, decimal points, or additional words. If the value cannot be found, reply with N/A."
)


def generate_employee_records(count: int, seed: int) -> List[EmployeeRecord]:
    rng = random.Random(seed)
    used_names: set[str] = set()
    records: List[EmployeeRecord] = []
    for idx in range(1, count + 1):
        name = _random_name(rng, used_names)
        age = rng.randint(22, 67)
        max_experience = max(0, age - 18)
        years_experience = rng.randint(0, max_experience)
        salary = rng.randint(45_000, 165_000)
        project_count = rng.randint(0, 60)
        city = rng.choice(CITIES)
        department = rng.choice(DEPARTMENTS)
        record: EmployeeRecord = {
            "id": idx,
            "name": name,
            "age": age,
            "city": city,
            "department": department,
            "salary": salary,
            "years_experience": years_experience,
            "project_count": project_count,
        }
        records.append(record)
    return records


def _random_name(rng: random.Random, used_names: set[str]) -> str:
    while True:
        first = rng.choice(FIRST_NAMES)
        suffix_letter = rng.choice(string.ascii_uppercase)
        suffix_number = rng.randint(0, 999)
        candidate = f"{first} {suffix_letter}{suffix_number:03d}"
        if candidate not in used_names:
            used_names.add(candidate)
            return candidate


def generate_questions(records: Sequence[EmployeeRecord], count: int, seed: int) -> List[QAEntry]:
    rng = random.Random(seed)
    questions: List[QAEntry] = []
    fields = list(NUMERIC_FIELDS.keys())
    for _ in range(count):
        record = rng.choice(records)
        field = rng.choice(fields)
        template = NUMERIC_FIELDS[field]
        question = template.format(name=record["name"])
        answer = str(record[field])
        questions.append(QAEntry(record_id=record["id"], field=field, question=question, answer=answer))
    return questions


# ---------- Formatters ----------


def format_json(records: Sequence[EmployeeRecord]) -> str:
    payload = [dict(r) for r in records]
    return json.dumps(payload, indent=2)


def format_csv(records: Sequence[EmployeeRecord]) -> str:
    if not records:
        return ""
    fieldnames = list(records[0].keys())
    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for r in records:
        writer.writerow(r)
    return buffer.getvalue().strip()


def format_xml(records: Sequence[EmployeeRecord]) -> str:
    lines: List[str] = ["<?xml version=\"1.0\" ?>", "<employees>"]
    for r in records:
        lines.append(f"  <employee id=\"{r['id']}\">")
        lines.append(f"    <name>{r['name']}</name>")
        lines.append(f"    <age>{r['age']}</age>")
        lines.append(f"    <city>{r['city']}</city>")
        lines.append(f"    <department>{r['department']}</department>")
        lines.append(f"    <salary>{r['salary']}</salary>")
        lines.append(f"    <years_experience>{r['years_experience']}</years_experience>")
        lines.append(f"    <project_count>{r['project_count']}</project_count>")
        lines.append("  </employee>")
    lines.append("</employees>")
    return "\n".join(lines)


def format_yaml(records: Sequence[EmployeeRecord]) -> str:
    lines: List[str] = ["records:"]
    for r in records:
        lines.append(f"  - id: {r['id']}")
        lines.append(f"    name: \"{r['name']}\"")
        lines.append(f"    age: {r['age']}")
        lines.append(f"    city: \"{r['city']}\"")
        lines.append(f"    department: \"{r['department']}\"")
        lines.append(f"    salary: {r['salary']}")
        lines.append(f"    years_experience: {r['years_experience']}")
        lines.append(f"    project_count: {r['project_count']}")
    return "\n".join(lines)


def format_html(records: Sequence[EmployeeRecord]) -> str:
    if not records:
        return ""
    headers = list(records[0].keys())
    lines: List[str] = ["<table>", "  <thead>", "    <tr>"]
    for h in headers:
        lines.append(f"      <th>{h}</th>")
    lines.extend(["    </tr>", "  </thead>", "  <tbody>"])
    for r in records:
        lines.append("    <tr>")
        for h in headers:
            lines.append(f"      <td>{r[h]}</td>")
        lines.append("    </tr>")
    lines.extend(["  </tbody>", "</table>"])
    return "\n".join(lines)


def format_markdown_table(records: Sequence[EmployeeRecord]) -> str:
    if not records:
        return ""
    headers = list(records[0].keys())
    header_row = "| " + " | ".join(headers) + " |"
    divider_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_rows: List[str] = []
    for r in records:
        row = "| " + " | ".join(str(r[h]) for h in headers) + " |"
        body_rows.append(row)
    return "\n".join([header_row, divider_row, *body_rows])


def format_markdown_kv(records: Sequence[EmployeeRecord]) -> str:
    lines: List[str] = ["# Employee Database"]
    for r in records:
        lines.append("")
        lines.append(f"## Record {r['id']}")
        lines.append("")
        lines.append("```")
        for key, value in r.items():
            lines.append(f"{key}: {value}")
        lines.append("```")
    return "\n".join(lines)


def format_ini(records: Sequence[EmployeeRecord]) -> str:
    lines: List[str] = []
    for r in records:
        lines.append(f"[employee_{r['id']}]")
        for key, value in r.items():
            lines.append(f"{key} = {value}")
        lines.append("")
    return "\n".join(lines).strip()


def format_pipe_delimited(records: Sequence[EmployeeRecord]) -> str:
    if not records:
        return ""
    headers = list(records[0].keys())
    rows: List[str] = []
    for r in records:
        parts = [f"{h}: {r[h]}" for h in headers]
        rows.append(" | ".join(parts))
    return "\n".join(rows)


def format_jsonl(records: Sequence[EmployeeRecord]) -> str:
    return "\n".join(json.dumps(r) for r in records)


def format_natural_language(records: Sequence[EmployeeRecord]) -> str:
    lines: List[str] = ["Employee Records Summary:"]
    for r in records:
        lines.append(
            f"{r['name']} (ID: {r['id']}) is a {r['age']}-year-old employee working in the "
            f"{r['department']} department in {r['city']}. They earn ${r['salary']} with "
            f"{r['years_experience']} years of experience and have completed {r['project_count']} projects."
        )
    return "\n".join(lines)


FORMAT_SPECS: Dict[str, FormatSpec] = {
    "json": FormatSpec("json", "JSON array", format_json),
    "csv": FormatSpec("csv", "CSV", format_csv),
    "xml": FormatSpec("xml", "XML", format_xml),
    "yaml": FormatSpec("yaml", "YAML", format_yaml),
    "html": FormatSpec("html", "HTML table", format_html),
    "markdown_table": FormatSpec("markdown_table", "Markdown table", format_markdown_table),
    "markdown_kv": FormatSpec("markdown_kv", "Markdown key-value blocks", format_markdown_kv),
    "ini": FormatSpec("ini", "INI sections", format_ini),
    "pipe_delimited": FormatSpec("pipe_delimited", "Pipe-delimited records", format_pipe_delimited),
    "jsonl": FormatSpec("jsonl", "JSON Lines", format_jsonl),
    "natural_language": FormatSpec("natural_language", "Natural language summary", format_natural_language),
}


def _indent_block(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join((prefix + line) if line != "" else "" for line in text.splitlines())


def build_blueprint_yaml(
    *,
    format_key: str,
    format_label: str,
    dataset_block: str,
    questions: Sequence[QAEntry],
    num_records: int,
    num_questions: int,
    models: Sequence[str] | None = None,
    temperatures: Sequence[float] | None = None,
    systems: Sequence[str] | None = None,  # values in {"dea", "null"}
) -> str:
    if models is None:
        models = ["CORE"]
    if temperatures is None:
        temperatures = [0.0]
    if not systems:
        systems = ["dea"]

    header_lines: List[str] = [
        f"title: \"Table-Format Sensitivity — {format_label} ({num_records}×{num_questions})\"",
        "description: |",
        f"  Measures exact-match retrieval accuracy for numeric lookups across {num_questions} questions",
        f"  using a seeded synthetic dataset of {num_records} employee records formatted as {format_label}.",
        "  Each prompt embeds the full dataset block and asks for a single numeric value.",
        "",
        "  References:",
        "  - Blog: [Which Table Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-input-data-format-for-llms)",
        "  - Script: https://github.com/weval-org/configs/blob/main/scripts/generate_table_format_eval.py",
        "",
        "  Reproduction command:",
        "  ```",
        # repro command inserted here
        "tags:",
        "  - Format-Sensitivity",
        "  - Data-Representation",
        "models:",
    ]
    header_lines.extend([f"  - {m}" for m in models])
    temps_str = ", ".join(f"{t:.1f}" if isinstance(t, float) else str(t) for t in temperatures)
    header_lines.append(f"temperatures: [{temps_str}]")
    header_lines.append("systems:")
    if "null" in systems:
        header_lines.append("  - null")
    if "dea" in systems:
        header_lines.append("  - |")
        header_lines.append(_indent_block(DEA_SYSTEM_PROMPT, 4))

    # Insert repro command block before tags end
    repro_cmd = (
        "python3 scripts/generate_table_format_eval.py "
        f"--formats {format_key} --num-records {num_records} --num-questions {num_questions} "
        f"--temperatures {temps_str} --systems "
        + ("both" if set(systems) == {"dea", "null"} else systems[0])
        + " --out-dir blueprints/table-format-sensitivity --models "
        + ",".join(models)
    )
    # Insert after the "  ```" placeholder line (which is currently at index 7)
    # Find index of placeholder
    placeholder_idx = header_lines.index("  ```")
    header_lines.insert(placeholder_idx + 1, _indent_block(repro_cmd, 2))
    header_lines.insert(placeholder_idx + 2, "  ```")

    header_lines.append("---")
    header = "\n".join(header_lines)

    # Prompts
    prompt_items: List[str] = []
    intro = (
        f"You are provided with {num_records} employee records formatted as {format_label}. Use the data to answer the question.\n\n"
        f"DATA START\n{dataset_block}\nDATA END"
    )

    for idx, qa in enumerate(questions):
        prompt_text = f"{intro}\n\nQuestion: {qa['question']}"
        item_lines = [
            f"- id: {format_key}-{idx:04d}",
            "  prompt: |",
            _indent_block(prompt_text, 4),  # Block scalar content indented deeper than key
            "  should:",
            f"    - $matches: '\\b{qa['answer']}\\b'",
            f"    - $matches: '^{qa['answer']}$'",
        ]
        prompt_items.append("\n".join(item_lines))

    body = "\n".join(prompt_items)
    return f"{header}\n{body}\n"


def write_blueprint(
    out_dir: str,
    filename: str,
    content: str,
) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def build_combined_blueprint_yaml(
    *,
    format_keys: Sequence[str],
    num_records: int,
    per_format_questions: int,
    models: Sequence[str],
    temperatures: Sequence[float],
    systems: Sequence[str],  # values in {"dea", "null"}
) -> str:
    # Prepare shared records and questions
    records = generate_employee_records(num_records, RECORD_SEED)
    questions = generate_questions(records, per_format_questions, QUESTION_SEED)

    header_lines: List[str] = [
        f"title: \"Table-Format Sensitivity — Combined ({len(format_keys)} formats, {num_records}×{per_format_questions}/fmt)\"",
        "description: |",
        f"  Combined blueprint covering multiple data formats. Each format uses the same seeded",
        f"  dataset of {num_records} employee records and {per_format_questions} questions per format.",
        "  We measure exact-match numeric retrieval per prompt.",
        "",
        "  References:",
        "  - Blog: [Which Table Format Do LLMs Understand Best?](https://www.improvingagents.com/blog/best-input-data-format-for-llms)",
        "  - Script: https://github.com/weval-org/configs/blob/main/scripts/generate_table_format_eval.py",
        "",
        "  Reproduction command:",
        "  ```",
        # repro command inserted here
        "tags:",
        "  - Format-Sensitivity",
        "  - Data-Representation",
        "models:",
    ]
    header_lines.extend([f"  - {m}" for m in models])
    temps_str = ", ".join(f"{t:.1f}" if isinstance(t, float) else str(t) for t in temperatures)
    header_lines.append(f"temperatures: [{temps_str}]")
    header_lines.append("systems:")
    if "null" in systems:
        header_lines.append("  - null")
    if "dea" in systems:
        header_lines.append("  - |")
        header_lines.append(_indent_block(DEA_SYSTEM_PROMPT, 4))

    # Insert repro command block
    repro_cmd = (
        "python3 scripts/generate_table_format_eval.py --combined "
        f"--formats {','.join(format_keys)} --num-records {num_records} --per-format-questions {per_format_questions} "
        f"--temperatures {temps_str} --systems "
        + ("both" if set(systems) == {"dea", "null"} else systems[0])
        + " --out-dir blueprints/table-format-sensitivity --models "
        + ",".join(models)
    )
    placeholder_idx = header_lines.index("  ```")
    header_lines.insert(placeholder_idx + 1, _indent_block(repro_cmd, 2))
    header_lines.insert(placeholder_idx + 2, "  ```")

    header_lines.append("---")
    header = "\n".join(header_lines)

    prompt_items: List[str] = []
    for fmt_key in format_keys:
        spec = FORMAT_SPECS[fmt_key]
        dataset_block = spec.formatter(records)
        intro = (
            f"You are provided with {num_records} employee records formatted as {spec.label}. Use the data to answer the question.\n\n"
            f"DATA START\n{dataset_block}\nDATA END"
        )
        for idx, qa in enumerate(questions):
            prompt_text = f"{intro}\n\nQuestion: {qa['question']}"
            item_lines = [
                f"- id: {fmt_key}-{idx:04d}",
                "  prompt: |",
                _indent_block(prompt_text, 4),
                "  should:",
                f"    - $matches: '\\b{qa['answer']}\\b'",
                f"    - $matches: '^{qa['answer']}$'",
            ]
            prompt_items.append("\n".join(item_lines))

    body = "\n".join(prompt_items)
    return f"{header}\n{body}\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate table-format sensitivity Weval blueprints.")
    parser.add_argument(
        "--formats",
        type=str,
        default="markdown_kv,csv,jsonl,markdown_table,yaml",
        help="Comma-separated list of formats (keys). Use 'all' for every supported format.",
    )
    parser.add_argument("--num-records", type=int, default=DEFAULT_NUM_RECORDS)
    parser.add_argument("--num-questions", type=int, default=DEFAULT_NUM_QUESTIONS)
    parser.add_argument(
        "--out-dir",
        type=str,
        default=os.path.join("blueprints", "table-format-sensitivity"),
        help="Output directory for generated YAML blueprints.",
    )
    parser.add_argument(
        "--models",
        type=str,
        default="CORE",
        help="Comma-separated list of model identifiers or collection placeholders (e.g., CORE, FRONTIER).",
    )
    parser.add_argument(
        "--combined",
        action="store_true",
        help="Generate a single combined blueprint containing all selected formats.",
    )
    parser.add_argument(
        "--per-format-questions",
        type=int,
        default=5,
        help="When --combined is set, number of questions per format.",
    )
    parser.add_argument(
        "--systems",
        type=str,
        default="dea",
        help="Which system prompts to include: dea|null|both",
    )
    parser.add_argument(
        "--temperatures",
        type=str,
        default="0.0,0.1,0.2",
        help="Comma-separated temperatures to write into the blueprint header.",
    )
    args = parser.parse_args()

    if args.formats.strip().lower() == "all":
        selected = list(FORMAT_SPECS.keys())
    else:
        selected = [s.strip() for s in args.formats.split(",") if s.strip()]

    invalid = [s for s in selected if s not in FORMAT_SPECS]
    if invalid:
        raise SystemExit(f"Unknown format keys: {invalid}. Valid: {sorted(FORMAT_SPECS.keys())}")

    models = [s.strip() for s in args.models.split(",") if s.strip()]
    try:
        temperatures = [float(s.strip()) for s in args.temperatures.split(",") if s.strip()]
    except ValueError:
        raise SystemExit("--temperatures must be a comma-separated list of numbers, e.g. 0.0,0.1,0.2")
    sys_opt = args.systems.strip().lower()
    if sys_opt not in {"dea", "null", "both"}:
        raise SystemExit("--systems must be one of: dea|null|both")
    systems = ["dea", "null"] if sys_opt == "both" else [sys_opt]

    if args.combined:
        yaml_text = build_combined_blueprint_yaml(
            format_keys=selected,
            num_records=args.num_records,
            per_format_questions=args.per_format_questions,
            models=models,
            temperatures=temperatures,
            systems=systems,
        )
        filename = (
            f"combined-{len(selected)}fmts-r{args.num_records}-qpf{args.per_format_questions}.yml"
        )
        path = write_blueprint(args.out_dir, filename, yaml_text)
        print(f"Wrote {path}")
    else:
        # Generate dataset and questions deterministically
        records = generate_employee_records(args.num_records, RECORD_SEED)
        questions = generate_questions(records, args.num_questions, QUESTION_SEED)

        # Produce one blueprint per format
        for fmt_key in selected:
            spec = FORMAT_SPECS[fmt_key]
            dataset_block = spec.formatter(records)
            yaml_text = build_blueprint_yaml(
                format_key=fmt_key,
                format_label=spec.label,
                dataset_block=dataset_block,
                questions=questions,
                num_records=args.num_records,
                num_questions=args.num_questions,
                models=models,
                temperatures=temperatures,
            )
            filename = f"table-format-sensitivity__{fmt_key}__r{args.num_records}__q{args.num_questions}.yml"
            path = write_blueprint(args.out_dir, filename, yaml_text)
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()


