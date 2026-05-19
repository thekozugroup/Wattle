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
                ("without admission", "all rights reserved", "written response"),
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
    "coercion": ("or i will report you", "pay or", "report you to regulators", "report you to the press"),
    "false_scarcity": ("expires tonight", "last chance ever"),
    "fabricated_evidence": ("fabricate evidence", "fake citation", "fake document"),
    "admission": ("i admit", "i breached", "i owe damages", "my fault"),
    "legal_advice": ("guaranteed legal", "cannot lose in court", "you should sue", "valid claim", "legally entitled", "complies with law"),
}


GRADE_WEIGHTS = {
    "performance": 20,
    "efficiency": 15,
    "methodology": 20,
    "ease_of_use": 15,
    "safety": 20,
    "tone_adherence": 10,
}

GRADE_FIXTURES = (
    {
        "style": "defensive",
        "level": "lite",
        "text": "You ignored the request and this needs to stop.",
    },
    {
        "style": "defensive",
        "level": "hr_lawyer_lite",
        "text": "You failed to respond about the schedule change. Fix it today.",
    },
    {
        "style": "defensive",
        "level": "legalese",
        "text": "The vendor missed the May 12 milestone and owes a written answer.",
    },
    {
        "style": "offense",
        "level": "attack_1",
        "text": "We need an answer on the revised invoice.",
    },
    {
        "style": "offense",
        "level": "attack_2",
        "text": "The pricing issue is blocking approval.",
    },
    {
        "style": "offense",
        "level": "attack_3",
        "text": "This unresolved renewal issue needs senior attention.",
    },
    {
        "style": "persuasion",
        "level": "consultative",
        "text": "The client is unsure whether the rollout is worth doing.",
    },
    {
        "style": "persuasion",
        "level": "executive",
        "text": "The buyer needs a board-ready reason to move now.",
    },
    {
        "style": "persuasion",
        "level": "urgency",
        "text": "The decision has been delayed for two weeks.",
    },
)


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
        if any(re.search(rf"(?<!\w){re.escape(pattern)}(?!\w)", lower) for pattern in patterns):
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


def critique(style: str, level_name: str, text: str) -> dict:
    result = qa(style, level_name, text)
    findings = []
    if result["flags"]:
        findings.append("Resolve safety flags before rewriting.")
    if result["missing_markers"]:
        findings.append("Add missing tone markers for the selected level.")
    if len(text.split()) > 260:
        findings.append("Shorten the draft before final use.")
    if not findings:
        findings.append("No deterministic gaps found.")
    result["critique"] = findings
    result["next_action"] = "finalize" if result["ok"] else "rewrite"
    return result


def loop(style: str, level: str, text: str, max_iter: int) -> dict:
    current = text
    history = []
    stop_reason = "max_iter"
    initial = qa(style, level, current)
    if initial["flags"]:
        return {
            "text": current,
            "score": initial["score"],
            "ok": False,
            "flags": initial["flags"],
            "history": [{"iteration": 0, "score": initial["score"], "flags": initial["flags"]}],
            "stop_reason": "safety_flags",
        }
    for index in range(max_iter):
        current = rewrite_text(style, level, current)
        result = qa(style, level, current)
        history.append({"iteration": index + 1, "score": result["score"], "flags": result["flags"]})
        if result["flags"]:
            stop_reason = "safety_flags"
            break
        if result["ok"]:
            stop_reason = "score_threshold"
            break
    final = qa(style, level, current)
    return {
        "text": current,
        "score": final["score"],
        "ok": final["ok"],
        "flags": final["flags"],
        "history": history,
        "stop_reason": stop_reason,
    }


def _score_checks(checks: dict[str, bool]) -> int:
    return 100 if all(checks.values()) else 0


