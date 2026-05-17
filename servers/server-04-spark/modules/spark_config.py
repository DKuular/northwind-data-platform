"""Load servers/server-04-spark/config/config.json (Silver/Gold batch, Bronze streaming)."""

from __future__ import annotations

import json
import os
from pathlib import Path


def config_path() -> Path:
    for key in ("SPARK_CONFIG_PATH", "SPARK_JOBS_CONFIG"):
        raw = os.environ.get(key)
        if raw:
            return Path(raw)
    return Path(__file__).resolve().parent.parent / "config" / "config.json"


def load_config() -> dict:
    path = config_path()
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def configure_event_log(builder, cfg: dict):
    """Enable spark.eventLog.* when spark_observability.event_log_enabled (overridable by SPARK_EVENT_LOG_ENABLED)."""
    obs = cfg.get("spark_observability") or {}
    enabled = bool(obs.get("event_log_enabled", False))
    raw = os.getenv("SPARK_EVENT_LOG_ENABLED")
    if raw is not None and raw.strip() != "":
        enabled = raw.strip().lower() in ("1", "true", "yes", "on")
    if not enabled:
        return builder
    log_dir = obs.get("event_log_dir", "file:///opt/spark/event-logs")
    b = builder.config("spark.eventLog.enabled", "true").config("spark.eventLog.dir", log_dir)
    if obs.get("event_log_compress", True):
        b = b.config("spark.eventLog.compress", "true")
    return b


def env_override(env_var: str, fallback: str) -> str:
    """Non-empty env wins over config.json defaults."""
    raw = os.getenv(env_var)
    if raw is not None and raw.strip() != "":
        return raw
    return fallback


def driver_log_level(cfg: dict) -> str:
    obs = cfg.get("spark_observability") or {}
    return env_override("SPARK_DRIVER_LOG_LEVEL", str(obs.get("driver_log_level", "WARN")))


def extra_jars_csv(cfg: dict) -> str:
    return ",".join(cfg["extra_jars"])


def minio_endpoint(cfg: dict) -> str:
    m = cfg["minio"]
    return os.getenv(m["endpoint_env"], m["default_endpoint"])


def minio_access_key(cfg: dict) -> str:
    m = cfg["minio"]
    return os.getenv(m["access_key_env"], "")


def minio_secret_key(cfg: dict) -> str:
    m = cfg["minio"]
    return os.getenv(m["secret_key_env"], "")


def bronze_bucket(cfg: dict) -> str:
    m = cfg["minio"]
    return os.getenv(m["bucket_env"], m["default_bucket"])


def bucket_name(cfg: dict, *, silver_override_env: str | None = "SILVER_BUCKET") -> str:
    """Prefer SILVER_BUCKET, then bucket_env from config, then default_bucket."""
    m = cfg["minio"]
    if silver_override_env:
        v = os.getenv(silver_override_env)
        if v:
            return v
    return os.getenv(m["bucket_env"], m["default_bucket"])
