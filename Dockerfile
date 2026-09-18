FROM python:3.12-slim
WORKDIR /app
# Copy requirements first: Docker caches each step, so dependencies are only
# reinstalled when this file changes, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 3000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3000"]
