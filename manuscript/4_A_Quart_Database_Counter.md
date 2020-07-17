# A Quart Database Counter

As you have seen in my other courses, I like to make real database driven applications using either MySQL or MongoDB.

In the next few lessons, we’ll build a counter app that will be a good boilerplate application for your Mysql-based Quart projects. I will take the concepts from my [Flask MySQL Boilerplate app](https://github.com/fromzeroedu/flask-mysql-boilerplate) but make it asynchronous and of course, use Quart.

But before we start writing the application, we need to understand one of the many quirks we’ll see when working with asynchronous applications, and this one is related to database ORMs. 

## ORMs and Async
For our original Flask MySQL boilerplate application, we used SQLAlchemy, the Python Database ORM or Object Relational Mapper.  However, for async projects we can’t use the same library without some form of penalization.

Flask-SQLAlchemy does work with Quart using the `flask_patch` function we discussed earlier, but it doesn't yield to the event loop when it does I/O. This will mean it cannot handle much concurrent load — [only a couple of concurrent requests](https://gitter.im/python-quart/lobby?at=5cd1da132e2caa1aa625ef83).

There’s also some issues that I won’t go into in too much detail, having to do with the overhead of how Python handles MySQL connections and the type of locking your transactions can do. I suggest you read [this blog post](http://techspot.zzzeek.org/2015/02/15/asynchronous-python-and-databases/) from Mike Bayer, the author of SQLAlchemy if you want to learn more about the subject. 

However, we don’t need to go back to using raw SQL queries in our codebase. It just happens that we can use the SQLAlchemy Core package from SQLAlchemy, which allows us to express queries in a nice way without the ORM overhead.

We’ll also be using the `aiomyql` package to connect to MySQL asynchronously.

So let’s go ahead and start coding our Quart MySQL boilerplate.

## Initial Setup
So let’s go ahead and start setting up our Quart MySQL boilerplate application. Like I’ve done in other courses, we’re going to build a counter application that stores a counter in MySQL and increases it by one every time you reload the page. This will allow us to see how a typical Quart MySQL application is laid out.

One new thing we’ll use here is Alembic for database migrations. Alembic is what powers Flask-Migrations under the hood, but Flask-Migrations won’t work with Quart since it uses the ORM component. Even though it’s a bit more complicated to set it up the first time, we will be using this boilerplate when we create other MySQL Quart applications down the road, so we won’t have to repeat the setup from scratch again.

So let’s begin by creating the Quart environment variables that will be loaded to our environment by `python-dotenv`. 

Make sure to create the project’s folder. I’ll call mine `quart-mysql-boilerplate`. Once that’s done, change the directory inside that folder.

So create the `.quartenv` file and type the following code:

{lang=bash,line-numbers=off}
```
QUART_APP='manage.py'
QUART_ENV=development
SECRET_KEY='my_secret_key'
DB_USERNAME=counter_user
DB_PASSWORD=counter_password
DB_HOST=localhost
DATABASE_NAME=counter
MYSQL_ROOT_PASSWORD=rootpass
```

First, the `QUART_APP` will be small kickstarter `manage.py` file that creates an instance of our application using the Factory pattern, just like I’ve done previously on my Flask course. 

Next  the `QUART_ENV` environment we’ll define as `development` so that we have meaningful error pages. We’ll also add a `SECRET_KEY`; even though it’s not essentially needed, it’s a good practice to have it.

The next five variables, `DB_USERNAME`, `DB_PASSWORD`, `DB_HOST`, and `DATABASE_NAME` will allow us to connect to the database. The `MYSQL_ROOT_PASSWORD` is needed so that our test utility can create the test database and destroy it on demand.

Save the file[^1].

We’ll now need to create a `settings.py` file, so we’ll use very similar variables from the `.quartenv` with the following format:

{lang=python,line-numbers=on}
```
import os

SECRET_KEY = os.environ["SECRET_KEY"]
DB_USERNAME = os.environ["DB_USERNAME"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
DB_HOST = os.environ["DB_HOST"]
DATABASE_NAME = os.environ["DATABASE_NAME"]
MYSQL_ROOT_PASSWORD = os.environ["MYSQL_ROOT_PASSWORD"]
```

As we saw earlier, `python-dotenv` will load the variables In `.quartenv` and load it as environment variables in our computer, so then `settings.py` can access them using `os.environ`. We do this so that we can then deploy to a production environment easily with the proper environment variables set in the production hosts. Save the file[^2].

We’ll now initialize our `pipenv` environment using the `python 3.7` initialization to guarantee we have the right Python version in the `Pipfile`.

{lang=bash,line-numbers=off}
```
$ pipenv install --python 3.7
Creating a virtualenv for this project…
Pipfile: /opt/quart-mysql-boilerplate/Pipfile
Using /usr/local/bin/python3 (3.7.3) to create virtualenv…
⠼ Creating virtual environment...Using base prefix '/usr/local/Cellar/python/3.7.3/Frameworks/Python.framework/Versions/3.7'
New python executable in /opt/quart-mysql-boilerplate/.venv/bin/python3.7
Also creating executable in /opt/quart-mysql-boilerplate/.venv/bin/python
Installing setuptools, pip, wheel...
done.
Running virtualenv with interpreter /usr/local/bin/python3

Successfully created virtual environment!
Virtualenv location: /opt/quart-mysql-boilerplate/.venv
Creating a Pipfile for this project…
Pipfile.lock not found, creating…
Locking [dev-packages] dependencies…
Locking [packages] dependencies…
Updated Pipfile.lock (a65489)!
Installing dependencies from Pipfile.lock (a65489)…
0/0 — 00:00:00
To activate this project's virtualenv, run pipenv shell.
Alternatively, run a command inside the virtualenv with pipenv run.
```

You might notice that the virtual environment that `Pipenv` created was located inside my working directory. This is not the default behavior, but I like to have the `venv` directory alongside my code, without committing it. To make that your default behavior, you need to set an environment variable in your host with the name `PIPENV_VENV_IN_PROJECT` set to `enabled`. On Mac you can add it to your `bash_profile` like this:

{lang=python,line-numbers=off}
```
export PIPENV_VENV_IN_PROJECT="enabled"
```

 In Windows 10, just edit your System Environment variables and set it. You can find them by typing `env` on your Windows search and click on the “Edit the System Environment Variables”.

![Figure 4.2.1](images/4.2.1.png)

Then click on the “Environment Variables” button on the lower right.

![Figure 4.2.2](images/4.2.2.png)

Click the “New” button, add the `PIPENV_VENV_IN_PROJECT` variable and set the value to “enabled”.

![Figure 4.2.3](images/4.2.3.png)

Now let’s go ahead and install Quart and `python-dotenv`.

{lang=bash,line-numbers=off}
```
$ pipenv install quart python-dotenv 
```

We’re now ready to start setting up MySQL and Alembic migrations.


[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-1/.quartenv

[^2]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-1/settings.py

## Setting up MySQL

Let’s now start to setup our MySQL server to connect to our application.

The following sections describe how to install MySQL locally and setup the counter database for Windows and Mac. Skip to the lesson that applies to you. 

If you want to use Docker, check out the lesson at the end of this section.

### Installing MySQL on Mac with Homebrew
Thanks to Homebrew installing MySQL on the Mac is pretty simple.  

 If you don’t have Homebrew, please follow the instructions [on their page](https://brew.sh).

Just do the following:
`brew install -y mysql`

If you want MySQL to launch automatically whenever you power on your Mac, you can do: `brew services start mysql`. I really don’t recommend that. Instead you can start it manually when you need it by doing `mysql.server start` and stopping with `mysql.server stop`.

Let’s check if mysql is working. Start the server by doing `mysql.server start` and then logging in using `mysql -uroot`. Exit using `exit;`

Now secure the installation by doing: `mysql_secure_installation`. MySQL offers a “validate password” plugin, but we won’t use that. Just type “n” and then enter a password. I will use “rootpass” as my root password. 

I will also remove the anonymous user and remove the ability to remote root login. I will also remove the test database and reload the privileges.

### Setting up a user, password and database for the application
It’s a good practice to create the database with a specific user and password and not use the root user from the application. 

In the next section we will be creating a visitor counter application, so we will create a database called “counter”. We will access this database with the user “counter\_app” and the password “mypassword”.

So, login to MySQL with your root user and password:
`mysql -uroot -prootpass`

Create the database:
`CREATE DATABASE counter;`

And now create the user and password:
`CREATE USER 'counter_app'@'%' IDENTIFIED BY 'mypassword';`

Allow the user full access to the database:
`GRANT ALL PRIVILEGES ON counter.* TO 'counter_app'@'%';`

And reload the privileges:
`FLUSH PRIVILEGES;`

Now exit using `CTRL-D` and try to login using the new app user:
`mysql -ucounter_app -pmypassword`

If you are able to login, you’re in good shape. Now try to use the `counter` database:
`USE counter;`

If you don’t get an error, we’re good. Now logout using `exit;`

## Installing MySQL on Windows 10 with Chocolatey
Thanks to Chocolatey, installing MySQL on Windows is pretty simple. We will install the MariaDB package which works exactly like MySQL. 

If you don’t have Chocolatey, please follow the instructions [on their page](https://chocolatey.org/).

Open a PowerShell as an administrator and type:
`choco install -y mariadb`

Now close the PowerShell application completely and open a new, regular session.

Let’s check if mysql is working. Log in using `mysql -uroot`. Exit using `exit;`

Secure the installation by creating a root password. I will use “rootpass”.  Type: `mysqladmin --user=root password "rootpass"` and press enter.

Now try logging in using `mysql -uroot -prootpass`.

If you login, it means everything is working. Exit using `CTRL-C`.

### Setting up a user, password and database for the application
It’s a good practice to create the database with a specific user and password and not use the root user from the application. 

In the next section we will be creating a visitor counter application, so we will create a database called “counter”. We will access this database with the user “counter_app” and the password “mypassword”.

So, login to MySQL with your root user and password:
`mysql -uroot -prootpass`

Create the database:
`CREATE DATABASE counter;`

And now create the user and password:
`CREATE USER 'counter_app'@'%' IDENTIFIED BY 'mypassword';`

Allow the user full access to the database:
`GRANT ALL PRIVILEGES ON counter.* TO 'counter_app'@'%';`

And reload the privileges:
`FLUSH PRIVILEGES;`

Now exit using `CTRL-C` and try to login using the new app user:
`mysql -ucounter_app -pmypassword`

If you are able to login, you’re in good shape. Now try to use the `counter` database:
`USE counter;`

If you don’t get an error, we’re good. Now logout using `exit;`

## Application Setup
At this point we’re ready to start building our Quart counter application. You should have MySQL server up and running with your counter database and user.

We’ll install a couple of database packages we will use. The first is `aiomysql`,  a library that allows Python applications to connect to MySQL asynchronously. This is normally done by the `PyMySQL` package in synchronous applications.

The second, as we mentioned, is the SQLAlchemy library, but even though we’ll install the whole package, we’ll be using the Core module for our application.

So go ahead and do:

{lang=bash,line-numbers=off}
```
$ pipenv install aiomysql sqlalchemy
```

Once that’s done, we’ll go ahead and create our database driver file, so go ahead and create a new file we’ll call `db.py`.

{lang=python,line-numbers=on}
```
from aiomysql.sa import create_engine
from quart import current_app


async def sa_connection():
    engine = await create_engine(
        user=current_app.config["DB_USERNAME"],
        password=current_app.config["DB_PASSWORD"],
        host=current_app.config["DB_HOST"],
        db=current_app.config["DATABASE_NAME"],
    )
    conn = await engine.acquire()
    return conn
```

First we will import the `create_engine` from the SqlAlchemy, or `sa` package inside `aiomysql`. We’ll also need to import the `current_app` from `quart`.

Think of the `current_app` as  the currently running instance of the Quart application. We’ll need it to read the settings that we’ve set for the database connection. Sp let’s create the engine using the user, password, host and database from those settings. We finally acquire the connection and return it to the caller.

Save the file[^1].

Now let’s go ahead and create our first and only blueprint of the application, the  `counter` module.

First, create the `counter` folder and inside create the empty `__init__.py` to declare it a module.

Then create the `models.py` file with the following contents: 

{lang=python,line-numbers=on}
```
from sqlalchemy import Table, Column, Integer, MetaData

metadata = MetaData()

counter_table = Table(
    "counter",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("count", Integer),
)
```

We’ll begin by importing some modules from `sqlalchemy`. The names might sound familiar: `Table` allows us to setup a table in the database, `Column` allows us to create the table columns, `Integer` is the only column type we use and finally `Metadata` which will allow us to do introspection about the table schema when we use migrations.

So let’s get the metadata out of the way first. Then, we define our `counter_table` as a table consisting of two columns: our `id` which will be the primary key and `count` which will hold the current counter of the application. Notice we also define the table with the `metadata` instance.

Save the file[^2]. 

Now let’s go ahead and build the `views.py` file which will be our main controller and blueprint.

{lang=python,line-numbers=on}
```
from quart import Blueprint, current_app
from sqlalchemy.sql import select

from counter.models import counter_table

counter_app = Blueprint("counter_app", __name__)


@counter_app.route("/")
async def init():
    conn = current_app.sac
    counter_query = select([counter_table])
    result = await conn.execute(counter_query)
    count = None

    if result.rowcount == 0:
        stmt = counter_table.insert(None).values(count=1)
        result = await conn.execute(stmt)
        await conn.execute("commit")
        count = 1
    else:
        row = await result.fetchone()
        count = row[counter_table.c.count] + 1
        stmt = counter_table.update(None).values(count=count)
        result = await conn.execute(stmt)
        await conn.execute("commit")
    return "<h1>Counter: " + str(count) + "</h1>"
```

We’ll import `Blueprint` to create the `counter_app` blueprint as well as the `current_app` which we'll need to get the database connection. Since we will be doing a select query, we’ll also import that from `SQLAlchemy`.

We’ll also import our `counter_table` from our model file.

So let’s define the blueprint itself, `counter_app`.

The only route this controller has is the root slash, which will call the `init` function.

We begin by fetching our database connection and building a query which will select all the records in the `counter_table` . In this application it will always be just one record as you’ll see below. We’ll get more familiar with the `select` function of `sqlalchemy` but for now just think of this as doing a `SELECT * FROM counter_table`.

We then feed the result of the query to the `result` variable, but notice the use of the `await` keyword there. Indeed the connection execution is an asynchronous operation that will resolve into a coroutine which will eventually resolve with the data we need.

We’ll also set an internal variable of `count` to `None`.

We then get to the main forking point of the script. If we don’t get any results from the query, it means it’s the first time we’re running the application, so we’ll build an insert statement, setting the value of the `count` column to `1`. We’ll then `await` the insert statement and store the results in the `result` variable and finally commit it to the database, again using an `await` operation.  Since this is the first time we run the application, we can safely say that the `count` variable is `1`.

Now if do get a result from the select query, we will fetch the first row of the result. We then add `1` to the contents of the `count` column and store it in the local `count` variable. We then build an update statement with the value of the local `count` variable, execute it and commit it.

Finally we return the value of the `count` variable to the request as HTML content.

As you can already notice, any database connection operations must be awaited, since they are I/O operations that can yield to the event loop.

Save the file[^3].

Next we’ll create the application factory, as we’ve done in the past in my Flask course. Call this file `application.py`.

{lang=python,line-numbers=on}
```
from quart import Quart

from db import sa_connection


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
        print("starting app")
        app.sac = await sa_connection()

    @app.after_serving
    async def close_db_conn():
        print("closing down app")
        await app.sac.close()

    return app
```

We begin by importing `Quart` and the `sa_connection` variable from the `db` file we created earlier.

Next, we define the factory variable as `create_app` with a `config_overrides` parameter that will allow our tests to change the settings environment variables when running them.

We then begin by creating an `app` instance of Quart and configure the app from the `settings.py` file contents. Then, update the app with any changes passed on the `config_overrides` parameter.

After that we import the `counter_app` blueprint from the `views.py` file and register it.

We now need a way for the application to open a reusable connection to the MySQL database server. For that we’ll use a couple of special decorators called `before_serving` and `after_serving`. These decorators setup functions to be executed the first time the application is started and right before the application will be closed, which allows us to open the connection once and keep it open for all requests, without needing to close and open it on a per-request basis.

For the `before_serving` function, we’ll put a short message to confirm we’re starting the app and then `await` a database connection. We’ll store this connection in a context variable called `sac` that will be available anywhere you call the `current_app` in any view or model.

Finally, with the `after_serving` function, we’ll close the database connection properly, so any pending database requests are properly taken care of.

Save the file[^4].

We’re almost done with the core application. We just need to create the bootstrap file that will spawn an instance of the application factory. We’ll call this file `manage.py`.

This is a simple file. We just need to import the `create_app` function and then execute it and store it in a variable called `app`.

{lang=python,line-numbers=on}
```
from application import create_app

app = create_app()
```

Save the file[^5] and let’s go ahead and start with the database migration configuration.

[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-2/db.py

[^2]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-3/counter/models.py

[^3]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-3/counter/views.py

[^4]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-3/application.py

[^5]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-3/manage.py

## Configuring Alembic Migrations
We’re now going to install Alembic to be able to do database migrations. If you’re not familiar with migrations, it’s just a way to track model changes in your codebase, so that other team members and the different environments can keep up to date as you change your database schema.

So we’ll install Alembic by doing:

{lang=bash,line-numbers=off}
```
$ pipenv install alembic
```

We will now initialize the migration setup which will create both an `alembic.ini` and a `migrations` folder.

So do:

{lang=bash,line-numbers=off}
```
$ pipenv run alembic init migrations
```

If you do an `ls` you’ll see the `alembic.ini` file and the `migrations` folder[^1].

We need to tell `alembic` three things. 
- First, we need it to use our environment variables to connect to the database.
- Second we need to tell it what models our application uses and finally,
- We need to tell it how to connect to the database.

So let’s begin setting up the environment variables in the `migrations/env.py` file.

Add the following at the top before `logging.config`:

{lang=python,line-numbers=on}
```
import os, sys
from dotenv import load_dotenv
from pathlib import Path
```

We’ll need all these libraries for the next step.

Then add this under `from alembic import context` on line 10:

{lang=python,line-numbers=on,starting-line-number=12}
```
# Path ops
parent = Path(__file__).resolve().parents[1]
load_dotenv(os.path.join(parent, ".quartenv"))
sys.path.append(str(parent))
```

The `parent` variable will figure out the parent folder so that we can fetch the `.quartenv` file location and pass it to the `python-dotenv` and finally we add that parent folder to the `sys.path` so that Alembic has access to it.

Then on line 35 right  before the `run_migrations_offline` function, let’s add the following:

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
# import all application models here
from counter.models import metadata as CounterMetadata

# and then add them here as a list
target_metadata = [CounterMetadata]
```

This is very important to remember: any new models you add subsequently, you need to add them here.

Save the file[^2].

With all that in place, we’ll finally move to the last step: tell Alembic how to connect to the database.

Open the `alembic.ini` file and change `sqlalchemy.url` on line 38 like this. 

{lang=python,line-numbers=on,starting-line-number=38}
```
sqlalchemy.url = mysql+pymysql://%(DB_USERNAME)s:%(DB_PASSWORD)s@%(DB_HOST)s:3306/%(DATABASE_NAME)s
```

These variables are coming from the `env.py` we edited earlier. Save the file[^3].

And with this, we’re ready to run our first migration.

[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/tree/step-4

[^2]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-5/migrations/env.py

[^3]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-5/alembic.ini
