r"""One sentence in Section 3.2, naming what the substitution actually does.

The paragraph already gives the decisive reason -- the quantity so obtained
is not Delta, so comparing it with Delta concludes about neither -- and
says a masked reading of Eq. (1) "would be indexed by a choice".  What it
does not say is the shape of the manoeuvre: Delta exists because an
autoregressive model has no backward process to weigh against, and the
substitution carries it to the one model class that does have one.

An argument, not a measurement, so it does not disturb the withdrawal it
explains.  "backward process" rather than "reverse process", which is the
spelling Section 2.2 uses throughout.

Run:  python fix_substitution.py <paper dir>
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


rep("main.tex",
    r"""between it and $\Delta$ compares two different things and concludes about
neither.  Those measurements are retained in the repository and are not
reported here.""",
    r"""between it and $\Delta$ compares two different things and concludes about
neither.  The substitution also puts a quantity devised to work around the
absence of a backward process on the one model class that has one.  Those
measurements are retained in the repository and are not reported here.""",
    "the manoeuvre is named")

print(f"done: {N} edits")
