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

For this and all of my other courses, I will be focusing on developing locally using Docker, as this is the preferred development environment used by professional teams. If you haven't used Docker before, don't worry, just follow the instructions. I also have a Docker for Flask course if you want to learn more about Docker.

So let's go ahead and set up our local Docker development environment.

First, you need to download the Docker desktop client for Windows or Mac, which you can find in the [Docker website](https://www.docker.com/products/docker-desktop). Just follow the instructions.

Once you have Docker client running, you can check if it's properly installed, by typing the following on your terminal:

{lang=bash,line-numbers=off}
```
$ docker run hello-world
```

If you see a welcome message, everything is good to go. Let's start by creating our `Dockerfile`.

First, create the directory where the application will live. You can create this directory inside your user's home directory.

If you plan to use a directory outside of your personal folder and you are a Mac user, you will need to add it to the Docker client file sharing resources on preferences.
 
So I'll call mine `counter_app`. so I will do `mkdir counter_app`.

Now `cd` into your application folder and open a code editor to create the `Dockerfile`. It looks like this:

{lang=yml,line-numbers=on,starting-line-number=1}
```
FROM ubuntu:20.04

# Install packages
RUN apt-get update && apt-get install -y \
    build-essential \
    make \
    gcc \
    git \
    unzip \
    wget \
    python3-dev \
    python3-pip \
    python-is-python3

ENV PIP_DISABLE_PIP_VERSION_CHECK=on

# Install poetry
RUN pip3 install poetry

# set "counter_app" as the working directory from which CMD, RUN, ADD references
WORKDIR /counter_app

# setup poetry
COPY pyproject.toml /counter_app/
RUN poetry config virtualenvs.create true \
    && poetry config virtualenvs.in-project false \
    && poetry install --no-interaction

# now copy all the files in this directory to /code
COPY . .

# Listen to port 5000 at runtime
EXPOSE 5000

# Define our command to be run when launching the container
CMD poetry run quart run --host 0.0.0.0
```

First we define the base image as an Ubuntu 20.04 image.

Next we install all the Ubuntu packages we will need. We'll also turn off the disruptive pip version check prompts.

Next, we install Poetry using `pip3`.

We then create the `counter_app` directory in the Docker instance and set it as the default location for the code.

At this point we need to set up Poetry, so we copy the `pyproject.toml` file to prepare the install. We then set some flags for Poetry to work best and install all the packages.

Right after that, we copy the contents of the local directory into the `counter_app` directory using the `COPY` command.

Once all the code in is place, we open the `5000` port and invoke the `poetry run` command.

[Save the file](https://fmze.co/fftq-4.2.1).

Now we need to create a `docker-compose` file that will build up both our application instance as well as the Postgres instance.

We will create the services using the following `docker-compose.yml` file:

{lang=yml,line-numbers=on,starting-line-number=1}
```
version: "2"
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./:/counter_app
    links:
      - db:postgres
    container_name: app_web_1
    depends_on:
      - db
    stdin_open: true
    tty: true
    environment:
      PORT: 5000
      SECRET_KEY: "you-will-never-guess"
      QUART_ENV: development
      DB_USERNAME: app_user
      DB_PASSWORD: app_password
      DB_HOST: postgres
      DATABASE_NAME: app
```

First we describe the Docker Compose file version as "2". We then start defining the services, which are essentially the containers that will be running at the same time.

The first service is the web application which we are calling `web`. We instruct Docker Compose to build the container using the `Dockerfile` in the same directory using the `build .` statement.

Next we open up port 5000 both in the host as well as in the container, as this will be the port that Quart is assigned to listen on.

Then we mount the current host's (Windows or Mac computer) directory as a volume inside the container, which will be mounted as  `counter_app`. This will allow us to code on the host machine and propagate those changes in the container instantly.

The `links` statement describes that this container is connected to another service which we will call `db`, but inside the container it will be reachable as `postgres`.

We then assign the name of the container to be `app_web_1` and instrust Docker Compose that it depends on the `db` service to be up.

The next two statements, `stdin_open` and `tty` are added so that we can execute the Python debugger and examine it from outside the container.

The rest of the web service definition is the environment variables. As you can see they are the similar to the ones we defined on the `.quartenv` file on our previous lesson, with some extra ones for the database user and password.

Next we'll define the Postgres database docker instance:

{lang=yml,line-numbers=on,starting-line-number=24}
```
  db:
    image: postgres:13-alpine
    restart: always
    container_name: app_db_1
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: app_user
      POSTGRES_PASSWORD: app_password
      POSTGRES_DB: app
```

This file is pretty much self-explanatory. We will use the Postgres 13 alpine image, instruct the container to always restart, put a name for it and open port 5432 to the host, which is the standard Postgres port.

[Save the file](https://fmze.co/fftq-4.2.2).

We won't start the Docker container yet, as we need a couple of more things in place.

## Initial Setup <!-- 4.3 -->

So let’s go ahead and start setting up our Quart counter application. Like I’ve done in other courses, we’re going to build a web application that stores a counter in the database and increases it by one every time you reload the page. This will allow us to see how a typical Quart database application is laid out.

One new thing we’ll use here is Alembic for database migrations. Alembic is what powers Flask-Migrations under the hood. Even though it’s a bit more complicated to set it up the first time, we will be using this application as a boilerplate when we create other database-driven Quart applications down the road, so we won’t have to repeat the setup from scratch again.

Let's initialize the Poetry environment with Quart and python-dot-env. You should have Poetry installed from the previous module, but if you haven't go ahead and install it by following the instructions [on this page](https://python-poetry.org/docs/#installation).

So type the following command: 

{lang=bash,line-numbers=off}
```
$ poetry init -n --name counter_app --python ^3.7 --dependency quart@0.15.1 --dependency python-dotenv@0.10.1`.
```

[This will write](https://fmze.co/fftq-4.3.1) the `pyproject.toml` but won't install the packages.

Now let's create the Quart environment variables that will be loaded to our environment by `python-dotenv`.

So create the `.quartenv` file and type the following code:

{lang=python,line-numbers=on}
```
QUART_APP='manage.py'
QUART_ENV=development
SECRET_KEY='my_secret_key'
DB_USERNAME=app_user
DB_PASSWORD=app_password
DB_HOST=localhost
DATABASE_NAME=app
```

First, the `QUART_APP` will be the kickstarter `manage.py` file that creates an instance of our application using the Factory pattern, just like I’ve done previously on my Flask course.

Next we’ll define the `QUART_ENV` environment as `development` so that we have meaningful error pages. We’ll also add a `SECRET_KEY`; even though it’s not essentially needed, it’s a good practice to have it.

The next five variables, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, and `DATABASE_NAME` will allow us to connect to the database. We'll use a generic `app` prefix for the user, password and database so that we don't have to worry when we use the same code for other applications.

[Save the file](https://fmze.co/fftq-4.3.2).

We’ll now need to create a `settings.py` file, so we’ll use very similar variables from the `.quartenv` with the following format:

{lang=python,line-numbers=on}
```
import os

QUART_APP=os.environ['QUART_APP']
QUART_ENV=os.environ['QUART_ENV']
SECRET_KEY = os.environ["SECRET_KEY"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
```

As we saw earlier, `python-dotenv` will load the variables in `.quartenv` and load it as environment variables in our computer, so then `settings.py` can access them using `os.environ`. We do this so that we can then deploy to a production environment easily with the proper environment variables set in the production hosts. [Save the file](https://fmze.co/fftq-4.3.3).

## Application Setup <!-- 4.4 -->

At this point we’re ready to start building our Quart counter application. 

So start the Docker client if you haven't already, and type the following on your terminal. Make sure you're on the counter application folder.

{lang=bash,line-numbers=off}
```
docker-compose up
```

Docker will start downloading the Postgres and Ubuntu images and set up your containers. Be patient, this might take a few minutes on the first run, but should be faster after that.

When everything is done, you will get an error building the web container, which is expected, but your Docker client should show the database service up and running.

We’ll install some database packages we will need. The first is `psycopg2-binary`, a library that allows Python applications to connect to Postgres databases. We'll also install the `databases` package that allows async connection to databases.

The third, as we mentioned earlier, is the SQLAlchemy library, but even though we’ll install the whole package, we’ll be using the Core module for our application.

So open the `pyproject.toml` file and add the following on the `[tool.poetry.dependencies]` section:

{lang=python,line-numbers=on,starting-line-number=11}
```
psycopg2-binary = "2.9.1"
databases = {version = "0.4.1", extras = ["postgresql"]}
sqlalchemy = "1.4"
```

[Save the file](https://fmze.co/fftq-4.4.1).

We haven't initialized our local Poetry environment, and we want to do that for two reasons:

First, installing the Poetry packages on the host machine allows our code editor to understand the packages and do linting so that we can see issues as we write the code.

Second, this will allow us to do a "hybrid" approach where we run the application on the host machine, but connect to the database on the Docker container, which allows us to run the application as well as tests without having to rebuild the web Docker container. 

For example, in my Visual Studio Code editor, I can have tests run from the UI or start/stop the application with one button. I have added the `vscode` configuration on the repository if you want to add it to your folder by heading over [to this URL](https://fmze.co/fftq-4.4.2).

Once the code is good to go, you can re-build the web app container and run the whole stack from Docker.

So stop the Docker compose with Control-C and go ahead and install all the Poetry packages by doing:

{lang=bash,line-numbers=off}
```
$ poetry install
```

Once that’s done, we’ll go ahead and create our database driver file, so create a new file we’ll call `db.py`.

{lang=python,line-numbers=on}
```
from databases import Database
from quart import current_app
import sqlalchemy

metadata = sqlalchemy.MetaData()


async def db_connection():
    database_url = f"postgresql://{current_app.config['DB_USERNAME']}:"
    database_url += f"{current_app.config['DB_PASSWORD']}@"
    database_url += f"{current_app.config['DB_HOST']}:5432/"
    database_url += f"{current_app.config['DATABASE_NAME']}"
    database = Database(database_url, min_size=5, max_size=20)

    return database
```

First we will import the `Datbase` class from the `databases` package, which gives us asynchronous connection to our Postgres instance.

We’ll also need to import the `current_app` from `quart`. Think of the `current_app` as the currently running instance of the Quart application. We’ll need it to read the settings that we’ve set for the database connection.

Finally, we will import the `sqlalchemy` package to define an application-wide `metadata` object that will track all the models in our application which will allow us to manage migrations when we start using `alembic`.

Next, let’s create the database connection using the user, password, host and database from those settings. Finally we acquire the connection and return it to the caller.

[Save the file](https://fmze.co/fftq-4.4.3).

Now let’s go ahead and create our first and only blueprint of the application, the `counter` module.

First, create the `counter` folder and inside create the empty `__init__.py` to declare it a module.

Then create the `models.py` file with the following contents:

{lang=python,line-numbers=on}
```
from sqlalchemy import Table, Column, Integer

from db import metadata

counter_table = Table(
    "counter",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("count", Integer),
)
```

We’ll begin by importing some modules from `sqlalchemy`. The names might sound familiar: `Table` allows us to setup a table in the database, `Column` allows us to create the table columns and `Integer` which is the only column type we use.

We also import our `metadata` object which will allow us to do introspection about the table schema when we use migrations. You need this object in any model you create.

Then, we define our `counter_table` as a table consisting of two columns: our `id` which will be the primary key and `count` which will hold the current counter of the application. Notice we define the table name as `counter` and add the `metadata` object as part of the definition.

[Save the file](https://fmze.co/fftq-4.4.4).

Now let’s go ahead and build the `views.py` file which will be our main controller and blueprint.

{lang=python,line-numbers=on}
```
from quart import Blueprint, current_app, Response

from counter.models import counter_table

counter_app = Blueprint("counter_app", __name__)


@counter_app.route("/")
async def init() -> str:
    conn = current_app.dbc  # type: ignore
    counter_query = counter_table.select()
    result = await conn.fetch_all(query=counter_query)
    count = None

    if not len(result):
        stmt = counter_table.insert().values(count=1)
        result = await conn.execute(stmt)
        await conn.execute("commit")
        count = 1
    else:
        row = result[0]
        count = row["count"] + 1
        counter_update = counter_table.update(
            counter_table.c.id == row["id"]
        ).values({"count": count})
        result = await conn.execute(counter_update)
        await conn.execute("commit")
    return "<h1>Counter: " + str(count) + "</h1>"
```

We’ll import `Blueprint` to create the `counter_app` blueprint as well as the `current_app` which we'll need to get the database connection.

We’ll also import our `counter_table` from our model file.

So let’s define the blueprint itself, `counter_app`.

The only route this controller has is the root slash, which will call the `init` function.

We begin by fetching our database connection from the `current_app.dbc`.

Next we build a query which will select all the records in the `counter_table` . In this application it will always be just one record as you’ll see below. We’ll get more familiar with the `select` function from `sqlalchemy`, but for now just think of this as doing a `SELECT * FROM counter_table`.

We then feed the result of the query to the `result` variable, but notice the use of the `await` keyword there. Indeed the connection execution is an asynchronous operation that will resolve into a coroutine which will eventually return the data we need.

We’ll also set an internal variable of `count` to `None`.

We then get to the main forking point of the script. If we don’t get any results from the query, it means it’s the first time we’re running the application, so we’ll build an insert statement, setting the value of the `count` column to `1`. We’ll then `await` the insert statement and store the results in the `result` variable and finally commit it to the database, again using an `await` operation. Since this is the first time we run the application, we can safely say that the `count` variable is `1`.

Now, on the else statement, if do get a result from the select query, we will fetch the first row of the result. We then add `1` to the contents of the `count` column and store it in the local `count` variable.

We then build an update statement with the value of the local `count` variable, execute it and commit it.

Finally we return the value of the `count` variable to the request as HTML content.

As you can already notice, any database connection operations must be awaited, since they are I/O operations that can yield to the event loop.

[Save the file](https://fmze.co/fftq-4.4.5).

Next we’ll create the application factory, as we’ve done in the past in my Flask course. Call this file `application.py`.

{lang=python,line-numbers=on}
```
from quart import Quart

from db import db_connection


def create_app(**config_overrides):
    app = Quart(__name__)

    # Load config
    app.config.from_pyfile("settings.py")

    # apply overrides for tests
    app.config.update(config_overrides)

    # import blueprints
    from counter.views import counter_app

    # register blueprints
    app.register_blueprint(counter_app)

    @app.before_serving
    async def create_db_conn():
        database = await db_connection()
        await database.connect()
        app.dbc = database

    @app.after_serving
    async def close_db_conn():
        await app.dbc.disconnect()

    return app
```

We begin by importing `Quart` and the `db_connection` variable from the `db` file we created earlier.

Next, we define the factory variable as `create_app` with a `config_overrides` parameter that will allow our tests to change the settings environment variables when running them.

We then begin by creating an `app` instance of Quart and configure the app from the `settings.py` file contents. Then, update the app with any changes passed on the `config_overrides` parameter.

After that we import the `counter_app` blueprint from the `views.py` file and register it.

We now need a way for the application to open a reusable connection to the MySQL database server. For that we’ll use a couple of special decorators called `before_serving` and `after_serving`. These decorators setup functions to be executed the first time the application is started and right before the application will be closed, which allows us to open the connection once and keep it open for all requests, without needing to close and open it on a per-request basis.

For the `before_serving` function, we’ll `await` a database connection. We then store this connection in a context variable called `dbc` that will be available anywhere you call the `current_app` in any view or model.

Finally, with the `after_serving` function, we’ll close the database connection properly, so any pending database requests are taken care of.

[Save the file](https://fmze.co/fftq-4.4.6).

We’re almost done with the core application. We just need to create the bootstrap file that will spawn an instance of the application factory. We’ll call this file `manage.py`.

This is a simple file. We just need to import the `create_app` function and then execute it and store it in a variable called `app`.

{lang=python,line-numbers=on}
```
from application import create_app

app = create_app()
```

[Save the file](https://fmze.co/fftq-4.4.7) and let’s go ahead and start with the database migration configuration.

## Configuring Alembic Migrations <!-- 4.5 -->

We’re now going to install Alembic to be able to do database migrations. If you’re not familiar with migrations, it’s just a way to track model changes in your codebase, so that other team members and the different environments can keep up to date as you change your database schema.

So we’ll install Alembic by adding it to the `pyproject.toml` as follows:

{lang=python,line-numbers=on,starting-line-number=14}
```
alembic = "1.6.5"
```

[Save the file](https://fmze.co/fftq-4.5.1).

We will now initialize the migration setup which will create both an `alembic.ini` and a `migrations` folder.

But before that, we need to install all the Poetry packages we've added. 

So type:

{lang=bash,line-numbers=off}
```
$ poetry update
```

Now we're ready for our first migration. Just type:

{lang=bash,line-numbers=off}
```
$ poetry run alembic init migrations
```

You’ll notice there's a new file, `env.py` inside a new `migrations` folder. There's also a new file called `alembic.ini` in the root folder.

We need to tell `alembic` three things.

- First, we need it to use our environment variables to connect to the database.
- Second we need to tell it what models our application uses and finally,
- Third, we need to tell it how to connect to the database.

So let’s begin setting up the environment variables in the `migrations/env.py` file.

Add the following at the top before `logging.config`:

{lang=python,line-numbers=on}
```
import os, sys
from dotenv import load_dotenv
from pathlib import Path
```

We’ll need all these libraries for the next step.

Then add this under `from alembic import context` after line 10:

{lang=python,line-numbers=on,starting-line-number=12}
```
# Path ops
parent = Path(__file__).resolve().parents[1]
load_dotenv(os.path.join(parent, ".quartenv"))
sys.path.append(str(parent))

```

The `parent` variable will figure out the parent folder so that we can fetch the `.quartenv` file location and pass it to the `python-dotenv` and finally we add that parent folder to the `sys.path` so that Alembic has access to it.

Then on line 35 right before the `run_migrations_offline` function, let’s add the following:

{lang=python,line-numbers=on,starting-line-number=35}
```
section = config.config_ini_section
config.set_section_option(section, "DB_USERNAME", os.environ.get("DB_USERNAME"))
config.set_section_option(section, "DB_PASSWORD", os.environ.get("DB_PASSWORD"))
config.set_section_option(section, "DB_HOST", os.environ.get("DB_HOST"))
config.set_section_option(section, "DATABASE_NAME", os.environ.get("DATABASE_NAME"))
```

We’re giving the `alembic.ini` file, which we’ll edit in a little bit, access to the environment variables.

Now we can move to step 2, tell Alembic what models we have in our application. So on line 25 let’s replace that whole block with the following:

{lang=python,line-numbers=on,starting-line-number=25}
```
from db import metadata

from counter.models import counter_table

target_metadata = metadata
```

This is very important to remember: any new models you add subsequently, you need to add them here.

[Save the file](https://fmze.com/fftq-4.5.2).

With all that in place, we’ll finally move to the last step: tell Alembic how to connect to the database.

Open the `alembic.ini` file and change `sqlalchemy.url` on line 42 like this.

{lang=python,line-numbers=on,starting-line-number=42}
```
sqlalchemy.url = postgresql://%(DB_USERNAME)s:%(DB_PASSWORD)s@%(DB_HOST)s:5432/%(DATABASE_NAME)s
```

These variables are coming from the `env.py` we edited earlier. [Save the file](https://fmze.co/fftq-4.5.3).

And with this, we’re ready to run our first migration.

## Our First Migration <!-- 4.6 -->

We’re now ready to create the tables in the database using the Alembic migration workflow. You will notice that the commands look a bit like Git commands. Initially you’ll need to write these down, but once you do it a couple of times, you’ll remember them.

But first, make sure you're Docker database container is up and running. If it isn't, just type `docker-compose up` or start it from the Docker Desktop application or from VSCode's Docker extension.

So now we're ready to create our first “migration commit”. For that just type: `poetry run alembic revision --autogenerate -m "create counter table"`

{lang=bash,line-numbers=off}
```
$ poetry run alembic revision --autogenerate -m "create counter table"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'counter'
  Generating /home/jorescobar/counter_app/migrations/versions/51d999a1e262_cr
  eate_counter_table.py ...  done
```

Thanks to the `target_metadata` setting we added earlier, Alembic can view the status of the database and compare against the table metadata in the application, generating the "obvious" migrations based on a comparison. This is achieved using the `--autogenerate` option to the alembic revision command, which places so-called candidate migrations into our new migrations file.

Check that a new `versions` file was created and take a look:

{lang=python,line-numbers=on}
```
"""create counter table

Revision ID: 2abbbb3287d2
Revises:
Create Date: 2021-11-03 17:43:35.192873

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2abbbb3287d2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('counter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('count', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('counter')
    # ### end Alembic commands ###
```

As you can see, there are three sections: one that holds what revision this is and how to get to the previous one, an `upgrade` list of commands and a `downgrade` list of commands. Always take a look at the newest revision file so that you can spot any inconsistencies or issues.

This looks good to me, so let’s apply these changes on the database by doing the following.

{lang=bash,line-numbers=off}
```
$ poetry run alembic upgrade head
```

You will see the following:

{lang=bash,line-numbers=off}
```
$ poetry run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 2abbbb3287d2, create counter table
```

Great, it went smoothly which means the tables were created. We can log in into Postgres and check the tables.

For that, let's connect to Postgres running in our Docker container by doing:

{lang=bash,line-numbers=off}
```
$ docker exec -it app_db_1 psql postgres -U app_user
```

And from there, you can check that the tables were created:

{lang=mysql,line-numbers=off}
```
postgres-> \c app
You are now connected to database "app" as user "app_user".
app-> \dt
              List of relations
 Schema |      Name       | Type  |  Owner
--------+-----------------+-------+----------
 public | alembic_version | table | app_user
 public | counter         | table | app_user
(2 rows)
```

We can see the counter table was created, but notice there’s an `alembic_version` table. This table holds the current migration version.

{lang=mysql,line-numbers=off}
```
app=> select * from alembic_version;
 version_num
--------------
 51d999a1e262
(1 row)
```

That hash matches with our latest revision value:

{lang=python,line-numbers=on,starting-line-number=12}
```
# revision identifiers, used by Alembic.
revision = '51d999a1e262'
```

Exit the Postgres server and we should be ready to run our application.

{lang=bash,line-numbers=off}
```
$ poetry run quart run
```

If you open `localhost:5000` you will see the first number of our counter:

![Figure 4.8.1](images/4.8.1.png)

Refreshing the page will increase the counter value. And there you have it, your first Quart database-driven application.

Here's something interesting I want you to notice: the Quart application is running in our host machine, and not from the Docker container, which allows us to debug easily and start and stop it quickly. For example, you can set breakpoints in your code editor and debug easily from there.

But if we want to run the whole application from the Docker containers, do the following:

{lang=bash,line-numbers=off}
```
docker-compose up
```

You will see the application in `localhost:5000`.

And this is very important: if you add any Poetry packages to the application, you will need to rebuild the web container doing the following Docker command:

{lang=bash,line-numbers=off}
```
docker-compose up --build
```

That will re-run the Dockerfile script and install any new packages you have added.

## Testing our Counter Application <!-- 4.7 -->

It’s great that we have a running application, but we know that any application needs good tests to insure it won’t break with new development.

In our synchronous applications we had used `unittest`, but for asynchronous applications, I’ve found that `pytest` is a better fit. `Pytest` also has an `asyncio` library that will allow us to test our code better.

So let’s begin by adding those libraries to the application. So just do:

{lang=bash,line-numbers=off}
```
$ poetry add pytest pytest-asyncio
```

Ok, with that out of the way let’s see how `pytest` works.

The `pytest` library works in a modular fashion using reusable functions called _fixtures_. Fixtures allow you to put the repetitive stuff in one function and then add them to the tests that need them.

The cool thing about these fixtures is that they can be used in a layered format, allowing you to build very complex foundations. Unfortunately this is also `pytest`’s Achilles’ heel, as some teams make such complex “fixture onions” that will make any newcomer spend lots of time to learn them. My recommendation is to always make tests as readable as possible, so avoid doing more than three layers of fixtures and keep them as single-purpose as possible with very descriptive names.

These fixtures can live in the same test files that use them or you can put them in a special file called `conftest`. Any `conftest` fixtures on a parent directory are available to the tests in the child directories. You’ll get the hang of it as you start building your tests.

The other difference with `unittest` is that `pytest` doesn’t require classes, although they can still be used.

To follow Poetry's directory structure recommendations, we'll create a `tests` folder on the root level where the `conftest` and all the tests will live.

Then create an `__init__.py` empty file inside the `tests` folder to make sure it's recognized as a Python module.

 Create the `conftest` file inside the `tests` folder and let's start working on it.

First, we’ll add the necessary imports we’ll use.

{lang=python,line-numbers=on}
```
import pytest
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(".quartenv")

from application import create_app
from db import metadata
```

Make sure to place the `load_dotenv` command before the `create_app` factory instantiation so that the environment variables are set.

We will now create the database instantiation fixture for all our tests, so let’s write that:

{lang=python,line-numbers=on,starting-line-number=12}
```
@pytest.fixture
async def create_db():
    print("Creating db")
    db_name = os.environ["DATABASE_NAME"]
    db_host = os.environ["DB_HOST"]
    db_username = os.environ["DB_USERNAME"]
    db_password = os.environ["DB_PASSWORD"]

    db_uri = "postgresql://%s:%s@%s:5432/" % (
        db_username,
        db_password,
        db_host,
    )

    engine = create_engine(db_uri + db_name)
    conn = engine.connect()

    db_test_name = os.environ["DATABASE_NAME"] + "_test"

    # drop database if exists from previous run
    try:
        conn.execute("COMMIT")
        conn.execute(f"DROP DATABASE {db_test_name} WITH (FORCE)")
    except:
        pass

    conn.execute("COMMIT")
    conn.execute("CREATE DATABASE " + db_test_name)
    conn.close()

    print("Creating test tables")
    engine = create_engine(db_uri + db_test_name)
    metadata.bind = engine
    metadata.create_all()
```

By default all pytest fixtures are function level, which means that pytest will create the database from scrath at the beginning of the function and destroy it at the end of the function. This works well for testing purposes, since each test function will work on isolation. For more complex applications, we can leverage fixtures to pre-load data for some of the tests, but we'll see examples of that later on.

We then load the credentials from the `dotenv` file. We then connect to the database and create the test database, which will be called the same as our application database with the string "_test" appended.

We also want to drop the database by default if it exists. This will let us handle interrupted test runs.

Finally we will create all the tables from the models in the application, using the `sqlalchemy` metadata property.

Now here’s something you will see often with `pytest` fixtures and that’s the use of the `yield` statement. 

{lang=python,line-numbers=on,starting-line-number=47}
```
    yield {
        "DB_USERNAME": db_username,
        "DB_PASSWORD": db_password,
        "DB_HOST": db_host,
        "DATABASE_NAME": db_test_name,
        "DB_URI": db_uri + db_test_name,
        "TESTING": True,
    }

    print("Destroying db")
    engine = create_engine(db_uri + db_name)
    conn = engine.connect()

    conn.execute("COMMIT")
    conn.execute(f"DROP DATABASE {db_test_name} WITH (FORCE)")
    conn.close()
```

We’re going to yield the application settings to the next test or fixture that includes it.

Essentially what yield does is to send the control back to the calling test, and you can define what data you want to share with it here. Once the test is completed, the rest of the commands below the yield are executed, so we will write the database cleanup commands in here, which in our case includes destroying the database.

Next, let’s create the Quart application itself.

{lang=python,line-numbers=on,starting-line-number=65}
```
@pytest.fixture
async def create_test_app(create_db):
    app = create_app(**create_db)
    await app.startup()
    yield app
    await app.shutdown()
```

This is also a function-scoped fixture and we will inject the `create_db` fixture to it as a dependency. That’s right: you can inject fixtures in other fixtures — but again, remember to limit the number of fixture layers to keep your tests manageable, like I mentioned earlier. By including `create_db` as a parent fixture to `create_test_app`, we won't need to call `create_db` in our tests, we just include `create_test_app` which in turns guarantees it calls the `create_db` fixture and runs it.

Inside the fixture, we create an instance of the factory `create_app` function and then call the Quart app method `startup` which will run the `before_serving` decorated function, which in our app establishes the database connection.

{lang=python,line-numbers=on,starting-line-number=21}
```
    @app.before_serving
    async def create_db_conn():
        print("Starting app")
        app.sac = await sa_connection()
```

We then yield the app itself to the calling test and once the tests are done, we do the `shutdown` method of the Quart app which calls the `after_serving` function in our `application.py`.

{lang=python,line-numbers=on,starting-line-number=27}
```
    @app.after_serving
    async def close_db_conn():
        print("Closing down app")
        await app.sac.close()
```

One thing I want you to notice, in the instantiation of the `create_app` we are passing the `create_db` fixture returned with a double asterisk in front of it:

{lang=python,line-numbers=on,starting-line-number=57}
```
app = create_app(**create_db)
```

The way this works is that the `create_db` fixture is returning a dictionary of variables which line up with our settings variables. Remember how `create_app` takes overrides as a parameter?

{lang=python,line-numbers=on,starting-line-number=12}
```
    # apply overrides for tests
    app.config.update(config_overrides)
```

This is exactly why, so that we can instantiate test apps with different configuration settings. The double asterisk in Python essentially passes the variables returned by `create_db` as a keyword argument list, so it’s the same as writing the following:

{lang=python,line-numbers=on,starting-line-number=63}
```
app = create_app(DB_USERNAME=create_db['DB_USERNAME'], DB_PASSWORD=create_db['DB_PASSWORD']...)
```

We’re almost there. We’ll create our last fixture, which will allow us to create a test client that we can use to hit the endpoints. This looks like this:

{lang=python,line-numbers=on,starting-line-number=73}
```
@pytest.fixture
def create_test_client(create_test_app):
    print("Creating test client")
    return create_test_app.test_client()
```

We will inject the `create_test_app` fixture from above. Yes, that means we’re already at two fixture levels from the first fixture in the file, but this is the only fixture we will need in our tests, so we’re good.

I just want to highlight how cool fixtures are. We can now just include `create_test_client` in each test, and that will automatically create the database using the `create_db` fixture and create the test application using the `create_test_app` fixture.

We don’t need to yield anything in this case since we don’t need to run any cleanups after the test is done.

[Save the file](https://fmze.co/fftq-4.7.1).

Now let’s create our actual test. Create a file called `test_counter` inside the `tests` folder. Any file that starts with the word `test_` will be automatically discovered by `pytest`.

For our first test, We want to be able to see that the counter is started when we first hit the page.

{lang=python,line-numbers=on,starting-line-number=1}
```
import pytest


@pytest.mark.asyncio
async def test_initial_response(create_test_client):
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 1" in str(body)
```

We need to decorate it as an `asyncio` test, since we’ll be doing I/O operations. We’ll also need the `create_test_client` fixture which will be seting up the test client and its dependencies. 

We then hit the test client with a request and await for the response. The data we get back is stored in the `body` variable and then check that the string “Counter: 1” is in the body.

[Save the file](https://fmze.co/fftq-4.7.2) and run the test using `poetry run pytest`. 

Make sure you're running your Docker Postgres container.

{lang=bash,line-numbers=off}
```
$ docker-compose up db -d
[+] Running 1/1
 ⠿ Container app_db_1  Started 
$ poetry run pytest
================================== test session starts ==================================
platform darwin -- Python 3.9.7, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /opt/quart-db-boilerplate
plugins: asyncio-0.16.0
collected 1 item                                                                        

tests/test_counter.py F                                                           [100%]

======================================= FAILURES ========================================
_________________________________ test_initial_response _________________________________

```

It fails!

What’s the problem? The issue here is that we don't have the `counter` model referenced anywhere, and when the `create_all` method is called on line 56 of the `conftest.py` file, there are no references to any models to be created.

So on line 3 of the `test_counter.py` file, add the following:

{lang=python,line-numbers=on,starting-line-number=3}
```
from counter.models import counter_table
```

[Save the file](https://fmze.co/fftq-4.7.3) and run the test again.

{lang=bash,line-numbers=off}
```
$ poetry run pytest
============================= test session starts ==============================
platform darwin -- Python 3.7.3, pytest-4.5.0, py-1.8.0, pluggy-0.13.0
rootdir: /opt/quart-mysql-boilerplate
plugins: asyncio-0.10.0
collected 1 item

counter/test_counter.py . [100%]

=========================== 1 passed in 0.19 seconds ===========================
```

 ## Completing our tests <!-- 4.8 -->

We now get a green line and the "tests passed label". If you look closer, you'll notice that the print statements we added aren’t being printed. For those to be printed, you need to add a `-s` flag to the command, like so: `poetry run pytest -s`.

{lang=bash,line-numbers=off}
```
$ poetry run pytest -s
================================== test session starts ==================================
platform darwin -- Python 3.9.7, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /opt/quart-db-boilerplate
plugins: asyncio-0.16.0
collected 1 item                                                                        

tests/test_counter.py Creating db
Creating test tables
Creating test client
.Destroying db

=========================== 1 passed in 0.11 seconds ===========================
```

This gives us a good insight of when things are called and the order of operations of our fixtures.

We’ll add just one more test to mark this part complete. I want to evaluate if I hit the page a second time, I get the number two in the counter.

{lang=python,line-numbers=on,starting-line-number=13}
```
@pytest.mark.asyncio
async def test_second_response(create_test_client):
    # Counter 1
    response = await create_test_client.get("/")
    body = await response.get_data()

    # Counter 2
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 2" in str(body)
```

We’ll mark the test as async and we will also need the `create_test_client` fixture we used in the previous test.

First, we generate a response from the homepage which should set the counter's value to "1".  That is because the database is being destroyed and created with each new `pytest` function that runs.

Since we test that the counter value is set to "1" on the first run within the previous test, there's no need to check the value.

Then we hit the page a second time, and this time we assert that the value is indeed "2", if everything is working correctly.

Run the test to see the result:

{lang=bash,line-numbers=off}
```
poetry run pytest -s
================================== test session starts ==================================
platform darwin -- Python 3.9.7, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /opt/quart-db-boilerplate
plugins: asyncio-0.16.0
collected 2 items                                                                       

tests/test_counter.py Creating db
Creating test tables
Creating test client
.Destroying db
Creating db
Creating test tables
Creating test client
.Destroying db


=================================== 2 passed in 1.25s ===================================
```

As you can see from the output, the database was created and destroyed twice.

But now, let's say we want to actually check if the value in the counter collection on the database is indeed "2". To do that, we need to interact with the models, which means we will need an app context. We’ll do that with the following code.

First, we need to import the `current_app` module from Quart to be able to get the database connection. So on line 2 add the following:

{lang=python,line-numbers=on,starting-line-number=2}
```
from quart import current_app
```

Then, add the `create_test_app` fixture to the `test_secord_response` function:

{lang=python,line-numbers=on,starting-line-number=15}
```
async def test_second_response(create_test_client, create_test_app):
```

Then, let's add the code to read the counter value directly from the counter collection.

{lang=python,line-numbers=on,starting-line-number=25}
```
    # check on the model itself
    async with create_test_app.app_context():
        conn = current_app.dbc
        counter_query = counter_table.select()
        result = await conn.fetch_all(counter_query)
        result_row = result[0]
        count = result_row["count"]
        assert count == 2
```

First we create an async context with the `with` Python keyword. Inside the block we can now get the Quart `current_app` context’s SQL connection object `dbc`. We can then build the query, execute it, get the first row and then check that the count column’s value is equal to two.

[Save the file](https://fmze.co/fftq-4.7.4) and run the tests.

{lang=bash,line-numbers=on}
```
$ poetry run pytest -s
================================== test session starts ==================================
platform darwin -- Python 3.9.7, pytest-6.2.5, py-1.11.0, pluggy-1.0.0
rootdir: /opt/quart-db-boilerplate
plugins: asyncio-0.16.0
collected 2 items                                                                       

tests/test_counter.py Creating db
Creating test tables
Creating test client
.Destroying db
Creating db
Creating test tables
Creating test client
.Destroying db


=================================== 2 passed in 1.28s ===================================
```

Looks good!

However, we haven't updated our Web app Docker instance yet, so let's go ahead and do that. On the terminal, type:

{lang=bash,line-numbers=off}
```
$ docker-compose up --build
```

This tells Docker to build all the services on the `docker-compose.yml` file. All the changes we've done to the Poetry packages will now be installed.

The web Docker container should now be up and running and you can visit `localhost:5000` in your browser to see the whole application running.

If you want to run the tests from the Docker quart web container, you can do:

```
docker-compose run --rm web poetry run pytest -s
```

If you are using VSCode, I have added the settings to run tests from the application. Just look for the "bottle" icon and click on it. You will see that in the first run it will detect the tests and add a testing tree.

At this point you can run all the tests by cllicking the run tests doble triangle, or debug using the triangle with the gear. Debugging will respect any breakpoint you add, so the test will stop at that point, and you can further introspect the stack.

And with that we have a working database powered Quart application with testing. We can use this as a boilerplate for any project that uses Quart and Postgres.

If you want to grab the updated boilerplate at any time, just visit [this Github repo](https://github.com/fromzeroedu/quart-postgres-boilerplate).
