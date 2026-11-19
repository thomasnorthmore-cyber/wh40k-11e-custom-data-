#!/usr/bin/env python3
"""Generate the complete Aeldari 11e catalogue from the user's CSV-derived JSON.

The 17 hand-tested unit selections are preserved verbatim in the v6 fixture.
All other Aeldari datasheets from the user's 2026-11-12 export are added.
Their source loadouts and wargear option rules remain visible as explanatory
rules. Complex natural-language replacement restrictions are NOT guessed:
newly generated model weapon entries are explicitly provisional selectable
wargear, pending verification of exact swaps and per-model eligibility.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, Counter
from html import unescape
from pathlib import Path
import json
import re
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"data"/"structured"/"source"
DATA=ROOT/"data"/"structured"/"aeldari-source-datasheets.json"
FIXTURE=ROOT/"tests"/"fixtures"/"aeldari-v6.cat"
TARGET=ROOT/"Aeldari 11e TEST.cat"
GST=ROOT/"Warhammer 40,000 11e Custom TEST.gst"
N="{http://www.battlescribe.net/schema/catalogueSchema}"
G="{http://www.battlescribe.net/schema/gameSystemSchema}"
ET.register_namespace("","http://www.battlescribe.net/schema/catalogueSchema")

def node(parent,tag,**attrs):
    return ET.SubElement(parent,N+tag,{k:str(v).lower() if isinstance(v,bool) else str(v) for k,v in attrs.items()})

def text_only(s):
    s=(s or "").replace("<br>","\n").replace("<br/>","\n").replace("<br />","\n")
    s=re.sub(r"</(?:p|li|div|ul)>","\n",s,flags=re.I)
    s=re.sub(r"<li[^>]*>","- ",s,flags=re.I)
    return re.sub(r"[ \t]+"," ",unescape(re.sub(r"<[^>]+>","",s))).strip()

def clean(s):
    return re.sub(r"[^a-z0-9]","",s.lower())

def grouped(key):
    d=defaultdict(list)
    for row in json.loads((SOURCE/(key+".json")).read_text(encoding="utf-8")):
        d[row["datasheet_id"]].append(row)
    for values in d.values():
        values.sort(key=lambda x:int(x.get("line") or 0))
    return d

def limit(parent,id,kind,value):
    node(parent,"constraint",id=id+"-"+kind,type=kind,field="selections",
         scope="parent",value=value,shared="true",
         percentValue="false",includeChildSelections="false",includeChildForces="false")

def characteristic(parent,name,typeid,value):
    el=node(parent,"characteristic",name=name,typeId=typeid)
    el.text=str(value or "-")
    return el

def profile(parent,id,name,typeid,typename,fields):
    p=node(parent,"profile",id=id,name=name,hidden="false",typeId=typeid,typeName=typename)
    c=node(p,"characteristics")
    for field,key,value in fields: characteristic(c,field,key,value)
    return p

def rules(parent,id,name,description):
    r=node(parent,"rule",id=id,name=name,hidden="false")
    node(r,"description").text=description or "-"
    return r

def profile_unit_stats(parent,uid,entry,index):
    base=f"source-{uid}-stats-{index}"
    inv=entry.get("inv_sv","-")
    if inv not in ("","-") and not inv.endswith("+"):inv+="+"
    profile(parent,base,entry["name"].strip().title(),"stat-11e0","Units",[
      ("M","m-11e0",entry.get("M")),("T","t-11e0",entry.get("T")),
      ("Sv","sv-11e0",entry.get("Sv")),("Inv","inv-11e0",inv),
      ("W","w-11e0",entry.get("W")),("Ld","ld-11e0",entry.get("Ld")),
      ("OC","oc-11e0",entry.get("OC"))])

def parse_composition(rows,unit_name):
    out=[]
    for r in rows:
        m=re.match(r"^\s*(\d+)(?:\s*[-–]\s*(\d+))?\s+(.+?)\s*$",r["description"])
        if not m:continue
        a=int(m.group(1));b=int(m.group(2) or a)
        title=re.sub(r"\s+models?$","",m.group(3).strip(),flags=re.I)
        if title.lower() in ("model", "models"): title=unit_name
        if a>30 or b>50 or b<a:continue
        out.append({"name":title,"min":a,"max":b})
    if not out:out=[{"name":unit_name,"min":1,"max":1}]
    return out

def base_costs(rows):
    segments=[];bucket="YOUR UNIT COSTS"
    for r in rows:
        desc=text_only(r.get("description",""))
        c=r.get("cost","").strip()
        if not c:
            if desc.upper().startswith("YOUR ") and "COST" in desc.upper():bucket=desc
            continue
        try:price=int(c)
        except ValueError:continue
        match=re.match(r"^(\d+)(?:\s*[-–]\s*(\d+))?\s+models?",desc,re.I)
        total=int(match.group(1)) if match else 1
        if match and match.group(2):total=int(match.group(2))
        segments.append({"min_total":total,"price":price,"description":desc,"group":bucket})
    initial=[x for x in segments if "3RD" not in x["group"].upper()]
    return (initial[0]["price"] if initial else (segments[0]["price"] if segments else 0),segments)

def weapon_fields(r):
    ranged=r.get("type","").lower()=="ranged"
    if ranged:
        rng=r.get("range","-")
        if rng not in ("","-","Melee") and not rng.endswith('"'):rng+='"'
        typ="Ranged Weapons";tid="fd-ranged-type"
        fields=[("Range","fd-rng",rng),("A","fd-rna",r["A"]),
                ("BS","fd-rbs",r["BS_WS"]+"+" if r["BS_WS"].isdigit() else r["BS_WS"]),
                ("S","fd-rs",r["S"]),("AP","fd-rap",r["AP"]),
                ("D","fd-rd",r["D"]),("Keywords","fd-rkw",text_only(r.get("description","")))]
    else:
        typ="Melee Weapons";tid="fd-melee-type"
        fields=[("Range","fd-mrng","Melee"),("A","fd-ma",r["A"]),
                ("WS","fd-mws",r["BS_WS"]+"+" if r["BS_WS"].isdigit() else r["BS_WS"]),
                ("S","fd-ms",r["S"]),("AP","fd-map",r["AP"]),
                ("D","fd-md",r["D"]),("Keywords","fd-mkw",text_only(r.get("description","")))]
    return typ,tid,fields

def build():
    original=ET.parse(FIXTURE).getroot()
    entries=original.find(N+"selectionEntries")
    assert entries is not None
    base={u.get("name") for u in entries.findall(N+"selectionEntry") if u.get("type")=="unit"}
    assert len(base)==17, f"v6 fixture should contain 17 units, got {len(base)}"
    source=json.loads(DATA.read_text(encoding="utf-8"))["datasheets"]
    assert len(source)==99,len(source)
    tables={key:grouped(key) for key in ("Datasheets_models","Datasheets_wargear",
        "Datasheets_options","Datasheets_unit_composition","Datasheets_models_cost",
        "Datasheets_abilities","Datasheets_keywords")}
    category_xml=ET.parse(GST).getroot()
    categories={x.get("name"):x.get("id") for x in category_xml.findall("./"+G+"categoryEntries/"+G+"categoryEntry")}
    aliases={"Infantry Character":"Character","Infantry Epic Hero":"Epic Hero",
       "Monster Epic Hero":"Monster Epic Hero","Mounted Character":"Mounted Character",
       "Fortifications":"Fortification","Dedicated Transports":"Dedicated Transport"}
    known={clean(n) for n in base}
    created=[]
    for src in source:
        sid=src["id"];name=src["name"]
        if clean(name) in known:continue
        uid="source-aeldari-"+sid
        existing_ids={e.get("id") for e in original.iter() if e.get("id")}
        assert uid not in existing_ids
        unit=node(entries,"selectionEntry",id=uid,name=name,hidden="false",type="unit")
        profs=node(unit,"profiles")
        stats=tables["Datasheets_models"][sid]
        for index,row in enumerate(stats):profile_unit_stats(profs,sid,row,index)
        if not stats:raise ValueError(f"Missing model statistics: {name}")
        for index,a in enumerate(tables["Datasheets_abilities"][sid]):
            title=a.get("name","").strip()
            description=text_only(a.get("description",""))
            if title and description:
                profile(profs,f"source-{sid}-ability-{index}",title,"ability-11e0",
                        "Abilities",[("Description","description-11e0",description)])
        kws=tables["Datasheets_keywords"][sid]
        regular=", ".join(dict.fromkeys(x["keyword"] for x in kws if x["is_faction_keyword"].lower()!="true"))
        faction=", ".join(dict.fromkeys(x["keyword"] for x in kws if x["is_faction_keyword"].lower()=="true"))
        profile(profs,"source-"+sid+"-keywords","Keywords","keywords-11e0","Keywords",[
            ("Keywords","unit-keywords-11e0",regular),
            ("Faction Keywords","faction-keywords-11e0",faction)])
        rr=node(unit,"rules")
        rules(rr,"source-"+sid+"-starting","Starting Equipment",
              text_only(src.get("loadout","")) or "Refer to datasheet")
        rules(rr,"source-"+sid+"-composition","Unit Composition",
              "; ".join(x.get("description","") for x in tables["Datasheets_unit_composition"][sid]))
        for index,opt in enumerate(tables["Datasheets_options"][sid]):
            desc=text_only(opt.get("description",""))
            if desc and desc.lower()!="none":rules(rr,f"source-{sid}-option-{index}","Wargear Option "+str(index+1),desc)
        pts,tiers=base_costs(tables["Datasheets_models_cost"][sid])
        if not tiers:raise ValueError(f"Missing points: {name}")
        rules(rr,"source-"+sid+"-points","Source Points Table",
              "; ".join(f"{r['group']}: {r['description']} = {r['price']} pts" for r in tiers))
        cat=node(unit,"categoryLinks")
        role=aliases.get(src["role"],src["role"])
        cid=categories.get(role) or categories.get("Infantry") or categories["Units"]
        node(cat,"categoryLink",id=f"source-{sid}-role",name=role,targetId=cid,primary="true",hidden="false")
        models=node(unit,"selectionEntries")
        comps=parse_composition(tables["Datasheets_unit_composition"][sid],name)
        model_ids=[]
        weapons=tables["Datasheets_wargear"][sid]
        if not weapons:raise ValueError(f"Missing wargear profiles: {name}")
        for index,comp in enumerate(comps):
            mid=f"source-{sid}-model-{index}"
            model_ids.append(mid)
            m=node(models,"selectionEntry",id=mid,name=comp["name"],hidden="false",type="model")
            limits=node(m,"constraints")
            limit(limits,mid,"min",comp["min"]);limit(limits,mid,"max",comp["max"])
            eq=node(m,"selectionEntryGroups")
            group=node(eq,"selectionEntryGroup",id=f"{mid}-equipment",
                       name="Wargear (source choices — restrictions shown in Rules)",
                       hidden="false")
            choices=node(group,"selectionEntries")
            # All source weapons appear, preserving each profile, while source
            # replacement sentences are displayed verbatim as Wargear Options.
            # Do not guess mandatory / per-model weapon ownership from HTML.
            for wi,weapon in enumerate(weapons):
                eid=f"{mid}-weapon-{wi}"
                upgrade=node(choices,"selectionEntry",id=eid,name=weapon["name"],hidden="false",type="upgrade")
                constraints=node(upgrade,"constraints")
                limit(constraints,eid,"min",0);limit(constraints,eid,"max",1)
                wprofiles=node(upgrade,"profiles")
                typ,tid,fields=weapon_fields(weapon)
                profile(wprofiles,eid+"-profile",weapon["name"],tid,typ,fields)
        cost=node(unit,"costs")
        node(cost,"cost",name="pts",typeId="pts-11e0",value=pts)
        # Apply model-count modifiers only for units whose costs are a simple
        # single tier progression. More complex units retain the exact points
        # table, rather than making inaccurate automatic claims.
        first=[t for t in tiers if "3RD" not in t["group"].upper()]
        if len(comps)==1 and len(first)>1:
            mods=node(unit,"modifiers")
            for ti,tier in enumerate(first[1:]):
                m=node(mods,"modifier",type="set",field="pts-11e0",value=tier["price"])
                conditions=node(m,"conditions")
                node(conditions,"condition",type="atLeast",
                    value=tier["min_total"],field="selections",scope="parent",
                    childId=model_ids[0],shared="true",includeChildSelections="true",
                    includeChildForces="false")
        created.append((sid,name,len(weapons)))
    original.set("revision","7")
    assert len(created)==82, f"Expected 82 additions, got {len(created)}"
    all_units=entries.findall(N+"selectionEntry")
    assert len(all_units)==99,len(all_units)
    ids=[x.get("id") for x in original.iter() if x.get("id")]
    dupes=[x for x,n in Counter(ids).items() if n>1]
    assert not dupes,dupes[:20]
    return original,created

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    tree,created=build()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(tree).write(args.out,encoding="utf-8",xml_declaration=True)
    ET.parse(args.out)
    print(f"PASS: generated {len(created)} source units alongside the 17 verified v6 units = 99 total")
    print(f"Output: {args.out}")
    for sid,name,n in created:print(f"{sid} {name}: {n} source wargear profiles")

if __name__=="__main__":main()
