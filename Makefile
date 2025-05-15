up:
	docker-compose up --build

down:
	docker-compose down

lint:
	flake8 .

format:
	black .

test:
	pytest

client:
	python client/client.py
