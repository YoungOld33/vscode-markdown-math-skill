---
name: vscode-markdown-math
description: Create, review, and repair math-heavy Markdown so formulas render in VS Code's built-in preview. Use for Markdown formula formatting, visible LaTeX backslashes, delimiter migration, or math-syntax audits; do not use for standalone LaTeX or PDF typesetting.
---

# VS Code Markdown Math

Produce Markdown whose mathematics renders predictably in VS Code's built-in preview without changing the author's mathematical meaning.

## Canonical syntax

- Write inline mathematics as `$...$`.
- Put display mathematics between `$$` lines, with a blank line before and after when the surrounding Markdown structure permits it.
- Treat `\(...\)` and `\[...\]` as legacy delimiters to migrate when VS Code compatibility is required.
- Preserve LaTeX commands such as `\times`, `\neq`, `\sum`, `\in`, `\mid`, `\text`, and `\operatorname`. Never solve visible backslashes by deleting backslashes globally.
- Keep subscripts and superscripts unescaped inside mathematics: use `a_{ij}`, not `a\_{ij}`.
- Prefer explicit grouping for font commands: `\mathbb{E}`, `\mathbf{0}`, and `\mathcal{P}`.
- Use semantic symbols when the meaning is clear, such as `A\setminus B` for set difference and `\lvert x\rvert` for absolute value in Markdown tables.

## Workflow

1. Inspect the actual `.md` source. Do not infer file corruption from JSON, chat, or log representations where one source backslash may appear as `\\`.
2. Determine whether the user requested an audit or authorized edits. For an audit, report findings without changing files.
3. Run `python scripts/markdown_math.py <path> [<path> ...]` to audit files or directories. Read the script output before editing.
4. For authorized repairs, run the same command with `--fix`. It converts only legacy formula delimiters outside fenced and inline code.
5. Review reported warnings manually. Do not automatically change mathematical notation, prose, currency dollar signs, code examples, or formulas inside fenced/inline code.
6. Re-run the audit and preview representative inline, display, list, and table formulas in VS Code.

## Repair rules

Apply these deterministic conversions outside code:

| Legacy source | VS Code-compatible source |
|---|---|
| `\(x+y\)` | `$x+y$` |
| a line containing only `\[` | `$$` |
| a line containing only `\]` | `$$` |

Keep indentation on display-delimiter lines so formulas nested in lists remain in the same list item.

Treat the following as review findings rather than unconditional fixes:

- Doubled escapes such as `\\(`, because they may be serialization artifacts or intentional literal text.
- `A-B`, because it may mean subtraction or set difference.
- `$` used as currency or literal text.
- Pipes inside table formulas; replace absolute-value pipes with `\lvert` and `\rvert` only when that meaning is clear.
- Stylistic forms such as `\arg\max`; normalize them only when the user requests notation cleanup.

## Validation requirements

- Opening and closing formula delimiters must balance.
- Grouping braces within formulas must balance, excluding literal `\{` and `\}`.
- No legacy delimiter may remain outside code after a requested migration, unless documented as intentional literal text.
- A successful source audit does not replace visual verification. Confirm that representative formulas render rather than showing raw commands.


