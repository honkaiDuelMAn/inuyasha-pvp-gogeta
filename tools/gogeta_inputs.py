"""Pin verified source inputs for the Gogeta build."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_manifest(manga_rpg: Path) -> dict[str, object]:
    baseline = json.loads((ROOT / "tools" / "original-hashes.json").read_text(encoding="utf8"))
    figures = {name: digest for name, digest in baseline.items() if name.endswith("_figure.swf")}
    return {
        "schema": 1,
        "mangaRpg": {
            "fileName": manga_rpg.name,
            "sha256": sha256(manga_rpg),
            "characterId": 5,
        },
        "inuYasha": {
            "baselineCommit": "c2fe0d8082011257ed054230776c5f24a2742f0d",
            "mainSwfSha256": sha256(ROOT / "public" / "game" / "game-original.swf"),
            "figureSha256": figures,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manga-rpg", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "source" / "gogeta" / "input-hashes.json",
    )
    args = parser.parse_args()
    source = args.manga_rpg.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_manifest(source), ensure_ascii=False, indent=2) + "\n",
        encoding="utf8",
    )
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
