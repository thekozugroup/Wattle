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

Single-file release bundle:

```bash
bash dist/Wattle.skill --install
```

Build the release bundle:

```bash
python3 scripts/build_skill_bundle.py
```

## Copy-Paste Agent Install Prompt

```text
Install Wattle for Codex from the release bundle. Use the local file `dist/Wattle.skill` if present, otherwise download `Wattle.skill` from the latest GitHub release for `thekozugroup/Wattle`. Run `bash dist/Wattle.skill --install` or `bash Wattle.skill --install`. Then verify with `npx skills ls -g -a codex --json` and confirm that `wattle` is installed. If the installer cannot use npx, run `bash Wattle.skill --extract /tmp/wattle-install` and install `/tmp/wattle-install/wattle` with the local skill installer.
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
python3 scripts/build_skill_bundle.py
bash dist/Wattle.skill --extract /tmp/wattle-release-check
```
