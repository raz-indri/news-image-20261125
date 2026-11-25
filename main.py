#!/usr/bin/env python3
"""Entry point for make.fun news-image-20261125 (program/v1, stdlib only).

Copies the pre-rendered front page news.png (which sits beside this file
in the repository) to $MAKEFUN_OUTPUT_DIR/entry.png. The image is fully
deterministic: the same repository always produces the same bytes.
"""

import hashlib
import os
import shutil
import sys


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, "news.png")
    if not os.path.isfile(source):
        print("missing news.png beside main.py", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    target = os.path.join(out_dir, "entry.png")
    os.makedirs(out_dir, exist_ok=True)
    shutil.copyfile(source, target)
    size = os.path.getsize(target)
    if size != os.path.getsize(source):
        print("copy size mismatch", file=sys.stderr)
        return 1
    digest = hashlib.sha256(open(target, "rb").read()).hexdigest()
    print("Wrote %s (%d bytes, sha256 %s) from news.png"
          % (target, size, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
