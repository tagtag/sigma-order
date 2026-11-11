#!/usr/bin/env python3
"""Does a shipped bundle actually run where it is going?

Twice now a tarball has been sent to a machine, unpacked, and failed on
something that could not fail here: a module that was present in the source
directory but not in the bundle, and a dependency version that the source
machine happened to pin.  Both cost a round trip to the remote machine and
back.

This extracts a bundle into an EMPTY directory -- nothing else on the path,
nothing inherited from the source tree -- and runs every self-test it
contains, with `python3 -I` so the working directory cannot supply an import
the bundle forgot.  A missing dependency shows up here, in seconds, instead
of after a model download on a rented GPU.

    python3 -I bundle_check.py ../sigfb-runpod.tar.gz
    python3 -I bundle_check.py ../sigfb-runpod.tar.gz --expect block_sigma_fb_selftest.py

Exit status is non-zero if anything is missing or any self-test fails, so it
can gate a release.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bundle", help="the .tar.gz to check")
    ap.add_argument("--expect", nargs="*", default=None,
                    help="self-tests that MUST be present (default: every "
                         "*_selftest.py in the bundle, and at least one)")
    ap.add_argument("--keep", action="store_true",
                    help="leave the extraction directory in place")
    args = ap.parse_args()

    if not os.path.exists(args.bundle):
        raise SystemExit(f"no such bundle: {args.bundle}")

    work = tempfile.mkdtemp(prefix="bundlecheck-")
    print(f"# {args.bundle}")
    print(f"# extracting into an empty directory: {work}")
    try:
        with tarfile.open(args.bundle) as t:
            names = t.getnames()
            for n in names:
                p = os.path.normpath(os.path.join(work, n))
                if not p.startswith(os.path.realpath(work) + os.sep) \
                        and p != os.path.realpath(work):
                    raise SystemExit(f"refusing to extract outside: {n}")
            # filter="data" is the 3.14 default and silences the warning;
            # the path check above is kept because it reports the offending
            # member by name instead of raising.
            try:
                t.extractall(work, filter="data")
            except TypeError:                      # Python < 3.11.4
                t.extractall(work)
        print(f"# {len(names)} entries")
        for n in sorted(names):
            print(f"    {n}")

        tests = sorted(os.path.basename(f) for f in
                       glob.glob(os.path.join(work, "*_selftest.py")))
        if args.expect:
            missing = [e for e in args.expect if e not in tests]
            if missing:
                print(f"\nFAIL: expected self-test(s) not in the bundle: "
                      f"{', '.join(missing)}")
                return 1
        if not tests:
            print("\nFAIL: the bundle contains no *_selftest.py, so nothing "
                  "here can verify it")
            return 1

        print(f"\n# running {len(tests)} self-test(s) with -I, so only the "
              f"bundle's own files are importable")
        bad = []
        for t in tests:
            r = subprocess.run([sys.executable, "-I", t], cwd=work,
                               capture_output=True, text=True)
            tail = (r.stdout + r.stderr).strip().splitlines()
            last = tail[-1] if tail else "(no output)"
            print(f"  {'OK  ' if r.returncode == 0 else 'FAIL'}  {t:<32} "
                  f"{last[:70]}")
            if r.returncode != 0:
                bad.append((t, r.stdout, r.stderr))

        # Every .py in the bundle must import on its own, not only the ones
        # with a self-test: an entry point that fails to import is exactly
        # the failure this script exists to catch.
        print("\n# importing every module in the bundle")
        for f in sorted(glob.glob(os.path.join(work, "*.py"))):
            name = os.path.basename(f)[:-3]
            r = subprocess.run(
                [sys.executable, "-I", "-c",
                 f"import sys; sys.path.insert(0, '.'); import {name}"],
                cwd=work, capture_output=True, text=True)
            if r.returncode != 0:
                err = r.stderr.strip().splitlines()
                print(f"  FAIL  {name}.py   {err[-1][:70] if err else ''}")
                bad.append((name + ".py (import)", r.stdout, r.stderr))
            else:
                print(f"  OK    {name}.py")

        if bad:
            print(f"\nFAIL: {len(bad)} problem(s)")
            for name, out, err in bad:
                print(f"\n--- {name} ---")
                print((err or out).strip()[-1500:])
            return 1
        print("\nPASS: the bundle stands on its own")
        return 0
    finally:
        if args.keep:
            print(f"# left in {work}")
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
