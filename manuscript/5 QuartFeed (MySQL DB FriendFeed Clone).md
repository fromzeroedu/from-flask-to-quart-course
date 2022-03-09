# QuartFeed, an SSE appplication using MySQL <!-- 5 -->

## Introduction to Server Sent Events <!-- 5.1 -->
Server Sent Events, or SSEs, or EventSource in JavaScript, are an extension to HTTP that allow a client to keep a connection open to a server, thereby allowing the server to send events to the client as it chooses.

By default, the server sends updates with a `data` payload. You can also have an `event` type, which by default is `message`, but could be things like `add` or `remove`. Additionally it has an `id` parameter that allows the client to continue where it left off if the connection was lost.

We are going to build a lightweight version of the popular FriendFeed website, one of the pioneers in the social media space. using Quart and SSE.

For our FriendFeed clone we’ll have the event type to be either `post`, which is a new post, `like` if some one liked the post and `comment` if it’s a comment to a `post`.

For a more complex version or exercise to students, we could also have `groups`, which could be distinct `/sse` endpoints and `like` events for comments.

## Setup (step-0) <!-- 5.2 -->

So let's start setting up our Quart Feed application. 

To start, we can clone the Quart PostgreSQL Boilerplate code that we built in the previous lesson. You can grab the latest version from my [Github repo here](https://github.com/fromzeroedu/quart-postgres-boilerplate).

If you still have the code in your computer, like I do, you can just make a copy of it. Make sure to rename the folder to something like "quartfeed_app".

If you have cache files lying around after the copy, make sure to delete those folders.

We begin by installing the requirements. Edit `pyproject.toml` and change the name of the application to "quartfeed_app". [Save the file](https://fmze.co/fftq-5.2.7).

Next we install the poetry packages by doing: `poetry install`.

For local development I will leave the `.quartenv` as is, since they have generic names that we can use for any Quart application.

Now let's go ahead and rename the `counter` directory to `user` since that will be the first module we will be working on.

Next open the `models.py` file inside the new `user` folder.

Modify the file as follows.

{lang=python,line-numbers=on}
```
from sqlalchemy import Table, Column, Integer, String

from db import metadata

user_table = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(15), index=True, unique=True),
    Column("password", String(128)),
)
```

First rename the table to `user_table` and change the table name, which is the first `Table` property to "user".

The `metadata` property will still come from the `db` module so leave that.

The first column, "id" will remain the same -- we still want that primary key in the table.

The second column we'll call "username". This is the first time we'll use the "String" `sqlalchemy` type, so let's add that to the import list on line 1. We'll define the length as `15` and then set the `index` property to `True` since we want to be able to search for users quickly using the `username` as a query, and finally we'll say that this column should be unique, since no two users should have the same username.

The next column is `password`, which is also a string with a length of 128 which coincides with the hashing algorithm we're going to use, which always generates a hash of 128 characters.

[Save the file](https://fmze.co/fftq-5.2.1).

Next, let's change the `user/views.py` file.

{lang=python,line-numbers=on}
```
from quart import Blueprint, current_app, Response

from user.models import user_table

user_app = Blueprint("user_app", __name__)


@user_app.route("/register")
async def register() -> str:
    return "<h1>User Registration</h1>"
```

On line 3, let's update the import to add the `user_table`.

Update line 4 to rename `counter_app` to `user_app`.

We actually don't need any of thie view function, so we'll go ahead and delete it.

On line 8  update the route to use the `user_app` and on line 9 we'll rename the function to `register` and we'll call this on the `/register` end point.

Finally we'll have this function just return the string "User Registration" just to make sure everything is working correctly.

[Save the file](https://fmze.co/fftq-5.2.2).

Let's go ahead and update the `application.py`. On line 16 and 19, update the `counter_app` to say `user_app`:

{lang=python,line-numbers=on,starting-line-number=15}
```
    # Import Blueprints
    from user.views import user_app

    # Register Blueprints
    app.register_blueprint(user_app)
```

[Save the file](https://fmze.co/fftq-5.2.3).

At this point, I want to make sure the application is running, by doing: `poetry run quart run`, and if I now go to `localhost:5000` on the `/register` endpoint, we can see that the application responds with the "User Registration" string, so all the routing seems to be working correctly.

![Figure 4.8.1](images/5.2.1.png)

If you are using VSCode, we can also use the run button on the editor, since we have the launcher files in our repository, and the nice thing with this approach is that we can set breakpoints and debug our application.

Ok, so let's start working on our migrations. The first thing we're going to do is go to the `migrations` folder and remove all files and directories from the `versions` folder, since these are all related to the `counter` app.

There's no need to change anytthing on the `alembic.ini` since we're using the same connection method.

Next, we'll take a look at the `env.py` on the `migrations` folder, and alll we need to do here is update the user model on line 27 like so:

{lang=python,line-numbers=on,starting-line-number=27}
```
from user.models import user_table
```

Also please remember if we add any new models, we need to add it here, so that the migrations script can detect any new schemas.

[Save the file](https://fmze.co/fftq-5.2.4).

So before we run the migration, we need to setup our Docker environment. So open the `Dockerfile` and change the references from `counter_app` to `quartfeed_app` in line 20 and 23.

{lang=python,line-numbers=on,starting-line-number=19}
```
# set "quartfeed_app" as the working directory from which CMD, RUN, ADD references
WORKDIR /quartfeed_app

# setup poetry
COPY pyproject.toml /quartfeed_app/
```

[Save the file](https://fmze.co/fftq-5.2.5) and next we'll update the `docker-compose.yml` with a similar change from `counter_app` to `quartfeed_app`:

{lang=python,line-numbers=on,starting-line-number=1}
```
version: "2"
services:
  web:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./:/quartfeed_app
```

[Save the file](https://fmze.co/fftq-5.2.6).

If you still have the containers and the images from the counter app, go ahead and delete them: both the web app and the database app. You can use the Docker Desktop application or the VSCode plugin.

So go ahead and run `docker-compose up --build` and that will build our new application and PostgreSQL containers.

After it finishes building, exit using `CTRL-C`, and then run just the database container so that we can execute our migration.

So we do: `poetry run alembic revision --autogenerate -m "Create user table"`. This will use the models metadata and create a new `versions` file so keep an eye out on that folder.

If you are using Docker, you can do `docker-compose run --rm web poetry run alembic revision --autogenerate -m "create user table"`

{lang=bash,line-numbers=off}
```
$ poetry run alembic revision --autogenerate -m "Create user table"
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.autogenerate.compare] Detected added table 'user'
INFO  [alembic.autogenerate.compare] Detected added index 'ix_user_username' on '['username']'
  Generating /opt/from-flask-to-quart-
  course/code/5_quart_feed/quartfeed_app/migrations/versions/c093ae180e73_create_user_table.py ...  done
```

Perfect! So now we check the new `versions` file.

{lang=python,line-numbers=on,starting-line-number=1}
```
"""create user table

Revision ID: 7c33d8dfbca6
Revises: 
Create Date: 2022-02-09 08:57:49.647375

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c33d8dfbca6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=15), nullable=True),
    sa.Column('password', sa.String(length=128), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_username'), 'user', ['username'], unique=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_user_username'), table_name='user')
    op.drop_table('user')
    # ### end Alembic commands ###

```

As we can see, the file has an `upgrade` section where the user table is created with the `id`, `username` and `password` columns, as well as creating an index on `username`.

The `downgrade` function, drops the `username` index and then drops the `user` database.

The next step is to apply the changes on the database using `poetry run alembic upgrade head`.

{lang=bash,line-numbers=off}
```
$ poetry run alembic upgrade head
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade  -> 7c33d8dfbca6, create user table
```

Great! So that applied the changes in the database and should have created the `user` table on our PostgreSQL container. Let's go ahead and check that out.

To connect to the database, run the following command in a new shell:

{lang=bash,line-numbers=off}
```
$ docker exec -it app_db_1 psql postgres -U app_user
```

So now we're on PostgreSQL. We can see the databases by doing `\l`, and as you can see there's an `app` database owned by the user `app_user`:

{lang=bash,line-numbers=off}
```
# \l
                                 List of databases
   Name    |  Owner   | Encoding |  Collate   |   Ctype    |   Access privileges   
-----------+----------+----------+------------+------------+-----------------------
 app       | app_user | UTF8     | en_US.utf8 | en_US.utf8 | 
 postgres  | app_user | UTF8     | en_US.utf8 | en_US.utf8 | 
 template0 | app_user | UTF8     | en_US.utf8 | en_US.utf8 | =c/app_user          +
           |          |          |            |            | app_user=CTc/app_user
 template1 | app_user | UTF8     | en_US.utf8 | en_US.utf8 | =c/app_user          +
           |          |          |            |            | app_user=CTc/app_user
(4 rows))
```

We can connect to the `app` database by doing `\c app` and if we list the tables there by using `\dt`, we'll see that we have the `alembic_version` table and the `user` table created.

{lang=bash,line-numbers=off}
```
\dt
              List of relations
 Schema |      Name       | Type  |  Owner   
--------+-----------------+-------+----------
 public | alembic_version | table | app_user
 public | user            | table | app_user
(2 rows)
```

We can check the contents of the `alembic_version` table by doing `SELECT * FROM alembic_version`.

{lang=bash,line-numbers=off}
```
# SELECT * from alembic_version;
 version_num  
--------------
 7c33d8dfbca6
(1 row)
```

As you can see, the `version_num` field coincides with the revision ID on the `versions` file.

We can also check the schema for the user table by doing: `\d user`.

{lang=bash,line-numbers=off}
```
# \d user;
                                     Table "public.user"
  Column  |          Type          | Collation | Nullable |             Default              
----------+------------------------+-----------+----------+----------------------------------
 id       | integer                |           | not null | nextval('user_id_seq'::regclass)
 username | character varying(15)  |           |          | 
 password | character varying(128) |           |          | 
Indexes:
    "user_pkey" PRIMARY KEY, btree (id)
    "ix_user_username" UNIQUE, btree (username)
```

We have the `id` which has a `nextval` function, meaning it automatically increments by one with each record, the username and password with the right lengths and the two indexes; one for the `id` and the other for the `username`.

Everything looks good, so we're ready to start working on the user registration component of our Quart application.


## User Registration - Initial Setup (step-1) <!-- 5.3 -->

We’re going to create a templates folder with a base and navbar templates using bootstrap. We’ll also create the `user` templates folder and create the `register.html` template in it.

First we create the `base.html` and this will be a shell of a standard HTML document with its required tags.

First we open and close the `<html>` tag. 

Then we create the `<head>` opening and closing tags and inside we'll put some `meta` tags that describe some of the characteristics of the document, including its character set which we'll set as `utf-8` and the viewposrt size.

We're going to be using Bootstrap, a presentation framework that will make it easier to make the application more appealing visually, so let's grab the CSS for Bootstrap in the head as well from their recommended CDN.

Finally we'll make the title a Jinja block, which we can override from each one of the templates.

Now we start with the body of the page. We'll insert all of the content from other templates, so we make this a container Bootstrap element and inside we'll define a `content` Jinja block.

Finally we need the Javascript component of Bootstrap, so we'll add it at the bottom of the page.

Save the file and now let's create the `navbar.html` template.

This navbar we'll use is actually a Bootstrap component, so I'm pretty much going to copy their initial setup and then customize it to have a "Login" and "Register" navigation elements.

Next we'll create a folder inside the `templates` directory called `user`. As you know from other courses, I like to keep the templates for each module separated in folders.

Inside we'll create `register.html` which essentially will be a Bootstrap form.

So first we'll extend the `base.html` template so that this template is embedded within the base html file. We define the title using a Jinja block and then create the content block.

First we create a Bootstrap row to contain all the form. 

We then define a div that will be 6 units wide with an offset of 3 units from the left of the page.

We put a registration sub-title and then define an error block if there is any error being passed to the template.

Now it's time to create the form. It will be a POST, since we will be sending data from the page and we define the action using the Jinja `url_for` property. This is a best practice; we don't use actual URLs anywhere on our forms, so that they can be dynamically generated.

Next we create the input fields using the Bootstrap recommendations. First the username and then the password.

Finally we create a submit button and that's it, we're done.

Save the file.

Our last step if to modify the `user/views` controller.

First we add the `render_template` module from `Quart`, add the methods to the view, so that it accepts both `GET` and `POST`, and finally add the render template function, but notice the format here; it's `return await` and not `await return`.

Save the file and start the application. On your browser, head over to `localhost:5000/register` and you should see our registration form.

Looking good! Now let's actually read these variables from the form on the next lesson.


## User Registration - Parsing the Form (step-2) <!-- 5.4 -->
Notice the `form = await request.form`,  and not `await form = request.form`.

Let’s check the user enters all the fields and setup an error variable




## User Registration - CSRF, check existing user and Password Hashing (step-3) <!-- 5.5 -->

Normally CSRF is included in libraries like Flask-WTForms, which don’t work in Quart, since they use the Flask request object, so we’ll do a quick implementation for it.

We’ll generate a UUID and store it in the session, and then check that the token on the form matches it.

We’ll then check that the username hasn’t been used earlier.

Finally, before we register the user, we don’t want to store clear passwords. Normally I would use Werkzeug, but Quart doesn’t include it, so we’ll install the passlib library. So do: `pipenv install passlib==1.7.1 `

Now let’s encode the password for the database.

And now we’ll save the user on the database.

## User Login (step-4) <!-- 5.6 -->

Implement Login and Logout using sessions and update navbar.

## Testing User Registration and User Login (step-5) <!-- 5.7 -->

Add the `create_all` method from the `test_counter` file and make it use the UserMetadata from the user model

Let’s first test the initial response and see that we get the registration page

We’re going to modify the login page and add a flash message if the user is coming from a successful registration. We’ll use this string to test if users are being registered.

We’ll also check in the database (e2e testing)

Then we’ll test registering a user without email or password

I notice that the test :
```python
    # missing password
    response = await create_test_client.post(
        "/register", form={"username": "testuser", "password": ""}
    )
    body = await response.get_data()
    assert "Please enter username and password" in str(body)
```

Is not passing. Why? Because the database lookup returns a result when passing an existing user (testuser) with no password, so I will add a “if not error” on the user exists block

```python
        # check if the user exists
        if not error:
            conn = current_app.sac
            stmt = user_table.select().where(
                user_table.c.username == form.get("username")
            )
            result = await conn.execute(stmt)
            row = await result.fetchone()
            if row and row.id:
                error = "Username already exists"
```

When doing the test with an unknown user:

```python
    response = await create_test_client.post(
        "/login", form={"username": "testuser2", "password": "test123"}
    )
```

I notice that it’s not passing because I’m assuming there’s a row returned:
```python
if not pbkdf2_sha256.verify(password, row.password):
            error = "User not found"
```

So I change it to an `elif`:
```python
        if not row:
            error = "User not found"
        # check the password
  >>    elif not pbkdf2_sha256.verify(password, row.password):
            error = "User not found"
```

Which goes to show you, testing makes your application better and safer.

Run the tests using `pipenv run pytest`

# Relationship Module (step-6)

- Relationship: set relationships `fm_userid -> to_userid`

We’ll create the relationship between users. We can enforce bi-directional (like Facebook friends) or unidirectional (like Twitter followers). We’ll do the second to simplify the code.

Create the model:

```python
from sqlalchemy import Column, Table, Integer, ForeignKey

from user.models import metadata as UserMetadata

relationship_table = Table(
    "relationship",
    UserMetadata,
    Column("id", Integer, primary_key=True),
    Column("fm_user_id", Integer, ForeignKey("user.id")),
    Column("to_user_id", Integer, ForeignKey("user.id")),
)
```
We need to use the `UserMetadata` since we are going to establish a foreign key to the user table.

Add the `relationship_table` to migrations/env.py
```python
from user.models import metadata as UserMetadata
from relationship.models import relationship_table

target_metadata = [UserMetadata]
```
We import it so that the auto-discovery can “see” the new table. However, notice we don’t add anything to the `target_metadata`_ 
Migration Execution
- Create the commit with `pipenv run alembic revision --autogenerate -m "create relationship table"`
- Check that the versions file was created properly, and then,
- Run the first migration with `pipenv run alembic upgrade head `

Create a simple profile user view so that you can follow other users:
- Created a `profile` route function, where we fetch the username and if we don’t find him, return a 404, and then fetch the relationship status
- Created a basic `profile.html` with a follow/unfollow/edit profile button
- Create `relationship.views` with the routes
- Add `relationshp` blueprint to `application`
- Add `login_required` decorator

# Follow/Unfollow users (step-7)

- Added  common methods to get users and check relationships to start a DRY pattern
- Created relationship add and remove
- Write tests
	- Need to change she scope of the `event_loop` scope to session, otherwise the relationship module runs and closes the loop


# Profile Edit (step-8)

# Profile edit
 - Setup form
- Views processing

# Add a profile image (step-9)

- Add a profile image
	- [Profile template](https://github.com/esfoobar/flaskbook/blob/master/templates/user/profile.html), [view processing](https://github.com/esfoobar/flaskbook/blob/master/user/views.py#L144-L149), [resize utility](https://github.com/esfoobar/flaskbook/blob/68fbd6ebd5344ff5a9a45dc2b607187a39490562/utilities/imaging.py)

- added imagemagick-dev to Dockerfile
- added wand to Pipfile
- Added enctype to form and image section
- Added UPLOADS\_FOLDER, IMAGES\_FOLDER, IMAGE\_URL to settings, .quartenv, docker-compose.yml
- Added saving functionality on user/views.py:profile\_edit
- added utilities/imaging.py
- -Added profile image\_url dict on get user by username
- added image field to user , did a migration:
	- `docker-compose run --rm web pipenv run alembic revision --autogenerate -m "added new image field user"` and then `docker-compose run --rm web pipenv run alembic upgrade head`
- Added image to profile edit and to profile page
- Added empty profile image to repo

# Create a Post  (step-10)

- created the post blueprint with the basic view controller
- created post model
	- Added server side datetiime using `server_defaault` per [instructions here]((https://stackoverflow.com/questions/13370317/sqlalchemy-default-datetime)
- created home page post form
- add the new model to migrations/env.py
- did a migration


# Friends Posts on Homepage using SSE (step-11)

- added broadcast.js
- added broadcast.js on home page
- created followers method on relationship
- add the post to the followers feed 
- added updated field to feed table
- get the latest 10 posts from feed order by desc updated
- user image url method (`image_url_from_image_ts`)
- IMPORTANT: This step just prints out the events to the JS Console, no templating yet. The initial render does work on the home page

# Template Literals (step-12)

- Create template literal for the whole section
- Pass the full post information on the context
- To print the actual statement: `print(stmt.compile(compile_kwargs={"literal_binds": True}))`
- NOTE: I've noticed that if you do code changes while the Quart application is running and the SSE page is open, erratic behavior can appear. Make sure to do the code changes, save, then stop and start Docker and do a HARD RELOAD of the browser page

# Databases Migration (step-13)

- Moved database connectivity over to [databases](https://www.encode.io/databases/)
- Testing and migrations updates

# Comments (step-14)

- Setup comments form toggle display and entry
- Post comment to backend
- Get comments query and add to context
- Render new comments from SSE

# Likes (step-15)

- Post likes to backend
- Finish frontend

- Test posts. comments and likes

