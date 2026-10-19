# Google Python Style Guide — full reference

Distilled-but-complete capture of every **Decision** plus the load-bearing examples,
organized by the original section numbers so you can look up a rule fast. For how this
repo *adapts* these rules, see the parent `SKILL.md` — when the two disagree, `SKILL.md`
wins (it reflects the actual codebase + ruff config).

> In this repo, ruff enforces §3.1–3.7, §3.13, §3.14 (formatting/imports-sorting)
> automatically. You rarely need to read those sections; run `ruff format` + `ruff check`.

---

## 2. Language rules

### 2.1 Lint
Run the linter (here: `ruff check`). Suppress an inappropriate warning narrowly with a
line-level comment (`# noqa: <CODE>` for ruff; `# pylint: disable=symbolic-name` in
pylint projects) and explain non-obvious suppressions. Unused args: delete them at the
top of the function with a `# Unused.` comment, or prefix `unused_`/use `_`.

### 2.2 Imports
Google rule: `import x` for packages/modules; `from x import y` where `y` is a *module*.
Use `from x import y as z` when two `y`s collide, `y` shadows a local/API name, or `y` is
inconveniently long/generic. `import y as z` only for standard abbreviations (`import
numpy as np`). **No relative imports** — always the full package path.
*Exemptions:* `typing`, `collections.abc`, `typing_extensions` symbols may be imported
directly. **(This repo extends that exemption to FastAPI/SQLModel/model/schema symbols —
see SKILL.md.)**

### 2.3 Packages
Import each module by its full path (`from doctor.who import jodie`), never assume the
binary's directory is on `sys.path` (`import jodie` is ambiguous).

### 2.4 Exceptions
- Use built-in exception classes where sensible — `ValueError` for a violated
  precondition / API misuse.
- **Do not use `assert` to validate preconditions or for logic** — asserts can be
  stripped. A litmus test: the `assert` could be removed without breaking the code.
  (`pytest` `assert` is the intended exception — that's how tests express expectations.)
- Custom exceptions inherit an existing exception class; names end in `Error`, no
  repetition (`foo.FooError`).
- **Never** bare `except:` / `except Exception:` unless you re-raise or you're a
  deliberate isolation point that records-and-suppresses (e.g. a thread's outermost
  block). Bare except also swallows typos, `sys.exit()`, `Ctrl+C`, test failures.
- Minimize the `try` body. Use `finally` for cleanup.

```python
def connect_to_next_port(self, minimum: int) -> int:
    if minimum < 1024:
        raise ValueError(f'Min. port must be at least 1024, not {minimum}.')
    port = self._find_next_open_port(minimum)
    if port is None:
        raise ConnectionError(f'Could not connect on port {minimum} or higher.')
    return port
```

### 2.5 Mutable global state
Avoid it. If unavoidable, declare at module level / class attribute, make it internal
(`_name`), expose only through public functions, and document *why* in a comment.
Module-level **constants** are encouraged: `_MAX_HOLY_HANDGRENADE_COUNT = 3`,
`SIR_LANCELOTS_FAVORITE_COLOR = "blue"` (CAPS_WITH_UNDER).

### 2.6 Nested / local / inner classes and functions
Fine when closing over a local value other than `self`/`cls` (e.g. decorators). Otherwise
prefer a module-level `_private` function — nested defs can't be tested directly and make
the enclosing function longer.

### 2.7 Comprehensions & generator expressions
OK for simple cases. **No multiple `for` clauses and no multiple filter expressions.**
Optimize for readability. Allowed: `[f(v) for v in iterable if cond]`. Not allowed:
`[(x, y) for x in range(10) for y in range(5) if x*y > 10]` — write nested loops instead.

### 2.8 Default iterators and operators
Use them: `for k in adict:`, `for k, v in adict.items():`, `if obj in alist:`,
`for line in afile:`. Not `.keys()` / `.readlines()`. Don't mutate a container while
iterating it.

### 2.9 Generators
Fine. Use `Yields:` (not `Returns:`) in the docstring. Force cleanup of expensive
resources — wrapping the generator in a context manager (PEP 533) is a good way.

### 2.10 Lambdas
OK for one-liners. If it spans multiple lines or exceeds ~60–80 chars, use a named nested
function. Prefer `operator.mul` over `lambda x, y: x * y`. Prefer generator expressions
over `map()`/`filter()` with a lambda.

### 2.11 Conditional expressions
OK for simple cases; each of the true-expr / if-expr / else-expr must fit on one line.
Use a full `if` statement when it gets complicated.

### 2.12 Default argument values
OK — but **never a mutable object as a default** (it's evaluated once at import and
shared/modified across calls). Use `None` and build inside, or an immutable default:
```python
def foo(a, b: Sequence | None = None):
    if b is None:
        b = []
def foo(a, b: Sequence = ()):   # empty tuple OK — immutable
    ...
```
Also avoid defaults evaluated at import that you didn't mean (`b=time.time()`,
`b=FLAGS.value`).

