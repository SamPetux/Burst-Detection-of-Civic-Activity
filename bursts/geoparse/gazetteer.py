"""Gazetteer hints for the LLM geoparser: toponyms of the thesis dictionary found in the text."""
from __future__ import annotations

from bursts.thesis_geocoder.district_keywords import DISTRICT_KEYWORDS

NAMES = {"avtozavodsky": "Автозаводский", "kanavinsky": "Канавинский", "leninsky": "Ленинский",
         "moskovsky": "Московский", "nizhegorodsky": "Нижегородский", "priokskiy": "Приокский",
         "sovetsky": "Советский", "sormovsky": "Сормовский"}


def find(text: str) -> list[tuple[str, str]]:
    t = (text or "").lower()
    hits = []
    for d, levels in DISTRICT_KEYWORDS.items():
        for kws in levels.values():
            for kw in kws:
                if kw in t:
                    hits.append((kw.strip(" ,."), d))
    # keep the longest keyword per district to avoid near-duplicates ("ул. бекетова" / "бекетова")
    best: dict[tuple[str, str], str] = {}
    for kw, d in hits:
        if not any(kw in other and kw != other for other, dd in hits if dd == d):
            best[(kw, d)] = kw
    return sorted(best)


def hints_block(text: str) -> str:
    hits = find(text)
    if not hits:
        return ""
    lines = "\n".join(f"- «{kw}» → {d} ({NAMES[d]})" for kw, d in hits[:8])
    return f"\n\nПодсказки справочника:\n{lines}"
