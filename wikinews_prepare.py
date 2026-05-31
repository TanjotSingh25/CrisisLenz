import argparse
import bz2
import json
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

import mwparserfromhell


HIGH_VALUE_KEYWORDS = {
    # Natural disasters / emergencies
    "earthquake": 10,
    "wildfire": 10,
    "forest fire": 10,
    "flood": 10,
    "hurricane": 9,
    "cyclone": 9,
    "storm": 6,
    "tsunami": 10,
    "evacuation": 9,
    "evacuated": 9,
    "disaster": 7,
    "emergency": 6,

    # Conflict / security / political instability
    "war": 10,
    "invasion": 10,
    "attack": 9,
    "missile": 9,
    "airstrike": 9,
    "strike": 6,
    "bomb": 8,
    "bombing": 9,
    "explosion": 8,
    "terror": 8,
    "terrorist": 8,
    "sanctions": 7,
    "coup": 9,
    "military": 6,
    "conflict": 7,
    "unrest": 8,
    "riot": 8,
    "protest": 6,
    "clashes": 8,
    "violence": 7,
    "insurgency": 8,

    # Business / operational disruption
    "airport": 6,
    "port": 6,
    "rail": 6,
    "train": 5,
    "highway": 5,
    "road closed": 6,
    "power outage": 9,
    "blackout": 9,
    "supply chain": 9,
    "factory": 5,
    "plant": 5,
    "chemical spill": 10,
    "oil spill": 10,
    "workers strike": 8,
    "general strike": 8,

    # Severity indicators
    "killed": 10,
    "dead": 9,
    "injured": 8,
    "missing": 7,
    "destroyed": 7,
    "damaged": 6,
    "closed": 5,
    "cancelled": 5,
    "canceled": 5,
}

LOW_VALUE_KEYWORDS = {
    "lunch": -12,
    "dinner": -8,
    "meets": -5,
    "meeting": -4,
    "speech": -5,
    "ceremony": -7,
    "award": -8,
    "film": -8,
    "music": -8,
    "album": -8,
    "movie": -8,
    "television": -6,
    "sports": -8,
    "football": -8,
    "cricket": -8,
    "celebrity": -8,
    "interview": -10,
    "wikinews interviews": -15,
    "opinion": -6,
}

CATEGORY_HINTS = {
    "natural_disaster": [
        "earthquake", "wildfire", "forest fire", "flood", "hurricane",
        "cyclone", "storm", "tsunami", "evacuation", "disaster"
    ],
    "political_security": [
        "war", "invasion", "sanctions", "coup", "military",
        "unrest", "riot", "protest", "attack", "clashes",
        "missile", "airstrike", "bomb", "bombing", "terror",
        "violence", "conflict", "insurgency"
    ],
    "infrastructure": [
        "airport", "port", "rail", "train", "highway", "road closed",
        "power outage", "blackout", "closed", "cancelled", "canceled"
    ],
    "industrial": [
        "factory", "plant", "chemical spill", "oil spill", "explosion"
    ],
}


def child_text(elem, tag_name):
    for child in elem:
        if child.tag.endswith(tag_name):
            return child.text
    return None


def child_elem(elem, tag_name):
    for child in elem:
        if child.tag.endswith(tag_name):
            return child
    return None


def clean_wikitext(wikitext):
    if not wikitext:
        return ""

    parsed = mwparserfromhell.parse(wikitext)
    text = parsed.strip_code()

    text = re.sub(r"\{\{.*?\}\}", " ", text, flags=re.DOTALL)
    text = re.sub(r"\[\[Category:.*?\]\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"thumb\|.*", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)

    return text.strip()


def extract_summary(text, max_chars=700):
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 80]

    if paragraphs:
        return paragraphs[0][:max_chars].strip()

    return text[:max_chars].strip()


def parse_date(date_string):
    if not date_string:
        return None

    try:
        if date_string.endswith("Z"):
            date_string = date_string.replace("Z", "+00:00")
        return datetime.fromisoformat(date_string)
    except ValueError:
        return None


def is_archive_or_index_page(article):
    title = article.get("title", "").strip()
    body = article.get("body", "")
    title_lower = title.lower()
    body_lower = body.lower()

    # Examples: Australia/2006, Canada/2007, United States/2008
    if re.search(r"/\d{4}$", title):
        return True

    # WikiNews date/category index pages often contain many date lines
    date_lines = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", body)
    if len(date_lines) >= 20:
        return True

    if "datenews" in body_lower and len(date_lines) >= 10:
        return True

    bad_title_prefixes = (
        "category:",
        "portal:",
        "template:",
        "wikinews:",
        "help:",
        "file:",
        "user:",
        "special:",
    )

    if title_lower.startswith(bad_title_prefixes):
        return True

    return False


