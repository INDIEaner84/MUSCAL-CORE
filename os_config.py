import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DeploymentMode(Enum):
    LOCAL_DEV = "local_dev"
    PRODUCTION = "production"
    SIMULATION = "simulation"

_ENV_MODE_MAP = {
    "local_dev": DeploymentMode.LOCAL_DEV,
    "production": DeploymentMode.PRODUCTION,
    "simulation": DeploymentMode.SIMULATION,
}

_BOOL_KEYS = {"enable_graph", "enable_sphere", "enable_system_runtime",
              "enable_browser", "enable_desktop", "verbose_logging", "simulation_mode"}
_INT_KEYS = {"max_rag_results", "boot_timeout", "health_check_interval"}
_FLOAT_KEYS = set()
_ENV_PREFIX = "MUSCAL_"


def _apply_env_overrides(cfg: 'MuscalConfig') -> None:
    for f in cfg.__dataclass_fields__:
        env_key = _ENV_PREFIX + f.upper()
        val = os.environ.get(env_key)
        if val is None:
            continue
        if f in _BOOL_KEYS:
            setattr(cfg, f, val.lower() in ("1", "true", "yes"))
        elif f in _INT_KEYS:
            setattr(cfg, f, int(val))
        elif f in _FLOAT_KEYS:
            setattr(cfg, f, float(val))
        else:
            field_type = cfg.__dataclass_fields__[f].type
            if field_type is str or field_type == "str":
                setattr(cfg, f, val)


@dataclass
class MuscalConfig:
    mode: DeploymentMode = DeploymentMode.LOCAL_DEV
    storage_path: str = "storage"
    memory_db: str = "storage/memory.db"  # DEPRECATED (ADR-010): use DB_PATH from config.py instead
    log_file: str = "storage/logs.jsonl"
    snapshot_file: str = "storage/kernel_snapshot_v0.1.json"
    enable_graph: bool = True
    enable_sphere: bool = True
    enable_system_runtime: bool = True
    enable_browser: bool = False
    enable_desktop: bool = False
    verbose_logging: bool = False
    max_rag_results: int = 3
    boot_timeout: float = 30.0
    health_check_interval: float = 5.0
    simulation_mode: bool = False
    allowed_shell_patterns: List[str] = field(default_factory=lambda: [
        "python3 *", "ls *", "cat *", "echo *", "mkdir *", "cp *", "mv *"
    ])
    denied_shell_patterns: List[str] = field(default_factory=lambda: [
        "rm -rf /", "sudo *", "chmod 777 *", "dd *", "> /dev/*", "mkfs*", "fdisk*"
    ])
    sphere_ring_capacity: Dict[str, int] = field(default_factory=lambda: {
        "inner": 5, "middle": 20, "outer": 100
    })


def load_config(mode: str = "", overrides: Optional[Dict[str, Any]] = None) -> MuscalConfig:
    env_mode = os.environ.get("MUSCAL_MODE", "")
    resolved = env_mode or mode or "local_dev"
    raw = _ENV_MODE_MAP.get(resolved, DeploymentMode.LOCAL_DEV)

    configs: Dict[DeploymentMode, Dict[str, Any]] = {
        DeploymentMode.LOCAL_DEV: {
            "mode": DeploymentMode.LOCAL_DEV,
            "enable_browser": True,
            "enable_desktop": True,
            "verbose_logging": True,
            "boot_timeout": 60.0,
        },
        DeploymentMode.PRODUCTION: {
            "mode": DeploymentMode.PRODUCTION,
            "enable_browser": False,
            "enable_desktop": False,
            "verbose_logging": False,
            "boot_timeout": 10.0,
            "health_check_interval": 2.0,
        },
        DeploymentMode.SIMULATION: {
            "mode": DeploymentMode.SIMULATION,
            "enable_browser": True,
            "enable_desktop": True,
            "verbose_logging": True,
            "simulation_mode": True,
            "boot_timeout": 30.0,
        },
    }

    cfg = MuscalConfig(**configs[raw])
    _apply_env_overrides(cfg)
    if overrides:
        for k, v in overrides.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
    return cfg
