FROM python:3.11-slim

# Установка системных зависимостей и линтеров для других языков
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    nodejs \
    npm \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ESLint для JavaScript/TypeScript
RUN npm install -g eslint

# Go (staticcheck)
RUN curl -sSfL https://install.golangci.com | sh -s -- -b /usr/local/bin v1.54.2 \
    || echo "staticcheck будет недоступен для Go-файлов"

# Rust (clippy — через rustup)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y \
    && /root/.cargo/bin/rustup component add clippy \
    || echo "clippy будет недоступен для Rust-файлов"

# hadolint (Dockerfile линтер)
RUN curl -sSfL https://github.com/hadolint/hadolint/releases/latest/download/hadolint-Linux-x86_64 -o /usr/local/bin/hadolint \
    && chmod +x /usr/local/bin/hadolint \
    || echo "hadolint будет недоступен"

# kubeval (Kubernetes манифесты)
RUN curl -sSfL https://github.com/instrumenta/kubeval/releases/latest/download/kubeval-linux-amd64.tar.gz | tar xz -C /usr/local/bin \
    && chmod +x /usr/local/bin/kubeval \
    || echo "kubeval будет недоступен"

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
