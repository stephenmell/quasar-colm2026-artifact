"""Heuristic recovery of AbstractOther set sizes from a stringified result.

Set-semantics programs sometimes lose the abstraction by interpolating an
AbstractOther into a string (`"...{}".format(x)` / f-strings route through
__format__/__str__, which are not overridden, so the dataclass repr leaks). By the
time the result is written to conformal_exec/<tau>/<task>.json it is a plain string
with `AbstractOther(_possibilities=frozenset({...}))` spliced into it.

We only need to know whether the set size exceeds 1, so parse it back out.

Why not just "find the next '}'": two real cases in the dataset break that.
  * elements may be double-quoted when they contain an apostrophe:
        {"I couldn't find any email...", "..."}
  * an AbstractOther repr can be nested INSIDE an element, so the first '}' seen
    belongs to the inner set:
        frozenset({"...", "code is: AbstractOther(_possibilities=frozenset({'', '463820'}))"})
    Naive comma counting reports 3 there; the true outer size is 2.
So the scan is quote-, escape- and brace-depth-aware, and we prefer
ast.literal_eval over counting whenever the payload parses.
"""
import ast

MARK = "AbstractOther(_possibilities=frozenset("


def _match_brace(s, i):
    """s[i] must be '{'. Return the index just past its matching '}', or None."""
    depth = 0
    quote = None
    while i < len(s):
        c = s[i]
        if quote is not None:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c in "{[(":
            depth += 1
        elif c in "}])":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return None


def _count_top_level_commas(inner):
    """Fallback when the payload will not literal_eval: commas outside quotes/brackets."""
    n = 0
    depth = 0
    quote = None
    i = 0
    while i < len(inner):
        c = inner[i]
        if quote is not None:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c in "{[(":
            depth += 1
        elif c in "}])":
            depth -= 1
        elif c == "," and depth == 0:
            n += 1
        i += 1
    return n


def set_sizes(s):
    """Sizes of every AbstractOther set found, in document order.

    Nested occurrences are reported as separate entries rather than multiplied out,
    so [2, 2] means an outer set of 2 with an inner set of 2 somewhere inside it.
    An empty `frozenset()` yields 0.
    """
    if not isinstance(s, str):
        return []
    out = []
    i = 0
    while True:
        j = s.find(MARK, i)
        if j < 0:
            return out
        k = j + len(MARK)
        if s.startswith(")", k):          # frozenset() -- empty
            out.append(0)
            i = k
            continue
        if not s.startswith("{", k):      # unrecognised shape; skip it
            i = k
            continue
        end = _match_brace(s, k)
        if end is None:                   # truncated repr; best effort
            out.append(_count_top_level_commas(s[k + 1:]) + 1)
            return out
        inner = s[k:end]                  # includes the braces
        try:
            out.append(len(ast.literal_eval(inner)))
        except Exception:
            out.append(_count_top_level_commas(inner[1:-1]) + 1)
        i = k + 1                         # +1 so nested sets are found too
    return out


def is_uncertain(s):
    """True if any recovered AbstractOther set holds more than one possibility."""
    return any(n > 1 for n in set_sizes(s))


def has_leak(s):
    """True if an AbstractOther repr is present at all (any size)."""
    return isinstance(s, str) and MARK in s


def _span(s, j):
    """Given the index j where MARK starts, return (end_exclusive, elements).

    end_exclusive points just past the closing '))' of AbstractOther(...).
    Returns None if the repr cannot be parsed.
    """
    k = j + len(MARK)
    if s.startswith(")", k):                 # frozenset() -- empty
        return k + 2, []
    if not s.startswith("{", k):
        return None
    e = _match_brace(s, k)
    if e is None or not s.startswith("))", e):
        return None
    try:
        return e + 2, list(ast.literal_eval(s[k:e]))
    except Exception:
        return None


