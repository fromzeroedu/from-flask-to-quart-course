from quart import Quart, render_template

app = Quart(__name__)


@app.route("/")
async def hello():
    name = "World!"
    return await render_template("hello.html", name=name)


app.run()
