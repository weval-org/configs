#!/usr/bin/env python3

import os


def number_to_english(number: int) -> str:
    """Return the lowercase English words for 1..100.

    Uses hyphen between tens and ones for 21..99 (e.g., 'seventy-nine').
    """
    if number < 1 or number > 100:
        raise ValueError("number_to_english supports only 1..100")

    ones = {
        0: "zero",
        1: "one",
        2: "two",
        3: "three",
        4: "four",
        5: "five",
        6: "six",
        7: "seven",
        8: "eight",
        9: "nine",
        10: "ten",
        11: "eleven",
        12: "twelve",
        13: "thirteen",
        14: "fourteen",
        15: "fifteen",
        16: "sixteen",
        17: "seventeen",
        18: "eighteen",
        19: "nineteen",
    }
    tens_words = {
        20: "twenty",
        30: "thirty",
        40: "forty",
        50: "fifty",
        60: "sixty",
        70: "seventy",
        80: "eighty",
        90: "ninety",
    }

    if number <= 19:
        return ones[number]
    if number == 100:
        return "one hundred"

    tens = (number // 10) * 10
    remainder = number % 10
    if remainder == 0:
        return tens_words[tens]
    return f"{tens_words[tens]}-{ones[remainder]}"


def english_number_regex(number: int) -> str:
    """Return a regex fragment that matches the English words for the number.

    For hyphenated numbers (e.g., 'seventy-nine'), allow either hyphen or space: 'seventy[ -]nine'.
    """
    english = number_to_english(number)
    if "-" in english:
        parts = english.split("-")
        return f"{parts[0]}[ -]{parts[1]}"
    return english


def generate_r_word(r_count: int) -> str:
    """Generate a variant of 'strawberry' that contains exactly r_count 'r' letters.

    The base structure is: 'st' + 'r' * a + 'awbe' + 'r' * b + 'y' where a + b = r_count.
    This keeps the word visually close to 'strawberry' while scaling the number of 'r's.
    """
    if r_count < 0:
        raise ValueError("r_count must be non-negative")
    a = r_count // 2
    b = r_count - a
    return "st" + ("r" * a) + "awbe" + ("r" * b) + "y"


def ideal_sentence(n: int) -> str:
    if n == 1:
        return "There is 1 R in the word."
    return f"There are {n} Rs in the word."


def imatches_regex(n: int) -> str:
    """Build the case-insensitive regex for the expected answer for number n."""
    english = english_number_regex(n)
    if n == 1:
        return f"\\bthere is (?:1|{english})\\b"
    return f"\\bthere are (?:{n}|{english})\\b"


def build_yaml() -> str:
    header = (
        "id: strawberry\n"
        "title: Strawberry\n"
        "description: The famous strawberry test\n"
        "tags:\n"
        "- Test\n"
        "models:\n"
        "- CORE\n"
        "- FRONTIER\n"
    )

    sections = [header]
    for n in range(1, 101):
        word = generate_r_word(n)
        prompt = (
            f"How many Rs are in the word {word}? "
            "Reply in the form, 'There are N Rs in the word.'"
        )
        ideal = ideal_sentence(n)
        regex = imatches_regex(n)

        section = (
            "---\n"
            f"id: '{n}'\n"
            f"prompt: {prompt}\n"
            f"ideal: {ideal}\n"
            "should:\n"
            f"- $imatches: {regex}\n"
        )
        sections.append(section)

    return "".join(sections)


def main() -> None:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    output_path = os.path.join(project_root, "blueprints", "strawberry.yml")
    yaml_content = build_yaml()
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(yaml_content)
    print(f"Wrote strawberry YAML to: {output_path}")


if __name__ == "__main__":
    main()


