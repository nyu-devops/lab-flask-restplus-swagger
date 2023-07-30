# lab-flask-restplus-swagger

[![Build Status](https://travis-ci.org/nyu-devops/lab-flask-restplus-swagger.svg?branch=master)](https://travis-ci.org/nyu-devops/lab-flask-restplus-swagger)
[![Codecov](https://img.shields.io/codecov/c/github/nyu-devops/lab-flask-restplus-swagger.svg)]()

**NYU DevOps** lab that demonstrates how to use [Flask-RESTX](https://flask-restx.readthedocs.io/en/latest/) to generate [Swagger](http://swagger.io)/[OpenAPI](https://www.openapis.org) documentation for your [Python](https://www.python.org) [Flask](http://flask.pocoo.org) application. This repository is part of lab for the NYU DevOps class [CSCI-GA.2820-001](https://cs.nyu.edu/courses/spring21/CSCI-GA.2820-001/), Graduate Division, Computer Science

## Introduction

When developing microservices with API's that others are going to call, it is critically important to provide the proper API documentation. OpenAPI has become a standard for documenting APIs and Swagger is an implementation of this. This lab shows you how to use a Flask plug-in called **Flask-RESTX** which is a fork of the original **Flask-RESTPlus** that is no longer maintained, to imbed Swagger documentation into your Python Flask microservice so that the Swagger docs are generated for you.

I feel that it is much better to include the documentation with the code because programmers are more likely to update the docs if it's right there above the code they are working on. (...at least that's the therory and I'm sticking to it) ;-)

## Prerequisite Installation using Vagrant

The easiest way to use this lab is with Vagrant and VirtualBox. If you don't have this software the first step is down download and install it. If you have an 2020 Apple Mac with the M1 chip, you should download Docker Desktop instead of VirtualBox. Here is what you need:

Download: [Vagrant](https://www.vagrantup.com/)

Intel Download: [VirtualBox](https://www.virtualbox.org/)

Apple M1 Download: [Apple M1 Tech Preview](https://docs.docker.com/docker-for-mac/apple-m1/)

Install each of those. Then all you have to do is clone this repo and invoke vagrant:

### Using Vagrant and VirtualBox (Intel only)

If you have an Intel Mac or Windows PC you can use these steps:

```bash
$ git clone https://github.com/nyu-devops/lab-flask-restplus-swagger.git
$ cd lab-flask-restplus-swagger
$ vagrant up
$ vagrant ssh
$ cd /vagrant
```

### Using Vagrant and Docker Desktop

If you have an Apple M1 Silicon Mac or other ARM
based computer, or if you just want to use Docker as a provider instead of VirtualBox, you can use these steps:

This is useful for owners of Apple M1 Silicon Macs which cannot run VirtualBox because they have a CPU based on ARM architecture instead of Intel.

Just add `--provider docker` to the `vagrant up` command like this:

```bash
$ git clone https://github.com/nyu-devops/lab-flask-restplus-swagger.git
$ cd lab-flask-restplus-swagger
$ vagrant up --provider docker
$ vagrant ssh
$ cd /vagrant
```

This will use a Docker container instead of a Virtual Machine (VM). Everything else should be the same.

## Running the code

You can now run `green` to run the tests and make sure that everything works as expected.

```bash
$ green
```

You can then run the server with:

```bash
$ honcho start
```

Finally you can see the microservice Swagger docs at: [http://localhost:8080/](http://localhost:8080/)

When you are done, you can exit and shut down the VM with:

```bash
$ exit
$ vagrant halt
```

If the VM is no longer needed you can remove it with:

```bash
$ vagrant destroy
```

## What's featured in the project?

    * service/routes.py -- the main Service using Python Flask-RESTX for Swagger
    * service/models.py -- a Pet model that uses Cloudant for persistence
    * tests/test_routes.py -- test cases using unittest for the microservice
    * tests/test_models.py -- test cases using unittest for the Pet model

This repository is part of the NYU graduate class **CSCI-GA.2810-001: DevOps and Agile Methodologies** taught by [John Rofrano](http://www.johnrofrano.com/), Adjunct Instructor, NYU Curant Institute, Graduate Division, Computer Science and at Stern Business School.
