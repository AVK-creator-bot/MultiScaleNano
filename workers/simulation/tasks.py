"""Celery worker for simulation jobs — disabled in production (mock results removed)."""

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
    raise NotImplementedError(
        "Legacy Celery/GROMACS worker is disabled. Use the OpenMM simulation_worker pipeline."
    )
