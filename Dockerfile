FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# server/app.py is the canonical app location required by the evaluator.
# PYTHONPATH=. ensures "from env import ..." etc. resolve from /app (the root).
ENV PYTHONPATH=/app

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--timeout", "30", "server.app:app"]
