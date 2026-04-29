Contributing Guide
==================

Welcome! There are many ways to contribute, including submitting bug
reports, improving documentation, submitting feature requests, reviewing
new submissions, or contributing code that can be incorporated into the
project.

Review process
--------------

For any **significant** changes please create a new GitHub issue and
enhancements that you wish to make. Describe the feature you would like
to see, why you need it, and how it will work. Discuss your ideas
transparently and get community feedback before proceeding.

Small changes can directly be crafted and submitted to the GitHub
Repository as a Pull Request. This requires creating a **repo fork** using
`instruction <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_.

Important notes
---------------

Please take into account that:

* Some companies still use old Spark versions, like 3.2.0. So it is required to keep compatibility if possible, e.g. adding branches for different Spark versions.
* Different users uses onETL in different ways - some uses only DB connectors, some only files. Connector-specific dependencies should be optional.
* Instead of creating classes with a lot of different options, prefer splitting them into smaller classes, e.g. options class, context manager, etc, and using composition.

Initial setup for local development
-----------------------------------

Install Git
~~~~~~~~~~~

Please follow `instruction <https://docs.github.com/en/get-started/quickstart/set-up-git>`_.

Clone the repo
~~~~~~~~~~~~~~

Open terminal and run these commands to clone a **forked** repo:

.. code:: bash

    git clone git@github.com:myuser/onetl.git -b develop

    cd onetl

Enable pre-commit hooks
~~~~~~~~~~~~~~~~~~~~~~~

Create virtualenv and install dependencies:

.. code:: bash

    make venv-install

Install pre-commit hooks:

.. code:: bash

    prek install --install-hooks

Test pre-commit hooks run:

.. code:: bash

    prek run

How to
------

Run tests locally
~~~~~~~~~~~~~~~~~

.. note::

    You can skip this if only documentation is changed.

Setup environment
^^^^^^^^^^^^^^^^^

Create virtualenv and install dependencies:

.. code:: bash

    make venv-install

Using docker-compose
^^^^^^^^^^^^^^^^^^^^

Build image for running tests:

.. code:: bash

    docker-compose build

Start all containers with dependencies:

.. code:: bash

    docker-compose --profile all up -d

You can run limited set of dependencies:

.. code:: bash

    docker-compose --profile mongodb up -d

Run tests:

.. code:: bash

    docker-compose run --rm onetl pytest

You can pass additional arguments, they will be passed to pytest:

.. code:: bash

    docker-compose run --rm onetl pytest -m mongodb -lsx -vvvv --log-cli-level=INFO

You can run interactive bash session and use it:

.. code:: bash

    docker-compose run --rm onetl bash

    pytest -m mongodb -lsx -vvvv --log-cli-level=INFO

See logs of test container:

.. code:: bash

    docker-compose logs -f onetl

Stop all containers and remove created volumes:

.. code:: bash

    docker-compose --profile all down -v

Without docker-compose
^^^^^^^^^^^^^^^^^^^^^^

.. warning::

    To run HDFS tests locally you should add the following line to your ``/etc/hosts`` (file path depends on OS):

    .. code::

        # HDFS server returns container hostname as connection address, causing error in DNS resolution
        127.0.0.1 hdfs

.. note::

    To run Oracle tests you need to install `Oracle instantclient <https://www.oracle.com/database/technologies/instant-client.html>`__,
    and pass its path to ``ONETL_ORA_CLIENT_PATH`` and ``LD_LIBRARY_PATH`` environment variables,
    e.g. ``ONETL_ORA_CLIENT_PATH=/path/to/client64/lib``.

    It may also require to add the same path into ``LD_LIBRARY_PATH`` environment variable

.. note::

    To run Greenplum tests, you should:

    * Download `VMware Greenplum connector for Spark <https://onetl.readthedocs.io/en/latest/connection/db_connection/greenplum/prerequisites.html>`_
    * Either move it to ``~/.ivy2/jars/``, or pass file path to ``CLASSPATH``
    * Set environment variable ``ONETL_GP_PACKAGE_VERSION=local``.

Start all containers with dependencies:

.. code:: bash

    docker-compose --profile all up -d

You can run limited set of dependencies:

.. code:: bash

    docker-compose --profile mongodb up -d

Run core tests:

.. code:: bash

    make test-core

Run specific connection tests:

.. code:: bash

    make test-spark PYTEST_ARGS="-m mongodb"
    make test-no-spark PYTEST_ARGS="-m ftp"

