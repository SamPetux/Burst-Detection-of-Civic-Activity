"""Build the IEEE A4 .docx from paper/<lang>/paper_<lang>.md and the IEEE conference template.

The template must first be normalised with LibreOffice (python-docx cannot open the original package):
    soffice --headless --convert-to docx --outdir <dir> conference-template-a4.docx
    python paper/build_docx.py --template <dir>/conference-template-a4.docx --md paper/ru/paper_ru.md --out paper/ru/paper_ru.docx
"""
from __future__ import annotations

import argparse
import copy
import re

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

TEX = [(r"\left", ""), (r"\right", ""), (r"\bigl", ""), (r"\bigr", ""), (r"\Bigl", ""), (r"\Bigr", ""),
       (r"\alpha", "α"), (r"\gamma", "γ"), (r"\Delta", "Δ"), (r"\mu", "μ"), (r"\tau", "τ"), (r"\rho", "ρ"),
       (r"\in", "∈"), (r"\ge", "≥"), (r"\le", "≤"), (r"\approx", "≈"), (r"\sim", "~"), (r"\cdot", "·"),
       (r"\dots", "…"), (r"\ldots", "…"), (r"\infty", "∞"), (r"\varnothing", "∅"),
       (r"\mathcal{D}", "𝒟"), (r"\mathbb{1}", "𝟙"), (r"\mathrm{Poisson}", "Poisson"), (r"\max", "max"),
       (r"\hat q", "q̂"), (r"\,", " "), (r"\;", " "), ("{,}", ","), (r"\%", "%")]


def tex_to_runs(s: str) -> list[tuple[str, str]]:
    """Inline TeX -> [(text, 'n'|'sub'|'sup')]; enough for the formulas used in the paper."""
    for a, b in TEX:
        s = s.replace(a, b)
    s = re.sub(r"\\mathbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\sqrt\{([^}]*)\}", r"√(\1)", s)
    s = re.sub(r"\\(text|mathrm)\{([^}]*)\}", r"\2", s)
    out, i = [], 0
    while i < len(s):
        ch = s[i]
        if ch in "_^" and i + 1 < len(s):
            kind = "sub" if ch == "_" else "sup"
            if s[i + 1] == "{":
                depth, j = 1, i + 2
                while j < len(s) and depth:
                    depth += {"{": 1, "}": -1}.get(s[j], 0); j += 1
                body = s[i + 2:j - 1]
                i = j
            else:
                body, i = s[i + 1], i + 2
            out.append((body.replace("{", "").replace("}", "").replace("^", "").replace("_", ""), kind))
        else:
            out.append((ch.replace("{", "").replace("}", ""), "n")); i += 1
    merged = []
    for t, k in out:
        if merged and merged[-1][1] == k:
            merged[-1] = (merged[-1][0] + t, k)
        else:
            merged.append((t, k))
    return merged


def add_runs(p, text: str, lang: str, size: float | None = None) -> None:
    """Markdown **bold**, *italic* and $math$ into runs of paragraph p."""
    for part in re.split(r"(\$[^$]+\$|\*\*[^*]+\*\*|\*[^*]+\*)", text):
        if not part:
            continue
        if part.startswith("$"):
            pieces, style = tex_to_runs(part[1:-1]), {"italic": False}
        elif part.startswith("**"):
            pieces, style = [(part[2:-2], "n")], {"bold": True}
        elif part.startswith("*"):
            pieces, style = [(part[1:-1], "n")], {"italic": True}
        else:
            pieces, style = [(part, "n")], {}
        for t, k in pieces:
            r = p.add_run(t)
            for key, v in style.items():
                setattr(r, key, v)
            r.font.subscript, r.font.superscript = k == "sub", k == "sup"
            if size:
                r.font.size = Pt(size)
            rpr = r._r.get_or_add_rPr()
            lang_el = OxmlElement("w:lang"); lang_el.set(qn("w:val"), lang); rpr.append(lang_el)


