"""资料展示 API：空间与属性记录来自 data/，评分保留来源说明。"""
import csv, io, json
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT/"data/network.json").read_text(encoding="utf-8"))
GEOMETRY_BYTES = (ROOT/"data/geometry.json").read_bytes()
PIPES = {p["pipe_id"]:p for p in DATA["pipes"]}
LEVELS = ["高","较高","中","低","未评估"]
app = FastAPI(title="供水管网安全风险评估与决策",version="0.2.0")
app.add_middleware(GZipMiddleware,minimum_size=1000)
Risk = Literal["","高","较高","中","低","未评估"]

def select_pipes(q="",risk="",material="",min_diameter=300):
    q=q.strip().casefold()
    records=[p for p in PIPES.values()
        if (not q or q in (p["pipe_id"]+" "+p["pipe_code"]+" "+p["road"]).casefold())
        and (not risk or p["risk_level"]==risk)
        and (not material or p["material"]==material)
        and p["diameter_mm"] is not None and p["diameter_mm"]>=min_diameter]
    return sorted(records,key=lambda p: (-(p["risk_score"] if p["risk_score"] is not None else -1),p["pipe_id"]))

@app.get("/api/health")
def health():return {"status":"ok","mode":DATA["meta"]["mode"],"records":len(PIPES)}

@app.get("/api/network")
def network():return Response(GEOMETRY_BYTES,media_type="application/json")

@app.get("/api/dashboard")
def dashboard(q:str=Query("",max_length=100),risk:Risk="",material:str=Query("",max_length=40),
              min_diameter:int=Query(300,ge=0,le=3000)):
    pipes=select_pipes(q,risk,material,min_diameter)
    summary={"count":len(pipes),"total_count":len(PIPES),
        "length_km":round(sum(p["length_m"] for p in pipes)/1000,2),
        "high_count":sum(p["risk_level"]=="高" for p in pipes),
        "priority_count":sum(p["risk_level"] in ["高","较高"] for p in pipes),
        "road_count":len({p["road"] for p in pipes}),
        "distribution":{r:sum(p["risk_level"]==r for p in pipes) for r in LEVELS},
        "materials":{m:sum(p["material"]==m for p in pipes) for m in sorted({p["material"] for p in pipes})},
        "diameters":{str(int(d)):sum(p["diameter_mm"]==d for p in pipes) for d in sorted({p["diameter_mm"] for p in pipes})}}
    return {"meta":DATA["meta"],"filters":{"materials":sorted({p["material"] for p in PIPES.values()})},
            "summary":summary,"pipes":[{k:v for k,v in p.items() if k not in ["factors","recommendation","recommendation_source"]} for p in pipes]}

@app.get("/api/pipes/{pipe_id}")
def detail(pipe_id:str):
    if pipe_id not in PIPES:raise HTTPException(404,"未找到该管段")
    return {"mode":DATA["meta"]["mode"],"pipe":PIPES[pipe_id]}

@app.get("/api/export")
def export(q:str=Query("",max_length=100),risk:Risk="",material:str=Query("",max_length=40),
           min_diameter:int=Query(300,ge=0,le=3000),ids:str=Query("",max_length=100000)):
    pipes=select_pipes(q,risk,material,min_diameter)
    if ids:
        chosen=set(ids.split(","));pipes=[p for p in pipes if p["pipe_id"] in chosen]
    output=io.StringIO(newline="");writer=csv.writer(output)
    writer.writerow(["管段ID","管段编号","道路","管径(mm)","管材","管龄(年)","长度(m)","资料评分","风险等级","排查建议","评分来源","建议来源"])
    def safe(v):
        s="" if v is None else str(v)
        return "'"+s if s[:1] in ["=","+","-","@","\t","\r"] else s
    for p in pipes:
        writer.writerow([safe(v) for v in [p["pipe_id"],p["pipe_code"],p["road"],p["diameter_mm"],
            p["material"],p["age_years"],p["length_m"],p["risk_score"],p["risk_level"],p["recommendation"],
            DATA["meta"]["score_source"],p["recommendation_source"]]])
    return Response(output.getvalue().encode("utf-8-sig"),media_type="text/csv",
        headers={"Content-Disposition":'attachment; filename="inspection-list.csv"'})
dist=ROOT/"frontend/dist"
if dist.is_dir():app.mount("/",StaticFiles(directory=dist,html=True),name="frontend")
