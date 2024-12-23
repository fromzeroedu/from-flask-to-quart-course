# A Quart Database Counter <!-- 4 -->

## ORMs and Async <!-- 4.1 -->

In the next few lessons, we’ll build a counter app that will be a good boilerplate application for your Postgres-based Quart projects.

But before we start writing the application, we need to understand one of the many quirks we’ll see when working with asynchronous applications, and this one is related to database ORMs.

For our original Flask database boilerplate application, we used SQLAlchemy ORM, the Python Database Object Relational Mapper. However, for async projects we can’t use the same library without some form of penalization.

Flask-SQLAlchemy does work with Quart using the `flask_patch` function we discussed earlier, but it doesn't yield to the event loop when it reads or writes. This will mean it cannot handle much concurrent load — [only a couple of concurrent requests](https://gitter.im/python-quart/lobby?at=5cd1da132e2caa1aa625ef83).

However, we don’t need to go back to using raw SQL queries in our codebase. It just happens that we can use the SQLAlchemy Core package from SQLAlchemy, which allows us to express queries in a nice way without sacrificing performance.

We’ll also be using the [`databases`](https://www.encode.io/databases/) package to connect to Postgres asynchronously.

So let’s go ahead and start coding our Quart Postgres counter application.

## Our Development Environment <!-- 4.2 -->

We now need two services to be running for our application: the Quart web server and a Postgres database server to store our data.

For this and all of my other courses, I will be focusing on developing locally using Docker, as this is the preferred development environment used by professional teams. If you haven't used Docker before, don't worry, just follow the instructions. So let's go ahead and set up our local Docker development environment.

First, you need to download the Docker desktop client for Windows or Mac, which you can find in the [Docker website](https://www.docker.com/products/docker-desktop).

Once you have Docker client running, you can check if it's properly installed, by typing the following on your terminal:

{lang=bash,line-numbers=off}
```
$ docker run hello-world
```

If you see a welcome message, everything is good to go. Let's start by creating our `Dockerfile`.

First, create the directory where the application will live. You can create this directory inside your user's home directory.

If you plan to use a directory outside of your personal folder and you are a Mac user, you will need to add it to the Docker client file sharing resources on preferences.
 
So let's call the directory `quart-app`, as this will be a boilerplate for any app. So do `mkdir quart-app`. Navigate inside this folder with `cd quart-app`.

Typically an application will have different services, like frontend and backend. Since this application will be just backend, we will create a new folder, which we will call `backend-service`. So do `mkdir backend-service`.

Now we can create our `Dockerfile` inside the backend service directory. We're going to use a multi-stage build approach, which is a Docker best practice that allows us to have different environments for development and production.

{lang=dockerfile,line-numbers=on,starting-line-number=1}
```
FROM ubuntu:22.04 as base

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Make Python 3.10 the default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

# Install poetry
ENV POETRY_VERSION=1.4.2
RUN curl -sSL https://install.python-poetry.org | python3 -

# Add poetry to PATH
ENV PATH="/root/.local/bin:$PATH"

# Configure poetry
RUN poetry config virtualenvs.create false

# set working directory
WORKDIR /app

# Copy only pyproject.toml first to cache dependencies
COPY pyproject.toml ./

# Generate poetry.lock and install dependencies
RUN poetry lock && poetry install --no-root

FROM base as development
# Install development tools
RUN apt-get update && apt-get install -y \
    vim \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application
COPY my_app my_app/

# Install the root package
RUN poetry install

# Listen to port 5001 at runtime
EXPOSE 5001

# Define our command to be run when launching the container
CMD poetry run hypercorn my_app.asgi:app -b 0.0.0.0:5001 --reload

FROM base as production
# Copy the rest of the application
COPY my_app my_app/

# Install the root package
RUN poetry install

# Listen to port 5001 at runtime
EXPOSE 5001

# Define our command to be run when launching the container
CMD poetry run hypercorn my_app.asgi:app -b 0.0.0.0:5001
```

Let's break down this Dockerfile stage by stage. The base stage sets up our foundational environment. We start with Ubuntu 22.04 as our base image and set `DEBIAN_FRONTEND=noninteractive` to prevent interactive prompts during package installation.

We then install essential packages including Python 3.10 and its development tools. Notice the `&& rm -rf /var/lib/apt/lists/*` at the end - this is a Docker best practice that reduces the image size by removing package lists after installation.

We make Python 3.10 the default Python 3 version using `update-alternatives`. After that, we install Poetry version 1.4.2 using the official installer script and add it to the PATH. We configure Poetry to not create virtual environments since we're in a container and that would be redundant.

We set up our working directory and copy just the `pyproject.toml` first. This is a crucial optimization - by copying only the dependency specifications first, we can cache the dependency installation layer and avoid reinstalling dependencies every time our application code changes.

In our development stage, we install additional development tools like vim and git that we might need while debugging. We then copy our application code and install it using Poetry. We expose port 5001 and set up Hypercorn (an ASGI server) to run our application with the reload flag for development.

The production stage is similar but streamlined. We copy the application code and install it, then expose the same port but run Hypercorn without the reload flag for better production performance.

This multi-stage approach lets us keep our development and production environments consistent while optimizing our production image size by excluding development tools. We can use different configurations for different environments and maintain a clean separation of concerns between base requirements, development needs, and production deployment.

[Save the file](https://fmze.co/fftq-4.2.1)

Now let's create a `docker-compose.yml` file in our project root directory. This file will orchestrate both our application and database services:

{lang=yml,line-numbers=on,starting-line-number=1}
```
version: "3.8"
services:
  web:
    build: 
      context: ./backend-service
      target: development
    ports:
      - "5001:5001"
    volumes:
      - ./backend-service:/app
    links:
      - db:postgres
    container_name: app_web_1
    depends_on:
      - db
    environment:
      PORT: 5001
      SECRET_KEY: "you-will-never-guess"
      ENV_FOR_DYNACONF: docker 
      DB_USERNAME: app_user
      DB_PASSWORD: app_password
      DB_HOST: postgres
      DATABASE_NAME: app

  db:
    image: postgres:14-alpine
    restart: always
    container_name: app_db_1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_password
      POSTGRES_DB: app
```

Let's examine this Docker Compose configuration. For our web service, we specify the build context as `./my-app`, which tells Docker where to find our Dockerfile, and we target the development stage of our multi-stage Dockerfile. We map port 5001 between the container and our host machine and mount our local directory into the container at `/app` so our code changes are immediately reflected.

We link the web service to the database service (which will be accessible as 'postgres' inside the web container) and specify that the web service depends on the database being up first.

We set up environment variables that our application will need - things like database credentials and application settings. Notice we've added `ENV_FOR_DYNACONF: docker` which will tell our configuration system which environment to use.

For the database service, we use the official Postgres 14 Alpine image (Alpine Linux is a lightweight distribution perfect for containers). We set it to always restart if it crashes and expose port 5432 for database connections. The environment variables here configure Postgres with the same credentials we referenced in the web service.

[Save the file](https://fmze.co/fftq-4.2.2)

These two files set up a complete development environment where we can build our Quart application with a Postgres database, all containerized and ready to run. The setup follows Docker best practices like multi-stage builds, layer caching, and proper dependency management, providing us with a consistent, reproducible environment that mirrors what we might use in production.

## Initial Application Setup <!-- 4.3 -->

So let's go ahead and start setting up our Quart counter application. Like I've done in other courses, we're going to build a web application that stores a counter in the database and increases it by one every time you reload the page. This will allow us to see how a typical Quart database application is laid out.

Let's initialize the Poetry environment with Quart. You should have Poetry installed from the previous module.

So cd to the `backend-service` folder and type the following command in your terminal: 

{lang=bash,line-numbers=off}
```
$ poetry init -n
```

This will generate our initial `pyproject.toml` file, but we need to modify it to match our application requirements:

{lang=python,line-numbers=on,starting-line-number=1}
```
[tool.poetry]
name = "my-app"
version = "0.1.0"
description = "A Quart counter application"
authors = ["Your Name <your.email@example.com>"]
packages = [{include = "my_app"}]

[tool.poetry.dependencies]
python = "^3.10"
quart = "0.18.4"
werkzeug = "2.3.7"
dynaconf = "3.1.12"

[tool.poetry.dev-dependencies]
black = "^23.3.0"
mypy = "^1.3.0"
```

You'll notice we're pinning specific versions for some of our dependencies. We're using Quart version 0.18.4 which is stable and works well with our application. We're also specifying Werkzeug 2.3.7 as it's a crucial dependency for Quart to work properly. 

Notice the package dynaconf. Dynaconf allows us to manage configuration settings in a very flexible way. Instead of having multiple configuration files for development, staging and production environments, dynaconf allows us to have a single configuration file with different sections. It also allows us to override these settings with environment variables, which is particularly useful when deploying to production or when working with Docker containers.

For development, we're adding black for code formatting and mypy for static type checking - these are essential tools for maintaining clean, type-safe Python code. Let's add a few more configuration sections:

{lang=python,line-numbers=on,starting-line-number=18}
```
[build-system]
requires = ["poetry-core>=1.0.0"]
build-backend = "poetry.core.masonry.api"

[tool.black]
line-length = 88
target-version = ['py310']

[tool.mypy]
python_version = "3.10"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
config_file = "mypy.ini"
ignore_missing_imports = true
```

The build-system section tells Poetry how to build our package. We're using poetry-core, which is the standard build backend for Poetry projects.

The black configuration sets our line length to 88 characters and specifies that we're targeting Python 3.10 compatibility. Finally, the mypy section configures our type checking tool with some sensible defaults - we're asking it to be quite strict with type checking, which will help us catch potential issues early in development.

[Save the file](https://fmze.co/fftq-4.3.1)

Now let's create our settings.toml file in the same folder, which will contain our application configuration. This is where dynaconf really shines, as it allows us to have different settings for different environments:

{lang=toml,line-numbers=on}
```
[default]
SECRET_KEY = "you-will-never-guess"
DB_USERNAME = "app_user"
DB_PASSWORD = "app_password"
DATABASE_NAME = "app"

[development]
DB_HOST = "localhost"

[docker]
DB_HOST = "db"
```

Let's break down how this configuration works. The `[default]` section contains settings that are common across all environments - things like database credentials and secret keys. These values will be used unless they're overridden in a specific environment section.

The `[development]` section is used when we're running our application directly on our host machine. In this case, we set `DB_HOST` to "localhost" because that's where our PostgreSQL server will be running when we're developing locally.

The `[docker]` section comes into play when we're running our application in Docker containers. Here, we set `DB_HOST` to "db" because that's the service name we defined for our database in our docker-compose file. When containers are running in the same Docker network, they can reference each other by their service names.

Dynaconf is smart enough to know which section to use based on the `ENV_FOR_DYNACONF` environment variable that we set in our docker-compose file. When we're running with Docker, it will automatically merge the `[default]` settings with the `[docker]` section, overriding any values that exist in both.

[Save the file](https://fmze.co/fftq-4.3.2)

***===

Before we start creating our application structure, it's a good idea to set up a local poetry environment. Even though we'll be running our application in Docker, we want to install our dependencies locally as well. This will enable our IDE to provide proper code completion, linting, and type checking while we're coding.

Since the application is expecting Python 3.10, we need to create the Poetry virtual environment with that version, otherwise we could get unexpected results. You need to have Python 3.10 locally available for this to work. If you don't, I recommend you install the excellent `pyenv` library and then add Python 3.10 to the list of executables.

Close your code editor. From your terminal, navigate to the `backend-service` folder and run:

{lang=bash,line-numbers=off}
```
$ poetry env use python3.10 && poetry install
$ poetry shell
```

The first command sets Poetry to use Python 3.10 and then installs all the application dependencies based on that Python version, including development dependencies like black and mypy, into this environment. Now your IDE will be able to use these tools to provide real-time feedback as you code.

The second command creates and activates a virtual environment specifically for our project.

Notice Poetry complains thet `my_app` does not contain any element. This is fine, as we haven't started writing our application yet.

Make sure to open your code editor from the `backend-service` this time and not from the root folder. It will automatically identify the virtual environment created by Poetry. We'll check that in a moment once we start writing Python code.

***===

Now let's create our first blueprint that will handle our home routes. Blueprints are a powerful feature in Quart, just like in Flask, that allow us to organize related routes and functionality into separate components. Think of blueprints as mini-applications that can be reused across different parts of your main application. For example, you might have a blueprint for user operations, another for admin functions and so on.

First let's create the main application folder and call it `my_app`. Add an `__init__.py` inside. This file is what makes Python treat our directory as a package - it's a special file that marks a directory as a Python package directory. Even though it's empty, its presence is what allows us to import modules from this directory.

Inside the `my_app` directory, create a new folder called `home_app` and inside another empty file called `__init__.py`. 

Now let's create our `views.py` file in the same directory. This will contain our blueprint's routes and views:

{lang=python,line-numbers=on}
```
from dynaconf import settings
from quart import Blueprint

home_app = Blueprint("home_app", __name__)


@home_app.route("/app-settings")
async def app_settings() -> str:
    """
    The home page for a home type
    """

    return (
        "<h3>Home: Hello World!</h3>"
        + f"<p>Dynaconf Environment: {settings.ENV_FOR_DYNACONF}</p><br>"
        + f"<p>DB_HOST: {settings.DB_HOST}</p>"  # type: ignore
    )
```

Let's break down what's happening here. First, we create a Blueprint instance named "home_app". The first argument "home_app" is the blueprint's name, which should be unique across your application. The second argument `__name__` tells the blueprint where its resources (like templates and static files) are located.

Just like in Flask, we use the `@route` decorator to define our routes, but here we use `@home_app.route` instead of `@app.route` because we're defining routes for our blueprint rather than the main application. All routes defined in this blueprint will be relative to wherever we register the blueprint in our main application. For example, if we register this blueprint at "/home", the full URL for this route would be "/home/app-settings".

Notice how we're using the `async` keyword here - this is because in Quart, all route handlers must be asynchronous. Even though we're not doing any I/O operations in this route yet, we still need to declare it as async.

Let's check that code linting and intellisense is working. In VSCode you should see the Poetry package's Python interpreter with something like "my-app" in its name. If it doesn't, open a terminal with the Poetry shell enabled and type: `which python` and copy that folder in the code editor's Python settings. You can tell intellisense is working if you hover over a library name and you get a hint of the package description.

[Save the file](https://fmze.co/fftq-4.3.3)

Now let's create our `application.py` file in the `my_app` directory. This file will serve as our application factory, which is a best practice in Flask/Quart applications as it allows us to create multiple instances of our application with different configurations:

{lang=python,line-numbers=on}
```
from typing import Any

from dynaconf import settings
from quart import Quart

from my_app.home_app.views import home_app


def init_config(app: Quart, **config_overrides: Any) -> None:
    """Initialize configuration"""
    app.config.from_object(settings)
    app.config.update(config_overrides)


async def create_app(**config_overrides: Any) -> Quart:
    """
    Factory application creator
    args: config_overrides = testing overrides
    """
    app = Quart(__name__)
    init_config(app, **config_overrides)

    # register blueprints
    app.register_blueprint(home_app)

    return app
```

Let's walk through this code. First, we're importing the necessary types and modules, including our `home_app` blueprint that we just created.

We define an `init_config` function that takes a Quart application instance and any configuration overrides we want to apply. It first loads our settings from dynaconf and then applies any overrides. This is particularly useful when we want to use different settings during testing.

The main function is `create_app`, which is our application factory. Notice that it's an async function - this is because in Quart, we might need to do some asynchronous setup when creating our application. The factory pattern allows us to create multiple instances of our application with different configurations, avoid circular dependencies, and make our application easier to test.

[Save the file](https://fmze.co/fftq-4.3.4)

Now let's create our `manage.py` file which will serve as the entry point when we want to run our application locally:

{lang=python,line-numbers=on}
```
"""
The entry point to our Python Quart application.
"""

import asyncio
from my_app.application import create_app

app = asyncio.run(create_app())
```

This file might look simple, but there's quite a bit happening here. We're using it as an entry point for our application when we want to run it locally (as opposed to running it in Docker). 

Remember that our `create_app` function is asynchronous - it returns a coroutine. In Python, we can't just call an async function directly; we need to run it in an event loop. That's exactly what `asyncio.run()` does - it creates a new event loop, runs our coroutine in it, and properly closes the loop when done.

[Save the file](https://fmze.co/fftq-4.3.5)

Now, let's create our `asgi.py` file. Remember from our Dockerfile that we specified `my_app.asgi:app` as our application entry point - this is the file that Hypercorn will use when running our application in Docker:

{lang=python,line-numbers=on}
```
"""
ASGI file for Hypercorn
"""

import os
import sys
import asyncio

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from my_app.application import create_app

app = asyncio.run(create_app())

if __name__ == "__main__":
    app.run()
```

While this looks similar to our manage.py file, there are a few key differences. First, we're explicitly adding our parent directory to Python's path with `sys.path.append`. This ensures that our application can be found when Hypercorn runs it. 

Remember the line in our Dockerfile where we specified the command:
`CMD poetry run hypercorn my_app.asgi:app -b 0.0.0.0:5001`

This is what tells Hypercorn to look for this file and use the `app` object we're creating here. The `-b 0.0.0.0:5001` part tells Hypercorn to bind to all network interfaces on port 5001, which is necessary for Docker networking to work properly.

[Save the file](https://fmze.co/fftq-4.3.6)

The last quick thing to add is a `.gitignore` file in the root folder, so that we don't check unwanted files into our repository. Just copy and paste this file:

{lang=bash,line-numbers=on}
```
.DS_Store
*.plist
*~
*.pyc
*.swp
*#
.metadata
*.log
__pycache__
.mypy_cache
.venv
.vscode
```

Now let's verify that everything is working properly. From your terminal, `cd` to the root directory of the project where your docker-compose.yml file is located, and run:

{lang=bash,line-numbers=off}
```
$ docker-compose up
```

You should see Docker building your images and then starting both your web service and the PostgreSQL database. Once everything is up and running, open your browser and navigate to:

```
http://localhost:5001/app-settings
```

You should see a page showing "Home: Hello World!" along with your Dynaconf environment settings and DB_HOST. The DB_HOST should show "db" since we're running in the Docker environment.

Congratulations! You've just built a solid foundation for a modern, async Python web application. We've set up a proper project structure using Poetry for dependency management, implemented configuration management with Dynaconf that adapts to different environments, and created a modular application using Blueprints.

In the next module, we'll build upon this foundation by adding database migrations. This will allow us to version control our database schema and make it easy to make changes to our database structure as our application evolves. Get ready to explore the powerful combination of Quart and database management!