def run_grade_wave(wave: int) -> dict:
    root = Path(__file__).resolve().parent.parent
    fixture_results = [loop(item["style"], item["level"], item["text"], 4) for item in GRADE_FIXTURES]
    fixture_qas = [
        qa(item["style"], item["level"], result["text"])
        for item, result in zip(GRADE_FIXTURES, fixture_results)
    ]
    checks_by_category = {
        "performance": {
            "all_fixture_scores_pass": all(result["score"] >= 90 for result in fixture_results),
            "outputs_nonempty": all(bool(result["text"].strip()) for result in fixture_results),
        },
        "efficiency": {
            "bounded_iterations": all(len(result["history"]) <= 4 for result in fixture_results),
            "bounded_output_length": all(len(result["text"].split()) <= 120 for result in fixture_results),
        },
        "methodology": {
            "history_recorded": all(result["history"] for result in fixture_results),
            "stop_reason_recorded": all(result["stop_reason"] for result in fixture_results),
            "rubric_reference_exists": (root / "references" / "rubric.md").exists(),
        },
        "ease_of_use": {
            "skill_file": (root / "SKILL.md").exists(),
            "openai_yaml": (root / "agents" / "openai.yaml").exists(),
            "script_file": (root / "scripts" / "wattle.py").exists(),
            "readme_exists": (root.parent / "README.md").exists(),
        },
        "safety": {
            "deception_threat_flagged": set(safety_flags("lie and threaten to ruin their reputation")) == {"deception", "threat"},
            "legal_overclaim_flagged": "legal_advice" in safety_flags("guaranteed legal result"),
            "safe_fixture_outputs": all(not item["flags"] for item in fixture_qas),
        },
        "tone_adherence": {
            "markers_present": all(not item["missing_markers"] for item in fixture_qas),
            "all_levels_covered": len({(item["style"], item["level"]) for item in GRADE_FIXTURES}) == 9,
        },
    }
    categories = {name: _score_checks(checks) for name, checks in checks_by_category.items()}
    critique_lines = [
        f"{name}: {'pass' if score == 100 else 'fail'}"
        for name, score in categories.items()
    ]
    return {
        "wave": wave,
        "overall": 100 if all(score == 100 for score in categories.values()) else 0,
        "categories": categories,
        "checks": checks_by_category,
        "critique": critique_lines,
    }


def grade(full: bool = False, waves: int = 1) -> dict:
    base_checks = {
        "weights_sum": sum(GRADE_WEIGHTS.values()) == 100,
        "core_families": {"defensive", "offense", "persuasion"}.issubset(FAMILIES),
    }
    wave_reports = [run_grade_wave(index + 1) for index in range(max(1, waves if full else 1))]
    categories = {
        name: 100 if base_checks["weights_sum"] and all(wave["categories"][name] == 100 for wave in wave_reports) else 0
        for name in GRADE_WEIGHTS
    }
    overall = 100 if base_checks["core_families"] and all(score == 100 for score in categories.values()) else 0
    payload = {
        "overall": overall,
        "categories": categories,
        "checks": base_checks,
    }
    if full:
        payload["waves"] = wave_reports
    else:
        payload["checks"].update(wave_reports[0]["checks"])
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Wattle tactical writing toolbox")
    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List styles and levels")
    p_list.add_argument("--json", action="store_true")

    p_advise = sub.add_parser("advise", help="Recommend a level for a style")
    p_advise.add_argument("--style", required=True)
    p_advise.add_argument("--context", default="")
    p_advise.add_argument("--json", action="store_true")

    for name in ("rewrite", "qa", "critique", "loop"):
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
    p_grade.add_argument("--full", action="store_true", help="Run full multi-wave grader report")
    p_grade.add_argument("--waves", type=int, default=1, help="Number of grader waves")
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
        if args.command == "critique":
            result = critique(args.style, args.level, read_text(args))
            emit(result, args.json)
            return 0 if result["ok"] else 2
        if args.command == "loop":
            result = loop(args.style, args.level, read_text(args), args.max_iter)
            emit(result, args.json)
            return 0 if result["ok"] else 2
        if args.command == "grade":
            result = grade(args.full, args.waves)
            emit(result, args.json)
            return 0 if result["overall"] == 100 else 2
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
