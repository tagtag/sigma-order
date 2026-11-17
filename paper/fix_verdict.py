r"""A build diagnostic that describes a draft the paper no longer is.

ceiling_resolution.py prints this on every build:

    WRONG SIGN. ... it is the opposite of what Section 5.4 claims.

Section 5.4 does not claim it.  It says "Nothing measured here shows the
room above an authored arrangement closing, and we withdraw the claim that
it is."  The verdict was written while the claim was still in the text and
was never revisited after the claim came out, so every build since has
printed an accusation about a sentence that is gone.

This matters for one reason only, and it is the reason the last three
defects survived: a message that is wrong in a way nobody acts on is how a
reader learns to skip that part of the output.  51 LaTeX errors sat under
a line that scrolled past every run.  A standing WRONG SIGN would train
the same blindness, and the next thing it said would go unread too.

So the three branches say what each means for the text as it now stands:

  FALLS      the measurement and the withdrawal agree -- expected, and
             the line to watch is whether it stops saying FALLS
  AT FLOOR   the move is unresolved; the withdrawal stands on weaker
             grounds but stands
  RISES      the data no longer support the withdrawal, and Section 5.4
             has to be reopened -- the loud case, and the only one

The arithmetic is untouched.  Only the words a human reads change, and
which of them is the alarm.

Run:  python fix_verdict.py <paper dir>
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


rep("ceiling_resolution.py",
    '''    if units < 0:
        print(f"WRONG SIGN.  On the set Eq. (8) is defined on the ceiling "
              f"fraction\\nFALLS by {abs(units):.1f} of its own steps across "
              f"the ladder.  That is not a\\nquestion of resolution -- the "
              f"move is resolved -- it is the opposite of\\nwhat Section 5.4 "
              f"claims.  The saturation argument cannot be made from\\nthis "
              f"statistic on this set.")
    elif units < 2:
        print("AT ITS OWN FLOOR.  The ceiling fraction moves by fewer than "
              "two of\\nits own smallest steps, which is the condition "
              "Section 5.3 refuses to\\nread as a size.  Section 5.4 cannot "
              "offer this as evidence either, and\\nthe saturation claim has "
              "no statistic left that is clear of its grid.")
    else:
        print(f"CLEAR OF ITS FLOOR by {units:.1f} steps.  The fraction is a "
              f"proportion over\\n{nmin} texts, so the 1/n! grid of "
              f"Section 5.3 does not reach it and\\nSection 5.4 may rest "
              f"on it.")''',
    '''    # Each branch says what it means for the text AS IT NOW STANDS.  The
    # first version of this verdict was written while Section 5.4 still
    # claimed saturation, and went on calling the measurement "the
    # opposite of what Section 5.4 claims" for weeks after the claim was
    # withdrawn -- an alarm about a sentence that no longer existed.  A
    # standing false alarm is how the 51 LaTeX errors on the next line
    # went unread, so the alarm is moved to the one case that is news.
    if units < 0:
        print(f"FALLS by {abs(units):.1f} of its own steps across the "
              f"ladder: resolved, and in\\nthe opposite direction to "
              f"saturation.  Section 5.4 withdraws the\\nsaturation claim, "
              f"and this is the measurement it withdraws on.  Expected;\\n"
              f"what would be news is this line not saying FALLS.")
    elif units < 2:
        print("AT ITS OWN FLOOR.  The ceiling fraction moves by fewer than "
              "two of\\nits own smallest steps, which is the condition "
              "Section 5.3 refuses to\\nread as a size.  The withdrawal in "
              "Section 5.4 still holds, on weaker\\ngrounds: not a "
              "measurement pointing the other way, just no measurement.")
    else:
        print(f"RISES, CLEAR OF ITS FLOOR, by {units:.1f} steps.  The "
              f"fraction is a proportion\\nover {nmin} texts, so the 1/n! "
              f"grid of Section 5.3 does not reach it.\\n\\n"
              f"** This is the one that needs acting on.  Section 5.4 "
              f"withdraws the\\n** saturation claim on the grounds that "
              f"this fraction does not rise.\\n** On these numbers it "
              f"does, and the withdrawal has to be reopened.")''',
    "1: the alarm moves to the case that is news",
    marker="what would be news is this line not saying FALLS")

print(f"done: {N} edits")
