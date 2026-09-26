"""演示 API。所有业务样例来自 demo_data/pipes.json，不读取竞赛原始文件。"""
import csv
import io
import json
from pathlib import Path
from typing import Literal
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "demo_data" / "pipes.json").read_text(encoding="utf-8"))
app = FastAPI(title="管网风险评估 · 演示接口", version="0.1.0")

def select_pipes(q="", risk="", material="", min_diameter=300):
    return [p for p in DATA["pipes"]
            if (not q or q.casefold() in (p["pipe_id"] + p["road"]).casefold())
            and (not risk or p["risk_level"] == risk)
            and (not material or p["material"] == material)
            and p["diameter_mm"] >= min_diameter]

@app.get("/api/health")
def health():
    return {"status": "ok", "mode": "demo"}

@app.get("/api/dashboard")
def dashboard(q: str = Query("", max_length=100),
              risk: Literal["", "高", "中", "低"] = "",
              material: str = Query("", max_length=40),
              min_diameter: int = Query(300, ge=0, le=3000)):
    pipes = sorted(select_pipes(q.strip(), risk, material, min_diameter),
                   key=lambda p: (-p["risk_score"], p["pipe_id"]))
    return {
        "meta": DATA["meta"],
        "filters": {"materials": sorted({p["material"] for p in DATA["pipes"]})},
        "summary": {"count": len(pipes),
                    "length_km": round(sum(p["length_m"] for p in pipes)/1000, 2),
                    "high_count": sum(p["risk_level"] == "高" for p in pipes),
                    "distribution": {r: sum(p["risk_level"] == r for p in pipes) for r in ["高", "中", "低"]}},
        "pipes": pipes,
    }

@app.get("/api/pipes/{pipe_id}")
def pipe_detail(pipe_id: str):
    for pipe in DATA["pipes"]:
        if pipe["pipe_id"] == pipe_id:
            return {"mode": "demo", "pipe": pipe}
    raise HTTPException(404, "未找到该管段")

@app.get("/api/export")
def export(q: str = Query("", max_length=100),
           risk: Literal["", "高", "中", "低"] = "",
           material: str = Query("", max_length=40),
           min_diameter: int = Query(300, ge=0, le=3000),
           ids: str = Query("", max_length=1000)):
    pipes = sorted(select_pipes(q.strip(), risk, material, min_diameter),
                   key=lambda p: -p["risk_score"])
    if ids:
        selected = set(ids.split(","))
        pipes = [p for p in pipes if p["pipe_id"] in selected]
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["数据类型", "管段编号", "道路", "管径(mm)", "管材", "风险分(非概率)", "等级", "排查建议", "评估时间"])
    for p in pipes:
        writer.writerow(["虚构演示数据", p["pipe_id"], p["road"], p["diameter_mm"],
                         p["material"], p["risk_score"], p["risk_level"],
                         p["recommendation"], DATA["meta"]["as_of"]])
    return Response(buffer.getvalue().encode("utf-8-sig"), media_type="text/csv",
                    headers={"Content-Disposition": 'attachment; filename="demo-inspection-list.csv"'})

# 构建前端后，单个 Python 服务也能提供完整页面。
dist = ROOT / "frontend" / "dist"
if dist.is_dir():
    app.mount("/", StaticFiles(directory=dist, html=True), name="frontend")
