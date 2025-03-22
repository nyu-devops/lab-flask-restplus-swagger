# lab-flask-restplus-swagger

[![Build Status](https://github.com/nyu-devops/lab-flask-restplus-swagger/actions/workflows/build.yml/badge.svg)](https://github.com/nyu-devops/lab-flask-restplus-swagger/actions)
[![codecov](https://codecov.io/gh/nyu-devops/lab-flask-restplus-swagger/branch/master/graph/badge.svg?token=y6OUlCB4bC)](https://codecov.io/gh/nyu-devops/lab-flask-restplus-swagger)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-red.svg)](https://www.python.org/)
[![Open in Remote - Containers](https://img.shields.io/static/v1?label=Remote%20-%20Containers&message=Open&color=blue&logo=visualstudiocode)](https://vscode.dev/redirect?url=vscode://ms-vscode-remote.remote-containers/cloneInVolume?url=https://github.com/nyu-devops/lab-flask-restplus-swagger)

**NYU DevOps** lab that demonstrates how to use [Flask-RESTX](https://flask-restx.readthedocs.io/en/latest/) to generate [Swagger](http://swagger.io)/[OpenAPI](https://www.openapis.org) documentation for your [Python](https://www.python.org) [Flask](http://flask.pocoo.org) application. This repository is part of lab for the NYU DevOps class [CSCI-GA.2820-001](https://cs.nyu.edu/courses/spring21/CSCI-GA.2820-001/), Graduate Division, Computer Science

## Introduction

When developing microservices with API's that others are going to call, it is critically important to provide the proper API documentation. OpenAPI has become a standard for documenting APIs and Swagger is an implementation of this. This lab shows you how to use a Flask plug-in called **Flask-RESTX** which is a fork of the original **Flask-RESTPlus** that is no longer maintained, to imbed Swagger documentation into your Python Flask microservice so that the Swagger docs are generated for you.

I feel that it is much better to include the documentation with the code because programmers are more likely to update the docs if it's right there above the code they are working on. (...at least that's the theory and I'm sticking to it) ;-)

### Prerequisite Installation

All of our development is done in Docker containers using **Visual Studio Code**. This project contains a `.devcontainer` folder that will set up a Docker environment in VSCode for you. You will need the following:

- Docker Desktop for [Mac](https://docs.docker.com/docker-for-mac/install/) or [Windows](https://docs.docker.com/docker-for-windows/install/)
- Microsoft Visual Studio Code ([VSCode](https://code.visualstudio.com/download))
- [Remote Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) VSCode Extension

It is a good idea to add VSCode to your path so that you can invoke it from the command line. To do this, open VSCode and type `Shift+Command+P` on Mac or `Shift+Ctrl+P` on Windows to open the command pallet and then search for "shell" and select the option **Shell Command: Install 'code' command in Path**. This will install VSCode in your path.

Then you can start your development environment up with:

```bash
    git clone https://github.com/nyu-devops/lab-flask-restplus-swagger.git
    cd lab-flask-restplus-swagger
    code .
```

The first time it will build the Docker image but after that it will just create a container and place you inside of it in your `/app` folder which actually contains the repo shared from your computer. It will also install all of the VSCode extensions needed for Python development.

If it does not automatically prompt you to open the project in a container, you can select the green icon at the bottom left of your VSCode UI and select: **Remote Containers: Reopen in Container**.

## Running the code

You can now run `pytest` to run the tests and make sure that everything works as expected.

```bash
make test
```

You can then run the server with:

```bash
honcho start
```

Finally you can see the microservice Swagger docs at: [http://localhost:8080/](http://localhost:8080/)

## What's featured in the project?

    * service/routes.py -- the main Service using Python Flask-RESTX for Swagger
    * service/models.py -- a Pet model that uses Cloudant for persistence
    * tests/test_routes.py -- test cases using unittest for the microservice
    * tests/test_models.py -- test cases using unittest for the Pet model

## License

Copyright (c) 2021, 2025 John Rofrano. All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the NYU graduate class **CSCI-GA.2810-001: DevOps and Agile Methodologies** taught by [John Rofrano](http://www.johnrofrano.com/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science and at Stern Business School.
