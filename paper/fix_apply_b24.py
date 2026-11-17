#!/usr/bin/env python3
"""Batch 24: Appendix A, first half -- #208 #209 #210 #211 #212 #213 #217
#218 #219 #221 #226(a).

  #208  The heading's "when the answer is fixed by construction" does not
        say what answer.  It is whether the conditionals are compatible.
  #209  "the answer differs between the two model classes because only one
        of them has a choice" -- name the classes and say what the choice
        is over.
  #210  The cycle affinity is used two sentences before it is defined.
  #211  An addition the author asked for: the physical reading of the
        asymmetry, in one sentence.  (The first draft had the Metropolis
        comparison the wrong way round -- Metropolis avoids the local
        normalisation by working with ratios -- and it is written here in
        the correct direction.)
  #212  "the largest value of the sweep exceeds the smallest by
        ToySpanRatio" -- of what, and how it stands to the ToyCapRatio
        given just before.
  #213  "It is the reason the text results in this paper rest on within-text
        ranks" -- what "it" is.
  #217  Appendix A's "masked model" and "autoregressive model" are not the
        evaluators of the main text.  They are small models trained on this
        toy system, and the words name architecture classes.
  #218  Section 3.2 is where the two classes' difference is established,
        but it is a section about the main-text evaluators.  The
        autoregressive half carries over as mathematics; the masked half's
        direct certificate is for modern masked LMs and does not, which is
        why this appendix measures it.
  #219  Nothing says what the two toy models are.  They are one backbone
        with two attention masks and two training objectives.
  #221  The values in the two paragraphs that follow never say which route
        built them.
  #226(a) "such a floor" -- the thing that cancels between arrangements is
        an additive part common to them, not a lower bound.

Idempotent.  Run from the directory holding main.tex.

    python3 -I fix_apply_b24.py [--dry-run]
"""

import argparse
import os
import sys

