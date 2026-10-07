"""Rebuild every Gogeta-specific runtime artifact deterministically."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

try:  # package import used by tests
    from .gogeta_art import GENERATED, build as build_art
    from .gogeta_bridge import (DEFAULT_OUTPUT as BRIDGE_OUTPUT, ORIGINAL_OUTPUT, ORIGINAL_SOURCE, build_bridge)
    from .gogeta_catalog import write as write_catalog
    from .gogeta_figure import DEFAULT_OUTPUT as FIGURE_OUTPUT, build_figure
    from .original_gogeta import DEFAULT_GAME as ORIGINAL_GAME, DEFAULT_LOADER_SOURCE, patch_original_game
except ImportError:  # direct ``python tools/build_gogeta.py`` execution
    from gogeta_art import GENERATED, build as build_art
    from gogeta_bridge import DEFAULT_OUTPUT as BRIDGE_OUTPUT, ORIGINAL_OUTPUT, ORIGINAL_SOURCE, build_bridge
    from gogeta_catalog import write as write_catalog
    from gogeta_figure import DEFAULT_OUTPUT as FIGURE_OUTPUT, build_figure
    from original_gogeta import DEFAULT_GAME as ORIGINAL_GAME, DEFAULT_LOADER_SOURCE, patch_original_game


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_ART = ROOT / "public" / "game" / "gogeta"


def sync_public_art(destination: Path = PUBLIC_ART) -> None:
    """Copy normalized checked-in art to the static runtime tree.

    The destination is replaced instead of merged so removed card IDs cannot
    survive as stale public assets.
    """

    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(GENERATED, destination)


def build(java: Path, ffdec: Path) -> None:
    build_art(GENERATED)
    sync_public_art(PUBLIC_ART)
    build_figure(FIGURE_OUTPUT)
    write_catalog()
    build_bridge(BRIDGE_OUTPUT, java.resolve(), ffdec.resolve())
    build_bridge(ORIGINAL_OUTPUT, java.resolve(), ffdec.resolve(), ORIGINAL_SOURCE)
    patch_original_game(ORIGINAL_GAME, DEFAULT_LOADER_SOURCE, java.resolve(), ffdec.resolve())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--java", type=Path, required=True)
    parser.add_argument("--ffdec", type=Path, required=True)
    args = parser.parse_args()
    build(args.java, args.ffdec)
    print("Built Gogeta art, figure, catalogs, PvP bridge and original-mode bridge")


if __name__ == "__main__":
    main()