### 2.13 Properties
Use `@property` only when the get/set involves trivial, cheap, unsurprising computation,
or to make an attribute read-only / lazy. A property that just reads/writes an internal
attribute isn't allowed — **make the attribute public instead**. Don't use a property for
computations a subclass might want to override.

### 2.14 True/False evaluations
Prefer implicit falsiness — `if not users:`, not `if len(users) == 0:`. Caveats:
- Always `if x is None:` / `is not None` to test for `None` (a real value may be falsy).
- Never `== False`; use `if not x:` (chain `if not x and x is not None:` to distinguish
  `False` from `None`).
- Empty sequences are falsy — `if seq:` / `if not seq:`.
- For integers, comparing against `0` explicitly (`if i % 10 == 0:`) avoids confusing
  `None` with `0`.
- Numpy arrays raise in a boolean context — use `.size`.
- Note `'0'` (string) is truthy.

### 2.16 Lexical scoping
OK to use. A nested function reads (but can't rebind) enclosing-scope names. Watch the
late-binding gotcha: a name assigned anywhere in a function is local throughout it.

### 2.17 Decorators
Use judiciously when there's a clear win (e.g. `@property`). Follow import/naming rules;
a decorator's docstring should say it's a decorator; unit-test it. Avoid external
dependencies inside the decorator (it runs at import time). **Never `@staticmethod`**
unless an external API forces it — write a module-level function instead. Use
`@classmethod` only for named constructors or class-specific routines touching process
state.

### 2.18 Threading
Don't rely on the atomicity of built-in types. Use `queue.Queue` to pass data between
threads; otherwise `threading` primitives, preferring `threading.Condition`.

### 2.19 Power features
Avoid metaclasses, bytecode access, on-the-fly compilation, dynamic inheritance, import
hacks, reflection (`getattr` tricks), custom `__del__`, etc. Std-lib that uses them
internally (`abc.ABCMeta`, `dataclasses`, `enum`) is fine to use.

### 2.20 `from __future__ import`
Encouraged to enable modern syntax per-file. Keep these imports until you're sure the
code only runs on a new-enough interpreter.

### 2.21 Type-annotated code
Strongly encouraged. Annotate public APIs at minimum; annotate error-prone or hard-to-
understand code. Type-check at build time (here: `ty`). See §3.19 for mechanics.

---

## 3. Style rules (most enforced by ruff here)

### 3.1 Semicolons
None. Never two statements on one line.

### 3.2 Line length
Google: **80**. **This repo: 88 (ruff default).** Exceptions (both): long imports, URLs/
paths in comments, long no-whitespace string constants, `# noqa`/pylint pragmas. **No
backslash continuation** — use implicit joining inside `()`/`[]`/`{}`. Break at the
highest syntactic level; if breaking twice, break at the same level both times.

### 3.3 Parentheses
Sparingly. Don't parenthesize `return`/conditions unless for line-continuation or to mark
a tuple. `onesie = (foo,)` for a 1-tuple. `return foo` / `return spam, beans`.

### 3.4 Indentation
4 spaces, never tabs. Align wrapped elements with the opening delimiter, or use a 4-space
hanging indent (nothing on the first line). Closing bracket either ends the line or aligns
with the opening line's indent.

### 3.4.1 Trailing commas
Add a trailing comma in a sequence only when the closing bracket is on its own line (it
also tells the formatter to put one item per line); and for 1-element tuples.

### 3.5 Blank lines
Two blank lines between top-level defs; one between methods and after a class docstring;
none right after a `def` line.

### 3.6 Whitespace
No space inside `()[]{}`; none before `,;:` (space after, except line-end); none before
the `(`/`[` of a call/index/slice. Surround `=`, comparisons, and booleans with single
spaces. **No spaces around `=` for kwargs/defaults — unless** a type annotation is present
(`imag: float = 0.0`). Don't vertically align tokens across lines.

### 3.7 Shebang
Only the program's main executable file needs `#!/usr/bin/env python3`.

### 3.8 Comments and docstrings
Triple-double-quote `"""` always. Summary line ≤ 80 chars ending in `.`/`?`/`!`, then a
blank line, then the rest at the same indent as the opening quote.

**3.8.2 Modules** — start with a docstring describing contents/usage (+ license
boilerplate where the project requires it). Test modules don't need one unless there's
something unusual to explain.

**3.8.3 Functions/methods** — docstring mandatory if public, nontrivial, or non-obvious.
Give enough to call the function without reading its body. Descriptive (`"""Fetches
rows."""`) or imperative (`"""Fetch rows."""`) but consistent within a file. Sections:
- `Args:` — each param: description (include type if not annotated); hanging indent for
  long descriptions; list `*foo`/`**bar` as such.
- `Returns:` / `Yields:` — semantics + any type info the annotation lacks. Omit if it
  returns `None`, or if the summary already starts "Returns/Yields ...". Document a tuple
  return as `A tuple (a, b), where a is ...`.
- `Raises:` — exceptions relevant to the interface. Don't document exceptions raised when
  the API contract itself is violated.

```python
def fetch_smalltable_rows(
    table_handle: smalltable.Table,
    keys: Sequence[bytes | str],
    require_all_keys: bool = False,
) -> Mapping[bytes, tuple[str, ...]]:
    """Fetches rows from a Smalltable.

    Retrieves rows pertaining to the given keys from the Table instance
    represented by table_handle.

    Args:
        table_handle: An open smalltable.Table instance.
        keys: A sequence of strings representing the key of each table row
          to fetch.  String keys will be UTF-8 encoded.
        require_all_keys: If True, only rows with values set for all keys are
          returned.

    Returns:
        A dict mapping keys to the corresponding table row data fetched.

    Raises:
        IOError: An error occurred accessing the smalltable.
    """
```

**3.8.3.1 Overridden methods** — decorate with `@override`; no docstring needed unless
behavior materially refines the base contract.

**3.8.4 Classes** — docstring below the `class` line; document public attributes in an
`Attributes:` section (same format as `Args:`). Summary describes what an *instance*
represents; for an `Exception` subclass, what the error *is* (`"""No more cheese is
available."""`), not when it's raised. Don't say "Class that..." / "Raised when...".

**3.8.5 Block/inline comments** — comment tricky code before the block; inline comments
start ≥2 spaces from code, `# ` then text. Explain *why*, never narrate *what* the code
obviously does.

**3.8.6** — proper capitalization, spelling, punctuation; complete sentences read best.

### 3.10 Strings
Use f-strings, `%`, or `.format` — even for all-string params. A single `+` join is OK;
don't *format* with `+`. **Never accumulate a string with `+`/`+=` in a loop** — append
to a list and `''.join(...)`, or use `io.StringIO` (avoids quadratic time). Be consistent
with `'` vs `"` in a file (**this repo: `"`**); use the other quote to avoid escaping.
`"""` for multi-line; use `textwrap.dedent` or concatenated literals to avoid embedded
indentation.

**3.10.1 Logging** — pass a literal pattern string + args, not an f-string:
`logging.info('Current $PAGER is: %s', os.getenv('PAGER', ''))`.

**3.10.2 Error messages** — match the actual condition precisely; make interpolated
pieces identifiable (`f'Not a probability: {p=}'`); keep them greppable; don't assume a
cause you didn't verify.

### 3.11 Files, sockets, stateful resources
Explicitly close them — prefer `with`. Use `contextlib.closing()` for non-`with` objects.
Don't rely on `__del__`/GC for cleanup with observable side effects.

### 3.12 TODO comments
`# TODO: <link/bug> - explanation`. Prefer a tracked bug over a username. Old style
`# TODO(handle): ...` is discouraged for new code.

### 3.13 Imports formatting
One import per line (typing/`collections.abc` may group symbols). At the top, after the
module docstring, before globals. Group: `__future__` → stdlib → third-party → first-party
sub-packages; sort lexicographically (case-insensitive) within a group. **Ruff (`I`) does
this for you.**

### 3.14 Statements
One statement per line. You may put a test result on the same line only for a single
`if` with no `else` (`if foo: bar(foo)`); never for `try`/`except`.

### 3.15 Getters and setters
Use accessor/mutator functions only when get/set does meaningful, non-trivial work (state
invalidated/rebuilt, significant cost). A pair that just reads/writes an attribute → make
the attribute public. Name them `get_foo()` / `set_foo()`. Don't re-bind new getters to an
old property — let stale access break visibly.

### 3.16 Naming
`module_name`, `package_name`, `ClassName`, `ExceptionName`, `function_name`,
`GLOBAL_CONSTANT_NAME`, `global_var_name`, `instance_var_name`,
`function_parameter_name`, `local_var_name`. Descriptive; avoid letter-deleting
abbreviations.
- **Avoid:** single-char names (except `i/j/k`, `e` in except, `f` for a file handle,
  unconstrained `_T`/`_P` TypeVars, established math notation); dashes in module names;
  `__dunder__` names; offensive terms; type-in-name (`names_dict`).
- **Internal** = one leading `_`. Double leading `__` triggers name-mangling — discouraged
  (hurts readability/testability). Files: `lower_with_under.py`, never dashes.
- Conventions table — Public / Internal: Modules `lower_with_under` / `_lower_with_under`;
  Classes & Exceptions `CapWords` / `_CapWords`; Functions `lower_with_under()` /
  `_lower_with_under()`; Constants `CAPS_WITH_UNDER` / `_CAPS_WITH_UNDER`; Vars & instance
  vars `lower_with_under` / `_lower_with_under`.

### 3.17 Main
Put runnable logic in `main()`; guard with `if __name__ == '__main__':`. Top-level code
runs on import — keep side effects out of it.

### 3.18 Function length
Prefer small, focused functions. No hard limit, but past ~40 lines consider splitting.

### 3.19 Type annotations
- **3.19.1** Annotate public APIs; balance safety vs flexibility. Don't annotate
  `self`/`cls` (use `Self` only when needed) or `__init__`'s `-> None`. Use `Any` when a
  type genuinely can't be expressed.
- **3.19.2** Line-break between variables, not between a name and its type. One param per
  line when long; align the closing `)` with `def`.
- **3.19.3** Forward refs: `from __future__ import annotations` or quote the name.
- **3.19.4** Spaces around `=` only when a param has both annotation and default
  (`a: int = 0`).
- **3.19.5 NoneType** — if an arg can be `None`, declare it. Prefer explicit `X | None`
  over `Optional`/`Union`; never implicit `a: str = None`.
- **3.19.6** Type aliases are `CapWords` (`_Private` if module-local); `: TypeAlias` in
  3.10+.
- **3.19.7** Ignore a line with `# type: ignore` (or tool-specific pragma).
- **3.19.8** Annotate a hard-to-infer variable inline (`a: Foo = f()`); don't add new
  `# type:` comments.
- **3.19.9** `list[int]` (single type); `tuple[int, ...]` (repeat) or `tuple[int, str]`
  (fixed).
- **3.19.10** TypeVars/ParamSpec for generics; descriptive names unless internal &
  unconstrained (`_T`, `_P` OK; `AddableType` for constrained). `AnyStr` for matched
  str/bytes.
- **3.19.11** `str` for text, `bytes` for binary; no `typing.Text` in new code.
- **3.19.12** Import typing/`collections.abc` symbols directly (grouping allowed). Prefer
  abstract containers (`Sequence`) in signatures over concrete (`list`); prefer built-in
  `tuple`/`list` over `typing.Tuple`/`List`.
- **3.19.13** Conditional imports only when a type-only import must be avoided at runtime
  (`if TYPE_CHECKING:`, quote the names). Discouraged — prefer refactoring.
- **3.19.14** Typing-induced circular deps are a smell; break with an `Any` alias if you
  must.
- **3.19.15** Always parameterize generics (`Mapping[int, str]`, not bare `Mapping`); make
  `Any` explicit when that's truly the type (but a TypeVar is often better).

---

## 4. Parting words
**BE CONSISTENT.** Match the local style of the file you're editing; local consistency
trumps global preference on choices the global guide leaves open. But don't cite
consistency to keep an old style when the codebase is clearly moving to a better one.
