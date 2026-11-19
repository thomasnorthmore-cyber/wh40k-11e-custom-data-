#!/usr/bin/env python3
"""Check that squad weapon profiles reflect selected weapon/model quantities."""
from pathlib import Path
import xml.etree.ElementTree as ET

C="{http://www.battlescribe.net/schema/catalogueSchema}"
cat=ET.parse(Path(__file__).resolve().parents[1]/"Aeldari 11e TEST.cat").getroot()
units={u.get("id"):u for u in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}

def profile(uid,pid):
    matches=[p for p in units[uid].findall("./"+C+"profiles/"+C+"profile") if p.get("id")==pid]
    assert len(matches)==1, f"{uid}: missing {pid}"
    return matches[0]

def check_variants(uid,base,quantity_ids,counts,source):
    for count in counts:
        pid=base if count==counts[0] else base+quantity_ids(count)
        p=profile(uid,pid)
        assert p.get("name").endswith(f"(x{count})"),f"{uid}: {pid} missing x{count}"
        assert p.get("hidden")=="true",f"{uid}: {pid} must start hidden"
        mods=p.findall("./"+C+"modifiers/"+C+"modifier")
        assert mods and mods[0].get("value")=="false",f"{uid}: {pid} cannot become visible"
        conditions=mods[0].findall("./"+C+"conditions/"+C+"condition")
        assert len(conditions)==1 and conditions[0].get("childId")==source and int(conditions[0].get("value"))==count,f"{uid}: {pid} trigger incorrect"
        if count<counts[-1]:
            assert len(mods)==2 and mods[1].get("value")=="true",f"{uid}: {pid} will persist when another weapon is added"
            upper=mods[1].find("./"+C+"conditions/"+C+"condition")
            assert upper.get("childId")==source and int(upper.get("value"))==count+1
        else:
            assert len(mods)==1

# Fire Dragons and Dark Reapers use a regular-model quantity selector (4–9)
# with mandatory equipment nested under each model. Do not duplicate each
# regular weapon profile for every squad size: New Recruit lists the selected
# model and its equipment in the roster.
for uid,model_id,gun,melee in (
    ("fd-unit-root","fd-regular-5","Dragon fusion gun","Close combat weapon"),
    ("dr-unit-root","dr-regular","Reaper launcher (starshot / starswarm)","Close combat weapon"),
):
    models=[m for m in units[uid].iter(C+"selectionEntry") if m.get("id")==model_id]
    assert len(models)==1, f"{uid}: missing regular-model counter"
    model=models[0]
    limits={c.get("type"):int(c.get("value")) for c in model.findall("./"+C+"constraints/"+C+"constraint")}
    assert limits=={"min":4,"max":9}, f"{uid}: expected 4–9 regular models"
    equipment={e.get("name") for e in model.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
    assert {gun,melee}<=equipment, f"{uid}: regular models must carry both ranged and melee gear"
    for entry in model.findall("./"+C+"selectionEntries/"+C+"selectionEntry"):
        assert {c.get("type"):int(c.get("value")) for c in entry.findall("./"+C+"constraints/"+C+"constraint")}=={"min":1,"max":1}, f"{uid}: model gear must be mandatory"
for pid in ("smoke-589-weapon-0-0","smoke-589-weapon-0-1"):
    check_variants("smoke-unit-589",pid,lambda n:"",[10],"smoke-589-model-0")
for uid,prefix,maxn in (("smoke-unit-591","mul-591-p-",6),("smoke-unit-605","mul-605-p-",2),("smoke-unit-612","mul-612-p-",4)):
    selected=[p for p in units[uid].findall("./"+C+"profiles/"+C+"profile") if p.get("id","").startswith(prefix)]
    for p in selected:
        pid=p.get("id")
        original=pid.split("-count-")[0]
        n=int(pid.rsplit("-count-",1)[1]) if "-count-" in pid else 1
        assert 1<=n<=maxn
        if n>1: assert p.get("name").endswith(f"(x{n})"),pid
        assert p.get("hidden")=="true",pid
        mods=p.findall("./"+C+"modifiers/"+C+"modifier")
        assert mods and mods[0].get("value")=="false",pid
        conditions=mods[0].findall("./"+C+"conditions/"+C+"condition")
        assert len(conditions)==1 and int(conditions[0].get("value"))==n,pid
        if n<maxn:
            assert len(mods)==2 and mods[1].get("value")=="true",pid
            next_condition=mods[1].find("./"+C+"conditions/"+C+"condition")
            assert next_condition.get("childId")==conditions[0].get("childId") and int(next_condition.get("value"))==n+1,pid
    stems={p.get("id").split("-count-")[0] for p in selected}
    for stem in stems:
        assert sum(p.get("id")==stem or p.get("id").startswith(stem+"-count-") for p in selected)==maxn,f"{uid}: missing variant for {stem}"
for n,label in ((5,"five"),(10,"ten")):
    for pid in ("weapon-longrifle-11e0","weapon-pistol-11e0","weapon-melee-11e0"):
        p=profile("unit-rangers-11e0",f"{pid}-qty-{n}")
        assert p.get("name").endswith(f"(x{n})")
        assert p.get("hidden")=="true"
        con=p.find("./"+C+"modifiers/"+C+"modifier/"+C+"conditions/"+C+"condition")
        assert con is not None and con.get("childId")==f"rangers-{label}-11e0"
print("PASS: weapon counts reflect squad size or each selected weapon quantity")
