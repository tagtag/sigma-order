#!/usr/bin/env python3
"""What the sentence splitter does, including where it is wrong.

`split_into_blocks` ends a block at any token whose decoded text, right-
stripped, ends with '.', '!' or '?'.  That rule is the whole of the sentence
segmentation this paper's within-text test rests on, and it had no test of any
kind: whether it produced the right blocks was visible only as a block count
in the output JSON, which nobody read.

The rule is wrong in three identifiable ways, pinned below.  They did not fire
on the corpora measured here -- every text split into exactly four blocks and
none was dropped, which `make_tables.py` now checks and refuses to package
without -- but a different corpus would hit all three, and the failure would
be silent: more blocks than sentences simply makes the permutation set larger,
and fewer makes it smaller.

    python3 -I block_split_selftest.py

No tokenizer, no weights, instant.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from aoar_core import split_into_blocks  # noqa: E402


def decode_identity(tok):
    """Stand-in for a tokenizer's single-token decode: the token is its text."""
    return tok


def blocks_of(tokens):
    return ["".join(b) for b in split_into_blocks(tokens, decode_identity)]


def check(name, tokens, expected, note=""):
    got = blocks_of(tokens)
    ok = got == expected
    print(f"  [{'ok ' if ok else 'FAIL'}] {name}")
    if note:
        print(f"         {note}")
    if not ok:
        print(f"         expected {expected}")
        print(f"         got      {got}")
    return ok


def main():
    ok = True

    print("1. the rule works on ordinary prose")
    ok &= check("two sentences",
                ["The", " cat", " sat", ".", " It", " slept", "."],
                ["The cat sat.", " It slept."])
    ok &= check("question and exclamation",
                ["Why", "?", " Because", "!"],
                ["Why?", " Because!"])
    ok &= check("trailing text with no terminal mark",
                ["A", " sentence", ".", " another", " one"],
                ["A sentence.", " another one"],
                "the remainder is kept as a final block rather than dropped")
    ok &= check("terminal mark with trailing space",
                ["Done", ". ", "Next", "."],
                ["Done. ", "Next."],
                "rstrip() is why the space does not defeat the match")

    print()
    print("2. where the rule is wrong, pinned so a change is visible")
    ok &= check("abbreviation splits a sentence in two",
                ["Dr", ".", " Smith", " arrived", ".", " He", " left", "."],
                ["Dr.", " Smith arrived.", " He left."],
                "WRONG: two sentences, three blocks")
    ok &= check("a decimal point splits a sentence",
                ["The", " value", " was", " 3", ".", "5", " units", ".",
                 " Then", " it", " fell", "."],
                ["The value was 3.", "5 units.", " Then it fell."],
                "WRONG: two sentences, three blocks")
    ok &= check("a closing quotation mark hides the stop",
                ["She", " said", " “stop", ".”", " Then", " she",
                 " left", "."],
                ["She said “stop.” Then she left."],
                "WRONG: two sentences, one block")

    print()
    print("3. the consequence for the permutation set")
    # n! grows fast, so a mis-split changes the test's size, not just its
    # labels: five blocks where there are four means 120 orders, which
    # block_order_pll.py then samples instead of enumerating.
    five = ["Dr", ".", " A", ".", " B", ".", " C", ".", " D", "."]
    n = len(blocks_of(five))
    print(f"  one abbreviation in a four-sentence passage gives {n} blocks "
          f"({'exact' if n <= 4 else 'sampled'} enumeration)")
    ok &= (n == 5)

    print()
    if ok:
        print("block split selftest: OK -- behaviour is as documented, "
              "including the three known failures")
        return 0
    print("block split selftest: FAILED -- the splitter no longer behaves "
          "as documented")
    return 1


if __name__ == "__main__":
    sys.exit(main())
