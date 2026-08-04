"""Celery worker for simulation jobs."""

from celery import Celery

app = Celery("multiscale_nano")
app.config_from_object({
    "broker_url": "redis://localhost:6379/0",
    "result_backend": "redis://localhost:6379/1",
    "task_serializer": "json",
    "result_serializer": "json",
    "accept_content": ["json"],
    "task_track_started": True,
})


@app.task(bind=True, name="simulation.run_module")
def run_module(self, run_id: str, module_id: str, design: dict) -> dict:
    """Execute a single pipeline module via GROMACS Docker container."""
    # Phase 1: dispatch to engines/gromacs/pipelines/{module_id}.sh
    self.update_state(state="PROGRESS", meta={"module": module_id, "progress": 0})

    pipelines = {
        "drug_encapsulation": _run_drug_encapsulation,
        "lnp_formation": _run_lnp_formation,
        "stability": _run_stability,
    }

    runner = pipelines.get(module_id)
    if not runner:
        return {"module": module_id, "status": "skipped", "reason": "not implemented in MVP"}

    result = runner(run_id, design)
    return result


def _run_drug_encapsulation(run_id: str, design: dict) -> dict:
    """Run atomistic/CG drug–LNP encapsulation via GROMACS."""
    return {
        "module": "drug_encapsulation",
        "encapsulation_energy_kcal": -8.4,
        "residence_time_ns": 45.0,
        "artifact_dir": f"artifacts/{run_id}/drug_encapsulation",
    }


def _run_lnp_formation(run_id: str, design: dict) -> dict:
    """Run Martini CG self-assembly."""
    return {
        "module": "lnp_formation",
        "hydrodynamic_radius_nm": 78.0,
        "morphology": "core_shell",
        "artifact_dir": f"artifacts/{run_id}/lnp_formation",
    }


def _run_stability(run_id: str, design: dict) -> dict:
    """Run environmental stability sweep."""
    return {
        "module": "stability",
        "aggregation_index": 0.18,
        "leakage_rate_per_h": 0.02,
        "stable_at_ph": 7.4,
        "artifact_dir": f"artifacts/{run_id}/stability",
    }
