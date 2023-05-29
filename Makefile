.PHONY: migrate server start-dramatiq

migrate:
	python3 manage.py migrate

server:
	python3 manage.py runserver

start-dramatiq:
ifeq ($(UNAME), Windows)
	venv\Scripts\activate.bat; \
	python3 manage.py rundramatiq;
else
	. .venv/bin/activate; \
	python3 manage.py rundramatiq;
endif