def no_numbering(p) -> None:
    """Captions carry their own label; switch off the template's automatic numbering."""
    ppr = p._p.get_or_add_pPr()
    num = OxmlElement("w:numPr")
    for tag, val in (("w:ilvl", "0"), ("w:numId", "0")):
        e = OxmlElement(tag); e.set(qn("w:val"), val); num.append(e)
    ppr.append(num)


def para_before(anchor, doc, style: str):
    st = {x.name: x for x in doc.styles}[style]
    p = doc.add_paragraph(style=st)
    anchor.addprevious(p._p)
    return p


def build(template: str, md: str, out: str, lang: str, figs: dict[str, tuple[str, str]]) -> None:
    doc = docx.Document(template)
    body = doc.element.body
    els = list(body)
    paras = {id(p._p): p for p in doc.paragraphs}
    text = open(md, encoding="utf-8").read()
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).strip()
    lines = text.splitlines()

    title = next(l[2:] for l in lines if l.startswith("# "))
    p0 = paras[id(els[0])]
    for r in p0.runs[1:]:
        r._r.getparent().remove(r._r)
    p0.runs[0].text = ""
    add_runs(p0, title, lang)
    body.remove(els[1])  # template note about sub-titles

    # authors: first non-empty block after title until blank line
    i = lines.index(next(l for l in lines if l.startswith("# "))) + 1
    while not lines[i].strip():
        i += 1
    auth = []
    while lines[i].strip():
        auth.append(lines[i].strip().rstrip(",")); i += 1
    blocks = [els[4], els[6], els[8]]
    for el in (els[5], els[7], els[9]):
        body.remove(el)
    for el, a in zip(blocks, auth):
        m = re.match(r"(.+?) \((.+)\)$", a)
        name, rest = m.group(1), [x.strip() for x in m.group(2).split(",")]
        org, city, mail = ", ".join(rest[:-3]) or rest[0], ", ".join(rest[-3:-1]), rest[-1]
        p = paras[id(el)]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        for k, line in enumerate([name, org, city, mail]):
            run = p.add_run(line)
            run.font.size = Pt(10)
            run.italic = k == 1
            if k < 3:
                run.add_break()
        if el is not blocks[-1]:
            from docx.enum.text import WD_BREAK
            p.add_run().add_break(WD_BREAK.COLUMN)

    abstract_el, keywords_el, end_sect = els[14], els[15], els[95]
    for el in els[16:95]:
        body.remove(el)

    def fill(el, label, txt):
        p = paras[id(el)]
        for r in list(p.runs):
            r._r.getparent().remove(r._r)
        r = p.add_run(label + "—"); r.bold = True; r.italic = True
        add_runs(p, txt, lang)

    abs_txt = next(l for l in lines if l.startswith("**Аннотация.**") or l.startswith("**Abstract.**"))
    kw_txt = next(l for l in lines if l.startswith("**Ключевые слова:**") or l.startswith("**Keywords:**"))
    fill(abstract_el, "Аннотация" if lang == "ru-RU" else "Abstract", abs_txt.split("**", 2)[2].strip())
    fill(keywords_el, "Ключевые слова" if lang == "ru-RU" else "Keywords", kw_txt.split("**", 2)[2].strip())

    start = next(k for k, l in enumerate(lines) if l.startswith("## "))
    k = start
    table_rows, in_refs = [], False
    while k < len(lines):
        l = lines[k].rstrip()
        k += 1
        if not l:
            continue
        if l.startswith("## "):
            head = re.sub(r"^[IVX]+\.\s*", "", l[3:])
            in_refs = head.lower().startswith(("список литературы", "references"))
            p = para_before(end_sect, doc, "Heading 1")
            add_runs(p, head, lang)
            if in_refs:
                p.paragraph_format.left_indent = None
            continue
        if in_refs:
            p = para_before(end_sect, doc, "references")
            add_runs(p, re.sub(r"\s*⟨[^⟩]*⟩", "", re.sub(r"^\[\d+\]\s*", "", l)), lang)
            continue
        if l.startswith("|"):
            table_rows.append([c.strip() for c in l.strip("|").split("|")])
            if k < len(lines) and lines[k].startswith("|"):
                continue
            rows = [r for r in table_rows if not set("".join(r)) <= set("-: ")]
            t = doc.add_table(rows=len(rows), cols=len(rows[0]))
            t.autofit = False
            ncol = len(rows[0])
            first_w = 0.62
            widths = [first_w] + [(3.45 - first_w) / (ncol - 1)] * (ncol - 1)
            for row in t.rows:
                for c, w in zip(row.cells, widths):
                    c.width = Inches(w)
            tblpr = t._tbl.tblPr
            for gc, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
                gc.set(qn("w:w"), str(int(w * 1440)))
            lay = OxmlElement("w:tblLayout"); lay.set(qn("w:type"), "fixed"); tblpr.append(lay)
            tw = tblpr.find(qn("w:tblW"))
            if tw is None:
                tw = OxmlElement("w:tblW"); tblpr.append(tw)
            tw.set(qn("w:w"), str(int(3.45 * 1440))); tw.set(qn("w:type"), "dxa")
            for tag in ("w:tblBorders",):
                b = OxmlElement(tag)
                for side in ("top", "bottom", "insideH"):
                    e = OxmlElement(f"w:{side}"); e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "4"); b.append(e)
                tblpr.append(b)
            for ri, row in enumerate(rows):
                for ci, cell in enumerate(row):
                    c = t.cell(ri, ci); c.text = ""
                    cp = c.paragraphs[0]; cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_runs(cp, f"**{cell}**" if ri == 0 else cell, lang, size=6.5)
            end_sect.addprevious(t._tbl)
            table_rows = []
            continue
        if l.startswith("**Таблица") or l.startswith("**Table"):
            p = para_before(end_sect, doc, "table head")
            no_numbering(p)
            add_runs(p, l.replace("**", ""), lang)
            continue
        p = para_before(end_sect, doc, "Body Text")
        add_runs(p, l, lang)
        for key, (img, cap) in figs.items():
            if l.startswith(key):
                fp = para_before(end_sect, doc, "Normal"); fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                fp.add_run().add_picture(img, width=Inches(3.4))
                cp = para_before(end_sect, doc, "figure caption")
                no_numbering(cp)
                add_runs(cp, cap, lang)
    doc.save(out)
    print("saved", out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--lang", default="ru-RU")
    a = ap.parse_args()
    ru = a.lang == "ru-RU"
    figs = {
        "*Доля ложных тревог.*" if ru else "*False-alarm rate.*": (
            "paper/figures/reliability_col.png",
            ("Рис. 1. Частота превышения квантиля прогноза Chronos-2 против номинальной, медиана и межквартильный "
             "размах по рядам страты; серая полоса — коридор [0,5α; 2α] при α = 1 %.") if ru else
            ("Fig. 1. Observed vs nominal exceedance of Chronos-2 forecast quantiles: median and interquartile "
             "range over the series of each stratum; grey band: [0.5α, 2α] at α = 1 %.")),
        "*Загрязнение контекста.*" if ru else "*Context contamination.*": (
            "paper/figures/power_contamination_col.png",
            ("Рис. 2. (а) Вероятность обнаружения внедрённых всплесков по стратам интенсивности при доле тревог 1 %; "
             "(б) обнаружение второго всплеска после сильного первого; чёрные отрезки — без первого всплеска.") if ru else
            ("Fig. 2. (a) Detection probability of injected bursts by intensity stratum at a 1 % alarm rate; "
             "(b) detection of a second burst after a strong first one; black ticks: without the first burst.")),
    }
    build(a.template, a.md, a.out, a.lang, figs)
