FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --upgrade pip && pip install . && apt-get update && apt-get install -y metasploit-framework nmap && rm -rf /var/lib/apt/lists/*
EXPOSE 8000
ENV OBLIVION_API_TOKEN=changeme
CMD ["oblivion", "api", "--dry-run"]