# Phase 3: Skills — ✅ Done

**Goal**: A `get_skills` tool that serves Markdown methodology guides, with every fact that the
code already knows (schema, category line items, worked-example numbers) filled in from the
code at read time, so the guides cannot drift from the app.

Branch: `feat/mcp-skills`. Depends on Phase 2 (`build_server`, `models.py`, `mcp_client`).

## Scope

- In scope: the skills loader and renderer, five skill files, the `get_skills` tool, new
  server `instructions`, a backend copy of `worked-examples.json`, drift tests, CLAUDE.md.
- Out of scope: new formulas or changes to `formulas.ts`; MCP resources or prompts (tools
  only, see phase-0 Out of Scope); Vercel bundling (Phase 4 verifies it).

## Implementation

### 1. Skill file format

Location: `backend/app/mcp_server/skills/<name>.md`. The file stem is the skill name
(`[a-z0-9-]+`). Under `backend/app/` so the Vercel bundle includes it (`scripts/**` is excluded).

```markdown
---
name: net-transfers
description: How the app computes daily TGA deposits, withdrawals and net transfers, with SQL.
formulas: [total-deposits, total-withdrawals, net-transfers, leading-flow]
---

# Net transfers
...
```

Frontmatter is three keys: `name` (must equal the file stem), `description` (one line, at
most 160 characters), `formulas` (list of `FormulaId`s from `formulas.ts`; may be `[]`).
Parse it by hand: the first line must be `---`, read until the next `---`, split each line on the
first `: `, and parse `formulas` as a bracketed comma list. Do **not** add a YAML dependency for
three keys.

### 2. Placeholders

The body may contain these tokens. Anything else matching `{{...}}` raises `SkillError`.

| Token | Renders to | Source |
|---|---|---|
| `{{schema}}` | One `### <table>` section per table: a Markdown table of `column`, `type` | `SELECT table_name, column_name, data_type FROM information_schema.columns WHERE table_schema = 'main' ORDER BY table_name, ordinal_position`, run with `run_select` on a fresh cursor (`max_rows=query_max_rows`) |
| `{{categories}}` | One `### <name>` section per `CATEGORY_REGISTRY` entry: its `kind` and a bullet list of `components` | `app.constants.categories.CATEGORY_REGISTRY` |
| `{{example:<dotted.path>}}` | The value at that path in the worked examples, numbers formatted with thousands separators (`f"{v:,}"`) | `backend/app/mcp_server/worked-examples.json` |

`{{example:net_transfers.outputs.fytd.net_transfers}}` → `108,932`. A path that doesn't
resolve, or resolves to a dict or list, raises `SkillError`.

Rendering happens on every `get_skills(name)` call (cheap: one small query, a dict walk), so
`{{schema}}` always matches the artifact being served.

### 3. `backend/app/mcp_server/worked-examples.json` (new)

A byte-for-byte copy of `frontend/src/features/methodology/worked-examples.json`. The Vercel
`api` service bundles only `backend/`, so the skills cannot read the frontend file in
production. `test_worked_examples_copy_matches_frontend` (below) fails the moment the two
differ, and its failure message gives the fix:
`cp frontend/src/features/methodology/worked-examples.json backend/app/mcp_server/worked-examples.json`.

### 4. `backend/app/mcp_server/skills.py` (new)

```python
SKILLS_DIR = Path(__file__).parent / "skills"
EXAMPLES_PATH = Path(__file__).parent / "worked-examples.json"

class SkillError(ValueError):
    """A skill file is malformed, or a placeholder does not resolve."""

@dataclass(frozen=True)
class SkillFile:
    name: str
    description: str
    formulas: tuple[str, ...]
    body: str               # raw, placeholders unrendered

def load_skills() -> dict[str, SkillFile]   # @functools.cache; sorted by name
def render(body: str, cur: duckdb.DuckDBPyConnection) -> str
```

`load_skills` raises `SkillError` naming the file for: missing or unclosed frontmatter, a
missing key, `name` ≠ stem, an empty description or one over 160 characters.

### 5. `backend/app/mcp_server/models.py`

Add:

```python
class SkillSummary(BaseModel):
    name: str
    description: str

class Skill(SkillSummary):
    formulas: list[str]
    body: str
```

