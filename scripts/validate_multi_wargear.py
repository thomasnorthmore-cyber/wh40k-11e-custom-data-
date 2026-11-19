#!/usr/bin/env python3
"""Regression checks for Falcon/Wraithlord multi-wargear in the TEST catalogue."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
C="{http://www.battlescribe.net/schema/catalogueSchema}"
cat=ET.parse(ROOT / "Aeldari 11e TEST.cat").getroot()
units={u.get("id"):u for u in cat.findall("./"+C+"selectionEntries/"+C+"selectionEntry")}
def check(uid, model_id, groups, profile_prefix, higher_or_fixed):
    unit=units[uid]
    models=[x for x in unit.findall(".//"+C+"selectionEntry") if x.get("id")==model_id]
    assert len(models)==1, f"{uid}: model missing"
    model=models[0]
    found={x.get("id"):x for x in model.findall("./"+C+"selectionEntryGroups/"+C+"selectionEntryGroup")}
    assert len(found)==len(groups), f"{uid}: incorrect group count"
    profiles=unit.findall("./"+C+"profiles/"+C+"profile")
    types=list(dict.fromkeys(p.get("typeName") for p in profiles))
    assert types[0]=="Units" and "Ranged Weapons" in types and "Melee Weapons" in types, f"{uid}: weapon tables missing"
    assert types.index("Ranged Weapons")<types.index("Melee Weapons")<types.index("Abilities")<types.index("Keywords"), f"{uid}: display sequence regressed"
    all_choices=set()
    for group_id,minimum_options in groups.items():
        group=found[group_id]
        choices=group.findall("./"+C+"selectionEntries/"+C+"selectionEntry")
        assert len(choices)>=minimum_options, f"{uid}: group {group_id} lacks options"
        default=group.get("defaultSelectionEntryId")
        assert default in {x.get("id") for x in choices}, f"{uid}: default selection missing"
        constraints=group.findall("./"+C+"constraints/"+C+"constraint")
        assert {x.get("type"):x.get("value") for x in constraints}=={"min":"1","max":"1"}, f"{uid}: group not single-choice"
        all_choices.update(x.get("id") for x in choices)
    conditional=[p for p in profiles if p.get("id","").startswith(profile_prefix)]
    assert conditional, f"{uid}: missing conditional weapon profiles"
    used=set()
    for p in conditional:
        assert p.get("hidden")=="true", f"{uid}: conditional weapon visible by default"
        conditions=p.findall("./"+C+"modifiers/"+C+"modifier/"+C+"conditions/"+C+"condition")
        assert len(conditions)==1, f"{uid}: conditional profile {p.get('name')} has no unique trigger"
        trigger=conditions[0].get("childId")
        assert trigger in all_choices, f"{uid}: profile points to a non-existent option {trigger}"
        used.add(trigger)
    assert used, f"{uid}: no active options referenced"
    cost=unit.find("./"+C+"costs/"+C+"cost")
    assert cost is not None and cost.get("value")==str(higher_or_fixed), f"{uid}: points changed"
    return len(conditional)

falcon=check("smoke-unit-609","smoke-609-model-0",{
    "falcon-group-turret":5,"falcon-group-underside":2
},"falcon-profile-",130)
wraithlord=check("smoke-unit-613","smoke-613-model-0",{
    "wl-group-arm1":2,"wl-group-arm2":2,"wl-group-heavy1":6,
    "wl-group-heavy2":6,"wl-group-sword":2
},"wl-profile-",125)
print(f"PASS: Falcon (2 independent choices, {falcon} weapon profiles), Wraithlord (5 choices, {wraithlord} weapon profiles), points and ordering")
