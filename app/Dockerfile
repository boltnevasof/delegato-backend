FROM python:3.12-slim AS builder

RUN pip install --no-cache-dir poetry==1.8.4

WORKDIR /build
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root --only main

FROM python:3.12-slim

ARG TARGETARCH

# Terraform + Ansible (needed by ProvisioningService)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl unzip openssh-client \
    && curl -fsSL "https://releases.hashicorp.com/terraform/1.5.7/terraform_1.5.7_linux_${TARGETARCH}.zip" \
        -o /tmp/terraform.zip \
    && unzip /tmp/terraform.zip -d /usr/local/bin/ \
    && rm /tmp/terraform.zip \
    && pip install --no-cache-dir ansible-core \
    && apt-get purge -y unzip \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
