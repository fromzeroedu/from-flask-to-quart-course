# Introduction to Quart <!-- 3 -->

## Introducing Quart <!-- 3.1 -->

As it happens with web development in general, you don't want to build your application from scratch just using Python. You want to leverage a web framework that can cut your development time, specially with the low level stuff, like parsing the request, building templates, routing and communicating with your datastore.

But unfortunately you can't just use Flask, Django or other synchronous frameworks with asynchronous code. All the input/output operations would completely block your thread and it would be a complete waste of time.

So for the asynchronous capabilities of Python, there have been some frameworks that have appeared on the scene that will allow you to leverage the power of `asyncio` with the tooling around web operations.

However, most of them are implemented in their own unique way, which is not a huge deal if you're just learning web development but it's a drag if you already know your way around an existing framework.

Which brings us to Quart. This wonderful new project has built most of the existing Flask API and converted it to asynchronous operations, allowing us to develop using the Flask libraries we already know and lets us focus on implementing the asynchronous part.

So let's go over the pros of using Quart as an asynchronous choice for our web development.

First, like I just mentioned, you don't have to relearn anything related to the setup of your application. You have the same basic tooling, including blueprints and Jinja templating.

Second, using Quart actually makes your application much more efficient and scalable than its Flask version, because of the asynchronous benefits we've discussed earlier.

Third, Quart is actively being developed and interest in the framework is slowly growing and gaining acceptance.

Of course, nothing in life is perfect and using Quart is no exception. Here are some cons of using Quart.

First, finding help when you're stuck in tools like Google and StackOverflow is very hard, since it's still a relative newcomer and the fact is that most Python developers are not using `asyncio` yet.

Second, a very limited number of extensions are supported. You can find a list of the supported extensions [in this url](http://pgjones.gitlab.io/quart/flask_extensions.html#supported-extensions), and as you can see, a lot of the popular ones are not in that list. [According to the Quart documentation](https://pgjones.gitlab.io/quart/flask_extensions.html), you can use extensions that are not in that list using a function called `flask_patch`, but in order for them to work, “Flask extensions must use the global request proxy variable to access the request, any other access e.g. via `get_current_object()` will require asynchronous access.” The documentation also says “The flask extension must be limited to creating routes, using the request and rendering templates. Any other more advanced functionality may not work.”

So using existing Flask extensions will be very limited and you will need to do heavy testing before intending to use them with Quart.

The way I approach this issue is to really understand what I am trying to accomplish by using this extension, and sometimes you might need to either do your own version of the extension or, better yet, contribute a version of it that works with Quart.

In the coming lessons, we'll be tackling some of these issues so that you can see how I go about this limitation.

And with that, let's go ahead and install Quart.

## Installing Quart and Hello World <!-- 3.2 -->

In this lesson we're going to install Quart. Make sure you have at least Python 3.7 installed.

Next, we're going to install the Poetry package manager. Poetry allows us to handle package management for our Python applications and replaces the previous `virtualenv` workflow. It's better than using a `requirements.txt` because it tracks package dependencies in more detail, avoiding the issues we had sometimes where package upgrades would break our application.

Check if you have Poetry installed by typing `poetry --version` in your terminal. If you don't, follow the Poetry installation instructions in the [Poetry docs page](https://python-poetry.org/docs/#installation).

To create our first Quart application folder, we will use Poetry to set that up for us. So navigate to the folder where you keep your Python applications. It can be your user's home directory or a completely different directory. Just do a `cd` to it.

Next, let's create a folder for our Quart project, with `mkdir quart-hello` and type `cd quart-hello` to start the process.

Now we'll initialize this folder to be a Poetry project. Poetry has an `init` module that can ask some details about the project, but for this time, we'll just initialize it with a simple configuration, so type `poetry init -n`. This will create a `pyproject.toml` without too much information.

Next, we want to create the virtual environment that Poetry will use, so type `poetry shell`. Poetry will create the virtual environment folder in your User directory and enable it automatically.

We now install `Quart` by doing `poetry add quart`. Poetry will add Quart and a bunch of other dependencies.

Open your favorite code editor and create a file called `hello.py` in the root folder.

We'll write the following code in `hello.py`:

{lang=python,line-numbers=on}
```
from quart import Quart

app = Quart(__name__)


@app.route("/")
async def hello():
    return "Hello World!"


app.run()
```

First we import the `Quart` class from the `quart` package. We then create an instance of a Quart app, using the `__name__` global as its identifier.

Next we'll define the root path that the application will respond on. And here's where we see our first difference with a Flask app: we need to prepend the route function with `async`, since we'll be doing input/output operations inside that are asynchronous. For now let's just return a simple “Hello World!”.

Finally we need to make the app start with `app.run()`.

Save the file.

Before we can run it, we need to define some environment variables, just like we did with Flask. In order for that to work, we're going to install the `python-dotenv` library, which allows us to create an `env` file to be loaded when Quart runs. So on the terminal type: `poetry add python-dotenv` and then create a `.quartenv` file in the root folder as follows:

{lang=python,line-numbers=on}
```
QUART_APP='hello'
QUART_ENV=development
SECRET_KEY='my_secret_key'
```

We're now ready to run our first Quart app. Just type: `poetry run quart`. You will be notified that the application is running on port 5000.

{lang=bash,line-numbers=off}
```
Running on http://127.0.0.1:5000 (CTRL + C to quit)
```

If you now open this URL on your browser, you'll see the “Hello World!” message.

Now let's create a template instead of returning the string directly to the user.

For that, we'll create a template folder so that we can render the page more dynamically with a context. So create a `templates` folder and inside create the `hello.html` file as follows:

{lang=html,line-numbers=on}
```
<HTML>
<header>
    <title>Home Page</title>
</header>

<body>
    <h1>Hello {{ name }}</h1>
</body>

</HTML>
```

In the `hello.py` file add `render_template` to the Quart import on line 1:

{lang=python,line-numbers=on,starting-line-number=1}
```
from quart import Quart, render_template
```

And change the `hello` function as follows:

{lang=python,line-numbers=on,starting-line-number=6}
```
@app.route("/")
async def hello():
    name = "World!"
    return await render_template("hello.html", name=name)
```

Did you notice that? For the first time we're using the `await` keyword. Why do you think that is?

If you said that `render_template` is a coroutine, you are right. Rendering a template can take some time, so Quart hands that off to a coroutine so that it can service other requests until the template is rendered.

Try taking out the `await` keyword, run the application and reload the page in the browser. You will get the following error:

{lang=python,line-numbers=off}
```
TypeError: 'coroutine' object is not iterable
```

As you can see by now, things are not so different from what this application would look like in Flask. Of course, this is a very simple app, so, as we make things more complex, you will definitely start to see the differences.

Check out the full code [here](https://fmze.co/fftq-3).

Let's now tackle how to build our first database driven Quart application.
