import csv, io, re
from dataclasses import dataclass

ALLOWED_BASIS = {"official", "derived", "estimated", "unknown", "demo"}

@dataclass
class ParsedCard:
    card_number: str | None
    subject: str
    team_franchise: str | None = None
    subset: str = "Base"
    parallel: str | None = None
    serial_numbered_to: int | None = None
    is_rookie: bool = False
    is_autograph: bool = False
    is_memorabilia: bool = False
    is_case_hit: bool = False


def parse_checklist_csv(text: str) -> list[ParsedCard]:
    reader = csv.DictReader(io.StringIO(text))
    out = []
    for row in reader:
        subject = (row.get("subject") or row.get("player") or row.get("name") or "").strip()
        if not subject:
            continue
        serial = row.get("serial_numbered_to") or row.get("numbered_to") or ""
        try: serial = int(serial) if serial else None
        except ValueError: serial = None
        flags = " ".join(str(v or "") for v in row.values()).lower()
        out.append(ParsedCard(
            card_number=(row.get("card_number") or row.get("number") or "").strip() or None,
            subject=subject,
            team_franchise=(row.get("team_franchise") or row.get("team") or "").strip() or None,
            subset=(row.get("subset") or "Base").strip(),
            parallel=(row.get("parallel") or "").strip() or None,
            serial_numbered_to=serial,
            is_rookie=str(row.get("is_rookie") or "").lower() in {"1","true","yes","rc"} or " rookie" in flags,
            is_autograph=str(row.get("is_autograph") or "").lower() in {"1","true","yes"} or "auto" in flags,
            is_memorabilia=str(row.get("is_memorabilia") or "").lower() in {"1","true","yes"} or any(x in flags for x in ["relic","patch","memorabilia"]),
            is_case_hit=str(row.get("is_case_hit") or "").lower() in {"1","true","yes"} or "case hit" in flags,
        ))
    return out


def odds_to_box_probability(*, packs_per_box: int | None, one_in_packs: float | None = None, hits_per_box: float | None = None) -> float | None:
    if hits_per_box is not None:
        if hits_per_box < 0: return None
        return min(1.0, hits_per_box) if hits_per_box <= 1 else 1.0
    if one_in_packs and packs_per_box and one_in_packs > 0 and packs_per_box > 0:
        p_pack = 1.0 / one_in_packs
        return round(1 - (1 - p_pack) ** packs_per_box, 6)
    return None


def classify_outcome(card) -> str:
    if card.is_case_hit or card.serial_numbered_to and card.serial_numbered_to <= 25:
        return "jackpot"
    if card.is_autograph or card.serial_numbered_to and card.serial_numbered_to <= 99:
        return "big_hit"
    if card.parallel or card.is_memorabilia or card.is_rookie:
        return "good_hit"
    return "common"
