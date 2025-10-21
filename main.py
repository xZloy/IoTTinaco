import os
from datetime import datetime, timezone
from typing import Optional, List, Literal
from fastapi import FastAPI, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, Column, String, DateTime, Float
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON as SQLITE_JSON

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./data.db"

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    JSONType = SQLITE_JSON
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    JSONType = JSONB
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Reading(Base):
    __tablename__ = "readings"
    id = Column(String, primary_key=True)
    device_id = Column(String, index=True, nullable=False)
    ts = Column(DateTime(timezone=True), nullable=False)
    level_pct = Column(Float, nullable=True)
    flow_lpm  = Column(Float, nullable=True)
    tds_ppm   = Column(Float, nullable=True)
    water_temp_c = Column(Float, nullable=True)
    pump  = Column(String, nullable=True)
    valve = Column(String, nullable=True)
    alerts = Column(JSONType, nullable=True)
    humidity_pct = Column(Float, nullable=True)
Base.metadata.create_all(engine)

class ReadingIn(BaseModel):
    device_id: str = Field(..., min_length=1)
    ts: Optional[datetime] = None
    level_pct: Optional[float] = Field(None, ge=0, le=100)
    flow_lpm: Optional[float] = Field(None, ge=0)
    tds_ppm: Optional[float] = Field(None, ge=0)
    waterTempC: Optional[float] = None
    pump: Optional[str] = None
    valve: Optional[str] = None
    alerts: Optional[List[str]] = None
    humidity_pct: Optional[float] = None

class ReadingOut(BaseModel):
    id: str
    device_id: str
    ts: datetime
    level_pct: float | None = None
    flow_lpm: float | None = None
    tds_ppm: float | None = None
    water_temp_c: float | None = None
    humidity_pct: float | None = None   
    pump: str | None = None
    valve: str | None = None
    alerts: list | None = None
    class Config: from_attributes = True


app = FastAPI(title="Tinaco API (simple cloud)", version="0.1.0")

@app.get("/health")
def health():
    return {"ok": True, "now": datetime.now(timezone.utc).isoformat()}

@app.post("/ingest")
def ingest(payload: ReadingIn):
    from uuid import uuid4
    db = SessionLocal()
    try:
        r = Reading(
            id=str(uuid4()),
            device_id=payload.device_id,
            ts=payload.ts or datetime.now(timezone.utc),
            level_pct=payload.level_pct,
            flow_lpm=payload.flow_lpm,
            tds_ppm=payload.tds_ppm,
            water_temp_c=payload.waterTempC,
            humidity_pct=payload.humidity_pct,
            pump=payload.pump,
            valve=payload.valve,
            alerts=payload.alerts or [],
        )
        db.add(r)
        db.commit()
        return {"readingId": r.id}
    finally:
        db.close()

@app.get("/readings", response_model=list[ReadingOut])
def list_readings(
    device_id: str,
    limit: int = Query(200, ge=1, le=5000),
    from_ts: Optional[datetime] = Query(None, alias="from"),
    to_ts: Optional[datetime] = Query(None, alias="to"),
):
    db = SessionLocal()
    try:
        q = db.query(Reading).filter(Reading.device_id == device_id)
        if from_ts: q = q.filter(Reading.ts >= from_ts)
        if to_ts:   q = q.filter(Reading.ts <= to_ts)
        q = q.order_by(Reading.ts.desc()).limit(limit)
        return q.all()
    finally:
        db.close()

@app.get("/readings/all", response_model=list[ReadingOut])
def list_all_readings(
    device_id: Optional[str] = None,
    limit: int = Query(10000, ge=1, le=100000),
    offset: int = Query(0, ge=0),
    from_ts: Optional[datetime] = Query(None, alias="from"),
    to_ts: Optional[datetime] = Query(None, alias="to"),
    sort: Literal["asc", "desc"] = Query("desc"),
):
    db = SessionLocal()
    try:
        q = db.query(Reading)
        if device_id:
            q = q.filter(Reading.device_id == device_id)
        if from_ts:
            q = q.filter(Reading.ts >= from_ts)
        if to_ts:
            q = q.filter(Reading.ts <= to_ts)
        q = q.order_by(Reading.ts.asc() if sort == "asc" else Reading.ts.desc())
        q = q.offset(offset).limit(limit)
        return q.all()
    finally:
        db.close()

@app.get("/analytics/daily")
def analytics_daily(device_id: str):
    sql = """
    SELECT
      DATE_TRUNC('day', ts) AS day,
      AVG(level_pct) AS avg_level,
      SUM(COALESCE(flow_lpm,0))/60.0 AS approx_liters,
      AVG(tds_ppm) AS avg_tds,
      AVG(water_temp_c) AS avg_temp_c,        
      AVG(humidity_pct) AS avg_humidity_pct,  
      COUNT(*) AS samples
    FROM readings
    WHERE device_id = :device_id
    GROUP BY 1
    ORDER BY 1 DESC
    LIMIT 60;
    """
    db = SessionLocal()
    try:
        rows = db.execute(text(sql), {"device_id": device_id}).fetchall()
        
        return [
            {
                "day": str(day),
                "avg_level": avg_level,
                "approx_liters": approx_liters,
                "avg_tds": avg_tds,
                "avg_temp_c": avg_temp_c,
                "avg_humidity_pct": avg_hum,
                "samples": samples
            }
            for (day, avg_level, approx_liters, avg_tds, avg_temp_c, avg_hum, samples) in rows
        ]
    finally:
        db.close()

