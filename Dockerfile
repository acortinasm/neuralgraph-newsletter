FROM python:3.13-slim

WORKDIR /app

# Install git for pip install from GitHub
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*

# Install neuralgraph driver from GitHub
RUN pip install --no-cache-dir git+https://github.com/acortinasm/neuralgraph.git#subdirectory=drivers/python

# Install dependencies
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pydantic-settings resend python-dotenv "email-validator>=2.3.0" "markdown>=3.10.2"

# Copy application code
COPY main.py auth.py config.py database.py models.py ./
COPY routers/ routers/
COPY services/ services/

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
