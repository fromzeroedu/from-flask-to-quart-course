# A Quart Database Counter

As you have seen in my other courses, I like to make real database driven applications using either MySQL or MongoDB.

In the next few lessons, we’ll build a counter app that will be a good boilerplate application for your Mysql-based Quart projects. I will take the concepts from my [Flask MySQL Boilerplate app](https://github.com/fromzeroedu/flask-mysql-boilerplate) but make it asynchronous and of course, use Quart.

But before we start writing the application, we need to understand one of the many quirks we’ll see when working with asynchronous applications, and this one is related to database ORMs. 

## ORMs and Async
For our original Flask MySQL boilerplate application, we used SQLAlchemy, the Python Database ORM or Object Relational Mapper.  However, for async projects we can’t use the same library without some form of penalization.

Flask-SQLAlchemy does work with Quart using the `flask_patch` function we discussed earlier, but it doesn't yield to the event loop when it does I/O. This will mean it cannot handle much concurrent load — only a couple of concurrent requests ([ref](https://gitter.im/python-quart/lobby?at=5cd1da132e2caa1aa625ef83)).

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

The next five variables, `DB_USERNAME`, `DB\_PASSWORD`, `DB_HOST`, and `DATABASE_NAME` will allow us to connect to the database. The `MYSQL_ROOT_PASSWORD` is needed so that our test utility can create the test database and destroy it on demand.

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

{lang=bash,line-numbers=on}
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

✔ Successfully created virtual environment!
Virtualenv location: /opt/quart-mysql-boilerplate/.venv
Creating a Pipfile for this project…
Pipfile.lock not found, creating…
Locking [dev-packages] dependencies…
Locking [packages] dependencies…
Updated Pipfile.lock (a65489)!
Installing dependencies from Pipfile.lock (a65489)…
  🐍   ▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉▉ 0/0 — 00:00:00
To activate this project's virtualenv, run pipenv shell.
Alternatively, run a command inside the virtualenv with pipenv run.
```

You might notice that the virtual environment that `Pipenv` created was located inside my working directory. This is not the default behavior, but I like to have the `venv` directory alongside my code, without committing it. To make that your default behavior, you need to set an environment variable in your host with the name `PIPENV_VENV_IN_PROJECT` set to `enabled`. On Mac you can add it to your `bash_profile` like this:

{lang=python,line-numbers=off}
```
export PIPENV_VENV_IN_PROJECT="enabled"
```

 In Windows 10, just edit your System Environment variables and set it. You can find them by typing `env` on your Windows search and click on the “Edit the System Environment Variables”.

![](Screen%20Shot%202019-09-15%20at%202.09.20%20PM.png)

Then click on the “Environment Variables” button on the lower right.

![](Screen%20Shot%202019-09-15%20at%202.09.46%20PM.png)

Click the “New” button, add the `PIPENV_VENV_IN_PROJECT` variable and set the value to “enabled”.

![](Screen%20Shot%202019-09-15%20at%202.11.36%20PM.png)

Now let’s go ahead and install Quart and `python-dotenv`.

{lang=bash,line-numbers=off}
```
$ pipenv install quart python-dotenv 
```

We’re now ready to start setting up MySQL and Alembic migrations.


[^1]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-1/.quartenv

[^2]:	https://github.com/fromzeroedu/quart-mysql-boilerplate/blob/step-1/settings.py
