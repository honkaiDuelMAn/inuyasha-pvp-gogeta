"""Extend the verified move catalog with Gogeta without changing old values."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHARED = {
    "guard",
    "energyUp",
    "moveLeft",
    "moveRight",
    "moveUp",
    "moveDown",
    "perfectGuard",
    "heal",
    "kikyosRevenge",
    "doubleRight",
    "doubleLeft",
    "summonShippo",
}


def extend_catalog(base: list[dict[str, object]], config: dict[str, object]) -> list[dict[str, object]]:
    result = json.loads(json.dumps(base))
    by_id = {move["id"]: move for move in result}
    for identifier in SHARED:
        move = by_id.get(identifier)
        if move is None:
            raise ValueError(f"baseline move missing: {identifier}")
        characters = move["characters"]
        if "go" not in characters:
            characters.append("go")

    for source in config["moves"]:
        identifier = source["id"]
        if identifier in by_id:
            raise ValueError(f"Gogeta move already exists: {identifier}")
        result.append({
            "id": identifier,
            "name": source["name"],
            "characters": ["go"],
            "advanced": False,
            "energy": source["energy"],
            "damage": source["damage"],
            "area": source["area"],
        })
    return result


def build() -> list[dict[str, object]]:
    base = json.loads((ROOT / "server" / "catalog.json").read_text(encoding="utf8"))
    # Rebuilding an already-extended checkout must start from only baseline moves.
    gogeta_ids = {
        move["id"]
        for move in json.loads((ROOT / "source" / "gogeta" / "moves.json").read_text(encoding="utf8"))["moves"]
    }
    base = [move for move in base if move["id"] not in gogeta_ids]
    for move in base:
        move["characters"] = [character for character in move["characters"] if character != "go"]
    config = json.loads((ROOT / "source" / "gogeta" / "moves.json").read_text(encoding="utf8"))
    return extend_catalog(base, config)


def write() -> None:
    catalog = build()
    encoded = json.dumps(catalog, ensure_ascii=False, indent=2) + "\n"
    (ROOT / "server" / "catalog.json").write_text(encoded, encoding="utf8", newline="\n")
    (ROOT / "public" / "net" / "catalog.mjs").write_text(
        "export const catalog = " + encoded.rstrip() + ";\n",
        encoding="utf8",
        newline="\n",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    write()
    print("Extended catalogs with Gogeta")


if __name__ == "__main__":
    main()
