.PHONY: migrate server dramatiq test

migrations:
	python3 manage.py makemigrations

migrate:
	python3 manage.py migrate

server:
	python3 manage.py runserver

shell:
	python3 manage.py shell

dramatiq:
ifeq ($(UNAME), Windows)
	venv\Scripts\activate.bat; \
	python3 manage.py rundramatiq;
else
	. .venv/bin/activate; \
	python3 manage.py rundramatiq;
endif

test:
	pytest -v

test-voice:
	pytest booking_api/voice/tests/ -v

test-cov:
	pytest --cov=booking_api.voice --cov-report=term-missing
