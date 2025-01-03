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

We now finish the route by returning the environment variables for Dynaconf and the Database Host. The idea is that we have an endpoint to check that everything's working as intended.

[Save the file](https://fmze.co/fftq-4.3.3)

Now let's create our `application.py` file in the `my_app` directory. This file will serve as our application factory, which is a best practice in Flask and Quart applications as it allows us to create multiple instances of our application with different configurations:

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

While this looks similar to our manage.py file, there are a couple of key differences. 

First, we're explicitly adding our parent directory to Python's path with `sys.path.append`. This ensures that our application can be found when Hypercorn runs it.  

Second, notice that we create the app task but then run it immediately after that.

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

If all went well, you will see a page showing "Home: Hello World!" along with your Dynaconf environment setting and DB_HOST. The DB_HOST should show "db" since we're running in the Docker environment.

Congratulations! You've just built a solid foundation for a modern, async Python web application. We've set up a proper project structure using Poetry for dependency management, implemented configuration management with Dynaconf that adapts to different environments, and created a modular application using Blueprints.

In the next module, we'll build upon this foundation by adding database migrations. This will allow us to version control our database schema and make it easy to make changes to our database structure as our application evolves. Get ready to explore the powerful combination of Quart and database management!

## Database Operations and Alembic Migrations <!-- 4.4 -->

Now that we have our basic application structure in place, let's add database support to our Quart application. We'll be using PostgreSQL as our database, and we'll set up a complete database migration workflow using Alembic. This is a crucial part of any production application as it allows us to version control our database schema changes.

Let's start by adding the required packages to our Poetry environment. Open up the `pyproject.toml` file and add the following dependencies:

{lang=python,line-numbers=on,starting-line-number=13}
```
psycopg2-binary = "^2.9.10"
databases = {version = "^0.9.0", extras = ["asyncpg"]}
sqlalchemy = "^2.0.36"
alembic = "^1.13.3"
```

Let's understand what each package does. The `psycopg2-binary` package is the PostgreSQL adapter for Python - it's what allows our Python code to talk to PostgreSQL. The `databases` package with the `asyncpg` extra provides async database support, which is crucial for our Quart application. SQLAlchemy is our ORM (Object Relational Mapper) that allows us to work with databases using Python objects instead of raw SQL. Finally, Alembic is SQLAlchemy's database migration tool, which helps us manage database schema changes over time.

[Save the file](https://fmze.co/fftq-4.4.1)

Now let's rebuild our web container to include these new packages:

{lang=bash,line-numbers=off}
```
$ docker-compose build web
```

Let's set up our database connection management. Create a new file `my_app/db.py`:

{lang=python,line-numbers=on}
```
import sqlalchemy
from databases import Database
from dynaconf import settings

metadata = sqlalchemy.MetaData()

async def db_connection() -> Database:
    database_url = f"postgresql+asyncpg://{settings['DB_USERNAME']}:"
    database_url += f"{settings['DB_PASSWORD']}@"
    database_url += f"{settings['DB_HOST']}:5432/"
    database_url += f"{settings['DATABASE_NAME']}"
    database = Database(database_url, min_size=5, max_size=20)
    
    return database
```

This file does several important things. First, it creates a metadata object that will store the schema information for all our models. Then, it provides an async function that creates and returns a database connection pool. Notice we're using connection pooling with `min_size=5` and `max_size=20` - this is a performance optimization that keeps a set of connections ready for use.

[Save the file](https://fmze.co/fftq-4.4.2)

Before we create our counter model, let's set up the counter structure. Create a new directory called `counter_app` inside `my_app` and add an empty `__init__.py` file to make it a Python package:

{lang=bash,line-numbers=off}
```
$ mkdir my_app/counter_app
$ touch my_app/counter_app/__init__.py
```

Now let's create our counter model. This will be a simple table with just an ID and a count field. Create a new file in `my_app/counter_app/models.py`:

{lang=python,line-numbers=on}
```
from sqlalchemy import Column, Integer, Table

from my_app.db import metadata

counter_table = Table(
    "counter",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("count", Integer),
)
```

In this model, we're using SQLAlchemy Core instead of the ORM. Why? Because when working with async applications, the Core API provides better performance and is more straightforward to use with async drivers. We define a table named 'counter' with two columns: an auto-incrementing ID and a count field that will store our counter value.

[Save the file](https://fmze.co/fftq-4.4.3)

With our model in place, let's set up Alembic for database migrations. First, we'll initialize Alembic in our project:

{lang=bash,line-numbers=off}
```
$ docker-compose run --rm web poetry run alembic init migrations
```

This command creates a migrations directory and an `alembic.ini` file. Let's configure Alembic by updating the `alembic.ini` file. Find the `sqlalchemy.url` line and update it to use our configuration:

{lang=ini,line-numbers=on,starting-line-number=65}
```
sqlalchemy.url = postgresql://%(DB_USERNAME)s:%(DB_PASSWORD)s@%(DB_HOST)s:5432/%(DATABASE_NAME)s
```

We're using variable interpolation here to make our configuration environment-agnostic. These variables will be populated from our settings.

[Save the file](https://fmze.co/fftq-4.4.4)

Now we need to add a few lines to `migrations/env.py` to connect our models to Alembic. First, we'll add these imports at the top of the file:

{lang=python,line-numbers=on,starting-line-number=11}
```
from dynaconf import settings
from my_app.counter_app.models import counter_table
from my_app.db import metadata as my_app_metadata
```

Then near line 25, we'll set our metadata:

{lang=python,line-numbers=on,starting-line-number=25}
```
target_metadata = my_app_metadata
```

Finally, we'll add the configuration section that will allow Alembic to read our environment variables:

{lang=python,line-numbers=on,starting-line-number=38}
```
section = config.config_ini_section
config.set_section_option(section, "DB_USERNAME", settings.get("DB_USERNAME", ""))
config.set_section_option(section, "DB_PASSWORD", settings.get("DB_PASSWORD", ""))
config.set_section_option(section, "DB_HOST", settings.get("DB_HOST", ""))
config.set_section_option(section, "DATABASE_NAME", settings.get("DATABASE_NAME", ""))
```

[Save the file](https://fmze.co/fftq-4.4.5)

Now let's generate our first migration. When we run the following command, Alembic will compare our models against the current state of the database and generate the necessary SQL to synchronize them:

{lang=bash,line-numbers=off}
```
$ docker-compose run --rm web poetry run alembic revision --autogenerate -m "create counter table"
```

You should see something like the following:

{lang=bash,line-numbers=off}
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'counter'
  Generating /app/migrations/versions/b515cc03d07e_create_counter_table.py ...  done
```

This will create a new file in the migrations/versions directory. Let's look at what Alembic generated:

{lang=python,line-numbers=on}
```
"""create counter table

Revision ID: 47c68318259a
Revises:
Create Date: 2024-11-01 16:45:58.725264

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '47c68318259a'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, None] = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('counter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('counter')
    # ### end Alembic commands ###
```

Alembic migrations are like version control for your database schema. Each migration file has a unique revision ID and contains two main functions:

1. `upgrade()`: This function contains the changes needed to move your database forward to this version. In our case, it's creating the counter table with its columns.
2. `downgrade()`: This contains the reverse operations needed to undo this migration. Here, it would drop the counter table.

Think of these migrations as a chain - each migration knows about the one that came before it through the `down_revision` variable. Alembic uses this to know how to move forward and backward through your database changes.

Now let's apply this migration:

{lang=bash,line-numbers=off}
```
$ docker-compose run --rm web poetry run alembic upgrade head
```

This results in the following output:
{lang=bash,line-numbers=off}
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> b515cc03d07e, create counter table
```

The `upgrade head` command tells Alembic to apply all pending migrations in the database until it reaches the most recent version (the "head").

Let's verify the tables were created in our database. We can connect to PostgreSQL running in our Docker container:

{lang=bash,line-numbers=off}
```
$ docker-compose exec db psql -U app_user app
```

This command breaks down as:
- `docker-compose exec db`: Run a command in the running database container
- `psql`: The PostgreSQL command-line interface
- `-U app_user`: Connect as our application user
- `app`: Connect to the 'app' database

Once connected, let's see what tables were created:

{lang=bash,line-numbers=off}
```
app=> \dt
              List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | app_user
 public | counter         | table | app_user
(2 rows)
```

You can see two tables: our `counter` table and an `alembic_version` table. The `alembic_version` table is special - it's how Alembic keeps track of which migrations have been applied. Let's look at its contents:

{lang=bash,line-numbers=off}
```
app=> select * from alembic_version;
 version_num  
-------------
 47c68318259a
(1 row)
```

This single row contains the ID of our last applied migration. Alembic uses this to know where in the migration chain we currently are, which helps it determine what migrations need to be applied when we run `upgrade` or what migrations need to be reverted when we run `downgrade`.

Exit the PostgreSQL prompt by typing `\q` and pressing Enter.

Now that we've verified our database is properly set up, we can move on to starting our application.

Let's create our counter blueprint and views. Create `views.py` inside the `counter_app` folder:

Now let's create our counter blueprint and views. This file will handle all the counter-related routes and database operations. Create `my_app/counter_app/views.py`:

{lang=python,line-numbers=on}
```
from quart import Blueprint, current_app

from my_app.counter_app.models import counter_table

counter_app = Blueprint("counter_app", __name__)
```

First, we import what we need:
- `Blueprint` from Quart for creating our modular component
- `current_app` which gives us access to the application context, including our database connection
- Our `counter_table` model that we created earlier

We create a Blueprint named "counter_app" - this is what we'll register in our main application later.

{lang=python,line-numbers=on,starting-line-number=6}
```
@counter_app.route("/")
async def init() -> str:
    conn = current_app.dbc  # type: ignore
    counter_query = counter_table.select()
    result = await conn.fetch_all(query=counter_query)
    count = None
```

Here we define our root route ("/") and make it async since we'll be doing database operations. We:
1. Get our database connection from the application context (the type ignore comment is for mypy)
2. Create a SELECT query using SQLAlchemy Core's expressive syntax
3. Fetch all rows that match our query (we expect either zero or one)
4. Initialize our count variable

Now comes the interesting part - handling the two possible scenarios:

{lang=python,line-numbers=on,starting-line-number=13}
```
    if not len(result):
        stmt = counter_table.insert().values(count=1)
        result = await conn.execute(stmt)
        await conn.execute("commit")
        count = 1
```

If we don't have any results (`not len(result)`), this is our first visit ever. We need to:
1. Create an INSERT statement setting count to 1
2. Execute the insert statement
3. Explicitly commit our transaction
4. Set our local count variable to 1

{lang=python,line-numbers=on,starting-line-number=19}
```
    else:
        row = result[0]
        count = row["count"] + 1
        update_stmt = (
            counter_table.update()
            .where(counter_table.c.id == row["id"])
            .values({"count": count})
        )
        result = await conn.execute(update_stmt)
        await conn.execute("commit")
```

If we do have results, we're incrementing an existing counter:
1. Get the first (and only) row
2. Calculate the new count by adding 1
3. Build an UPDATE statement that:
   - Updates our counter table
   - Matches the row by ID (using counter_table.c.id to reference the column)
   - Sets the count to our new value
4. Execute the update and commit the transaction

{lang=python,line-numbers=on,starting-line-number=29}
```
    return f"<h1>Counter: {str(count)}</h1>"
```

Finally, we return a simple HTML response showing the current count.

Notice how we use `await` for all database operations. This is crucial because:
1. These operations take time to complete
2. While we're waiting for the database, other requests can be processed
3. When the database operation finishes, we resume exactly where we left off

Also notice our transaction management - we explicitly commit after both INSERT and UPDATE operations. In a more complex application, we might want to use a context manager for transactions, but for this simple example, explicit commits work fine.

[Save the file](https://fmze.co/fftq-4.4.6)

For our last step, let's update our `application.py` to include our new counter blueprint and database connection management.

First we'll import the new `counter_app` blueprint and the `db_connection` from the new `db` module.

{lang=python,line-numbers=on,starting-line-number=6}
```
from my_app.counter_app.views import counter_app
from my_app.db import db_connection
```

And then in line 27 we do the following:

{lang=python,line-numbers=on,starting-line-number=27}
```
    app.register_blueprint(counter_app)

    @app.before_serving
    async def create_db_conn() -> None:
        database = await db_connection()
        await database.connect()
        app.dbc = database

    @app.after_serving
    async def close_db_conn() -> None:
        await app.dbc.disconnect()  # type: ignore
```

We've added the counter blueprint registration and, most importantly, two special lifecycle hooks using `before_serving` and `after_serving` decorators. These decorators are specific to Quart and are crucial for proper application lifecycle management.

The `before_serving` decorator runs before the first request is handled by our application. This is different from Flask's `before_first_request` in an important way: in an async application, we might have multiple workers handling requests, and we need our database connection to be available to all of them. By setting up the connection in `before_serving`, we ensure that our database connection pool is established once when the application starts, not when the first request comes in.

Similarly, `after_serving` runs when we're shutting down our application. This gives us a chance to properly close our database connections. This is crucial for preventing connection leaks and ensuring all our database operations are properly completed before shutdown.

Both of these hooks are asynchronous because database operations in our application are asynchronous. We store the database connection in `app.dbc` which makes it available throughout our application via the `current_app` proxy. This is a pattern that ensures we're reusing connections efficiently rather than creating new connections for each request.

[Save the file](https://fmze.co/fftq-4.4.7)

With everything in place, we can start our application using docker-compose to bring up both our web service and the PostgreSQL database:

{lang=bash,line-numbers=off}
```
$ docker-compose up
```

You might see quite a bit of output as both services start up - this is normal. Once you see the message that the application is running, visit http://localhost:5001 in your browser (note we're using port 5001 as configured in our docker-compose.yml), and you should see the counter starting at 1. Refresh the page, and watch it increment!

## Testing our Application <!-- 4.5 -->

It's great that we have a running application, but we know that any application needs good tests to insure it won't break with new development.

In our synchronous applications we had used `unittest`, but for asynchronous applications, I've found that `pytest` is a better fit. `Pytest` also has an `asyncio` library that will allow us to test our code better.

Let's update our pyproject.toml file to include all the testing dependencies and configuration we'll need. First, let's add our testing libraries to the dependencies section:

{lang=python,line-numbers=on,starting-line-number=17}
```
pytest = "^8.3.3"
pytest-asyncio = "^0.24.0"
sqlalchemy-utils = "^0.41.2"
```

We're adding several new packages here. First, we have `pytest`, which is our main testing framework. It provides a more modern and flexible approach to testing than unittest, with features like fixtures and better async support. 

The `pytest-asyncio` package is crucial for our asynchronous tests - it provides the tools we need to properly test coroutines and async functions in our Quart application.

We're also adding `sqlalchemy-utils`, which provides additional utilities for SQLAlchemy that we'll use in our testing setup, particularly for database management during tests.

Next, we'll add a new section specifically for pytest configuration:

{lang=python,line-numbers=on,starting-line-number=45}
```
[tool.pytest.ini_options]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v -s"
```

The pytest configuration section contains several important settings. The asyncio_mode setting tells pytest-asyncio to automatically handle async tests. We set asyncio_default_fixture_scope to "function" which ensures our fixtures are created and destroyed for each test function, giving us clean test isolation. 

We specify the testpaths setting to tell pytest where to look for our test files, in this case the "tests" directory. The python_files and python_functions settings define the naming pattern pytest will use to identify our test files and functions - they should start with "test_". 

Finally, we set some default command line options with addopts. The -v flag gives us verbose output so we can see exactly what tests are running, while -s allows print statements to show up in the output, which will be helpful for debugging.

[Save the file](https://fmze.co/fftq-4.5.1)

Now let's configure our test settings in settings.toml. We'll need two different test environments: one for running tests on our local machine and another for running them in our Docker container:

{lang=python,line-numbers=on,starting-line-number=13}
```
[testing]
TESTING = true
DB_HOST = "localhost"
DATABASE_NAME = "app_test"

[docker-testing]
TESTING = true
DB_HOST = "db"
DATABASE_NAME = "app_test"
```

In this configuration, we've set up two different testing environments. The `testing` section is used when we want to run our tests directly on our host machine. In this case, we set `DB_HOST` to "localhost" since we'll be connecting to a database running locally. 

We've also added a new `docker-testing` section which will be used when running tests inside our Docker container. Here, we set `DB_HOST` to "db", which matches the service name of our database container in our Docker Compose configuration.

Both environments set `TESTING` to true and use a separate database named "app_test". Using a different database for testing is a best practice as it keeps our test data completely isolated from our development or production data.

[Save the file](https://fmze.co/fftq-4.5.2)

Next, let's update our docker-compose.yml to add a test service. First, we'll update some paths in our existing configuration, then add our test service:

{lang=yaml,line-numbers=on,starting-line-number=25}
```
test:
  extends: web
  environment:
    ENV_FOR_DYNACONF: docker-testing
    PORT: 5001
    SECRET_KEY: "you-will-never-guess"
    DB_USERNAME: app_user
    DB_PASSWORD: app_password
  container_name: app_test_1
```

We're creating a new service called `test` that extends our web service, which means it inherits all the configuration from our web service. This is a great feature of Docker Compose that helps us avoid duplicating configuration.

The key difference in the test service is that we set `ENV_FOR_DYNACONF` to "docker-testing", which tells our application to use the docker-testing configuration we just created in settings.toml. This ensures our tests run in an isolated environment with its own database.

We also give it a unique container name `app_test_1` to avoid any conflicts with our development containers.

[Save the file](https://fmze.co/fftq-4.5.3)

Now let's set up our test fixtures using pytest's `conftest.py` mechanism. In the pytest world, fixtures are powerful tools that help us set up the state our tests need. Think of fixtures as building blocks that prepare everything your tests require - like database connections, test data, or application configuration. The great thing about fixtures is that they're reusable across multiple tests and can even build on top of each other.

Unlike our previous approach of having tests inside each blueprint, we're going to create a dedicated `tests` folder in the root of our `backend-service` folder. This is a deliberate choice that brings several benefits. First, it gives us a clear separation between application code and test code. Second, it makes it easier to run all our tests with a single command. And third, it allows us to share fixtures and testing utilities across all our tests without duplicating code.

Let's create our `conftest.py` file in the tests directory and walk through its implementation piece by piece. First, let's add our imports:

{lang=python,line-numbers=on,starting-line-number=1}
```
from typing import AsyncGenerator
import pytest
from dynaconf import settings
from my_app.application import create_app
from my_app.db import metadata
from quart import Quart
from quart.typing import TestClientProtocol
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database
from typing_extensions import Never
```

We're importing everything we need to create our test environment, including SQLAlchemy utilities for database management, Quart's test client, and our application's components.

Now let's create our first fixture that will handle the database setup for tests:

{lang=python,line-numbers=on,starting-line-number=12}
```
@pytest.fixture(scope="function")
async def create_db() -> AsyncGenerator[dict, Never]:
    # We only need to switch environment when running tests locally
    if settings.ENV_FOR_DYNACONF == "DEVELOPMENT":
        settings.configure(ENV_FOR_DYNACONF="TESTING")
    
    db_test_url = f"postgresql://{settings['DB_USERNAME']}:"
    db_test_url += f"{settings['DB_PASSWORD']}@"
    db_test_url += f"{settings['DB_HOST']}/"
    db_test_url += f"{settings['DATABASE_NAME']}"

    # drop the database if it exists
    if database_exists(db_test_url):
        drop_database(db_test_url)
    
    # create the testing database
    create_database(db_test_url)

    yield {
        "db_test_url": db_test_url,
    }

    # Drop database after test is complete
    drop_database(db_test_url)
```

This section handles the database lifecycle for both local and Docker testing environments. When running tests locally with `poetry run pytest`, the environment starts in "DEVELOPMENT" mode and needs to be switched to "TESTING". However, when running `docker-compose run --rm test poetry run pytest`, the environment is already set to "docker-testing" by our docker-compose.yml configuration. After setting up the environment, it creates a fresh test database for each test and cleans up afterward.

Next, we'll create our test application fixture:

{lang=python,line-numbers=on,starting-line-number=38}
```
@pytest.fixture(scope="function")
async def create_test_app(create_db: dict[str, str]) -> AsyncGenerator[Quart, None]:
    app = await create_app()

    # Create engine and create all tables
    engine = create_engine(create_dbi["db_test_url"])
    metadata.create_all(engine)

    # Start the database connection
    await app.startup()
    
    yield app
    
    # Stop the database connection
    await app.shutdown()
    
    # Clean up
    metadata.drop_all(engine)
```

This fixture builds on top of `create_db` to set up our test application. It creates the application instance, sets up the database schema, and establishes connections. After the test runs, it properly shuts everything down and cleans up the database.

Finally, let's create our test client fixture:

{lang=python,line-numbers=on,starting-line-number=77}
```
@pytest.fixture(scope="function")
def create_test_client(create_test_app: Quart) -> TestClientProtocol:
    return create_test_app.test_client()
```

This fixture creates a test client that we'll use to make requests to our application during tests. It depends on the `create_test_app` fixture, showing how pytest fixtures can build on each other to create complex test environments.

[Save the file](https://fmze.co/fftq-4.5.4)

Now let's create our first test file. Create a directory called `counter_app` inside the `tests` directory and add a new file called `test_counter.py`. Let's write our first test:

{lang=python,line-numbers=on,starting-line-number=1}
```
import pytest
from my_app.counter_app.models import counter_table
from quart import Quart, current_app
from quart.testing import QuartClient


@pytest.mark.asyncio
async def test_initial_response(create_test_client: QuartClient) -> None:
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 1" in str(body)
```

First, we import pytest and Quart's testing utilities. The QuartClient type hint helps our IDE understand the test client's capabilities.

The `@pytest.mark.asyncio` decorator tells pytest this is an async test, which means we can use await inside it. 

Our test function injects the `create_test_client` fixture we created earlier. This fixture provides a test client that can make HTTP requests to our application. Notice that the fixture is typed as QuartClient - this helps with code completion and type checking.

We then make a GET request to the root path ("/") using the test client. Since this is an async operation, we use `await`. Similarly, getting the response data is also async, so we await that too.

Finally, we verify that the string "Counter: 1" appears in the response body. This checks that when we first hit our counter endpoint, it properly initializes with a value of 1.

[Save the file](https://fmze.co/fftq-4.5.5)

Let's run just this test to make sure it works:

{lang=bash,line-numbers=off}
```
docker-compose run --rm test poetry run pytest
```

Since this is the first time running this container, it will take a little more time as it installs the new dependencies. But as you can see here at the end it says that our test passed although there's some warnings which are not related to our tests, but things that some libraries need to update.

{lang=bash,line-numbers=off}
```
tests/counter_app/test_counter.py::test_initial_response PASSED
```

Now let's add our second test that checks the counter increment and database state. Our second test is more complex:

{lang=python,line-numbers=on,starting-line-number=14}
```
@pytest.mark.asyncio
async def test_second_response(
    create_test_client: QuartClient,
    create_test_app: Quart,
) -> None:
    # Counter 1
    response = await create_test_client.get("/")
    body = await response.get_data()

    # Counter 2
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 2" in str(body)
```

Here we test the counter increment. We make two requests: the first sets up our initial state, and the second verifies that the counter increments. The first hit returns the number 1 because each new test starts with a new database, as we have specified that fixtures are function scoped.

We need both the test client for making requests and the test app for database access, so we inject both fixtures.

Finally, we verify the database state:

{lang=python,line-numbers=on,starting-line-number=28}
```
    async with create_test_app.app_context():
        conn = current_app.dbc  # type: ignore
        counter_query = counter_table.select()
        result = await conn.fetch_all(counter_query)
        result_row = result[0]
        count = result_row["count"]
        assert count == 2
```

This is where we ensure the data was properly saved. We need an application context to access the database connection, which is why we used the `async with` statement. We create a simple select query, fetch all records (though we know there's only one), and verify the count is 2. The `type: ignore` comment tells mypy to skip type checking for that line since we know the dbc attribute exists but mypy can't verify it.

[Save the file](https://fmze.co/fftq-4.5.5)

Let's run the tests again:

{lang=bash,line-numbers=off}
```
docker-compose run --rm test poetry run pytest
```

The tests pass, confirming that our counter application is working as expected. 

{lang=bash,line-numbers=off}
```
tests/counter_app/test_counter.py::test_initial_response PASSED
tests/counter_app/test_counter.py::test_second_response PASSED
```

As you can see, this time the test docker instance started much faster. We're now confident that our application is running correctly with the support of these tests.

## Linting and Debugging with VSCode <!-- 4.6 -->

## Code Analysis and Debugging Tools <!-- 4.6.1 -->

As our application grows in complexity, we need to make sure we're writing code that is not only functional but also maintainable and reliable. This is where linting and type checking come into play. While Python's dynamic nature is one of its greatest strengths, it can also lead to subtle bugs that might only surface at runtime. For a production application, especially one handling asynchronous operations, we want to catch as many potential issues as possible before our code even runs.

Think of linting as having a very experienced Python developer looking over your shoulder as you code, pointing out potential mistakes, style issues, and areas that could be improved. The linter helps maintain consistency across your codebase and catches common programming errors before they become problems. This is particularly important when working in a team, but even for solo developers, it helps maintain high code quality standards.

One of the most powerful tools in our arsenal is mypy, a static type checker for Python. While Python is a dynamically typed language, it has supported type hints since Python 3.5, and these have become increasingly sophisticated with each new Python release. Type hints serve two main purposes: they make your code more self-documenting, and they allow tools like mypy to catch type-related errors before runtime.

Let's look at how type hints work in practice. In our counter application, we've been using them in our function signatures. For example, when we defined our database connection function:

{lang=python,line-numbers=on}
```
async def db_connection() -> Database:
    database_url = f"postgresql://{settings['DB_USERNAME']}:"
    # ... rest of the function
    return database
```

The `-> Database` annotation tells both our IDE and mypy that this function will return a Database object. If we accidentally tried to return something else, mypy would warn us before we even ran the code. 

Type hints become even more valuable with async code. Consider our counter route:

{lang=python,line-numbers=on}
```
@counter_app.route("/")
async def init() -> str:
    conn = current_app.dbc
    # ... rest of the function
    return f"<h1>Counter: {str(count)}</h1>"
```

The `-> str` return type annotation makes it clear that this route will always return a string, even though it's doing asynchronous database operations. This helps catch errors where we might accidentally return something else, like a database result object.

By combining linting and type checking, we create a powerful development environment that helps us write more reliable code. Let's set up these tools in Visual Studio Code, which has become the de facto standard for Python development thanks to its excellent debugging capabilities, extensive marketplace of extensions, and fantastic container integration. If you are not using VSCode, you can skip the rest of this module.

## Setting Up Our Development Environment <!-- 4.6.2 -->

There are two approaches we can take to set up our development environment: we can work directly from our host machine with a local Poetry installation, or we can use VSCode's devcontainer feature. Let's explore both approaches so you can choose what works best for you.

### Local Development Setup 

Let's first set up our local environment. We'll start by creating a VSCode configuration that will allow us to run and debug our application. First, create a `.vscode` folder in your project root and let's add a `launch.json` file:

{lang=json,line-numbers=on}
```
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Quart",
      "type": "python",
      "request": "launch",
      "module": "quart",
      "env": {
        "QUART_APP": "${workspaceRoot}/my_app/manage.py",
        "QUART_DEBUG": "1"
      },
      "args": [
        "run",
        "--host",
        "0.0.0.0",
        "--port",
        "5002"
      ],
      "jinja": true
    }
  ]
}
```

[Save the file](https://fmze.co/fftq-4.6.1)

This configuration tells VSCode how to run our Quart application in debug mode. We're specifying our manage.py file as the entry point and enabling debug mode through the QUART_DEBUG environment variable.

We'll also need a `settings.json` file to configure our Python environment and testing setup:

{lang=json,line-numbers=on}
```
{
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.testing.unittestEnabled": false,
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

[Save the file](https://fmze.co/fftq-4.6.2)

These settings enable pytest as our test runner and configure automatic code formatting when we save our files. Remember that for this setup to work, you'll need to have the Docker database container running since our application depends on it.

To set up the local environment, make sure you're on the `backend-service` folder and run these commands in your terminal. Make sure you have Python 3.10 available locally. If you don't, I recommend you install the [pyenv](https://github.com/pyenv/pyenv) package and follow the instructions.

{lang=bash,line-numbers=off}
```
poetry env use python3.10
poetry lock
poetry install
```

This creates a new virtual environment using Python 3.10 and installs all our dependencies. 

Before we can start coding, we need to install some essential VSCode extensions. Open the Extensions panel (you can use Cmd+Shift+X on Mac or Ctrl+Shift+X on Windows) and install the following.

The Python extension (ms-python.python) is the foundation of Python development in VSCode. It provides IntelliSense, debugging capabilities, and integration with various Python tools. It's the main extension that powers our Python development experience.

The Black Formatter extension (ms-python.black-formatter) enforces a consistent code style across your project. Black is nicknamed "The Uncompromising Code Formatter" because it has very few configuration options - it formats your code in the one way it thinks is best. This might seem restrictive, but it eliminates endless debates about code formatting in team settings.

The isort extension (ms-python.isort) automatically organizes and formats your Python imports. It sorts them into sections (standard library, third-party, and local), alphabetically within each section, and can automatically combine imports from the same module. This keeps your imports clean and consistent throughout your codebase.

The mypy extension (ms-python.mypy-type-checker) provides real-time type checking as you code. Remember those type hints we talked about earlier? Mypy uses them to catch type-related errors before you even run your code. It's like having a very pedantic friend who's really good at spotting potential bugs related to type mismatches.

One last thing, make sure your VSCode is pointing to the right Python interpreter. Normally it picks up this location from the poetry install we did earlier. But in subsequent sessions you might want to do a `poetry shell` first and then start VSCode with `code dot`. You can see the location of the Poetry Python by doing `which python` after the `poetry shell` and then verify it's the same Python package by searching "Python Interpreter" on the VSCode command palette.

Let's see how these extensions work together. Let's mess up our code in the application.py.

{lang=python,line-numbers=on}
```
from dynaconf import settings
from quart import Quart
from my_app.home_app.views import home_app
from my_app.logger import get_logger
from my_app.counter_app.views import counter_app
from my_app.db import db_connection

from typing import Any
def init_config(app:Quart,**config_overrides:Any) -> None:
    """Initialize configuration"""
    app.config.from_object(settings)
    app.config.update(config_overrides)
```

When you save this file with our extensions enabled, it automatically transforms into the following.

{lang=python,line-numbers=on}
```
from typing import Any

from dynaconf import settings
from quart import Quart

from my_app.counter_app.views import counter_app
from my_app.db import db_connection
from my_app.home_app.views import home_app
from my_app.logger import get_logger


def init_config(app: Quart, **config_overrides: Any) -> None:
    """Initialize configuration"""
    app.config.from_object(settings)
    app.config.update(config_overrides)
```

Notice how the extensions have:
- Sorted imports into standard library, third-party, and local application imports
- Added consistent spacing around operators and after commas
- Fixed indentation and line breaks
- Added proper spacing around type hints
- Ensured consistent blank lines between imports and function definitions

This automatic formatting happens every time you save a file, ensuring your code always maintains a consistent style.

Mypy is also at play here. Let's change the return type of the `init_config` to a string instead of None.

{lang=python,line-numbers=on}
```
def init_config(app: Quart, **config_overrides: Any) -> str:
    """Initialize configuration"""
    app.config.from_object(settings)
    app.config.update(config_overrides)
```

Notice how the whole block is red? That file is also marked as red on the file tree. This is telling us that there's an issue with the file. You should not commit any files that are red into the repository.

Let's try out VSCode's powerful debugging features. First, let's debug our running application. Open the `views.py` file in the counter_app folder and let's add a breakpoint. Click to the left of the line number where we increment our counter:

{lang=python,line-numbers=on,starting-line-number=19}
```
    else:
        row = result[0]
        count = row["count"] + 1  # Click left of this line
```

A red dot will appear, indicating your breakpoint. Now press the little green button on the Run and Debug panel and make sure "Python Quart" is selected. VSCode will launch our Quart application in debug mode. Open your browser and navigate to http://localhost:5002. The application will pause at your breakpoint. Remember that you need your Docker database container for the application to run.

In the Debug Console (View > Debug Console if it's not visible), you can inspect variables like `row` and `count`. Try typing `row["count"]` in the debug console to see the current counter value. You can also use the debug toolbar to step through the code line by line (F10) or step into function calls (F11).

We can also debug our tests this way. But first stop the run command and remove the breakpoint in the `views.py`.

Open the `tests/counter_app/test_counter.py` file and set a breakpoint in our second test:

{lang=python,line-numbers=on,starting-line-number=28}
```
    async with create_test_app.app_context():
        conn = current_app.dbc  # Set breakpoint here
```

Open the Testing panel in VSCode (the flask icon in the sidebar) and click the debug icon (play button with a bug) next to the test you want to debug. The test will run and pause at your breakpoint. You can now inspect the database connection and step through the test code.

The debug console is particularly useful for async code because you can see the exact state of your application at any point in the event loop. This helps tremendously when tracking down issues with coroutines and async/await patterns.

### Development Container Setup

While the local setup works well, I prefer using VSCode's devcontainer feature. Development containers provide a consistent, isolated environment that matches our production setup exactly. They eliminate the "it works on my machine" problem and make it much easier to onboard new team members.

Let's create a `devcontainer.json` file in a folder we'll call `.devcontainer` on the root folder where `docker-compose.yml` lives:

{lang=json,line-numbers=on}
```
{
    "name": "My Dev Container",
    "dockerComposeFile": "../docker-compose.yml",
    "service": "web",
    "runServices": [
        "db",
        "web"
    ],
    "workspaceFolder": "/app",
    "overrideCommand": false,
    "customizations": {
        "vscode": {
            "settings": {
                "python.pythonPath": "/usr/bin/python3"
            },
            "extensions": [
                "ms-python.python",
                "ms-python.black-formatter",
                "ms-python.isort",
                "matangover.mypy"
            ]
        }
    },
    "postCreateCommand": "poetry config virtualenvs.create true && poetry install",
    "remoteUser": "root"
}
```

[Save the file](https://fmze.co/fftq-4.6.3)

This configuration tells VSCode to:

- Use our existing docker-compose.yml file
- Start both our web and database services
- Set up the workspace in the /app directory
- Automatically install all our required extensions through the `customizations.vscode.extensions` section. Notice how we're installing the same extensions we installed manually in our local setup: Python, Black Formatter, isort, and mypy
- Set up Poetry after the container is created

Before you run this, make sure that you delete all the images and containers that have the same name, otherwise you will get an error.

When you open this project in VSCode, you'll see a prompt asking if you want to reopen it in a container. Once you do, VSCode will build the container and set up a complete development environment with all our tools and dependencies ready to go.

The beauty of this approach is that everyone on your team gets the exact same development environment, complete with:

- The correct Python version
- All required dependencies
- Consistent linting and formatting rules
- Database access already configured
- Debug configurations ready to use

Before we run the application, remember to do your first Alembic migration. Just open a terminal on VSCode and run:

{lang=bash,line-numbers=off}
```
poetry run alembic upgrade head
```

You can now run and debug your application directly from VSCode, run tests with the built-in test explorer, and get immediate feedback from mypy and black as you code.