def is_interview_or_bad_format(article):
    title = article.get("title", "").strip().lower()
    body = article.get("body", "").strip().lower()

    if title.startswith("wikinews interviews"):
        return True

    if "interview with" in title:
        return True

    if title.startswith("interview:"):
        return True

    # Long interview pages are usually bad demo signals.
    if " interview " in body[:1500] and len(body) > 8000:
        return True

    # Extremely long pages are usually not clean signal-style articles.
    if len(body) > 15000:
        return True

    return False


def extract_articles(input_path, output_path, min_chars=250):
    count = 0
    skipped = 0

    with bz2.open(input_path, "rb") as file, open(output_path, "w", encoding="utf-8") as out:
        context = ET.iterparse(file, events=("end",))

        for _, elem in context:
            if not elem.tag.endswith("page"):
                continue

            title = child_text(elem, "title") or ""
            namespace = child_text(elem, "ns") or ""
            revision = child_elem(elem, "revision")
            redirect = child_elem(elem, "redirect")

            if namespace != "0" or redirect is not None or revision is None:
                skipped += 1
                elem.clear()
                continue

            timestamp = child_text(revision, "timestamp")
            text_elem = child_elem(revision, "text")
            raw_text = text_elem.text if text_elem is not None else ""

            body = clean_wikitext(raw_text)

            if len(body) < min_chars:
                skipped += 1
                elem.clear()
                continue

            article = {
                "source_type": "wikinews_dump",
                "source_name": "Wikinews",
                "title": title,
                "published_at": timestamp,
                "summary": extract_summary(body),
                "body": body,
                "language": "en",
                "url": f"https://en.wikinews.org/wiki/{title.replace(' ', '_')}",
            }

            out.write(json.dumps(article, ensure_ascii=False) + "\n")
            count += 1

            if count % 1000 == 0:
                print(f"Extracted {count} articles...")

            elem.clear()

    print(f"Done. Extracted {count} articles.")
    print(f"Skipped {skipped} pages.")
    print(f"Output: {output_path}")


def weighted_keyword_score(article):
    title = article.get("title", "").lower()
    summary = article.get("summary", "").lower()
    body = article.get("body", "").lower()

    score = 0
    matched = []

    # Title matters most.
    for keyword, weight in HIGH_VALUE_KEYWORDS.items():
        if keyword in title:
            score += weight * 2.0
            matched.append(keyword)

        if keyword in summary:
            score += weight * 1.3
            matched.append(keyword)

        # Body gets lower weight to avoid false positives from long articles.
        if keyword in body:
            score += weight * 0.35
            matched.append(keyword)

    for keyword, weight in LOW_VALUE_KEYWORDS.items():
        if keyword in title:
            score += weight * 2.0

        if keyword in summary:
            score += weight * 1.3

        if keyword in body:
            score += weight * 0.35

    category_scores = {}

    full_text = f"{title} {summary} {body}"

    for category, keywords in CATEGORY_HINTS.items():
        category_score = 0
        for keyword in keywords:
            if keyword in title:
                category_score += HIGH_VALUE_KEYWORDS.get(keyword, 0) * 2.0
            if keyword in summary:
                category_score += HIGH_VALUE_KEYWORDS.get(keyword, 0) * 1.3
            if keyword in body:
                category_score += HIGH_VALUE_KEYWORDS.get(keyword, 0) * 0.35

        category_scores[category] = category_score

    best_category = max(category_scores, key=category_scores.get)

    if category_scores[best_category] <= 0:
        best_category = "general_risk"

    return round(score, 2), best_category, sorted(set(matched))


def is_valid_article_shape(article):
    if is_archive_or_index_page(article):
        return False

    if is_interview_or_bad_format(article):
        return False

    title = article.get("title", "").strip()
    body = article.get("body", "").strip()

    if len(title) < 10:
        return False

    if len(body) < 250:
        return False

    if len(body) > 15000:
        return False

    return True


