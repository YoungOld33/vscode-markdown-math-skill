# VS Code Markdown Math Skill

A reusable Codex skill for creating, auditing, and repairing math-heavy Markdown so formulas render correctly in VS Code's built-in preview.

## Features

- Standardizes inline math as `$...$` and display math as `$$...$$`.
- Migrates legacy `\\(...\\)` and `\\[...\\]` delimiters.
- Detects unbalanced math delimiters and grouping braces.
- Reports suspicious double escaping, escaped underscores, and table-pipe conflicts.
- Preserves valid LaTeX commands such as `\\times`, `\\neq`, `\\sum`, and `\\operatorname`.
- Skips fenced code blocks and inline code.
- Includes audit-only and safe `--fix` modes.

## Installation

Clone the repository into your personal Codex skills directory:

```powershell
git clone https://github.com/YoungOld33/vscode-markdown-math-skill.git "$env:USERPROFILE\\.codex\\skills\\vscode-markdown-math"
```

Alternatively, download the repository and copy its contents to:

```text
~/.codex/skills/vscode-markdown-math/
```

## Usage with Codex

Invoke the skill explicitly:

```text
Use $vscode-markdown-math to review and fix the math formulas in this Markdown document.
```

Codex may also select the skill automatically when a task involves Markdown formulas, visible LaTeX backslashes, or VS Code math-preview compatibility.

## Standalone checker

Audit one file or an entire directory:

```powershell
python scripts/markdown_math.py path/to/document.md
python scripts/markdown_math.py path/to/docs
```

Apply safe delimiter repairs in place:

```powershell
python scripts/markdown_math.py path/to/docs --fix
```

The fixer changes only legacy formula delimiters outside fenced and inline code. Mathematical notation and meaning remain unchanged.

## Repository structure

```text
SKILL.md
agents/
  openai.yaml
scripts/
  markdown_math.py
```

## Scope

This skill targets Markdown rendered by VS Code. It is not intended for standalone LaTeX projects or PDF typesetting.
