seed:          # re‑creates tables + loads CSV_LIMIT rows
	docker compose exec web alembic upgrade head
	docker compose exec web python etl.py

reset:         # drop, recreate, reseed
	docker compose exec db psql -U postgres -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make seed