EDITS = [
    # ---- #208 -------------------------------------------------------------
    ("main.tex",
     "\\section{What a masked evaluator reports when the answer is fixed by\nconstruction}",
     "\\section{What a masked evaluator reports on a system where compatibility\n"
     "is known by construction}",
     "208 heading"),

    # ---- #209 + #211 -------------------------------------------------------
    ("main.tex",
     "Equation~\\eqref{eq:glauber} is not complete until one says where\n"
     "$p_\\theta(\\cdot \\mid x_{-k})$ is obtained, and the answer differs between the\n"
     "two model classes because only one of them has a choice.  A masked model\n"
     "emits this conditional directly, in one forward pass: it is what the training\n"
     "objective asks of it, and what sampling from it uses.  An autoregressive\n"
     "model emits no such thing --- no position of it attends to both sides --- so\n"
     "for that class the conditional has to be recovered from the joint, by scoring\n"
     "the $V$ complete sequences that differ at site $k$ alone and normalising.\n"
     "Table~\\ref{tab:capacity} uses the emitted conditionals for its masked rows\n"
     "and recovered ones for its autoregressive row.  The asymmetry is forced, and\n"
     "it leaves a question the table cannot answer on its own: does a non-zero\n"
     "reading belong to the masked model, or to the route by which its rates were\n"
     "built?",
     "Equation~\\eqref{eq:glauber} is not complete until one says where\n"
     "$p_\\theta(\\cdot \\mid x_{-k})$ is obtained, and the answer differs between a\n"
     "masked model and an autoregressive one, because only the masked one has more\n"
     "than one route to it.  A masked model emits this conditional directly, in one\n"
     "forward pass: it is what the training objective asks of it, and what sampling\n"
     "from it uses.  An autoregressive model emits no such thing --- no position of\n"
     "it attends to both sides --- so for that class the conditional has to be\n"
     "recovered from the joint, by scoring the $V$ complete sequences that differ\n"
     "at site $k$ alone and normalising.  Table~\\ref{tab:capacity} uses the\n"
     "emitted conditionals for its masked rows and recovered ones for its\n"
     "autoregressive row.  In physical terms the asymmetry reads as follows.  A\n"
     "masked model emits exactly the conditional a heat-bath (Glauber) update calls\n"
     "for, in one forward pass.  An autoregressive model does not, so the\n"
     "conditional has to be assembled by an explicit local normalisation over the\n"
     "$V$ states at site $k$ --- the step a Metropolis rule avoids by working with\n"
     "ratios.  The asymmetry is forced, and it leaves a question the table cannot\n"
     "answer on its own: does a non-zero reading belong to the masked model, or to\n"
     "the route by which its rates were built?",
     "209+211 main:1589"),

    # ---- #210 + #217 + #219 -------------------------------------------------
    ("main.tex",
     "The system is a dense pairwise Markov random field on $L = \\ToyL$ sites with\n"
     "$V = \\ToyV$ symbols, whose $\\ToyStates$ states can be enumerated, trained on\n"
     "$N = \\ToyN$ samples; $\\sigEP$ and the cycle\n"
     "affinities~\\cite{schnakenberg} are then\n"
     "computed from the full transition matrix: the rates are exact and no\n"
     "quantity here is estimated from samples, though the affinities are\n"
     "summarised over a finite chosen set of cycles rather than over all of\n"
     "them.  A cycle affinity $A$ is the log of the product of transition rates\n"
     "around a closed cycle of states divided by the product around the same cycle\n"
     "reversed; all of them vanish exactly when the chain is reversible, so\n"
     "$\\mathrm{rms}|A|$ in Table~\\ref{tab:capacity} is a second, independent reading\n"
     "of the same failure.  Model size is varied through the transformer width $d$.",
     "The system is a dense pairwise Markov random field on $L = \\ToyL$ sites with\n"
     "$V = \\ToyV$ symbols, whose $\\ToyStates$ states can be enumerated, and the\n"
     "models are trained on $N = \\ToyN$ samples drawn from it.  A \\emph{cycle\n"
     "affinity} $A$~\\cite{schnakenberg} is the log of the product of transition\n"
     "rates around a closed cycle of states divided by the product around the same\n"
     "cycle reversed; all of them vanish exactly when the chain is reversible, so\n"
     "$\\mathrm{rms}|A|$ in Table~\\ref{tab:capacity} is a second, independent\n"
     "reading of the same failure.  Both $\\sigEP$ and the affinities are computed\n"
     "from the full transition matrix: the rates are exact and no quantity here is\n"
     "estimated from samples, though the affinities are summarised over a finite\n"
     "chosen set of cycles rather than over all of them.  Model size is varied\n"
     "through the transformer width $d$.\n"
     "\n"
     "The two model classes here are architectures, not the evaluators of the main\n"
     "text: these are small models trained on this toy system\n"
     "(Table~\\ref{tab:capacity}), and nothing below bears on the AR ladder of\n"
     "Section~\\ref{sec:methods}.  They share a backbone --- a three-layer,\n"
     "four-head transformer encoder --- and differ in the attention mask and the\n"
     "training objective.  The masked one leaves attention unrestricted and is\n"
     "trained to predict a single masked site from the other $L-1$; the\n"
     "autoregressive one uses an upper-triangular attention mask and is trained to\n"
     "predict the next site from those before it, with a beginning-of-sequence\n"
     "token prepended.  Width, depth, optimiser and seed are the same for both.\n"
     "Because the two objectives differ, the \\emph{loss} column of\n"
     "Table~\\ref{tab:capacity} is not comparable between the two rows.",
     "210+217+219 main:1603"),

    # ---- #218 (a) + #221 (a) ------------------------------------------------
    ("main.tex",
     "An autoregressive model always defines such a joint,\n"
     "so it returns zero \\emph{whatever its accuracy}: $\\sigEP = \\ToySigmaAR$ with\n"
     "root-mean-square cycle affinity $\\ToyRmsAR$ (Table~\\ref{tab:capacity}).",
     "An autoregressive model always defines such a joint\n"
     "(Section~\\ref{sec:scope}) --- a factorisation determines one, which is a\n"
     "mathematical fact and so carries over to the small model trained here --- so\n"
     "it returns zero \\emph{whatever its accuracy}: $\\sigEP = \\ToySigmaAR$ with\n"
     "root-mean-square cycle affinity $\\ToyRmsAR$ (Table~\\ref{tab:capacity},\n"
     "autoregressive row, whose rates are built by the recovered route, that class\n"
     "having no emitted one).",
     "218a+221a main:1618"),

    # ---- #218 (b) + #221 (b) + #212 + #213 + #226(a) ------------------------
    ("main.tex",
     "Masked conditionals are in general not those of any joint, and the measurement\n"
     "shows the consequence: $\\sigEP$ runs from $\\ToySigmaMin$ to $\\ToySigmaMax$,\n"
     "more than $\\ToyOrdersAbove$ orders of magnitude above the autoregressive value\n"
     "(Figure~\\ref{fig:capacity}), and at the widest model it is not\n"
     "smaller but larger, by a factor of $\\ToyCapRatio$ between $d = \\ToyDMin$\n"
     "and $d = \\ToyDMax$.  The $\\ToyNCap$ widths are not monotone in\n"
     "it (Table~\\ref{tab:capacity}), so the endpoints are what this ratio compares;\n"
     "the largest value of the sweep exceeds the smallest by $\\ToySpanRatio$.  This is a statement\n"
     "about the masked instrument and about nothing else.  It is the reason the text\n"
     "results in this paper rest on within-text ranks, where such a floor cancels between the arrangements of one text, rather than on the magnitude of $\\Delta$.",
     "Masked conditionals need not be those of any one joint\n"
     "(Section~\\ref{sec:scope}).  The certificate cited there is for modern masked\n"
     "language models and does not carry over to a model of this size, so whether\n"
     "it holds here is a measurement, and this is it: $\\sigEP$ runs from\n"
     "$\\ToySigmaMin$ to $\\ToySigmaMax$, more than $\\ToyOrdersAbove$ orders of\n"
     "magnitude above the autoregressive value (Figure~\\ref{fig:capacity};\n"
     "Table~\\ref{tab:capacity}, masked rows, whose rates are built from the\n"
     "conditionals the model emits).  At $d = \\ToyDMax$ it is not smaller than at\n"
     "$d = \\ToyDMin$ but larger, by a factor of $\\ToyCapRatio$.\n"
     "The $\\ToyNCap$ widths are not monotone in it\n"
     "(Table~\\ref{tab:capacity}), so that factor compares the two endpoints and\n"
     "not the whole sweep: across all $\\ToyNCap$ widths the largest $\\sigEP$\n"
     "exceeds the smallest by $\\ToySpanRatio$.  This is a statement\n"
     "about the masked instrument and about nothing else.  What it shows is that\n"
     "the part of a reading that comes from the instrument rather than from the\n"
     "text can be large, and that is why the text results in this paper rest on\n"
     "within-text ranks rather than on the magnitude of $\\Delta$: a part common to\n"
     "every arrangement of one text cancels when the arrangements are ranked\n"
     "against each other.",
     "212+213+218b+221b+226a main:1624",
     "batch 30 (length)"),
]

