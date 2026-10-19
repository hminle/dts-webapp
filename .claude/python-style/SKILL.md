---
name: python-style
description: >
  Python coding conventions for the secolab backend — the Google Python
  Style Guide adapted to this repo (ruff owns formatting + lint; double quotes;
  88-char lines). Use this skill whenever writing, editing, refactoring, modernizing,
  or reviewing any Python in backend/ — FastAPI routers, services, models, schemas,
  scripts, tests, Alembic env. Two jobs: make NEW code follow the house style, and
  bring EXISTING backend code into conformance when asked to "refactor", "clean up",
  "modernize", "make this conform", or "fix the style" of a module. It governs
  imports, naming, type hints, docstrings, exceptions, comprehensions, truthiness,
  and mutable defaults. Apply it even when the user just says "add an endpoint",
  "write a service function", "tidy this up", or pastes a traceback without saying
  "style" — and always finish by running ruff format + ruff check so the diff is clean.
---

# Python style (secolab backend)

The Google Python Style Guide, adapted to this repo. Two principles:

1. **Ruff owns formatting AND mechanical lint.** Layout (line length, quotes,
   whitespace, trailing commas, import sorting) and a big slice of semantics
   (naming `N`, modern syntax `UP`, mutable defaults / `raise from` `B`,
   comprehensions `C4`, relative-import ban `TID`) are enforced by `ruff` —
   configured in `backend/pyproject.toml`. Don't hand-format or re-derive those
   rules; run the tool. Your job is the judgment ruff *can't* check.
2. **Match the surrounding code (Google §4: "BE CONSISTENT").** Where Google's
   examples and this repo disagree, the repo wins — hence double quotes and 88-char,
   not Google's `'` and 80.

Full rule text (by §number) is in
[`references/google-python-style-guide.md`](references/google-python-style-guide.md);
the applied ruff rule set is documented in
[`assets/ruff-google.toml`](assets/ruff-google.toml).

## Always run ruff

From `backend/` (activate conda env `py13` first):

```bash
uv run ruff format . && uv run ruff check .
```

`format` fixes layout; `check` flags lint (add `--fix` for the safe auto-fixes).
Disagree with one line? Suppress narrowly with `# noqa: <CODE>` + a reason — don't
reshape code to dodge the linter.

## What ruff can't judge — spend your attention here

**Imports — the repo's hybrid rule.** Google says "modules only"; we don't, because
FastAPI/SQLModel read better with direct symbols. The split:

- **`app.services.*` → import the module**, call through it (`authz.can(...)`,
  `roles_service.list_roles(...)`). Keeps call sites self-documenting and dodges
  service-to-service circular imports.
  ```python
  from app.services import authz
  from app.services import roles as roles_service
  ```
- **Models, schemas, `typing`, `collections.abc`, third-party → import the name.**
  ```python
  from typing import Annotated
  from fastapi import APIRouter, Depends, status
  from app.models.user import User
  from app.schemas.role import RoleCreate, RoleRead
  ```
- No relative imports (ruff `TID` enforces this; the rule is here so you know *why*:
  full `app.` paths prevent a module being imported twice under two names).

**Type annotations — annotate everything.** This is the house style and the rule a
model most easily forgets on throwaway code: **every function carries a return type**
(including `-> None`), and params are typed. Use `X | None` (never `Optional`/`Union`),
built-in generics (`list[int]`, `dict[str, int]`), and abstract `collections.abc` types
(`Sequence`, `Mapping`, `Container`) in signatures for things you only read/iterate.
Don't annotate `self`/`cls` or `__init__`'s `-> None`. Type-check with `uv run ty check`.

**Docstrings — present where they earn it, Google-shaped.** Triple-double-quoted,
one-line summary ending in a period. Modules that encode non-obvious rules get a real
docstring explaining the *why* (see `app/services/authz.py`). Functions get one when
public, nontrivial, or non-obvious — a thin wrapper can skip it; don't write ceremonial
filler. When documenting params/returns/raises, use Google sections (`Args:`,
`Returns:`/`Yields:`, `Raises:`); reference file §3.8.3 has the exact shape.

**Exceptions.** Raise built-ins for precondition/programming errors (`ValueError` for a
bad argument). `assert` is never validation or control flow — it can be compiled out;
in `pytest` it's the right tool. No bare `except:` / `except Exception:` to swallow —
catch the specific exception(s). Inside `except`, re-raise with `raise ... from exc`
(or `from None` to intentionally drop the chain) — ruff `B904` flags the bare form.
Custom exceptions end in `Error` and inherit a built-in.

**The compact judgment list** (ruff catches some; you own the rest):
- Mutable default args are shared across calls — use `None` + build inside (`B006`).
- Implicit truthiness: `if not seq:` over `if len(seq) == 0:`; but `if x is None:` when
  you mean "was it set?" (0/""/[] are falsy). Never `== None` / `== False`.
- Comprehensions: one `for`, at most one `if` — past that, write the loop.
- Build strings with f-strings/`%`/`.format`; never `+=` a string in a loop —
  append to a list and `"".join(...)`.
- Public attribute over a trivial getter/setter; `@property` only for real (cheap,
  unsurprising) computation. Module **constants** in CAPS are good; mutable module
  globals and "power features" (metaclasses, `__del__`, reflection) are not.

## Refactoring existing backend code

When asked to make an existing module conform ("refactor", "clean up", "modernize"):

1. **Let ruff do the mechanical pass first.** `uv run ruff check <path> --fix` then
   `uv run ruff format <path>` clears naming, modern-syntax, import, and safe-fixable
   lint in one shot. Review what `--fix` changed; for the rest run `ruff check <path>`
   and address them by hand.
2. **Then the judgment pass** — the things ruff can't see: add missing return types
   and param annotations, add/clean docstrings, swap `assert`-for-validation to
   `ValueError`, narrow broad `except`, apply the hybrid import rule, fix `len()==0`
   truthiness. This is where the skill, not the linter, carries the change.
3. **Preserve behavior; keep the diff reviewable.** Don't reformat or rewrite lines
   unrelated to the conformance goal — a refactor PR that also churns 200 untouched
   lines is hard to review. Refactor a module (or a few related ones) at a time, not
   the whole tree at once.
4. **Verify.** Run the affected tests (`uv run pytest tests/test_<area>.py`) and
   `uv run ty check` before declaring done. Conforming style must not change behavior;
   the tests are how you prove it.

## Project conventions (in `backend/CLAUDE.md`, restated where they touch style)

Async path operations; `Annotated[..., Depends(...)]` with reusable `*Dep` aliases; the
deliberate `models/` (DB columns) vs `schemas/` (HTTP contract) split so sensitive
columns never leak; session idiom
`(await session.execute(select(...))).scalar_one_or_none()`; plain `str` (not `EmailStr`)
on email fields on purpose. `alembic/versions/` is autogenerated and lint-excluded —
never hand-edit or reformat it.
