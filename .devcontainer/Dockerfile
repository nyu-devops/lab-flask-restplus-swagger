# Image for a Python 3 development environment
FROM rofrano/nyu-devops-base:sp25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install -U pip pipenv && \
    sudo pipenv install --system --dev

ENV PORT=8080
EXPOSE $PORT
