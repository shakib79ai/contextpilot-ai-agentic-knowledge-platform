.PHONY: up down logs migrate backend-shell eval test

up:
	docker-compose up --build

down:
	docker-compose down

logs:
	docker-compose logs -f

migrate:
	docker-compose exec backend alembic upgrade head

backend-shell:
	docker-compose exec backend bash

eval:
	docker-compose exec backend python -m evals.run_eval --dataset ../evals/test_cases/sample_eval_set.jsonl

test:
	cd backend && pytest ../tests -q
