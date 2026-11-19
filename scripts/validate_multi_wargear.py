#!/usr/bin/env python3
"""Falcon and Wraithlord models retain precise selection limits and weapon profiles."""
from pathlib import Path
import xml.etree.ElementTree as ET
C="{http://www.battlescribe.net/schema/catalogueSchema}"
root=ET.parse(Path(__file__).resolve().parents[1]/"tests/fixtures/aeldari-v6.cat").getroot()
units={u.get("id"):u for u in root.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
def entry(parent,id,tag="selectionEntry"):
    items=[e for e in parent.iter(C+tag) if e.get("id")==id]
    assert len(items)==1,(id,len(items))
    return items[0]
def limits(e,minimum,maximum):
    data={c.get("type"):int(c.get("value")) for c in e.findall("./"+C+"constraints/"+C+"constraint")}
    assert data=={"min":minimum,"max":maximum}, (e.get("id"),data)
falcon=units["smoke-unit-609"]
assert falcon.find("./"+C+"costs/"+C+"cost").get("value")=="130"
fmodel=entry(falcon,"smoke-609-model-0")
for gid,number in (("falcon-group-turret",5),("falcon-group-underside",2)):
    group=entry(fmodel,gid,"selectionEntryGroup")
    limits(group,1,1)
    options=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
    assert len(options)==number
    assert group.get("defaultSelectionEntryId") in {e.get("id") for e in options}
    for e in options:
        profiles=e.findall("./"+C+"profiles/"+C+"profile")
        assert profiles,f"{e.get('name')}: missing equipped weapon characteristics"
wraith=units["smoke-unit-613"]
assert wraith.find("./"+C+"costs/"+C+"cost").get("value")=="125"
model=entry(wraith,"smoke-613-model-0")
groups={
 "wl-group-arms":(2,2,{"wl-arms-catapult":1,"wl-arms-flamer":1}),
 "wl-group-heavy":(0,2,{"wl-heavy-missile":2,"wl-heavy-bright":1,"wl-heavy-scatter":1,"wl-heavy-shuriken":1,"wl-heavy-star":1}),
 "wl-group-wargear":(0,1,{"wl-wargear-ghost":2}),
}
for gid,(minimum,maximum,choices) in groups.items():
    group=entry(model,gid,"selectionEntryGroup")
    limits(group,minimum,maximum)
    assert {e.get("id") for e in group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}==set(choices)
    for id,expected in choices.items():
        gear=entry(group,id)
        profiles=gear.findall("./"+C+"profiles/"+C+"profile")
        assert len(profiles)==expected,f"{id}: expected {expected} weapon mode profiles"
        assert all(p.get("hidden")=="false" and p.find("./"+C+"modifiers") is None for p in profiles),f"{id}: detached display triggers remain"
assert entry(model,"wl-arms-catapult").find("./"+C+"profiles/"+C+"profile").get("name")=="Shuriken catapult"
assert entry(model,"wl-arms-flamer").find("./"+C+"profiles/"+C+"profile").get("name")=="Flamer"
assert len([p for p in wraith.findall("./"+C+"profiles/"+C+"profile") if p.get("typeName") in ("Ranged Weapons","Melee Weapons")])==0
print("PASS: Falcon 1-of-5/1-of-2 weapon slots and Wraithlord two arms/optional heavy weapons/Ghostglaive")
