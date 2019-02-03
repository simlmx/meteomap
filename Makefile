#
# building
#

.PHONY: build build_web build_db run_db run_web run run_exec_web

USER = --user `id -u`:`id -g`


build: docker-compose.yml Dockerfile.web Dockerfile.db requirements.txt
	docker-compose build

build_web:
	docker-compose build web

build_db:
	docker-compose build db

#
# running
# 

# run the postgresql docker image
run_db:
	docker-compose run db

run_web:
	docker-compose run web $(USER)

run:
	docker-compose up

run_exec_web:
	docker-compose exec $(USER) web bash
