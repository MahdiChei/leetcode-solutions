import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

README_FILE = ROOT / "README.md"
METADATA_FILE = ROOT / ".github" / "leetcode_metadata.json"

START_MARKER = "<!-- AUTO-GENERATED:{section} -->"
END_MARKER = "<!-- END AUTO-GENERATED:{section} -->"


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def load_metadata():
    if not METADATA_FILE.exists():
        return {}

    try:
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_metadata(metadata):
    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
        f.write("\n")


def detect_language(folder):
    extensions = {
        ".py": "Python",
        ".php": "PHP",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".java": "Java",
        ".cpp": "C++",
        ".c": "C",
        ".cs": "C#",
        ".go": "Go",
        ".rs": "Rust",
        ".kt": "Kotlin",
        ".swift": "Swift",
        ".rb": "Ruby",
        ".scala": "Scala",
        ".sql": "SQL",
    }

    # Prefer files named solution.*
    solution_files = sorted(folder.glob("solution.*"))

    for file in solution_files:
        if file.suffix.lower() in extensions:
            return extensions[file.suffix.lower()]

    # Fallback: inspect all files in the folder
    for file in folder.iterdir():
        if file.is_file() and file.suffix.lower() in extensions:
            return extensions[file.suffix.lower()]

    return "Unknown"


def title_from_slug(slug):
    """
    two-sum -> Two Sum
    valid-parentheses -> Valid Parentheses
    """
    return " ".join(word.capitalize() for word in slug.split("-"))


def discover_problems():
    """
    Find directories such as:

    0001-two-sum/
    0015-3sum/
    0020-valid-parentheses/
    """

    problems = []

    pattern = re.compile(r"^(\d+)-(.+)$")

    for path in ROOT.iterdir():

        if not path.is_dir():
            continue

        match = pattern.match(path.name)

        if not match:
            continue

        number = match.group(1)
        slug = match.group(2)

        # Ignore folders that don't contain a solution
        has_solution = any(
            file.is_file() and file.name.startswith("solution.")
            for file in path.iterdir()
        )

        if not has_solution:
            continue

        problems.append({
            "number": number,
            "slug": slug,
            "title": title_from_slug(slug),
            "language": detect_language(path),
            "folder": path,
        })

    return problems


# ---------------------------------------------------------
# Metadata
# ---------------------------------------------------------

def update_metadata(metadata, problems):
    now = datetime.now(timezone.utc).isoformat()

    for problem in problems:

        number = problem["number"]

        if number not in metadata:

            metadata[number] = {
                "title": problem["title"],
                "difficulty": "Unknown",
                "language": problem["language"],
                "solved_at": now,
            }

        else:

            # Keep existing solved_at.
            metadata[number]["title"] = problem["title"]
            metadata[number]["language"] = problem["language"]

            if "difficulty" not in metadata[number]:
                metadata[number]["difficulty"] = "Unknown"

            if "solved_at" not in metadata[number]:
                metadata[number]["solved_at"] = now


# ---------------------------------------------------------
# README generation
# ---------------------------------------------------------

def replace_section(content, section, new_content):

    start = START_MARKER.format(section=section)
    end = END_MARKER.format(section=section)

    pattern = re.compile(
        re.escape(start) + r".*?" + re.escape(end),
        re.DOTALL
    )

    replacement = (
        f"{start}\n"
        f"{new_content}\n"
        f"{end}"
    )

    if pattern.search(content):
        return pattern.sub(replacement, content)

    # If the section doesn't exist, append it.
    return (
        content.rstrip()
        + "\n\n"
        + replacement
        + "\n"
    )


def generate_progress(metadata):

    easy = 0
    medium = 0
    hard = 0

    for item in metadata.values():

        difficulty = item.get("difficulty", "Unknown").lower()

        if difficulty == "easy":
            easy += 1

        elif difficulty == "medium":
            medium += 1

        elif difficulty == "hard":
            hard += 1

    total = len(metadata)

    return f"""| Difficulty | Solved |
|---|---:|
| Easy | {easy} |
| Medium | {medium} |
| Hard | {hard} |
| **Total** | **{total} |"""


def generate_languages(metadata):

    languages = sorted({
        item.get("language", "Unknown")
        for item in metadata.values()
    })

    if not languages:
        return "No solutions yet."

    return "\n".join(
        f"- {language}"
        for language in languages
    )


