"""Copy only the accepted text-file inventory into a new plain folder."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_public import scan, tree_files

ROOT = Path(__file__).resolve().parents[1]


def stage(source: Path, destination: Path, *, checkout: bool = False) -> None:
    if destination.exists() or destination.is_symlink():
        raise ValueError("staging destination must be new")
    src, dst = source.resolve(), destination.resolve()
    if src == dst or src in dst.parents or dst in src.parents:
        raise ValueError("staging destination must be separate from the source")
    files, issues = tree_files(source, checkout=checkout)
    if issues:
        raise ValueError("source file inventory is not approved")
    destination.mkdir(parents=True)
    for rel, path in files.items():
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(path.read_bytes())
    if scan(destination):
        raise ValueError("staged tree blocked by the public-content gate")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        stage(ROOT, args.destination, checkout=True)
    except (ValueError, OSError):
        raise SystemExit("staging blocked; no upload performed") from None
    print("Approved text files staged, without history; no upload performed.")


if __name__ == "__main__":
    main()
