"""DataFrame ↔ Pydantic compatibility helpers.

Pydantic models reject ``pandas.NaT``/``NaN`` as well as raw ``datetime64``
dtypes when they expect strings. The helpers here normalize a DataFrame
into a shape that ``model.parse_obj(df.to_dict(orient="records"))`` can
consume without surprises.
"""

from __future__ import annotations

import pandas as pd

# Columns that carry a wall-clock instant (vs. a calendar date).
_TIMESTAMP_COLUMNS: frozenset[str] = frozenset({"created_at", "updated_at"})


def convert_df_for_pydantic(df: pd.DataFrame) -> pd.DataFrame:
    """Make a DataFrame safe for Pydantic + Starlette JSON encoding.

    Operations:

    * Datetime columns named ``created_at`` / ``updated_at`` are stringified
      with second precision (``%Y-%m-%dT%H:%M:%S``).
    * All other datetime columns are stringified as calendar dates
      (``%Y-%m-%d``) — matches the wire format the API uses for
      ``record_date`` and friends.
    * ``NaN`` / ``NaT`` / pandas ``NA`` are replaced with ``None``. Float
      columns are first cast to ``object`` dtype because pandas otherwise
      coerces ``None`` back to ``NaN``, which then crashes
      ``json.dumps(allow_nan=False)`` in Starlette on multi-table
      responses.

    Args:
        df: source DataFrame (not modified — a copy is returned).

    Returns:
        A new DataFrame with stringified datetimes and ``None``-typed nulls.
    """
    out = df.copy()

    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            fmt = "%Y-%m-%dT%H:%M:%S" if col in _TIMESTAMP_COLUMNS else "%Y-%m-%d"
            out[col] = out[col].dt.strftime(fmt)

    return out.astype(object).where(pd.notna(out), None)
