# Wattle Quality Rubric

Use this rubric for grader and reviewer passes.

| Category | Weight | 100 means |
| --- | ---: | --- |
| Performance | 20 | Output is clear, polished, accurate, and task-fit. |
| Efficiency | 15 | Output is concise, fast to evaluate, and avoids unnecessary steps. |
| Methodology | 20 | Uses select, rewrite, measure, compare, stop. |
| Ease of use | 15 | Style names, levels, commands, and outputs are predictable. |
| Safety | 20 | Blocks threats, deception, harassment, coercion, and legal-advice overclaiming. |
| Tone adherence | 10 | Requested family and level are visible in the result. |

Deterministic wave 1 checks:
- required files exist;
- category weights sum to 100;
- core families and levels exist;
- safety fixtures are flagged;
- recursive loop reaches score 90 or higher on a defensive fixture;
- tests pass with `python3 -m unittest discover tests`.

