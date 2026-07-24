#!/usr/bin/env python3
"""Collate raw/*.json (951 cases) -> ip_rights_all.csv, with OG comparison where available."""
import os, json, re, glob
import pandas as pd

RAW="raw"
OG="../../merged_coded_orders (2).csv"

def extract(txt):
    txt=txt.strip()
    try:
        env=json.loads(txt)
        if isinstance(env,dict) and "result" in env and "ip_status" not in env:
            if env.get("is_error"): raise ValueError(env.get("result","error"))
            txt=env["result"]
    except json.JSONDecodeError:
        pass
    txt=re.sub(r"^```(json)?|```$","",txt.strip(),flags=re.M).strip()
    m=re.search(r"\{.*\}",txt,re.S)
    if not m: raise ValueError("no JSON")
    return json.loads(m.group(0))

rows=[]; errs=[]
for p in sorted(glob.glob(f"{RAW}/*.json")):
    cid=os.path.basename(p)[:-5]; raw=open(p).read()
    if not raw.strip(): errs.append((cid,"empty")); continue
    try:
        o=extract(raw)
        rows.append(dict(
            case_id=o.get("case_id",cid),
            ip_status=o.get("ip_status"),
            ip_evidence=o.get("ip_evidence",""),
            rights_asserted=json.dumps(sorted(x.lower() for x in o.get("rights_asserted",[]))),
            rights_evidence=json.dumps(o.get("rights_evidence",{}),ensure_ascii=False),
            rights_anchor_order=o.get("rights_anchor_order",""),
            notes=o.get("notes","")))
    except Exception as e:
        errs.append((cid,str(e)[:90]))

df=pd.DataFrame(rows)

# compare against OG where the case existed in the coded set
og=pd.read_csv(OG)
def norm(v):
    s=str(v).strip()
    if s in ("nan","","[]"): return []
    try: l=json.loads(s.replace("'",'"'))
    except Exception: l=[t.strip() for t in s.strip("[]").replace("'","").split(",") if t.strip()]
    return sorted(i.strip().lower() for i in ([l] if isinstance(l,str) else l))
og_r=og.groupby("case_id").rights_asserted.first().map(lambda v: json.dumps(norm(v)))
og_ip=og.groupby("case_id").ip_case_confirmed.first().astype(str).str.lower()
df=df.merge(og_r.rename("rights_OG"),on="case_id",how="left").merge(og_ip.rename("ip_OG"),on="case_id",how="left")
df["in_OG"]=df.rights_OG.notna()
df["rights_changed"]=df.in_OG & (df.rights_asserted!=df.rights_OG)

# --- audit framing ---
# in_OG (present in merged_coded)  = old classifier judged it IP (and coded it)
# NOT in_OG (the 183)              = old classifier judged it NON-IP and dropped it
df["old_label"]=df.in_OG.map({True:"IP (kept)",False:"non-IP (dropped)"})
df["ip_yes"]=df.ip_status.str.lower().eq("yes")

df.to_csv("ip_rights_all.csv",index=False)

# THE key audit file: cases the OLD classifier dropped as non-IP but the NEW one says ARE ip.
recovered = df[(~df.in_OG) & df.ip_yes]
recovered.to_csv("ip_rights_RECOVERED_false_negatives.csv",index=False)

# other direction: cases OLD kept as IP but NEW says are NOT ip (false positives to review)
dropped = df[df.in_OG & df.ip_status.str.lower().eq("no")]
dropped.to_csv("ip_rights_FALSE_POSITIVES.csv",index=False)

# the full re-audit of the old non-IP set, whatever the verdict
df[~df.in_OG].to_csv("ip_rights_OLD_nonIP_reaudit.csv",index=False)
# coded cases whose rights moved
df[df.rights_changed].to_csv("ip_rights_CHANGED.csv",index=False)

print(f"parsed {len(df)} / 951 cases  | errors {len(errs)}")
print("ip_status overall:", df.ip_status.value_counts(dropna=False).to_dict())
print()
print(f"OLD non-IP set re-audited: {(~df.in_OG).sum()} cases")
print(f"   -> RECOVERED (old=non-IP, new=yes IP): {len(recovered)}   << cases to ADD back")
print(f"   -> new agrees non-IP (no/unclear):     {(~df.in_OG).sum()-len(recovered)}")
print(f"OLD IP set: {df.in_OG.sum()} cases")
print(f"   -> new says NOT ip (false positives):  {len(dropped)}   << review for removal")
print(f"   -> rights changed vs OG:               {int(df.rights_changed.sum())}")
for c,e in errs[:20]: print("  ERR",c,e)
print("\nwrote: ip_rights_all.csv, ip_rights_RECOVERED_false_negatives.csv,")
print("       ip_rights_FALSE_POSITIVES.csv, ip_rights_OLD_nonIP_reaudit.csv, ip_rights_CHANGED.csv")
