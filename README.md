# lab-flask-restplus-swagger

[![Build Status](https://travis-ci.org/nyu-devops/lab-flask-restplus-swagger.svg?branch=master)](https://travis-ci.org/nyu-devops/lab-flask-restplus-swagger)
[![Codecov](https://img.shields.io/codecov/c/github/nyu-devops/lab-flask-restplus-swagger.svg)]()

**NYU DevOps** lab that demonstrates how to use [Flask-RESTPlus](https://flask-restplus.readthedocs.io/en/stable/) to generate [Swagger](http://swagger.io)/[OpenAPI](https://www.openapis.org) documentation for your [Python](https://www.python.org) [Flask](http://flask.pocoo.org) application. This repository is part of lab for the NYU DevOps class [CSCI-GA.3033-014](http://cs.nyu.edu/courses/fall17/CSCI-GA.3033-014/) for Fall 2017.

## Introduction

When developing microservices with API's that others are going to call, it is critically important to provide the proper API documentation. OpenAPI has become a standard for documenting APIs and Swagger is an implementation of this. This lab shows you how to use a Flask plug-in called **Flask-RESTPlus** to imbed Swagger documentation into your Python Flask microservice so that the Swagger docs are generated for you.

I feel that it is much better to include the documentation with the code because programmers are more likely to update the docs if it's right there above the code they are working on. (...at least that's the therory and I'm sticking to it) ;-)

## Prerequisite Installation using Vagrant

The easiest way to use this lab is with Vagrant and VirtualBox. if you don't have this software the first step is down download and install it.

Download [VirtualBox](https://www.virtualbox.org/)

Download [Vagrant](https://www.vagrantup.com/)

Then all you have to do is clone this repo and invoke vagrant:

```shell
    git clone https://github.com/nyu-devops/lab-flask-restplus-swagger.git
    cd lab-flask-restplus-swagger
    vagrant up
    vagrant ssh
    cd /vagrant
```

## Prerequisite Installation using Virtualenv

Since this lab has no database (it's just an in memory array) you can use **Virtualenv** to setup your Python environment instead of **Vagrant**.

**Note:** _If you are using a Mac, this will work right out-of-the-box becasue the Mac has everything you need to do software development right from Apple. If you are using Windows, you will need to install [Python 2.7](https://www.python.org/downloads/release/python-2712/) and `pip` first becasue Windows does not ship with any development tools. :( I strongly recommend that Windows users use the Vagrant approach above._

To use `virtualenv` follow these commands:

If you don't already have `virtualenv` you must install it at least once:

```shell
    pip install virtualenv
```

To create a virtual environment to run the code use the following:

```shell
    git clone https://github.com/nyu-devops/lab-flask-restplus-swagger.git
    cd lab-flask-restplus-swagger
    virtualenv venv
    source venv/bin/activate
    pip install -r requirements.txt
```

That will install all of the required Python packages using `pip` into a virtual environment that isolates any library conflicts.

You can deactivate the virtual environment at any time with the command:

    deactivate

To `activate` the virtual envirnment again just change into the directory and use:

    source venv/bin/activate

If you ever run the server or the tests and you are getting an error that packages are not found, check to make sure that you have activated the virtual environment.

## Running the code

You can now run `nosetests` to run the tests and make sure that everything works as expected.

    nosetests
    coverage report -m

You can then run the server with:

    python run.py

Finally you can see the microservice Swagger docs at: [http://localhost:5000/](http://localhost:5000/)

When you are done, you can exit and shut down the VM with:

    exit
    vagrant halt

If the VM is no longer needed you can remove it with:

    vagrant destroy


## What's featured in the project?

    * app/service.py -- the main Service using Python Flask-RESTPlus for Swagger
    * app/models.py -- a Pet model that uses Redis for persistence
    * tests/test_server.py -- test cases using unittest for the microservice
    * tests/test_pets.py -- test cases using unittest for the Pet model
