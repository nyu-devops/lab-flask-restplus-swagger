# Image for a Python 3 development environment
FROM rofrano/nyu-devops-base:sp25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN python -m pip install -U pip pipenv && \
    pipenv install --system --dev

ENV PORT=8080
EXPOSE $PORT

# Enable color terminal for docker exec bash
ENV TERM=xterm-256color

# Become a regular user
USER $USERNAME