You can pass additional arguments, they will be passed to pytest:

.. code:: bash

    make test-spark PYTEST_ARGS="-m mongodb -lsx -vvvv --log-cli-level=INFO"

Stop all containers and remove created volumes:

.. code:: bash

    docker-compose --profile all down -v


Build documentation
~~~~~~~~~~~~~~~~~~~

.. note::

    You can skip this if only source code behavior remains the same.

Create virtualenv and install dependencies:

.. code:: bash

    make venv-install

Build documentation using Sphinx:

.. code:: bash

    make docs-serve

Then open in browser ``http://localhost:8000/``.


Create pull request
~~~~~~~~~~~~~~~~~~~

Commit your changes:

.. code:: bash

    git commit -m "Commit message"
    git push

Then open Github interface and `create pull request <https://docs.github.com/en/get-started/quickstart/contributing-to-projects#making-a-pull-request>`_.
Please follow guide from PR body template.

After pull request is created, it get a corresponding number, e.g. 123 (``pr_number``).

Write release notes
~~~~~~~~~~~~~~~~~~~

``onETL`` uses `towncrier <https://pypi.org/project/towncrier/>`_
for changelog management.

To submit a change note about your PR, add a text file into the
`docs/changelog/next_release <./next_release>`_ folder. It should contain an
explanation of what applying this PR will change in the way
end-users interact with the project. One sentence is usually
enough but feel free to add as many details as you feel necessary
for the users to understand what it means.

**Use the past tense** for the text in your fragment because,
combined with others, it will be a part of the "news digest"
telling the readers **what changed** in a specific version of
the library *since the previous version*.

Finally, name your file following the convention that Towncrier
understands: it should start with the number of an issue or a
PR followed by a dot, then add a patch type, like ``feature``,
``doc``, ``misc`` etc., and add ``.md`` as a suffix. If you
need to add more than one fragment, you may add an optional
sequence number (delimited with another period) between the type
and the suffix.

In general the name will follow ``<pr_number>.<category>.md`` pattern,
where the categories are:

- ``feature``: Any new feature
- ``bugfix``: A bug fix
- ``improvement``: An improvement
- ``doc``: A change to the documentation
- ``dependency``: Dependency-related changes
- ``misc``: Changes internal to the repo like CI, test and build changes

A pull request may have more than one of these components, for example
a code change may introduce a new feature that deprecates an old
feature, in which case two fragments should be added. It is not
necessary to make a separate documentation fragment for documentation
changes accompanying the relevant code changes.

Examples for adding changelog entries to your Pull Requests
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: markdown
    :caption: mddocs/docs/changelog/next_release/2345.bugfix.md

    Fixed behavior of `WebDAV` connector

.. code-block:: markdown
    :caption: mddocs/docs/changelog/next_release/3456.feature.md

    Added support of `timeout` in ``S3`` connector

.. tip::

    See `pyproject.toml <pyproject.toml>`_ for all available categories
    (``tool.towncrier.type``).

.. _Towncrier philosophy:
    https://towncrier.readthedocs.io/en/stable/#philosophy

How to skip change notes check?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Just add ``ci:skip-changelog`` label to pull request.

Release Process
---------------

.. note::

    This is for repo maintainers only

Before making a release from the ``develop`` branch, follow these steps:

1. Checkout to ``develop`` branch and update it to the actual state

.. code:: bash

    git checkout develop
    git pull -p

2. Get current release version

.. code:: bash

    VERSION=$(cat onetl/VERSION)

3. Build changelog for current release

.. code:: bash

    make docs-generate-changelog

4. Commit and push changes to ``develop`` branch

.. code:: bash

    git add .
    git commit -m "Prepare for release ${VERSION}"
    git push

5. Merge ``develop`` branch to ``master``, **WITHOUT** squashing

.. code:: bash

    git checkout master
    git pull
    git merge develop
    git push

6. Add git tag to the latest commit in ``master`` branch

.. code:: bash

    git tag "$VERSION"
    git push origin "$VERSION"

7. Update version in ``develop`` branch **after release**:

.. code:: bash

    git checkout develop

    NEXT_VERSION=$(echo "$VERSION" | awk -F. '/[0-9]+\./{$NF++;print}' OFS=.)
    echo "$NEXT_VERSION" > onetl/VERSION

    git add .
    git commit -m "Bump version"
    git push
