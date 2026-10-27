FROM python:3.11.15-slim-bookworm@sha256:d29f48a31a8b408ed19272ca1e7b10ebae13b240a27e862d3d4217c528e2e0c3
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.lock .
RUN python -m pip install --no-cache-dir -r requirements.lock && \
    groupadd --gid 10001 portal && useradd --uid 10001 --gid portal portal && \
    mkdir -p /data/uploads && chown -R portal:portal /data
COPY --chown=portal:portal main.py ./
COPY --chown=portal:portal app ./app
USER 10001:10001
EXPOSE 8007
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007", "--no-access-log"]