def generate_recent(metadata):

    if not metadata:
        return "No solutions yet."

    items = []

    for number, data in metadata.items():

        items.append({
            "number": number,
            **data
        })

    items.sort(
        key=lambda x: x.get("solved_at", ""),
        reverse=True
    )

    items = items[:5]

    lines = [
        "| # | Problem | Difficulty | Language | Solved |",
        "|---:|---|---|---|---|"
    ]

    for item in items:

        number = int(item["number"])

        title = item.get(
            "title",
            f"Problem {number}"
        )

        difficulty = item.get(
            "difficulty",
            "Unknown"
        )

        language = item.get(
            "language",
            "Unknown"
        )

        solved_at = item.get(
            "solved_at",
            ""
        )

        # Keep the displayed date readable
        if solved_at:
            try:
                dt = datetime.fromisoformat(
                    solved_at.replace("Z", "+00:00")
                )
                solved_display = dt.strftime("%Y-%m-%d")
            except ValueError:
                solved_display = solved_at[:10]
        else:
            solved_display = ""

        folder = f"{number:04d}-{item.get('slug', title.lower().replace(' ', '-'))}"

        lines.append(
            f"| {number} | "
            f"[{title}](./{folder}/) | "
            f"{difficulty} | "
            f"{language} | "
            f"{solved_display} |"
        )

    return "\n".join(lines)


def generate_all_problems(metadata):

    if not metadata:
        return "No solutions yet."

    items = []

    for number, data in metadata.items():

        items.append({
            "number": number,
            **data
        })

    # Numerical descending order
    items.sort(
        key=lambda x: int(x["number"]),
        reverse=True
    )

    lines = [
        "| # | Problem | Difficulty | Language |",
        "|---:|---|---|---|"
    ]

    for item in items:

        number = int(item["number"])

        title = item.get(
            "title",
            f"Problem {number}"
        )

        difficulty = item.get(
            "difficulty",
            "Unknown"
        )

        language = item.get(
            "language",
            "Unknown"
        )

        slug = item.get(
            "slug",
            title.lower().replace(" ", "-")
        )

        folder = f"{number:04d}-{slug}"

        lines.append(
            f"| {number} | "
            f"[{title}](./{folder}/) | "
            f"{difficulty} | "
            f"{language} |"
        )

    return "\n".join(lines)


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

def main():

    print("Scanning LeetCode solutions...")

    problems = discover_problems()

    print(f"Found {len(problems)} solution(s).")

    metadata = load_metadata()

    # Keep slug information in metadata so README links
    # remain correct.
    for problem in problems:

        number = problem["number"]

        if number not in metadata:
            metadata[number] = {}

        metadata[number]["slug"] = problem["slug"]

    update_metadata(metadata, problems)

    save_metadata(metadata)

    if README_FILE.exists():

        readme = README_FILE.read_text(
            encoding="utf-8"
        )

    else:

        readme = """# LeetCode Solutions

My solutions to LeetCode problems, automatically synchronized using GitHub Actions.

## Progress

<!-- AUTO-GENERATED:PROGRESS -->
| Difficulty | Solved |
|---|---:|
| Easy | 0 |
| Medium | 0 |
| Hard | 0 |
| **Total** | **0** |
<!-- END AUTO-GENERATED:PROGRESS -->

## Languages

<!-- AUTO-GENERATED:LANGUAGES -->
No solutions yet.
<!-- END AUTO-GENERATED:LANGUAGES -->

## Recent Solutions

<!-- AUTO-GENERATED:RECENT -->
No solutions yet.
<!-- END AUTO-GENERATED:RECENT -->

## All Problems

<!-- AUTO-GENERATED:PROBLEMS -->
No solutions yet.
<!-- END AUTO-GENERATED:PROBLEMS -->
"""

    readme = replace_section(
        readme,
        "PROGRESS",
        generate_progress(metadata)
    )

    readme = replace_section(
        readme,
        "LANGUAGES",
        generate_languages(metadata)
    )

    readme = replace_section(
        readme,
        "RECENT",
        generate_recent(metadata)
    )

    readme = replace_section(
        readme,
        "PROBLEMS",
        generate_all_problems(metadata)
    )

    README_FILE.write_text(
        readme,
        encoding="utf-8"
    )

    print("README updated.")
    print("Metadata updated.")


if __name__ == "__main__":
    main()
