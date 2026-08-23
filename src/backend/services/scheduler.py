import asyncio
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.job import Job

from src.backend.services.workflow import marks_change_workflow

logger = logging.getLogger("scheduler")
logging.basicConfig(level=logging.INFO)

JOB_ID = "marks_change_workflow"

# Defense-in-depth against overlapping runs. APScheduler's own
# max_instances=1 (set below) already prevents the scheduler from
# starting a second run while one is in flight, but this lock also
# protects against any other code path calling the job function
# directly (e.g. a manual /run-now endpoint) while a scheduled run
# is still executing.
_run_lock = asyncio.Lock()

scheduler = AsyncIOScheduler(
    executors={"default": AsyncIOExecutor()},
    job_defaults={
        # Never run two instances of this job concurrently.
        "max_instances": 1,
        # If the scheduler was blocked (e.g. process was busy) and a
        # run is more than 60s late, skip it instead of firing a
        # burst of overdue runs back-to-back.
        "misfire_grace_time": 60,
        # Don't coalesce is default False anyway; being explicit.
        "coalesce": True,
    },
    timezone=timezone.utc,
)


async def _run_marks_change_workflow_job() -> None:
    """
    Wrapper around marks_change_workflow() that:
      - guarantees only one run executes at a time (extra safety
        beyond APScheduler's max_instances)
      - guarantees a single failing run (or an exception inside the
        workflow) can NEVER crash the scheduler or stop future runs
      - logs start/finish/duration/errors for observability
    """
    if _run_lock.locked():
        logger.warning(
            "[scheduler] Previous run of %s still in progress — "
            "skipping this tick.",
            JOB_ID,
        )
        return

    async with _run_lock:
        started_at = datetime.now(timezone.utc)
        logger.info("[scheduler] %s started at %s", JOB_ID, started_at.isoformat())

        try:
            await marks_change_workflow()
        except Exception:
            # Swallow the exception here on purpose: an unhandled
            # exception raised out of a scheduled job would otherwise
            # be logged by APScheduler but the important thing is it
            # must NEVER prevent the next scheduled tick from firing.
            logger.exception(
                "[scheduler] %s raised an unhandled exception", JOB_ID
            )
        finally:
            finished_at = datetime.now(timezone.utc)
            duration = (finished_at - started_at).total_seconds()
            logger.info(
                "[scheduler] %s finished at %s (took %.2fs)",
                JOB_ID,
                finished_at.isoformat(),
                duration,
            )


def start_scheduler() -> None:
    if scheduler.get_job(JOB_ID) is None:
        scheduler.add_job(
            _run_marks_change_workflow_job,
            trigger=IntervalTrigger(minutes=10),
            id=JOB_ID,
            replace_existing=True,
            next_run_time=datetime.now(timezone.utc),  # fire once immediately, then every 10 min
        )

    if not scheduler.running:
        scheduler.start()
        logger.info("[scheduler] Started — %s will run every 10 minutes.", JOB_ID)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[scheduler] Stopped.")


def get_job_status() -> dict:
    job: Job | None = scheduler.get_job(JOB_ID)
    return {
        "running": scheduler.running,
        "job_registered": job is not None,
        "next_run_time": job.next_run_time.isoformat() if job and job.next_run_time else None,
        "currently_executing": _run_lock.locked(),
    }
