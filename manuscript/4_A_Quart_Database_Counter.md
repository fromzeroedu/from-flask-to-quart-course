# A Quart Database Counter <!-- 4 -->

As you have seen in my other courses, I like to make real database driven applications using either MySQL or MongoDB.

In the next few lessons, we’ll build a counter app that will be a good boilerplate application for your Mysql-based Quart projects. I will take the concepts from my [Flask MySQL Boilerplate app](https://github.com/fromzeroedu/flask-mysql-boilerplate) but make it asynchronous and of course, use Quart.

But before we start writing the application, we need to understand one of the many quirks we’ll see when working with asynchronous applications, and this one is related to database ORMs. 

## ORMs and Async <!-- 4.1 -->
For our original Flask MySQL boilerplate application, we used SQLAlchemy, the Python Database ORM or Object Relational Mapper.  However, for async projects we can’t use the same library without some form of penalization.

Flask-SQLAlchemy does work with Quart using the `flask_patch` function we discussed earlier, but it doesn't yield to the event loop when it does I/O. This will mean it cannot handle much concurrent load — [only a couple of concurrent requests](https://gitter.im/python-quart/lobby?at=5cd1da132e2caa1aa625ef83).

There’s also some issues that I won’t go into in too much detail, having to do with the overhead of how Python handles MySQL connections and the type of locking your transactions can do. I suggest you read [this blog post](http://techspot.zzzeek.org/2015/02/15/asynchronous-python-and-databases/) from Mike Bayer, the author of SQLAlchemy if you want to learn more about the subject. 

However, we don’t need to go back to using raw SQL queries in our codebase. It just happens that we can use the SQLAlchemy Core package from SQLAlchemy, which allows us to express queries in a nice way without the ORM overhead.

We’ll also be using the `aiomyql` package to connect to MySQL asynchronously.

So let’s go ahead and start coding our Quart MySQL boilerplate.

## Initial Setup <!-- 4.2 -->
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

## Setting up MySQL <!-- 4.3 -->

Let’s now start to setup our MySQL server to connect to our application.

The following sections describe how to install MySQL locally and setup the counter database for Windows and Mac. Skip to the lesson that applies to you. 

If you want to use Docker, check out the lesson at the end of this section.

### Installing MySQL on Mac with Homebrew <!-- 4.4 -->
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

## Installing MySQL on Windows 10 with Chocolatey <!-- 4.5 -->
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

## Application Setup <!-- 4.6 -->
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

## Configuring Alembic Migrations <!-- 4.7 -->
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

## Our First Migration <!-- 4.8 -->

We’re now ready to create the tables in the database using the Alembic migration workflow. You will notice that the commands look a bit like Git commands. Initially you’ll need to write these down, but once you do it a couple of times, you’ll remember them.

So we’ll create our first “migration commit”, by running:

{lang=bash,line-numbers=off}
```
$ pipenv run alembic revision --autogenerate -m "create counter table"
```

Thanks to the `target_metadata` setting we added earlier, Alembic can view the status of the database and compare against the table metadata in the application, generating the “obvious” migrations based on a comparison. This is achieved using the `--autogenerate` option to the alembic revision command, which places so-called candidate migrations into our new migrations file.

Make sure your MySQL server is up and running, then execute the command and you should see something like the following:

{lang=bash,line-numbers=off}
```
$ pipenv run alembic revision --autogenerate -m "create counter table"
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'counter'
  Generating /opt/quart-mysql-
  boilerplate/migrations/versions/2abbbb3287d2_create_counter_table.py ... done
```

Check that a new `versions` file[^1] was created and take a look:

{lang=python,line-numbers=on}
```
"""create counter table

Revision ID: 2abbbb3287d2
Revises: 
Create Date: 2019-09-19 10:46:47.608330

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

This looks good to me, so let’s apply these changes on the database by doing:

{lang=bash,line-numbers=off}
```
$ pipenv run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl MySQLImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 2abbbb3287d2, create counter table
```

Great, it went smoothly which means the tables were created. We can log in into MySQL and check the tables.

{lang=mysql,line-numbers=off}
```
mysql> use counter;
mysql> show tables;
+-------------------+
| Tables_in_counter |
+-------------------+
| alembic_version   |
| counter           |
+-------------------+
2 rows in set (0.00 sec)
```

We can see the counter table was created, but notice there’s an `alembic_version` table. This table holds the current migration version.

{lang=mysql,line-numbers=off}
```
mysql> select * from alembic_version;
+--------------+
| version_num  |
+--------------+
| 2abbbb3287d2 |
+--------------+
1 row in set (0.00 sec)
```

That hash matches with our latest revision value:

{lang=python,line-numbers=off}
```
# revision identifiers, used by Alembic.
revision = '2abbbb3287d2'
```

Exit the MySQL server and we should be ready to run our application. Just do:

{lang=bash,line-numbers=off}
```
$ pipenv run quart run
Running on http://127.0.0.1:5000 (CTRL + C to quit)
starting app
Running on 127.0.0.1:5000 over http (CTRL + C to quit)
```

If you open `localhost:5000` you will see the first number of our counter:

![Figure 4.8.1](images/4.8.1.png)

Refreshing the page will increase the counter value. And there you have it, your first Quart database-driven application.

[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-5/migrations/versions/2abbbb3287d2\_create\_counter\_table.py

## Testing our Counter Application <!-- 4.9 -->
It’s great that we have a running application, but we know that any application needs good tests to insure it won’t break with new development.

In our synchronous applications we had used `unittest`, but for asynchronous applications, I’ve found that `pytest` is a better fit. `Pytest` also has an `asyncio` library that will allow us to test our code better.

So let’s begin by adding those libraries to the application. So just do:

{lang=bash,line-numbers=off}
```
$ pipenv install pytest pytest-asyncio
```

Ok, with that out of the way let’s see how `pytest` works.

The `pytest` library works in a modular fashion using reusable functions called _fixtures-_. Fixtures allow you to put the repetitive stuff in one function and then add them to the tests that need them. 

The cool thing about theses fixtures is that they can be used in a layered format, allowing you to build very complex foundations. Unfortunately this is also `pytest`’s Achilles’ heel, as some teams make such complex “fixture onions” that will make any newcomer spend lots of time to learn them. My recommendation is to always make tests as readable as possible, so avoid doing more than three layers of fixtures and keep them as single-purpose as possible with very descriptive names.

These fixtures can live in the same test files that use them or you can put them in a special file called `conftest`. Any `conftest` fixtures on a parent directory are available to the tests in the child directories. You’ll get the hang of it as you start building your tests.

The other difference with `unittest` is that `pytest` doesn’t require classes, although they can still be used.

So let’s create our first `conftest` file. Create it on the root application folder.

First, we’ll add the necessary imports we’ll use.

{lang=python,line-numbers=on}
```
import pytest
import asyncio
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv(".quartenv")

from application import create_app
```

Make sure to place the `load_dotenv` command before the `create_app` factory instantiation so that the environment variables are set.

We will now create the database instantiation part of our test, so let’s write that:

{lang=python,line-numbers=on,starting-line-number=13}
```
@pytest.mark.asyncio
@pytest.fixture(scope="module")
async def create_db():
    print("Creating db")
    db_name = os.environ["DATABASE_NAME"] + "_test"
    db_host = os.environ["DB_HOST"]
    db_root_password = os.environ["MYSQL_ROOT_PASSWORD"]
    if db_root_password:
        db_username = "root"
        db_password = db_root_password
    else:
        db_username = os.environ["DB_USERNAME"]
        db_password = os.environ["DB_PASSWORD"]

    db_uri = "mysql+pymysql://%s:%s@%s:3306" % (db_username, db_password, db_host)

    engine = create_engine(db_uri)
    conn = engine.connect()
    conn.execute("CREATE DATABASE " + db_name)
    conn.execute("COMMIT")
    conn.close()

    yield {
        "DB_USERNAME": db_username,
        "DB_PASSWORD": db_password,
        "DB_HOST": db_host,
        "DATABASE_NAME": db_name,
        "DB_URI": db_uri,
        "TESTING": True,
    }

    print("Destroying db")
    engine = create_engine(db_uri)
    conn = engine.connect()
    conn.execute("DROP DATABASE " + db_name)
    conn.execute("COMMIT")
    conn.close()
```

First we need two decorators: one called `mark.asyncio` which will tell `pytest` that we have async operations in the test or fixture. 

We also need to tell `pytest` that this is a module-level fixture, which means it will be run only once across any modules that import it, and since this `conftest` is in the root folder of the application, it means it will only be run once for all our tests, and that makes sense: we only need to create the test database once.

We then load the credentials from the `dotenv` file. Notice how we have an if/else block that uses the root password if it’s present. If you took my Flask course, you know this is necessary for cloud development IDEs like PythonAnywhere where we don’t have root access. We then connect to the database and create the test database.

Now here’s something you will see often with `pytest` fixtures and that’s the use of the `yield` statement. We’re going to yield the application settings to the next test or fixture that includes it.

Essentially what yield does is to send the control back to the calling test, and you can define what data you want to share with it here. Once the test is completed, the rest of the commands below the yield are executed, so we will write the database cleanup commands in here. We’ll put some print statements to see the order of operations when we run the tests so we can have a better picture of how the fixture is executed.

Next, let’s create the Quart application itself.

{lang=python,line-numbers=on,starting-line-number=55}
```
@pytest.fixture(scope="module")
async def create_test_app(create_db):
    app = create_app(**create_db)
    await app.startup()
    yield app
    await app.shutdown()
```

This also needs to be a module-level fixture and we will inject the `create_db` fixture to it as a dependency. That’s right, you can inject fixtures in other fixtures — but again, remember to limit the number of fixture layers to keep your tests manageable, like I mentioned earlier.

We then create an instance of the factory `create_app` function and then call the Quart app method `startup` which will run the `before_serving` decorated function, which in our app establishes the database connection.

{lang=python,line-numbers=on,starting-line-number=22}
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

{lang=python,line-numbers=on,starting-line-number=13}
```
    # apply overrides for tests
    app.config.update(config_overrides)
```

This is exactly why, so that we can instantiate test apps with different configuration settings. The double asterisk in Python essentially passes the variables returned by `create_db` as a keyword argument list, so it’s the same as writing the following:

{lang=python,line-numbers=on,starting-line-number=57}
```
app = create_app(DB_USERNAME=create_db['DB_USERNAME'], DB_PASSWORD=create_db['DB_PASSWORD']...)
```

We’re almost there. We’ll create our last fixture, which will allow us to create a test client that we can use to hit the endpoints. This looks like this:

{lang=python,line-numbers=on,starting-line-number=63}
```
@pytest.fixture
def create_test_client(create_test_app):
	print("Creating test client")
    return create_test_app.test_client()
```

We will inject the `create_test_app` fixture from above. Yes, that means we’re already at two fixture levels from the first fixture in the file, but this is the only fixture we will need in our tests, so we’re good.

We don’t need to yield anything in this case since we don’t need to run any cleanups after the test is done. Also notice this is not a module-level fixture which means it will be executed with every test that calls it.

Save the file[^1].

Now let’s create our actual test. Create a file called `test_counter` inside the `counter` folder. Any file that starts with the word `test_` will be automatically discovered by `pytest`.

{lang=python,line-numbers=on,starting-line-number=1}
```
import pytest
from quart import current_app
from sqlalchemy import create_engine, select

from counter.models import counter_table, metadata as CounterMetadata


@pytest.fixture(scope="module")
def create_all(create_db):
	print("Creating Counter Tables")
    engine = create_engine(create_db["DB_URI"] + "/" + create_db["DATABASE_NAME"])
    CounterMetadata.bind = engine
    CounterMetadata.create_all()

```

First we do the necessary imports. We’re going to need the counter models to create the database tables as well as access to their metadata.

So first let’s create a fixture that we’ll only need on this test which is to create the counter tables. We will make it a module-level fixture so that it can access the `create_db` properties (which is also a module level fixture).

To do that we create an engine, but notice we will use the dictionary object passed in the yield statement in `create_db` instead of using the actual settings, since this is this test’s custom settings.

We then bind that engine to the `CounterMetadata` object and finally execute the `create_all` method, which will create the counter tables on the database.

Finally we’re ready to create our very first test, so let’s keep it simple. We want to be able to see that the counter is started when we first hit the page.

{lang=python,line-numbers=on,starting-line-number=17}
```
@pytest.mark.asyncio
async def test_initial_response(create_test_client, create_all):
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 1" in str(body)
```

We need to decorate it as an `asyncio` test, since we’ll be doing I/O operations. We’ll also need both the `create_test_client` fixture as well as the `create_counter_tables` fixture. We then hit the test client with a request and await for the response. The data we get back is stored in the `body` variable and then check that the string “Counter: 1” is in the body.

Save the file[^2] and run the test using `pipenv run pytest`.

{lang=bash,line-numbers=off}
```
$ pipenv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.7.3, pytest-4.5.0, py-1.8.0, pluggy-0.13.0
rootdir: /opt/quart-mysql-boilerplate
plugins: asyncio-0.10.0
collected 1 item

counter/test_counter.py E                                                [100%]

==================================== ERRORS ====================================
___________________ ERROR at setup of test_initial_response ____________________
ScopeMismatch: You tried to access the 'function' scoped fixture 'event_loop' with a 'module' scoped request object, involved factories
counter/test_counter.py:9:  def create_counter_tables(create_db)
conftest.py:13:  def create_db(event_loop)
.venv/lib/python3.7/site-packages/pytest_asyncio/plugin.py:204:  def event_loop(request)
=========================== 1 error in 0.02 seconds ============================
```

It fails!

What’s the problem? The issue here is that `pytest` has a built-in function-level event loop that’s not persisted across functions, so we need to grab an event loop at the very top so that this one is persisted. Let’s add it on the `conftest` file.

{lang=python,line-numbers=on,starting-line-number=14}
```
@pytest.fixture(scope="module")
def event_loop(request):
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()
```

Save the file[^3] and run the test again.

{lang=bash,line-numbers=off}
```
$ pipenv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.7.3, pytest-4.5.0, py-1.8.0, pluggy-0.13.0
rootdir: /opt/quart-mysql-boilerplate
plugins: asyncio-0.10.0
collected 1 item

counter/test_counter.py .                                                [100%]

=========================== 1 passed in 0.19 seconds ===========================
```

Perfect! We now get a green line and the test passed label.

But if you notice, the print statements we added aren’t being printed. For those to be printed, you need to add a flag to the command, like so: `pipenv run pytest -s`.

{lang=bash,line-numbers=off}
```
 pipenv run pytest -s
============================= test session starts ==============================
platform darwin -- Python 3.7.3, pytest-4.5.0, py-1.8.0, pluggy-0.13.0
rootdir: /opt/quart-mysql-boilerplate
plugins: asyncio-0.10.0
collected 1 item

counter/test_counter.py Creating db
Creating Counter Tables
Starting app
Creating test client
.Closing down app
Destroying db


=========================== 1 passed in 0.11 seconds ===========================
```

This gives us a good insight of when things are called and the order of operations of our fixtures. Notice that the “Starting app” and “Closing down app” are coming from the `application.py` print statements.

We’ll add just one more test to mark this part complete. I want to evaluate if I hit the page a second time, I get the number two in the counter.

{lang=python,line-numbers=on,starting-line-number=24}
```
@pytest.mark.asyncio
async def test_second_response(
    create_test_app, create_test_client, create_counter_tables
):
    response = await create_test_client.get("/")
    body = await response.get_data()
    assert "Counter: 2" in str(body)
```

We’ll mark the test as async and we will also need the fixtures we used in the previous test as well as the `create_test_app` fixture itself, since we’ll be interacting with the application context.

First, we generate a response from the homepage and check if we get the “Counter: 2” label. Something you will notice different here as compared to the `unittest` library behavior we saw in the past is that the database is _not_ reset between tests. We would have to manually do that by calling the `CounterMetadata.drop_all()` method.

Let’s  now check if the database has the right value. To do that, we need to interact with the models, which means we will  need an app context. We’ll do that with the following:

{lang=python,line-numbers=on,starting-line-number=33}
```
    async with create_test_app.app_context():
        conn = current_app.sac
        counter_query = select([counter_table.c.count])
        result = await conn.execute(counter_query)
        result_row = await result.first()
        count = result_row[counter_table.c.count]
        assert count == 2
```

First we create an async context with the `with` Python keyword. Inside the block we can now get the  Quart`current_app`context’s SQL connection object `sac`. We can then build the query, execute it, get the first row and then check that the count column’s value is equal to two.

Save the file[^4] and run the tests.

{lang=bash,line-numbers=on}
```
$ pipenv run pytest
============================= test session starts ==============================
platform darwin -- Python 3.7.3, pytest-4.5.0, py-1.8.0, pluggy-0.13.0
rootdir: /opt/quart-mysql-boilerplate
plugins: asyncio-0.10.0
collected 2 items

counter/test_counter.py ..                                               [100%]

=========================== 2 passed in 0.13 seconds ===========================
```

Looks good!

And with that we have a working MySQL based Quart application with testing. We can use this as a boilerplate for any project that uses Quart and MySQL.

[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-6/conftest.py

[^2]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-6/counter/test\_counter.py

[^3]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-7/conftest.py

[^4]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-7/counter/test\_counter.py

## Docker Setup <!-- 4.10 -->
Another way to work on the application is by using Docker. There are many benefits of working with Docker that I won't go into, but I would like to show you how to setup our Quart counter application in a Docker environment.

The first thing we need to do is setup the `Dockerfile`. The Dockerfile looks like this:

{lang=python,line-numbers=on,starting-line-number=1}
```
FROM python:3.7.3-slim

# Install pipenv
RUN pip install pipenv

# Make a local directory
RUN mkdir /counter_app

# Set "counter_app" as the working directory from which CMD, RUN, ADD references
WORKDIR /counter_app

# Now copy all the files in this directory to /counter_app
ADD . .

# Install pipenv
RUN pipenv install

# Listen to port 5000 at runtime
EXPOSE 5000

# Define our command to be run when launching the container
CMD pipenv run quart run --host 0.0.0.0
```

First we need to define a Python image. For that we will use the `python:3.7.3-slim` image which includes a simple Debian Linux OS and no other packages installed.

Next we install `pipenv`, since it's not included in the image.

We then create the `counter_app` directory and set it as the default location for the code.

Right after that, we copy the contents of the local directory into the `counter_app` directory using the `ADD` command.

Once all the code in is place, we run `pipenv install`, open the `5000` port and invoke the `quart run` command.

[Save the file](https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-8/Dockerfile).

Now we need to create a `docker-compose` file that will build up both our application instance as well as the MySQL instance.

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
      - db:mysql
    container_name: counterappmysql_web_1
    depends_on:
      - db
    stdin_open: true
    tty: true
    environment:
      PORT: 5000
      SECRET_KEY: "you-will-never-guess"
      DEBUG: 1 # can't pass True here, but 1 works
      MYSQL_ROOT_PASSWORD: rootpass
      DB_USERNAME: counter_user
      DB_PASSWORD: counter_password
      DB_HOST: mysql
      DATABASE_NAME: counter
```

First we describe the Docker Compose file version as "2". We then start defining the services, which are essentially the containers that will be running at the same time.

The first service is the web application which we are calling `web`. We instruct Docker Compose to build the container using the `Dockerfile` in the same directory using the `build .` statement.

Next we open up port 5000 both in the host as well as in the container, as this will be the port that Quart is assigned to listen on.

Then we mount the current directory as volume inside the container, which will be called `counter_app`.

The `links` statement describes that this container is connected to another service which we will call `db`, but inside the container it will be reachable as `mysql`.

We then assign the name of the container to be `counterappmysql_web_1` and instrust Docker Compose that it depends on the `db` service to be up.

The next two statements, `stdin_open` abd `tty` are added so that we can do Python Debugger and examine it from outside the container.

The rest of the file is the environment variables. As you can see they are the same ones defined on the `.quartenv` file.

Next we'll define the MySQL database docker instance:

{lang=yml,line-numbers=on,starting-line-number=25}
```
  db:
    image: mysql:5.7
    restart: always
    container_name: counterappmysql_db_1
    ports:
      - "3306:3306"
    environment:
      MYSQL_USER: counter_user
      MYSQL_PASSWORD: counter_password
      MYSQL_ROOT_PASSWORD: rootpass
      MYSQL_DATABASE: counter
```

This is file is pretty much self-explanatory. We will use the MySQL 5.7 image, instruct the container to always restart, put a name for it and open port 3306 to the host.

[Save the file](https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-8/docker-compose.yml). We're now ready to test the Docker environment.

One word of caution before you continue, if you have installed the packages locally using `pipenv`, make sure to delete the `.venv` folder before you build the containers, otherwise the packages will be copied to the container on the `ADD` step and `pipenv` won't be able to lock the packages.

Also, double check that the folder where the application lives (in my case it's `/opt`) has been marked as shared inside the Docker client.

To start the environment, type `docker-compose up --build`. You will see the MySQL image and the Quart container being built. After a few seconds you should see that the container is up and running.

However, if you hit the `http://localhost:5000` URL on your browser, you will get an error. This is because the tables haven't been created. To do that we will need to run a migration.

So press `CTRL-C` to stop the containers and run the following command:

{lang=bash,line-numbers=off}
```
docker-compose run --rm web pipenv run alembic upgrade head
```

The containers should be brought up and the migration should execute.

Restart the Docker environment with `docker-compose up` and hit `http://localhost:5000`. You should now be able to see the Counter title with the numnber "1". If you you reload the page, the counter should increment.

Finally, to run the tests, you can do:

{lang=bash,line-numbers=off}
```
docker-compose run --rm web pipenv run pytest -s
```

And that's it! You have your Quart MySQL boilerplate application up and running. If you make any changes to the code, the container should automatically restart and pick up the changes.
