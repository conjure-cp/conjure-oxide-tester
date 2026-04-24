# settings.py

import json
import shutil
import subprocess
from pathlib import Path


class Settings:
    def __init__(self, config_path: str = "settings.json"):
        """Loads configuration from the specified JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file '{config_path}' not found.")

        with config_file.open("r", encoding="utf-8") as f:
            settings = json.load(f)

        self.runner_commands = settings.get("runner_commands", {})
        self.db_path = settings.get("outfile", "results.db")

        # runsolver config
        runsolver_cfg = settings.get("runsolver_cfg", {})
        self.wall = runsolver_cfg.get("walltime", 3600)
        self.cpus = runsolver_cfg.get("cpus", 1)
        self.mem = runsolver_cfg.get("memory", 8192)

        # Build the command string immediately upon initialization
        self.has_runsolver = self._check_runsolver()
        self.runsolver_cmd = self._build_runsolver_cmd()

    @staticmethod
    def _check_runsolver() -> bool:
        """Check if runsolver is available and works."""
        if shutil.which("runsolver") is None:
            return False
        try:
            # Simple test to see if it runs
            subprocess.run(
                "runsolver --version", shell=True, capture_output=True, check=True
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _build_runsolver_cmd(self) -> str:
        """Constructs the base runsolver command based on loaded limits."""
        if self.has_runsolver:
            return f"runsolver -R {self.mem} -C {self.cpus} -W {self.wall}"

        print(
            "Warning: 'runsolver' is not installed or broken. Running solvers directly without limits."
        )
        return ""


config = Settings("settings.json")
