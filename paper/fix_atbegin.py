r"""\AtBeginDocument is LaTeX's, not ours.

The undefined-macro check knows the generated macros are CamelCase names
from make_tables.py, so it treats every CamelCase command it cannot find a
definition for as a missing number.  The lineno block added one LaTeX
command of that shape, and the check said what it is built to say:

    [macros] \AtBeginDocument is used and nothing defines it

True about this file, false about the document -- which is the failure mode
the comment on LATEX_CAPS already describes.  The list grows by one.

Run:  python fix_atbegin.py <paper dir>
"""
import io
import os
import sys

os.chdir(sys.argv[1])
N = 0


def rep(path, a, b, label, marker=None):
    global N
    assert a not in b or marker, f"{label}: b contains a; pass a marker"
    s = io.open(path, encoding="utf-8").read()
    if marker is not None:
        if marker in s:
            print(f"  (already) {label}")
            return
    elif s.count(a) == 0 and s.count(b) >= 1:
        print(f"  (already) {label}")
        return
    assert s.count(a) == 1, f"{label}: {s.count(a)} in {path}"
    io.open(path, "w", encoding="utf-8").write(s.replace(a, b))
    print(f"  {label}")
    N += 1


rep("check_paper.py",
    '''    "DeclareUrlCommand",
}''',
    '''    "DeclareUrlCommand",
    # The lineno block in the preamble; \\AtBeginDocument is the only
    # CamelCase command it uses, since the patch macros it defines are
    # lowercase and are caught by the local-definition half of the check.
    "AtBeginDocument",
}''',
    "the list of commands that are LaTeX's and not ours")

print(f"done: {N} edits")