def build_replay_dataset(
    input_path,
    output_path,
    good_output_path,
    bad_output_path,
    good_count,
    bad_count,
    min_score,
    bad_max_score,
    seed,
    include_internal_labels,
    start_date=None,
    end_date=None,
):
    random.seed(seed)

    good_candidates = []
    bad_candidates = []

    total = 0
    skipped_shape = 0

    start_dt = parse_date(start_date) if start_date else None
    end_dt = parse_date(end_date) if end_date else None

    with open(input_path, "r", encoding="utf-8") as file:
        for line in file:
            total += 1
            article = json.loads(line)

            if not is_valid_article_shape(article):
                skipped_shape += 1
                continue

            article_dt = parse_date(article.get("published_at"))

            if start_dt and article_dt and article_dt < start_dt:
                continue

            if end_dt and article_dt and article_dt > end_dt:
                continue

            score, category, matched = weighted_keyword_score(article)

            prepared = dict(article)
            prepared["filter_score"] = score
            prepared["category_hint"] = category
            prepared["matched_keywords"] = matched

            # Useful crisis/business-risk signals
            if score >= min_score and category != "general_risk":
                if include_internal_labels:
                    prepared["demo_quality"] = "signal_candidate"
                good_candidates.append(prepared)

            # Bad/noise examples: article-shaped, but low relevance
            elif score <= bad_max_score:
                if include_internal_labels:
                    prepared["demo_quality"] = "noise_candidate"
                bad_candidates.append(prepared)

    good_candidates.sort(key=lambda x: x["filter_score"], reverse=True)

    selected_good = good_candidates[:good_count]

    if len(bad_candidates) > bad_count:
        selected_bad = random.sample(bad_candidates, bad_count)
    else:
        selected_bad = bad_candidates

    final_dataset = selected_good + selected_bad
    random.shuffle(final_dataset)

    Path(output_path).write_text(
        json.dumps(final_dataset, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    Path(good_output_path).write_text(
        json.dumps(good_candidates[: max(good_count * 2, 100)], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    Path(bad_output_path).write_text(
        json.dumps(bad_candidates[: max(bad_count * 5, 50)], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Total extracted articles scanned: {total}")
    print(f"Skipped bad-shape/archive/interview pages: {skipped_shape}")
    print(f"Good candidates found: {len(good_candidates)}")
    print(f"Bad/noise candidates found: {len(bad_candidates)}")
    print(f"Selected good signals: {len(selected_good)}")
    print(f"Selected bad/noise signals: {len(selected_bad)}")
    print(f"Final mixed replay dataset: {output_path}")
    print(f"Good candidate review file: {good_output_path}")
    print(f"Bad candidate review file: {bad_output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Prepare Wikinews replay data for Crisis Lens"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser("extract")
    extract_parser.add_argument("--input", required=True)
    extract_parser.add_argument("--output", default="all_wikinews_articles.jsonl")
    extract_parser.add_argument("--min-chars", type=int, default=250)

    build_parser = subparsers.add_parser("build")
    build_parser.add_argument("--input", default="all_wikinews_articles.jsonl")
    build_parser.add_argument("--output", default="final_replay_signals.json")
    build_parser.add_argument("--good-output", default="good_candidates.json")
    build_parser.add_argument("--bad-output", default="bad_candidates.json")
    build_parser.add_argument("--good-count", type=int, default=85)
    build_parser.add_argument("--bad-count", type=int, default=15)
    build_parser.add_argument("--min-score", type=float, default=18)
    build_parser.add_argument("--bad-max-score", type=float, default=3)
    build_parser.add_argument("--seed", type=int, default=42)
    build_parser.add_argument("--include-internal-labels", action="store_true")
    build_parser.add_argument("--start-date", default=None)
    build_parser.add_argument("--end-date", default=None)

    args = parser.parse_args()

    if args.command == "extract":
        extract_articles(
            input_path=Path(args.input),
            output_path=Path(args.output),
            min_chars=args.min_chars,
        )

    elif args.command == "build":
        build_replay_dataset(
            input_path=Path(args.input),
            output_path=Path(args.output),
            good_output_path=Path(args.good_output),
            bad_output_path=Path(args.bad_output),
            good_count=args.good_count,
            bad_count=args.bad_count,
            min_score=args.min_score,
            bad_max_score=args.bad_max_score,
            seed=args.seed,
            include_internal_labels=args.include_internal_labels,
            start_date=args.start_date,
            end_date=args.end_date,
        )


if __name__ == "__main__":
    main()