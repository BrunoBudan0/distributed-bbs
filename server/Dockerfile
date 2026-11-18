FROM python:3.13-slim AS unit-tests

WORKDIR /app

COPY requirements.txt requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt

COPY database ./database
COPY src ./src
COPY tests ./tests
RUN PYTHONPATH=src python -m pytest -q tests && touch /unit-tests-passed

FROM python:3.13-slim

RUN useradd --create-home bbs

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=unit-tests /unit-tests-passed /unit-tests-passed
COPY database ./database
COPY src ./src

RUN mkdir /data && chown bbs:bbs /data

USER bbs

CMD ["python", "src/app.py"]
