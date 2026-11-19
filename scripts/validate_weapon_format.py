#!/usr/bin/env python3
"""Regression check for consistent weapon profile notation.

Live New Recruit column widths and wrapping are controlled by its renderer,
not by arbitrary styling attributes in .cat/.gst files.
"""
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root=Path(__file__).resolve().parents[1]
C="{http://www.battlescribe.net/schema/catalogueSchema}"
cat=ET.parse(root/"Aeldari 11e TEST.cat").getroot()
weapons=[p for p in cat.iter(C+"profile") if p.get("typeName") in ("Ranged Weapons","Melee Weapons")]
assert weapons,"No weapon profiles found"
count=0
for p in weapons:
    ch={x.get("name"):(x.text or "").strip() for x in p.findall("./"+C+"characteristics/"+C+"characteristic")}
    assert all(x in ch for x in ("Range","A","S","AP","D")), f"{p.get('id')}: incomplete weapon table"
    assert re.fullmatch(r'\d+"|Melee|N/A|—|-',ch["Range"]), f"{p.get('id')}: invalid range {ch['Range']}"
    skill="BS" if p.get("typeName")=="Ranged Weapons" else "WS"
    assert skill in ch and re.fullmatch(r'[2-6]\+|—|-',ch[skill]), f"{p.get('id')}: invalid {skill} {ch.get(skill)}"
    count+=1
print(f"PASS: {count} ranged/melee profiles use consistent range and BS/WS notation")
