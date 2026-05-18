import re
from html import escape

from django.utils.safestring import mark_safe


class QuizBlobError(ValueError):
    pass


def fix_mojibake(value):
    if not isinstance(value, str):
        return value
    if "â" in value or "�" in value or "€" in value:
        try:
            fixed = value.encode("latin1", errors="ignore").decode("utf-8", errors="ignore")
            if fixed and fixed != value:
                return fixed
        except Exception:
            pass
    return value


def normalize_questions(raw):
    if isinstance(raw, list):
        rows = raw
    elif isinstance(raw, dict) and isinstance(raw.get("questions"), list):
        rows = raw["questions"]
    elif isinstance(raw, dict) and isinstance(raw.get("items"), list):
        rows = raw["items"]
    elif isinstance(raw, dict) and isinstance(raw.get("data"), list):
        rows = raw["data"]
    else:
        raise QuizBlobError("Expected a list of questions or an object with a questions/items/data list.")

    questions = [normalize_question(q, i) for i, q in enumerate(rows, start=1)]
    if not questions:
        raise QuizBlobError("Question blob contains no questions.")
    return questions


def normalize_question(row, ordinal):
    if not isinstance(row, dict):
        raise QuizBlobError(f"Question {ordinal} is not an object.")

    text = fix_mojibake(row.get("text") or row.get("stem") or row.get("question") or "")
    if not str(text).strip():
        raise QuizBlobError(f"Question {ordinal} is missing text/stem/question.")

    choices, answer_idx = normalize_choices(row, ordinal)
    explanation = fix_mojibake(row.get("explanation") or row.get("explanations") or row.get("rationale") or "")

    extras = {}
    for key in ("id", "topic", "model", "category", "difficulty"):
        if row.get(key) not in (None, ""):
            extras[key] = row[key]
    if isinstance(row.get("extras"), dict):
        extras.update({k: v for k, v in row["extras"].items() if v not in (None, "")})

    return {
        "text": text,
        "choices": choices,
        "answer": answer_idx,
        "explanation": explanation,
        "extras": extras,
    }


def normalize_choices(row, ordinal):
    if isinstance(row.get("choices"), list) and row["choices"]:
        choices = [fix_mojibake(choice) for choice in row["choices"]]
        answer = row.get("answer")
        if isinstance(answer, int):
            answer_idx = answer
        else:
            answer_idx = letter_to_index(row.get("correct_answer") or row.get("answer_letter"), choices)
    elif isinstance(row.get("options"), dict) and row["options"]:
        letters = [letter for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" if letter in row["options"]]
        choices = [fix_mojibake(row["options"][letter]) for letter in letters]
        answer_idx = letter_to_index(row.get("correct_answer") or row.get("answer_letter") or row.get("answer"), letters)
    elif isinstance(row.get("items"), list) and row["items"]:
        items = row["items"]
        letters = [str(item[0]) for item in items if isinstance(item, (list, tuple)) and len(item) >= 2]
        choices = [fix_mojibake(item[1]) for item in items if isinstance(item, (list, tuple)) and len(item) >= 2]
        answer_idx = letter_to_index(row.get("correct") or row.get("correct_answer") or row.get("answer"), letters)
    else:
        raise QuizBlobError(f"Question {ordinal} is missing choices/options.")

    if not choices:
        raise QuizBlobError(f"Question {ordinal} has no choices.")
    if answer_idx < 0 or answer_idx >= len(choices):
        raise QuizBlobError(f"Question {ordinal} has an answer outside the choice range.")
    return choices, answer_idx


def letter_to_index(value, letters):
    if isinstance(value, int):
        return value
    token = str(value or "").strip().upper().rstrip(".")
    if token in letters:
        return letters.index(token)
    if token.startswith("OPTION "):
        token = token.removeprefix("OPTION ").strip()
        if token in letters:
            return letters.index(token)
    return 0


def looks_like_html(text):
    return isinstance(text, str) and bool(re.search(r"</?[a-zA-Z][^>]*>", text))


def render_markdown_basic(text):
    if not isinstance(text, str):
        return ""
    text = fix_mojibake(text)
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out = []
    para = []
    ordered = []
    unordered = []
    quote = []

    math_pattern = re.compile(r"(\$\$[\s\S]+?\$\$|\\\[[\s\S]+?\\\]|\\\([\s\S]+?\\\)|(?<!\$)\$[^$\n]+\$(?!\$))")

    def inline_md(value):
        parts = []
        last = 0
        for match in math_pattern.finditer(value):
            if match.start() > last:
                parts.append(("text", value[last : match.start()]))
            parts.append(("math", match.group(0)))
            last = match.end()
        if last < len(value):
            parts.append(("text", value[last:]))

        rendered = []
        for kind, chunk in parts:
            if kind == "math":
                rendered.append(escape(chunk))
                continue
            chunk = escape(chunk)
            chunk = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', chunk)
            chunk = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", chunk)
            chunk = re.sub(r"__(.+?)__", r"<strong>\1</strong>", chunk)
            chunk = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"<em>\1</em>", chunk)
            chunk = re.sub(r"`([^`]+)`", r"<code>\1</code>", chunk)
            rendered.append(chunk)
        return "".join(rendered)

    def flush_para():
        if para:
            out.append(f"<p>{'<br>'.join(inline_md(x) for x in para)}</p>")
            para.clear()

    def flush_ordered():
        if ordered:
            out.append("<ol>" + "".join(f"<li>{inline_md(x)}</li>" for x in ordered) + "</ol>")
            ordered.clear()

    def flush_unordered():
        if unordered:
            out.append("<ul>" + "".join(f"<li>{inline_md(x)}</li>" for x in unordered) + "</ul>")
            unordered.clear()

    def flush_quote():
        if quote:
            out.append(f"<blockquote>{'<br>'.join(inline_md(x) for x in quote)}</blockquote>")
            quote.clear()

    def flush_blocks():
        flush_para()
        flush_ordered()
        flush_unordered()
        flush_quote()

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_blocks()
            continue
        if line.startswith(">"):
            flush_para()
            flush_ordered()
            flush_unordered()
            quote.append(line[1:].lstrip())
            continue
        ordered_match = re.match(r"^\s*\d+\.\s+(.+)$", line)
        if ordered_match:
            flush_para()
            flush_unordered()
            flush_quote()
            ordered.append(ordered_match.group(1))
            continue
        unordered_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if unordered_match:
            flush_para()
            flush_ordered()
            flush_quote()
            unordered.append(unordered_match.group(1))
            continue
        flush_ordered()
        flush_unordered()
        flush_quote()
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            flush_para()
            level = min(len(heading_match.group(1)), 6)
            out.append(f"<h{level}>{inline_md(heading_match.group(2).strip())}</h{level}>")
            continue
        para.append(line)

    flush_blocks()
    return "\n".join(out)


def render_rich_html(text):
    if not isinstance(text, str):
        return ""
    normalized = re.sub(r"<br\s*/?>", "\n", fix_mojibake(text), flags=re.IGNORECASE)
    if looks_like_html(normalized):
        return mark_safe(normalized)
    return mark_safe(render_markdown_basic(normalized))


def render_choice_html(text):
    if not isinstance(text, str):
        return ""
    normalized = re.sub(r"<br\s*/?>", "\n", fix_mojibake(text), flags=re.IGNORECASE)
    return mark_safe(escape(normalized).replace("\n", "<br>"))
