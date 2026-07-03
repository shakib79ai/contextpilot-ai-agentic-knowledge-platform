from app.celery_app import celery_app


@celery_app.task(name="app.tasks.evaluation.run_eval_set_task")
def run_eval_set_task(dataset_path: str) -> dict:
    from evals.run_eval import run_eval

    return run_eval(dataset_path)
