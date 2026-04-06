FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Install the package itself so [project.scripts] entry points are registered.
# This makes "serve" = "server.app:main" discoverable by openenv validate.
RUN pip install --no-cache-dir -e .

EXPOSE 7860

ENV PYTHONUNBUFFERED=1
ENV PORT=7860
ENV PYTHONPATH=/app

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "30", "server.app:app"]
