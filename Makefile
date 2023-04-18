all: down build up test
down:
	docker-compose down --remove-orphans
build:
	docker-compose build
up:
	docker-compose up -d api
test: up
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests

unit-test:
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit

integration-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/integration

e2e-tests: up
	docker-compose run --rm --no-deps --entrypoint=pytest api /tests/e2e

