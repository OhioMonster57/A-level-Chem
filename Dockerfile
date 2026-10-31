FROM python:3.12-slim
RUN apt-get update && apt-get install --no-install-recommends --yes poppler-utils && rm -rf /var/lib/apt/lists/*
RUN useradd --create-home --uid 10001 appuser
WORKDIR /app
COPY --chown=appuser:appuser server.py grading.py work_store.py ./
COPY --chown=appuser:appuser app ./app
USER appuser
EXPOSE 3000
CMD ["python3", "server.py"]
