# Wattle

Simple terms: Wattle is an installable Codex skill for tactical writing. It helps an agent pick a style, rewrite in small passes, and QA the result before presenting it.

## Install

From this repository:

```bash
npx skills add ./wattle
```

Optional global Codex install:

```bash
npx skills add ./wattle -g -a codex --copy
```

From GitHub after this repo is pushed:

```bash
npx skills add thekozugroup/Wattle/wattle
```

## Use

```bash
python3 wattle/scripts/wattle.py list
python3 wattle/scripts/wattle.py advise --style defensive --context "HR escalation email"
python3 wattle/scripts/wattle.py critique --style persuasion --level executive --text "Please buy this."
python3 wattle/scripts/wattle.py loop --style defensive --level hr_lawyer_lite --input draft.txt
python3 wattle/scripts/wattle.py grade
python3 wattle/scripts/wattle.py grade --full --waves 15 --json
```

Skill triggers include `$wattle`, `/wattle defensive hr_lawyer_lite`, `defensive lite`, `legalese`, `attack_2`, and client persuasion requests.

## Verify

```bash
python3 -m unittest discover tests
python3 /Users/michaelwong/.codex/skills/.system/skill-creator/scripts/quick_validate.py ./wattle
python3 wattle/scripts/wattle.py grade --full --waves 15 --json
```