### 6. `backend/app/mcp_server/server.py`

- Register:
  `def get_skills(name: str | None = None) -> list[SkillSummary] | Skill`, read-only like the
  rest. No name → summaries for every skill. With a name → render on a fresh cursor in a worker
  thread (`anyio.to_thread.run_sync`, same as `run_query`, so make the tool `async`). Unknown name
  → `ToolError(f"No skill {name!r}. Available: {', '.join(names)}.")`. `SkillError` and
  `QueryRejected` → `ToolError`.
- Replace `INSTRUCTIONS` with:

  > U.S. Treasury Daily Treasury Statement data (public domain), refreshed once per business
  > day. Amounts are millions of U.S. dollars. The fiscal year starts October 1. Start with
  > get_skills("start-here"): it says which tool to use for which question. Read the matching
  > skill before computing a figure yourself, so your numbers match the app's.

### 7. The five skills

Write each body from the source named. Copy formula wording from the `expression` and
`pitfalls` fields of `formulas.ts` for the listed ids. Do not invent definitions. Every SQL
example goes in a fenced ` ```sql ` block and must run on the seeded test DB (tested).

| File | `formulas` | Body must cover | Source |
|---|---|---|---|
| `start-here.md` | `[today-mtd-fytd, fiscal-year]` | The five tools and when to use each (API first for anything the app shows; `run_query` for custom cuts); units (millions, floats); fiscal year from Oct 1; that data is one row per Treasury line per business day; the row and byte limits and what to do when hit; a list of the other four skills | `phase-0-setup.md` Tool Contracts + Limits, CLAUDE.md |
| `data-model.md` | `[day-of-fiscal-year]` | What each table is (one line each, from `ENDPOINTS[...].display_name`), the `metadata` table keys, `daily_net_transfers` being derived at ingestion, the `day_of_fiscal_year = DENSE_RANK() OVER (ORDER BY record_date)` rule within a fiscal year of `deposits_withdrawals`, then `{{schema}}`. One SQL example: rows per fiscal year in `deposits_withdrawals` | `app/constants/endpoints.py`, `app/core/schema.py`, `app/ingest/populate.py` |
| `net-transfers.md` | `[total-deposits, total-withdrawals, net-transfers, leading-flow]` | The formula, the four Treasury lines it uses, its sign convention, the worked example rendered from `{{example:net_transfers.*}}` (inputs and outputs for `today` and `fytd`), SQL that computes it for one date from `deposits_withdrawals`, and the note that `daily_net_transfers` and `call_api("net_transfers_get_for_date")` already hold it | `formulas.ts`, `app/utils/deposits_withdrawals.py:16` |
| `year-over-year.md` | `[yoy-difference, yoy-percent, yoy-summary, comparison-modes, weekly-comparison]` | Aligning dates by `day_of_fiscal_year` (not calendar date), `percent = difference ÷ \|previous\| × 100` and why `\|previous\|`, the `{{example:yoy.*}}` and `{{example:yoy_negative_base.*}}` numbers, comparison modes, Friday-aligned weekly comparison, which `call_api` operations return these | `formulas.ts`, `app/utils/yoy.py:255`, `app/services/weekly.py` |
| `categories.md` | `[major-spending, major-receipts, tbill-interest, irs-refunds, category-comparison]` | That a major category is a sum of FYTD amounts over a fixed list of Treasury lines, then `{{categories}}`, the Medicare worked example from `{{example:categories.medicare.*}}`, SQL summing one category for one date, and which `call_api` operations return them | `app/constants/categories.py`, `app/services/categories.py` |

### 8. `backend/tests/test_mcp_skills.py` (new)

| Test | Expect |
|---|---|
| `test_skill_names` | `set(load_skills()) == {"start-here", "data-model", "net-transfers", "year-over-year", "categories"}` |
| `test_frontmatter_formulas_exist` | every id in every skill's `formulas` appears in `formulas.ts` as `id: '<id>'` (read the file at `parents[2] / "frontend/src/features/methodology/formulas.ts"`, like `test_formula_examples.py:31`) |
| `test_worked_examples_copy_matches_frontend` | the backend copy's bytes equal the frontend file's; message gives the `cp` command |
| `test_every_skill_renders` (parametrize over names; uses `client` fixture for the seeded DB) | `render(...)` returns a string with no `{{` left |
| `test_schema_placeholder_lists_tables` | the rendered `data-model` contains `### deposits_withdrawals`, `### daily_net_transfers`, `### metadata` |
| `test_categories_placeholder` | the rendered `categories` contains `### Medicare` and `HHS - Medicare Prescription Drugs` |
| `test_example_placeholder` | `render("{{example:net_transfers.outputs.fytd.net_transfers}}", cur) == "108,932"` |
| `test_unknown_placeholder` (parametrize `{{nope}}`, `{{example:no.such.path}}`, `{{example:net_transfers}}`) | `SkillError` |
| `test_skill_sql_runs` (parametrize over every ` ```sql ` block in every skill, id = `"<skill>-<n>"`) | `run_select(cur, block)` returns without raising |
| `test_bad_frontmatter` | write a skill file with `name` ≠ stem into a `tmp_path`, monkeypatch `SKILLS_DIR`, call `load_skills.cache_clear()`, then `load_skills()` → `SkillError` naming the file |
| `test_get_skills_tool` (async, `mcp_client`) | no name → 5 summaries; `"net-transfers"` → `body` contains `108,932`; `"nope"` → `ToolError` listing names |

Update `test_tool_names` in `test_mcp_tools.py` to include `"get_skills"`.

### 9. `CLAUDE.md`

In the Frontend architecture bullet that starts "Formula copy lives in", change the end to:
"…checks against the real formula code. `backend/app/mcp_server/worked-examples.json` is a
copy the MCP skills read (`test_mcp_skills.py` enforces it). Change a formula and all three
must be updated in the same commit."

## Verification

- [x] `cd backend && uv run pytest tests/test_mcp_skills.py tests/test_mcp_tools.py -x` — all pass.
- [x] `cd backend && uv run pytest` — full suite passes.
- [x] `cd backend && uv run ruff check . && uv run ruff format --check .` — clean.
- [x] `git diff --exit-code docs/contracts/openapi.json` — no change.
- [x] Drift check by hand: change one number in the frontend `worked-examples.json`, run
      `uv run pytest tests/test_mcp_skills.py` — `test_worked_examples_copy_matches_frontend`
      fails (and `test_formula_examples.py` too). Revert.
- [ ] In Claude Code: ask "how does this app compute net transfers, and what was it FYTD on the
      latest day?" The agent calls `get_skills("start-here")`, then `get_skills("net-transfers")`,
      then `call_api` or `run_query`, and its explanation matches the Methodology page.

## Notes

- A skill explains *how to get a number with these tools*. The Methodology page explains *what
  the number means* to a person. Overlap is expected; the formulas come from the same
  `formulas.ts` entries.
- **Found while writing `net-transfers.md`.** The two TGA total rows exist only from
  2022-04-18; before that `calculate_daily_net_transfers` sums the day's TGA rows, and up to
  2021-09-30 statements use `account_type = 'Federal Reserve Account'`. The skill's SQL is
  marked as valid from 2022-04-18 and points to `daily_net_transfers` for earlier dates.
- `data-model.md` writes the day-number rule as
  `DENSE_RANK() OVER (PARTITION BY record_fiscal_year ORDER BY record_date)`, the same rule as
  CLAUDE.md's "within the fiscal year" wording, in a form that runs.
- `run_select` is called for `{{schema}}`, so the placeholder goes through the same lockdown
  and limits as agent SQL; `get_skills` maps `DataUnavailable` like `run_query` does.
- Verified on landing:
  - Every skill SQL block, run on the real artifact, reproduces the worked examples:
    - Medicare FYTD 81,533.
    - Net transfers −16,755 today and 108,932 FYTD on 2026-10-19.
    - YoY day 12 is 108,932 vs 94,000: a difference of 14,932, or 15.89 %.
  - The hand drift check failed `test_worked_examples_copy_matches_frontend` and two
    `test_formula_examples.py` tests, then was reverted.
  - 33 skill and tool tests; full suite 183 passed.
  - The Claude Code conversation check is left for the owner.
