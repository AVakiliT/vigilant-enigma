all: down build up test
down:
	docker-compose down --remove-orphans
build:
	docker-compose build
up:
	docker-compose up -d app
test: up
	docker-compose run --rm --no-deps --entrypoint=pytest app /tests