# Image for a Python 3 development environment
FROM rofrano/nyu-devops-base:su26

# Install GitHub CLI
RUN sudo apt-get update && sudo apt-get install -y gh

# Install claude code
RUN curl -fsSL https://claude.ai/install.sh | bash
# Setup Claude Code environment
ENV ANTHROPIC_BASE_URL="http://host.docker.internal:11434" \
    ANTHROPIC_AUTH_TOKEN="ollama" \
    ANTHROPIC_API_KEY=""

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install -U pip pipenv && \
    sudo pipenv install --system --dev

ENV PORT=8080
EXPOSE $PORT
