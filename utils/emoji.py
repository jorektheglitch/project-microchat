from dataclasses import dataclass, field
from enum import StrEnum
import logging
from pathlib import Path


class EmojiStatus(StrEnum):
    component = "component"
    fully_qualified = "fully-qualified"
    minimally_qualified = "minimally-qualified"
    unqualified = "unqualified"


@dataclass
class Emoji:
    raw: str
    description: str
    note: str | None = None
    status: EmojiStatus = field(kw_only=True)
    version: str = field(kw_only=True)

    def __hash__(self) -> int:
        return hash(self.raw)


PREAMBLE = """
from dataclasses import dataclass
from typing import Self


@dataclass(frozen=True)
class Emoji(str):
    raw: str
    description: str
    note: str | None = None

    def __new__(cls: type[Self], raw: str, description: str, note: str | None = None) -> Self:
        return super().__new__(cls, raw)
""".strip()


class EmojiSet:
    def __init__(self, default: Emoji):
        pass


def main(testdata: Path, output: Path) -> None:
    emojis = parse_testdata(testdata)
    emojis.sort(key=lambda emoji: emoji.description)
    qualified_emojis = [emoji for emoji in emojis if emoji.status == EmojiStatus.fully_qualified]
    emoji_by_description: dict[str, Emoji] = {}
    emoji_variance: dict[str, dict[str, Emoji]] = {}

    for emoji in qualified_emojis:
        emoji_by_description.setdefault(emoji.description, emoji)
        if not emoji.note:
            emoji_variance[emoji] = {}

    for emoji in qualified_emojis:
        if emoji.note:
            variants = emoji_variance.setdefault(emoji.description, {})
            if emoji.note in variants:
                logging.warning("Duplicated emoji variant: '%s' emoji already have '%s' variant",
                                emoji.description, emoji.note,
                                )
            variants[emoji.note] = emoji

    emoji_variance = {emoji: variants for emoji, variants in emoji_variance.items() if variants}


def parse_testdata(testdata: Path) -> list[Emoji]:
    emojis = []
    with testdata.open(encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                continue
            emoji = parse_testdata_line(line)
            emojis.append(emoji)
    return emojis


def parse_testdata_line(line: str) -> Emoji:
    """
    code points; status # emoji name
    """
    code_points, _, tail = line.lstrip().partition(";")
    status_raw, _, tail = tail.lstrip().partition("#")
    emoji_raw, _, raw_description = tail.lstrip().partition(" ")
    version_raw, _, raw_description = raw_description.lstrip().partition(" ")
    description_raw, _, note = raw_description.lstrip().partition(":")

    code_points = code_points.strip()
    status = EmojiStatus(status_raw.strip())
    version = version_raw.strip()
    description = description_raw.strip()
    note = note.strip() or None

    if description == "flag":
        description = f"{note or ''} flag".strip()
        note = None
    elif description.startswith("man ") or description.startswith("woman "):
        pass

    emoji = Emoji(emoji_raw, status=status, version=version, description=description, note=note)

    return emoji


if __name__ == "__main__":
    from argparse import ArgumentParser, Namespace

    logging.basicConfig()

    class Arguments(Namespace):
        testdata: Path
        output: Path

    parser = ArgumentParser()
    args = parser.parse_args(namespace=Arguments())

    args.testdata = Path(__file__).parent / "emoji-test.txt"
    args.output = Path(__file__).parent / "tmp-out.py"
    main(testdata=args.testdata, output=args.output)
