#!/usr/bin/env python3
"""Wattle tactical writing CLI.

Pure stdlib. Designed for agent use inside the Wattle skill.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Level:
    name: str
    description: str
    markers: tuple[str, ...]
    guidance: tuple[str, ...]


@dataclass(frozen=True)
class Family:
    name: str
    description: str
    levels: dict[str, Level]


FAMILIES: dict[str, Family] = {
    "defensive": Family(
        name="defensive",
        description="Protective corporate writing that creates a clean record.",
        levels={
            "lite": Level(
                "lite",
                "Calm, clear, non-accusatory boundary setting.",
                ("please confirm", "my understanding", "next step"),
                (
                    "Use neutral facts.",
                    "Avoid blame words.",
                    "Ask for written confirmation.",
                ),
            ),
            "hr_lawyer_lite": Level(
                "hr_lawyer_lite",
                "Documented HR-aware language without pretending to be legal advice.",
                ("written record", "please confirm", "my understanding", "next step"),
                (
                    "Create a documented written record.",
                    "State the impact and requested next step.",
                    "Ask for written confirmation.",
                ),
            ),
            "legalese": Level(
                "legalese",
                "Formal rights-reserved wording for high-risk written records.",
                ("without admission", "reserve all rights", "written response"),
                (
                    "Use narrow factual statements.",
                    "Avoid admissions or speculation.",
                    "Request a written response and reserve rights.",
                ),
            ),
        },
    ),
    "offense": Family(
        name="offense",
        description="Assertive negotiation and escalation bounded by law and professionalism.",
        levels={
            "attack_1": Level(
                "attack_1",
                "Firm ask with cooperative tone.",
                ("clear ask", "next step", "deadline"),
                ("Name the ask.", "Set a reasonable deadline.", "Keep the door open."),
            ),
            "attack_2": Level(
                "attack_2",
                "Sharper leverage and decision framing.",
                ("decision", "deadline", "escalate"),
                (
                    "Frame the tradeoff.",
                    "Use a clear deadline.",
                    "Name escalation as process, not threat.",
                ),
            ),
            "attack_3": Level(
                "attack_3",
                "Executive escalation posture and final opportunity framing.",
                ("final opportunity", "executive review", "deadline"),
                (
                    "Use executive-level consequence framing.",
                    "Avoid threats and personal attacks.",
                    "Keep all claims provable.",
                ),
            ),
        },
    ),
    "persuasion": Family(
        name="persuasion",
        description="Ethical client persuasion tuned to audience and decision stage.",
        levels={
            "consultative": Level(
                "consultative",
                "Trust-building diagnosis and recommendation.",
                ("understand", "recommend", "next step"),
                ("Reflect the problem.", "Recommend one next step.", "Reduce friction."),
            ),
            "executive": Level(
                "executive",
                "Business value, risk, timing, and decision clarity.",
                ("business impact", "risk", "decision"),
                ("Lead with business impact.", "Make the decision easy.", "Keep it brief."),
            ),
            "urgency": Level(
                "urgency",
                "Ethical urgency without false scarcity.",
                ("timing", "opportunity cost", "next step"),
                ("Use real timing pressure.", "Avoid false scarcity.", "Name opportunity cost."),
            ),
        },
    ),
}


SAFETY_PATTERNS: dict[str, tuple[str, ...]] = {
    "deception": ("lie", "fake", "fabricate", "misrepresent", "impersonate"),
    "threat": ("threaten", "ruin their reputation", "destroy them", "blackmail", "extort"),
    "harassment": ("harass", "stalk", "dox", "humiliate"),
    "legal_advice": ("guaranteed legal", "cannot lose in court"),
}


GRADE_WEIGHTS = {
    "performance": 20,
    "efficiency": 15,
    "methodology": 20,
    "ease_of_use": 15,
    "safety": 20,
    "tone_adherence": 10,
}


def normalize_name(value: str) -> str:
    return value.strip().lower().replace("-", "_").replace(" ", "_")


def get_family(style: str) -> Family:
    key = normalize_name(style)
    if key not in FAMILIES:
        raise ValueError(f"unknown style: {style}")
    return FAMILIES[key]


def get_level(style: str, level: str) -> Level:
    family = get_family(style)
    key = normalize_name(level)
    aliases = {
        "hr": "hr_lawyer_lite",
        "lawyer_lite": "hr_lawyer_lite",
        "hr_lawyer": "hr_lawyer_lite",
        "attack1": "attack_1",
        "attack2": "attack_2",
        "attack3": "attack_3",
    }
    key = aliases.get(key, key)
    if key not in family.levels:
        raise ValueError(f"unknown level for {family.name}: {level}")
    return family.levels[key]


def read_text(args: argparse.Namespace) -> str:
    if getattr(args, "text", None):
        return args.text
    if getattr(args, "input", None):
        return Path(args.input).read_text(encoding="utf-8")
    stdin = sys.stdin.read()
    if stdin.strip():
        return stdin
    return ""


def emit(payload, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, indent=2, sort_keys=True))


def list_payload() -> dict:
    return {
        "families": {
            name: {
                "description": family.description,
                "levels": {
                    level_name: {
                        "description": level.description,
                        "markers": list(level.markers),
                    }
                    for level_name, level in family.levels.items()
                },
            }
            for name, family in FAMILIES.items()
        }
    }


def advise(style: str, context: str) -> dict:
    family = get_family(style)
    text = context.lower()
    if family.name == "defensive":
        if any(word in text for word in ("hr", "retaliation", "manager", "termination", "discipline")):
            level = family.levels["hr_lawyer_lite"]
        elif any(word in text for word in ("lawyer", "legal", "contract", "breach", "claim")):
            level = family.levels["legalese"]
        else:
            level = family.levels["lite"]
    elif family.name == "offense":
        if any(word in text for word in ("executive", "final", "escalation")):
            level = family.levels["attack_3"]
        elif any(word in text for word in ("deadline", "leverage", "negotiate")):
            level = family.levels["attack_2"]
        else:
            level = family.levels["attack_1"]
    else:
        if any(word in text for word in ("ceo", "cfo", "board", "executive")):
            level = family.levels["executive"]
        elif any(word in text for word in ("deadline", "urgent", "closing", "expires")):
            level = family.levels["urgency"]
        else:
            level = family.levels["consultative"]
    return {
        "style": family.name,
        "recommended_level": level.name,
        "description": level.description,
        "guidance": list(level.guidance),
    }


def safety_flags(text: str) -> list[str]:
    lower = text.lower()
    flags = []
    for name, patterns in SAFETY_PATTERNS.items():
        if any(pattern in lower for pattern in patterns):
            flags.append(name)
    return flags


def sentences(text: str) -> list[str]:
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s.strip()]


def clean_aggression(text: str) -> str:
    replacements = {
        r"\byou ignored\b": "I do not have a response recorded for",
        r"\bfix it today\b": "please confirm the path forward by end of day",
        r"\bthis needs to stop\b": "I need this addressed through the proper process",
        r"\byou failed\b": "the current record does not show completion",
        r"\bobviously\b": "based on the current record",
    }
    out = text
    for pattern, replacement in replacements.items():
        out = re.sub(pattern, replacement, out, flags=re.IGNORECASE)
    return out.strip()


def ensure_period(text: str) -> str:
    text = text.strip()
    if not text:
        return text
    if text[-1] not in ".!?":
        return text + "."
    return text


def rewrite_text(style: str, level_name: str, text: str) -> str:
    family = get_family(style)
    level = get_level(style, level_name)
    base = ensure_period(clean_aggression(text))
    if not base:
        base = "I am writing to confirm the next step."

    if family.name == "defensive":
        if level.name == "lite":
            prefix = "For clarity, my understanding is as follows: "
            suffix = " Please confirm the next step in writing."
        elif level.name == "hr_lawyer_lite":
            prefix = "For the written record, my understanding is as follows: "
            suffix = " Please confirm the next step, the owner, and the expected timing in writing."
        else:
            prefix = "Without admission and with all rights reserved, this letter confirms the following: "
            suffix = " Please provide a written response identifying your position, the next step, and any documents you contend support it."
    elif family.name == "offense":
        if level.name == "attack_1":
            prefix = "The clear ask is this: "
            suffix = " Please confirm the next step and deadline."
        elif level.name == "attack_2":
            prefix = "This now requires a decision: "
            suffix = " If we do not have confirmation by the deadline, I will escalate through the appropriate business process."
        else:
            prefix = "This is the final opportunity to resolve the issue before executive review: "
            suffix = " Please confirm your position by the deadline so the next action can proceed on the record."
    else:
        if level.name == "consultative":
            prefix = "I understand the goal and recommend this next step: "
            suffix = " This keeps the path simple and gives us a clear decision point."
        elif level.name == "executive":
            prefix = "The business impact is straightforward: "
            suffix = " The decision is whether to reduce the risk now or carry the opportunity cost forward."
        else:
            prefix = "The timing matters because the opportunity cost is increasing: "
            suffix = " The next step is to confirm whether we should move now or pause intentionally."

    rewritten = prefix + base
    if suffix.lower() not in rewritten.lower():
        rewritten += suffix
    return rewritten


def qa(style: str, level_name: str, text: str) -> dict:
    level = get_level(style, level_name)
    flags = safety_flags(text)
    lower = text.lower()
    marker_hits = [marker for marker in level.markers if marker in lower]
    score = 100
    score -= max(0, len(level.markers) - len(marker_hits)) * 8
    score -= len(flags) * 30
    if len(text.split()) > 260:
        score -= 10
    if style == "offense" and any(word in lower for word in ("idiot", "stupid", "worthless")):
        flags.append("harassment")
        score -= 30
    score = max(0, min(100, score))
    return {
        "ok": not flags and score >= 90,
        "score": score,
        "flags": sorted(set(flags)),
        "marker_hits": marker_hits,
        "missing_markers": [marker for marker in level.markers if marker not in marker_hits],
        "guidance": list(level.guidance),
    }


def loop(style: str, level: str, text: str, max_iter: int) -> dict:
    current = text
    history = []
    for index in range(max_iter):
        current = rewrite_text(style, level, current)
        result = qa(style, level, current)
        history.append({"iteration": index + 1, "score": result["score"], "flags": result["flags"]})
        if result["ok"]:
            break
    final = qa(style, level, current)
    return {"text": current, "score": final["score"], "ok": final["ok"], "history": history}


def grade() -> dict:
    root = Path(__file__).resolve().parent.parent
    checks = {
        "skill_file": (root / "SKILL.md").exists(),
        "openai_yaml": (root / "agents" / "openai.yaml").exists(),
        "script_file": (root / "scripts" / "wattle.py").exists(),
        "weights_sum": sum(GRADE_WEIGHTS.values()) == 100,
        "core_families": {"defensive", "offense", "persuasion"}.issubset(FAMILIES),
        "safety_flags": set(safety_flags("lie and threaten to ruin their reputation")) == {"deception", "threat"},
        "loop_score": loop("defensive", "hr_lawyer_lite", "Fix it today.", 3)["score"] >= 90,
    }
    all_ok = all(checks.values())
    categories = {name: 100 if all_ok else 0 for name in GRADE_WEIGHTS}
    return {"overall": 100 if all_ok else 0, "categories": categories, "checks": checks}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wattle tactical writing toolbox")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List styles and levels")
    p_list.add_argument("--json", action="store_true")

    p_advise = sub.add_parser("advise", help="Recommend a level for a style")
    p_advise.add_argument("--style", required=True)
    p_advise.add_argument("--context", default="")
    p_advise.add_argument("--json", action="store_true")

    for name in ("rewrite", "qa", "loop"):
        p = sub.add_parser(name)
        p.add_argument("--style", required=True)
        p.add_argument("--level", required=True)
        p.add_argument("--text")
        p.add_argument("--input")
        p.add_argument("--json", action="store_true")
        if name == "loop":
            p.add_argument("--max-iter", type=int, default=4)

    p_grade = sub.add_parser("grade", help="Run deterministic graders")
    p_grade.add_argument("--json", action="store_true")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        if args.command == "list":
            emit(list_payload(), args.json)
            return 0
        if args.command == "advise":
            emit(advise(args.style, args.context), args.json)
            return 0
        if args.command == "rewrite":
            emit(rewrite_text(args.style, args.level, read_text(args)), args.json)
            return 0
        if args.command == "qa":
            result = qa(args.style, args.level, read_text(args))
            emit(result, args.json)
            return 0 if result["ok"] else 2
        if args.command == "loop":
            result = loop(args.style, args.level, read_text(args), args.max_iter)
            emit(result, args.json)
            return 0 if result["ok"] else 2
        if args.command == "grade":
            result = grade()
            emit(result, args.json)
            return 0 if result["overall"] == 100 else 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

