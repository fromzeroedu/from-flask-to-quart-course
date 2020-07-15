# Introduction

## Welcome to the Book!

Hi and welcome to “From Zero to Flask”. My name is Jorge Escobar and I have been building professional Python applications for the last 10 years and now want to teach you, from scratch, how to build Flask applications using the techniques used in real world tech companies.

Flask is my favorite Python web framework. A framework is a set of libraries and tools to make web development easier and more efficient, as it tackles all the functionality required by the majority of the applications and lets you focus on the creative parts.

At the end of the course, you will have built a Python-Flask-based database-driven personal blog application using the techniques I will show you. You will also have to develop a brand new feature using the concepts you learned in the course.

The course starts from the basic Flask concepts, and slowly builds into areas like database fundamentals, building the ORM models, templates, image processing and secure form design.

There are many Flask courses and tutorials out there, but this is the only course to take the professional approach I use in all my courses.

So if you’re ready to start your journey from scratch to become a professional web developer, come join me. See you in the course!

## Roadmap and Requirements

In this course you will learn the fundamentals of Flask, how to isolate your dependencies using virtual environments, then we’ll go over routing, templates, sessions and database migrations with a simple page counter application.

We will then build a blog application with author registration, login, post blog articles, adding photos, pagination and editing and deleting posts.

In every step of the way, we will be writing units tests for each of the blog features, just like professional developers do.

So, what do you need to properly learn this course?

First, you need to have a basic understanding of the Python language. I have an excellent course for that called “From Zero to Python”, but if you know the Python language basics, that’ll be enough.

Second, setup a development environment. We have two options in the course: you can install Python and MySQL locally in your computer, or you can follow the course using an online development platform, where you can code in the cloud from wherever you are.

And third, you need to be passionate about learning, the professional way, how to become a software developer. I’m sure you have seen some online tutorials or even taken some programming courses. However, I warn you, most of the material out there is not updated or teaches the most advanced concepts and uses a lot of point-and-click tools and easy concepts. If you want to learn the easy way, this is not the course for you. But if you want to learn, and suffer a little bit at the beginning, but come out on the other end with solid knowledge, then you have found the right course.

{lang=python,line-numbers=on,starting-line-number=32}
```
from flask import Flask

from settings import CORS_ORIGINS, MONGODB_SETTINGS

# setup db
db = MongoEngine()

def create_app(**config_overrides):
    app = Flask(__name__)
```

Here's an image:

![PythonAnyhwere Welcome Page](images/1.1.png)
