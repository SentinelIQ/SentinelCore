FROM python:3.13-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para alguns pacotes Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential weasyprint git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install "poetry>=2.0.0"

# Copy the poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Configure Poetry to not create a virtual environment
RUN poetry config virtualenvs.create false

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-root


# Copy the rest of the application
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "sentineliq.wsgi:application"] 