import json
import re
from pathlib import Path
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
METADATA_PATH = ROOT / ".github" / "leetcode_metadata.json"


LANGUAGES = {
    ".py": "Python",
    ".php": "PHP",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".cpp": "C++",
    ".c": "C",
    ".cs": "C#",
    ".go": "Go",
    ".rs": "Rust",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".rb": "Ruby",
    ".sql": "SQL",
}


def load_metadata():
    if not METADATA_PATH.exists():
        return {}

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def save_metadata(metadata):
    METADATA_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(METADATA_PATH, "w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)


def get_problem_number(folder_name):
    match = re.match(r"^(\d+)-", folder_name)

    if not match:
        return None

    return int(match.group(1))


def get_problem_title(folder_name):
    match = re.match(r"^\d+-(.+)$", folder_name)

    if not match:
        return folder_name

    title = match.group(1)

    return title.replace("-", " ").title()


def read_problem_readme(problem_dir):
    readme_path = problem_dir / "README.md"

    if not readme_path.exists():
        return {}

    content = readme_path.read_text(encoding="utf-8")

    difficulty = None

    for level in ["Easy", "Medium", "Hard"]:
        if re.search(rf"\b{level}\b", content, re.IGNORECASE):
            difficulty = level
            break

    return {
        "difficulty": difficulty or "Unknown"
    }


def detect_language(problem_dir):
    for file in problem_dir.iterdir():

        if not file.is_file():
            continue

        if file.name.lower() == "readme.md":
            continue

        extension = file.suffix.lower()

        if extension in LANGUAGES:
            return LANGUAGES[extension]

    return "Unknown"


def collect_problems(metadata):
    problems = []

    for item in ROOT.iterdir():

        if not item.is_dir():
            continue

        problem_number = get_problem_number(item.name)

        if problem_number is None:
            continue

        problem_info = read_problem_readme(item)

        difficulty = problem_info.get("difficulty", "Unknown")
        language = detect_language(item)

        problem_key = f"{problem_number:04d}"

        if problem_key not in metadata:
            metadata[problem_key] = {
                "solved_at": datetime.now(timezone.utc).isoformat()
            }

        problems.append({
            "number": problem_number,
            "title": get_problem_title(item.name),
            "difficulty": difficulty,
            "language": language,
            "solved_at": metadata[problem_key]["solved_at"],
        })

    return problems


def generate_progress(problems):
    counts = {
        "Easy": 0,
        "Medium": 0,
        "Hard": 0,
    }

    for problem in problems:
        difficulty = problem["difficulty"]

        if difficulty in counts:
            counts[difficulty] += 1

    total = sum(counts.values())

    return (
        "| Difficulty | Solved |\n"
        "|---|---:|\n"
        f"| Easy | {counts['Easy']} |\n"
        f"| Medium | {counts['Medium']} |\n"
        f"| Hard | {counts['Hard']} |\n"
        f"| **Total** | **{total}** |"
    )


def generate_languages(problems):
    languages = sorted(
        {
            problem["language"]
            for problem in problems
            if problem["language"] != "Unknown"
        }
    )

    if not languages:
        return "No solutions yet."

    return "\n".join(f"- {language}" for language in languages)


def generate_problem_table(problems):
    if not problems:
        return "No solutions yet."

    sorted_problems = sorted(
        problems,
        key=lambda problem: problem["number"],
        reverse=True
    )

    lines = [
        "| # | Problem | Difficulty | Language |",
        "|---:|---|---|---|"
    ]

    for problem in sorted_problems:
        lines.append(
            f"| {problem['number']} | "
            f"{problem['title']} | "
            f"{problem['difficulty']} | "
            f"{problem['language']} |"
        )

    return "\n".join(lines)


def generate_recent_table(problems):
    if not problems:
        return "No solutions yet."

    recent = sorted(
        problems,
        key=lambda problem: problem["solved_at"],
        reverse=True
    )[:5]

    lines = [
        "| # | Problem | Difficulty | Language |",
        "|---:|---|---|---|"
    ]

    for problem in recent:
        lines.append(
            f"| {problem['number']} | "
            f"{problem['title']} | "
            f"{problem['difficulty']} | "
            f"{problem['language']} |"
        )

    return "\n".join(lines)


def replace_section(content, section_name, new_content):
    pattern = (
        rf"(<!-- AUTO-GENERATED:{section_name} -->)"
        rf".*?"
        rf"(<!-- END AUTO-GENERATED:{section_name} -->)"
    )

    replacement = (
        rf"\1\n"
        f"{new_content}\n"
        rf"\2"
    )

    updated_content, count = re.subn(
        pattern,
        replacement,
        content,
        flags=re.DOTALL
    )

    if count == 0:
        raise RuntimeError(
            f"Could not find AUTO-GENERATED:{section_name} "
            f"markers in README.md"
        )

    return updated_content


def update_readme(problems):
    content = README_PATH.read_text(encoding="utf-8")

    content = replace_section(
        content,
        "PROGRESS",
        generate_progress(problems)
    )

    content = replace_section(
        content,
        "LANGUAGES",
        generate_languages(problems)
    )

    content = replace_section(
        content,
        "RECENT",
        generate_recent_table(problems)
    )

    content = replace_section(
        content,
        "PROBLEMS",
        generate_problem_table(problems)
    )

    README_PATH.write_text(
        content,
        encoding="utf-8"
    )


def main():
    metadata = load_metadata()

    problems = collect_problems(metadata)

    save_metadata(metadata)

    update_readme(problems)

    print(f"Found {len(problems)} LeetCode problems.")
    print("README.md updated successfully.")


if __name__ == "__main__":
    main()
