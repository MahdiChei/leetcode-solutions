import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[2]

README_FILE = ROOT / "README.md"
METADATA_FILE = ROOT / ".github" / "leetcode_metadata.json"

LEETCODE_GRAPHQL = "https://leetcode.com/graphql"

START_MARKER = "<!-- AUTO-GENERATED:{section} -->"
END_MARKER = "<!-- END AUTO-GENERATED:{section} -->"


# =========================================================
# LeetCode GraphQL
# =========================================================

def leetcode_request(query, variables=None, operation_name=None):
    """
    Make an authenticated request to LeetCode GraphQL.
    """

    session = os.environ.get("LEETCODE_SESSION")
    csrf_token = os.environ.get("LEETCODE_CSRF_TOKEN")

    if not session or not csrf_token:
        raise RuntimeError(
            "LEETCODE_SESSION or LEETCODE_CSRF_TOKEN is missing."
        )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://leetcode.com/",
        "Origin": "https://leetcode.com",
        "x-csrftoken": csrf_token,
    }

    cookies = {
        "LEETCODE_SESSION": session,
        "csrftoken": csrf_token,
    }

    payload = {
        "query": query,
        "variables": variables or {},
    }

    if operation_name:
        payload["operationName"] = operation_name

    response = requests.post(
        LEETCODE_GRAPHQL,
        json=payload,
        headers=headers,
        cookies=cookies,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(
            f"LeetCode GraphQL error: {data['errors']}"
        )

    return data.get("data", {})


def get_question_data(slug):
    """
    Get title, number and difficulty for a problem.
    """

    query = """
    query questionData($titleSlug: String!) {
        question(titleSlug: $titleSlug) {
            questionFrontendId
            title
            titleSlug
            difficulty
        }
    }
    """

    data = leetcode_request(
        query,
        {
            "titleSlug": slug
        },
        "questionData",
    )

    return data.get("question")


def get_recent_accepted_submissions(limit=100):
    """
    Get recent accepted submissions.

    Returns:
        {
            "two-sum": {
                "timestamp": "...",
                "title": "Two Sum"
            }
        }
    """

    query = """
    query recentAcSubmissions($username: String!, $limit: Int!) {
        recentAcSubmissionList(
            username: $username
            limit: $limit
        ) {
            id
            title
            titleSlug
            timestamp
        }
    }
    """

    # First get the authenticated user's username.
    user_query = """
    query {
        userStatus {
            username
        }
    }
    """

    user_data = leetcode_request(
        user_query
    )

    user_status = user_data.get("userStatus")

    if not user_status or not user_status.get("username"):
        raise RuntimeError(
            "Could not determine the LeetCode username."
        )

    username = user_status["username"]

    data = leetcode_request(
        query,
        {
            "username": username,
            "limit": limit,
        },
        "recentAcSubmissions",
    )

    submissions = data.get(
        "recentAcSubmissionList"
    ) or []

    result = {}

    for submission in submissions:

        slug = submission.get("titleSlug")

        if not slug:
            continue

        # Keep the newest submission for each problem.
        if (
            slug not in result
            or submission.get("timestamp", 0)
            > result[slug].get("timestamp", 0)
        ):
            result[slug] = submission

    return result


# =========================================================
# Files / Metadata
# =========================================================

def load_metadata():

    if not METADATA_FILE.exists():
        return {}

    try:
        with open(
            METADATA_FILE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    except (json.JSONDecodeError, OSError):
        return {}


def save_metadata(metadata):

    METADATA_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        METADATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

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

    solution_files = sorted(
        folder.glob("solution.*")
    )

    for file in solution_files:

        extension = file.suffix.lower()

        if extension in extensions:
            return extensions[extension]

    for file in folder.iterdir():

        if not file.is_file():
            continue

        extension = file.suffix.lower()

        if extension in extensions:
            return extensions[extension]

    return "Unknown"


def discover_problems():

    problems = []

    pattern = re.compile(
        r"^(\d+)-(.+)$"
    )

    for path in ROOT.iterdir():

        if not path.is_dir():
            continue

        match = pattern.match(
            path.name
        )

        if not match:
            continue

        number = match.group(1)
        slug = match.group(2)

        has_solution = any(
            file.is_file()
            and file.name.startswith("solution.")
            for file in path.iterdir()
        )

        if not has_solution:
            continue

        problems.append({
            "number": number,
            "slug": slug,
            "language": detect_language(path),
            "folder": path,
        })

    return problems


# =========================================================
# Metadata update
# =========================================================

def update_metadata(metadata, problems):

    print("Fetching LeetCode metadata...")

    recent_submissions = get_recent_accepted_submissions()

    for problem in problems:

        number = problem["number"]
        slug = problem["slug"]

        print(
            f"Processing #{int(number)} {slug}..."
        )

        question = get_question_data(slug)

        if not question:
            print(
                f"WARNING: Could not get metadata for {slug}"
            )

            continue

        title = question.get(
            "title",
            slug
        )

        difficulty = question.get(
            "difficulty",
            "Unknown"
        )

        if number not in metadata:
            metadata[number] = {}

        metadata[number]["title"] = title
        metadata[number]["slug"] = slug
        metadata[number]["difficulty"] = difficulty
        metadata[number]["language"] = problem["language"]

        # -------------------------------------------------
        # Actual accepted submission timestamp
        # -------------------------------------------------

        submission = recent_submissions.get(slug)

        if submission:

            timestamp = submission.get(
                "timestamp"
            )

            if timestamp:

                try:
                    timestamp_int = int(
                        timestamp
                    )

                    dt = datetime.fromtimestamp(
                        timestamp_int,
                        tz=timezone.utc
                    )

                    metadata[number][
                        "solved_at"
                    ] = dt.isoformat()

                except (ValueError, TypeError):
                    pass

        # If LeetCode no longer returns the submission,
        # keep the existing timestamp.
        if "solved_at" not in metadata[number]:

            metadata[number][
                "solved_at"
            ] = datetime.now(
                timezone.utc
            ).isoformat()


# =========================================================
# README
# =========================================================

def replace_section(
    content,
    section,
    new_content
):

    start = START_MARKER.format(
        section=section
    )

    end = END_MARKER.format(
        section=section
    )

    pattern = re.compile(
        re.escape(start)
        + r".*?"
        + re.escape(end),
        re.DOTALL
    )

    replacement = (
        f"{start}\n"
        f"{new_content}\n"
        f"{end}"
    )

    if pattern.search(content):

        return pattern.sub(
            replacement,
            content
        )

    return (
        content.rstrip()
        + "\n\n"
        + replacement
        + "\n"
    )


def generate_progress(metadata):

    counts = {
        "Easy": 0,
        "Medium": 0,
        "Hard": 0,
    }

    for item in metadata.values():

        difficulty = item.get(
            "difficulty",
            "Unknown"
        )

        if difficulty in counts:
            counts[difficulty] += 1

    total = len(metadata)

    return f"""| Difficulty | Solved |
|---|---:|
| Easy | {counts["Easy"]} |
| Medium | {counts["Medium"]} |
| Hard | {counts["Hard"]} |
| **Total** | **{total}** |"""


def generate_languages(metadata):

    languages = sorted({
        item.get(
            "language",
            "Unknown"
        )
        for item in metadata.values()
    })

    if not languages:
        return "No solutions yet."

    return "\n".join(
        f"- {language}"
        for language in languages
    )


def format_date(timestamp):

    if not timestamp:
        return ""

    try:

        dt = datetime.fromisoformat(
            timestamp.replace(
                "Z",
                "+00:00"
            )
        )

        return dt.strftime(
            "%Y-%m-%d"
        )

    except ValueError:

        return timestamp[:10]


def generate_recent(metadata):

    if not metadata:
        return "No solutions yet."

    items = []

    for number, data in metadata.items():

        items.append({
            "number": number,
            **data
        })

    # Actual solve time: newest first.
    items.sort(
        key=lambda item: item.get(
            "solved_at",
            ""
        ),
        reverse=True
    )

    items = items[:5]

    lines = [
        "| # | Problem | Difficulty | Language | Solved |",
        "|---:|---|---|---|---|"
    ]

    for item in items:

        number = int(
            item["number"]
        )

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
            ""
        )

        folder = (
            f"{number:04d}-{slug}"
        )

        lines.append(
            f"| {number} | "
            f"[{title}](./{folder}/) | "
            f"{difficulty} | "
            f"{language} | "
            f"{format_date(item.get('solved_at'))} |"
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

    # Problem number DESCENDING.
    items.sort(
        key=lambda item: int(
            item["number"]
        ),
        reverse=True
    )

    lines = [
        "| # | Problem | Difficulty | Language |",
        "|---:|---|---|---|"
    ]

    for item in items:

        number = int(
            item["number"]
        )

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
            ""
        )

        folder = (
            f"{number:04d}-{slug}"
        )

        lines.append(
            f"| {number} | "
            f"[{title}](./{folder}/) | "
            f"{difficulty} | "
            f"{language} |"
        )

    return "\n".join(lines)


# =========================================================
# Main
# =========================================================

def main():

    print(
        "========================================"
    )
    print(
        " Updating LeetCode dashboard"
    )
    print(
        "========================================"
    )

    problems = discover_problems()

    print(
        f"Found {len(problems)} solution(s)."
    )

    metadata = load_metadata()

    update_metadata(
        metadata,
        problems
    )

    save_metadata(
        metadata
    )

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

    print(
        "README updated successfully."
    )

    print(
        "Metadata updated successfully."
    )


if __name__ == "__main__":
    main()
