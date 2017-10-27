[![Code Climate](https://codeclimate.com/github/failmap/admin/badges/gpa.svg)](https://codeclimate.com/github/failmap/admin) [![Build Status](https://travis-ci.org/failmap/admin.svg?branch=master)](https://travis-ci.org/failmap/admin) [![Test Coverage](https://codeclimate.com/github/failmap/admin/badges/coverage.svg)](https://codeclimate.com/github/failmap/admin/coverage)

# Support fail map
We keep organizations on their toes to protect everyone's data. Do you like this? Your donation insures continuous support, updates,
and new features.

The Internet Cleanup Foundation helps cleaning up bad stuff on the web.

Donate to this project safely, easily and quickly by clicking on an amount below.

<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/5" target="_blank">&euro;5</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/10" target="_blank">&euro;10</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/25" target="_blank">&euro;20</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/50" target="_blank">&euro;50</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/100" target="_blank">&euro;100</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/200" target="_blank">&euro;200</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa/500" target="_blank">&euro;500</a>
<a href="https://useplink.com/payment/qaCyn8t6Tar7c5zVS6Fa" target="_blank">&euro;other</a>

# System requirements
Linux or MacOS capable of running Python3 and git.

# Software Requirements

Download and install below system requirements to get started:

- [git](https://git-scm.com/downloads) (download and install)
- [python3](https://www.python.org/downloads/) (download and install)
- [direnv](https://direnv.net/) (download and install, then follow [setup instructions](https://direnv.net/))
- [rabbitmq](http://www.rabbitmq.com/download.html) (for scanners only, download and install)

After installation of above tools, all following steps use the command line:

    sudo easy_install pip  # installs pip, a python package manager, with the command pip3


# Obtaining the software

In a directory of your choosing:

    # download the software
    git clone --recursive https://github.com/failmap/admin/

    # enter the directory of the downloaded software
    cd admin

    # sets Debug to true in this folder. Do not change the settings.py file.
    direnv allow

# Quickstart

Below commands result in a failmap installation that is suitable for testing and development. It is
capable of handling thousands of urls and still be modestly responsive.

If you need a faster, more robust installation, please [contact us](mailto:hosting@internetcleanup.foundation).

    # download even more requirements needed to run this software
    pip3 install -e .

    # creates the database
    failmap-admin migrate

    # create a user to view the admin interface
    failmap-admin createsuperuser

    # loads a series of sample data into the database
    failmap-admin load-dataset testdata

    # calculate the scores that should be displayed on the map
    failmap-admin rebuild-ratings

    # finally start the development server
    failmap-admin runserver

Now visit the [map website](http://127.0.0.1:8000/) and/or the
[admin website](http://127.0.0.1:8000/admin/) at http://127.0.0.1:8000

# Scanning services (beta)

Todo: add celery beat information

Some scanners require RabbitMQ to be installed. We're currently in transition from running scanners
manually to supporting both manual scans and celery beat.

Each of the below commands requires their own command line window:

    # start rabbitmq
    rabbitmq-server

    # start a worker
    failmap-admin celery worker -ldebug

These services help fill the database with accurate up to date information. Run each one of them in
a separate command line window and keep them running.

    # handles all new urls with an initial (fast) scan
    failmap-admin onboard-service

    # slowly gets results from qualys
    failmap-admin scan-tls-qualys-service

    # makes many gigabytes of screenshots
    failmap-admin screenshot-service

# Using the software

## The map website

The website is the site intended for humans. There are some controls on the website, such as the
time slider, twitter links and the possibilities to inspect organizations by clicking on them.

Using the map website should be straightforward.

## The admin website

Use the admin website to perform standard [data-operations](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete),
run a series of actions on the data and read documentation of the internal workings of the failmap software.

The admin website is split up in four key parts:
1. Authentication and Authorization
This stores information about who can enter the admin interface and what they can do.

2. Map
Contains all information that is presented to normal humans.
This information is automatically filled based on the scans that have been performed over time.

3. Organizations
Lists of organizations, coordinates and internet adresses.

4. Scanners
Lists of endpoints and assorted scans on these endpoints.


# Troubleshooting getting started

If you need a specific branch, for example "mapwebsite"

    git checkout mapwebsite

This repository uses [submodules](https://git-scm.com/docs/git-submodule) to pull in
external dependencies. If you have not cloned the repository with `--recursive` or you need to
restore the submodules to the expected state run:

    git submodule update

# Development

## Code quality / Testing

This project sticks to default pycodestyle/pyflakes configuration to maintain code quality.

To run code quality checks and unit tests run:

    tox

To make life easier you can use `autopep8`/`isort` before running `tox` to automatically fix most style issues:

    tox -e autofix

To run only a specific test use:

    tox -- -k test_name

To only run a specific test suite user for example:

    .tox/py34/bin/failmap-admin test tests/test_smarturl.py

To generate coverage report after tests in HTML run:

    coverage html
    open htmlcov/index.html

Pytest allows to drop into Python debugger when a tests fails. To enable run:

    tox -- --pdb

## Direnv / Virtualenv

This project has [direnv](https://direnv.net/) configuration to automatically manage the Python
virtual environment. Install direnv and run `direnv allow` to enable.

Alternatively you can manually create a virtualenv using:

    virtualenv venv

Be sure to active the environment before starting development every time:

    . venv/bin/activate
    export DEBUG=1

# Versioning

Version for the project is losely semver with no specific release schedule or meaning to version numbers (eg: stable/unstable).

Formal releases are created by creating a Git tag with the desired version number. These tags will trigger automated builds which will release the specified code under that version. Tags can be pushed from a local repository or created through the Gitlab interface: https://gitlab.com/failmap/admin/tags/new

Informal releases are created by new commits pushed/merged to the master. The version number of the last formal release will be suffixed with the current short Git SHA.

For all releases artifacts will be created. Currently only Docker containers are pushed into the [registry](https://gitlab.com/failmap/admin/container_registry). Each artifact will be tagged with the appropriate version (formal or informal). Where needed abstract tags will also be created/updated for these artifacts (eg: Docker build/staging/latest tags).

For local development informal release or a special `dev0` build release is used which indicates a different state from the formal releases.

# Thanks to
This project is being maintained by the [Internet Cleanup Foundation](https://internetcleanup.foundation).
Special thanks to the SIDN Fonds for believing in this method of improving privacy.

Thanks to the many authors contributing to open software.