FILES = sorted({e[0] for e in EDITS})


def apply_edits(root, dry_run=False):
    cache = {}
    for name in FILES:
        with open(os.path.join(root, name), encoding="utf-8") as fh:
            cache[name] = fh.read()
    made = skipped = passed = 0
    for edit in EDITS:
        name, old, new, label = edit[:4]
        later = edit[4] if len(edit) > 4 else None
        text = cache[name]
        # Which test means "already applied" depends on how the two
        # strings nest.  If old is a substring of new (an insertion), old
        # survives the edit, so only the presence of new can decide; if new
        # is a substring of old (a deletion), new is there before the edit,
        # so old has to be looked for first.
        done = (new in text) if old in new else (old not in text and new in text)
        if done:
            print(f"  skip  {label:<30} already applied")
            skipped += 1
            continue
        n = text.count(old)
        if n != 1:
            if later and old not in text:
                # A later batch rewrote this passage, so on a re-run neither
                # the old text nor this batch's own replacement is here.
                print(f"  pass  {label:<30} superseded by {later}")
                passed += 1
                continue
            print(f"  MISS  {label:<30} target occurs {n} times in {name}")
            return None
        cache[name] = text.replace(old, new, 1)
        print(f"  apply {label:<30} {name}")
        made += 1
    if not dry_run:
        for name, text in cache.items():
            with open(os.path.join(root, name), "w", encoding="utf-8") as fh:
                fh.write(text)
    return made, skipped, passed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    print("batch 24: Appendix A, first half")
    print("-" * 60)
    result = apply_edits(args.root, args.dry_run)
    if result is None:
        print("-" * 60)
        print("FAIL  nothing written.")
        return 1
    made, skipped, passed = result
    print("-" * 60)
    print(f"{'DRY RUN  ' if args.dry_run else ''}{made} applied, "
          f"{skipped} already in place"
          + (f", {passed} superseded later." if passed else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
