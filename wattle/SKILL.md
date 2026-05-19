---
name: wattle
description: Use when the user wants tactical writing help with defensive corporate communication, HR/lawyer-lite wording, legalese, assertive negotiation, client persuasion, tone selection, recursive rewriting, or QAQC of a draft against a chosen tone. Triggers on phrases like "use Wattle", "/wattle", "defensive lite", "HR/lawyer lite", "legalese", "attack level", "persuade this client", "make this safer", "corporate email defense", or "rewrite this tactically".
---

# Wattle

Wattle is a tactical writing toolbox for agents. It helps select a style, rewrite a draft, then QAQC the result before calling the writing task complete.

## Quick Use

1. Identify the writing family:
   - `defensive`: protect the sender in corporate, HR, vendor, or stakeholder records.
   - `offense`: assertive negotiation and escalation. No threats, deception, harassment, or coercion.
   - `persuasion`: client-facing influence, alignment, and conversion.
2. If the user did not specify a level, ask for the level and recommend one:
   - `python3 scripts/wattle.py advise --style defensive --context "<context>"`
   - `python3 scripts/wattle.py list`
3. Rewrite the draft in small passes. Preserve facts, dates, names, quoted text, legal claims, numbers, and commitments.
4. Run QAQC before final output:
   - `python3 scripts/wattle.py qa --style defensive --level hr_lawyer_lite --text "<draft>"`
5. If the score is below 90, run another small rewrite pass or use:
   - `python3 scripts/wattle.py loop --style defensive --level hr_lawyer_lite --input draft.txt`
6. For scoring details, read `references/rubric.md` only when grading or auditing Wattle itself.

## Slash Aliases

Treat these as activation phrases:
- `/wattle defensive lite`
- `/wattle defensive hr_lawyer_lite`
- `/wattle defensive legalese`
- `/wattle offense attack_1`
- `/wattle offense attack_2`
- `/wattle offense attack_3`
- `/wattle persuasion consultative`
- `/wattle persuasion executive`
- `/wattle persuasion urgency`

## Style Levels

### Defensive

- `lite`: calm, clear, non-accusatory, boundary-setting.
- `hr_lawyer_lite`: documented, precise, record-aware, asks for written confirmation.
- `legalese`: formal reservation of rights, no admissions, narrow requests, clear paper trail.

### Offense

This family means assertive negotiation, not abuse.

- `attack_1`: firm ask, clear consequence, cooperative tone.
- `attack_2`: sharper leverage, deadlines, decision framing.
- `attack_3`: executive escalation posture, final opportunity framing, still lawful and professional.

Reject or redirect requests for threats, deception, harassment, blackmail, doxxing, extortion, impersonation, or fabricated evidence.

### Persuasion

- `consultative`: diagnose problem, build trust, recommend next step.
- `executive`: business value, risk, timing, decision clarity.
- `urgency`: ethical urgency, opportunity cost, deadline, no false scarcity.

## Salix-Style Loop

Borrow the Salix method: measure, edit, remeasure, stop.

```
for iteration in 1..4:
    qa = scripts/wattle.py qa STYLE LEVEL TARGET
    if qa.score >= 90 and qa.ok:
        stop
    edit only the highest-value gaps
    preserve facts, commitments, citations, numbers, URLs, and quoted text
```

Stop when:
- score is 90 or higher;
- safety flags remain unresolved;
- the user needs to choose a risk level;
- two passes do not improve the score.

## Output Rules

- Give the user the rewritten text first.
- Then give a short rationale: style, level, risk posture, QA score.
- Do not claim legal advice. Use "legalese" as a tone, not as counsel.
- For HR or legal exposure, recommend review by qualified counsel when stakes are high.

## Local CLI

The bundled script is stdlib-only:

```
python3 scripts/wattle.py list
python3 scripts/wattle.py advise --style defensive --context "manager retaliation email"
python3 scripts/wattle.py rewrite --style persuasion --level executive --text "..."
python3 scripts/wattle.py qa --style offense --level attack_2 --text "..."
python3 scripts/wattle.py loop --style defensive --level hr_lawyer_lite --input draft.txt --max-iter 4
python3 scripts/wattle.py grade
```