def recover_possibilities(s, limit=1024):
    """Reconstruct the concrete strings the program would have produced.

    Each AbstractOther repr is replaced by each of its elements, recursively, so the
    result is the Cartesian product over every leaked set (including nested ones).
    A string with no leak comes back unchanged, as a single-element list.

    All observed leaks are sets of strings spliced into a surrounding string, so
    substituting the element text is exactly what `.format()` would have produced
    had the value been concrete.
    """
    if not isinstance(s, str):
        return [s]
    j = s.find(MARK)
    if j < 0:
        return [s]
    span = _span(s, j)
    if span is None:
        return [s]                            # unparseable -- leave it alone
    end, els = span
    if not els:                               # empty set: nothing to substitute
        return [s]
    out = []
    for el in els:
        cand = s[:j] + str(el) + s[end:]
        out.extend(recover_possibilities(cand, limit))
        if len(out) >= limit:
            break
    return out[:limit]


def covers(s, utility):
    """Set coverage: True if ANY recovered possibility satisfies `utility`.

    `utility` takes the candidate string and returns truthy/falsy; exceptions on an
    individual candidate are treated as that candidate not covering.
    """
    for cand in recover_possibilities(s):
        try:
            if utility(cand):
                return True
        except Exception:
            continue
    return False


if __name__ == "__main__":
    CASES = [
        ("no abstraction here", [], False),
        ("x: " + MARK + "{'a', 'b'}))", [2], True),
        ("x: " + MARK + "{'only'}))", [1], False),
        ("x: " + MARK + "))", [0], False),
        # comma inside an element must not be counted
        ("x: " + MARK + "{'a, b, c'}))", [1], False),
        ("x: " + MARK + "{'a, b', 'c'}))", [2], True),
        # double-quoted element containing an apostrophe
        ('x: ' + MARK + '{"couldn\'t find it", "found it"}))', [2], True),
        # escaped quote inside an element
        ("x: " + MARK + "{'she said \\'hi\\'', 'b'}))", [2], True),
        # newline escapes
        ("x: " + MARK + "{'a\\nb', 'c'}))", [2], True),
        # two separate sets in one string
        ("p " + MARK + "{'a','b'})) q " + MARK + "{'c','d','e'}))", [2, 3], True),
        # the real nested case: outer 2, inner 2
        (MARK + '{"I couldn\'t find any email.", "code is: ' + MARK
         + "{'', '463820'}))\"}))", [2, 2], True),
        # outer size 1 but nested set of 2 -- must still be flagged
        (MARK + '{"code is: ' + MARK + "{'', '463820'}))\"}))", [1, 2], True),
    ]
    bad = 0
    for s, want_sizes, want_unc in CASES:
        got, unc = set_sizes(s), is_uncertain(s)
        ok = got == want_sizes and unc == want_unc
        bad += not ok
        print(f"  {'ok ' if ok else 'FAIL'} sizes={got!s:<10} uncertain={unc!s:<6} {s[:58]!r}")
    print(f"\n{len(CASES)-bad}/{len(CASES)} size self-tests passed\n")

    REC = [
        ("plain string", ["plain string"]),
        ("x: " + MARK + "{'a', 'b'}))", ["x: a", "x: b"]),
        ("x: " + MARK + "{'only'})) end", ["x: only end"]),
        # two independent sets -> cartesian product
        ("p " + MARK + "{'a','b'})) q " + MARK + "{'c','d'})) r",
         ["p a q c r", "p a q d r", "p b q c r", "p b q d r"]),
        # nested: outer 2, one element carrying an inner set of 2 -> 3 concretes
        (MARK + '{"no code found.", "code is: ' + MARK + "{'', '463820'}))\"}))",
         ["no code found.", "code is: ", "code is: 463820"]),
        # empty set stays as-is (nothing to substitute)
        ("x: " + MARK + "))", ["x: " + MARK + "))"]),
    ]
    bad2 = 0
    for s, want in REC:
        got = sorted(recover_possibilities(s))
        ok = got == sorted(want)
        bad2 += not ok
        print(f"  {'ok ' if ok else 'FAIL'} {len(got)} candidate(s) from {s[:46]!r}")
        if not ok:
            print(f"       got  {got}\n       want {sorted(want)}")
    print(f"\n{len(REC)-bad2}/{len(REC)} recovery self-tests passed")
