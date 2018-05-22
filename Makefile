#
# building
#

.PHONY: build build_web build_db \
	run_db run_web run


build: docker-compose.yml Dockerfile.web Dockerfile.db requirements.txt
	docker-compose build
	touch .built_web
	touch .built_db

build_web: .built_web

build_db: .built_db

.built_web: docker-compose.yml Dockerfile.web requirements.txt
	docker-compose build web
	touch .built_web

.built_db: docker-compose.yml Dockerfile.db
	docker-compose build db
	touch .built_db

#
# running
# 

# run the postgresql docker image
run_db: .built_db
	docker-compose run db

run_web: .built_web
	docker-compose run web

run: .built_db .built_web
	docker-compose up

run_dev: .built_web
	docker-compose run \
		--volume `pwd`/downloads:/meteomap/downloads \
		--volume `pwd`/logs:/meteomap/logs \
		--user `id -u`:`id -g` \
		web bash
