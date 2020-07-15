# Introduction

## Welcome to the course
Hi and welcome to “From Flask to Quart”. My name is Jorge Escobar and I’m super excited to introduce you to a new dimension in the world of Python Web Development. I’m talking about Asynchronous Python development.

Introduced with Python version 3.7, the Asynchronous I/O library, also called “asyncio”, allows developers to write code that runs concurrently as opposed to sequentially, which translates into a higher throughput of your application in situations where response time and speed are really important.

Programming with asyncio does require a different way of thinking on how you develop your code and we will go over those idiosyncrasies as we develop, step by step and from simple to complex, different asynchronous applications that will introduce you to these new concepts.

The star of this course is the Quart web framework. Built on top of the Flask micro framework, Quart shares a lot of the common functionality you’re already used to working with in Flask, but under the hood, has converted the low-level API functions to work in asynchronous fashion, bringing the best of two worlds together.

We will also have a chance to work with asynchronous database libraries, like aiomysql and motor, which allows your async applications to talk to both MySql and MongoDB databases.

We will also explore some of the frontend communication channels that leverage your async applications on the javascript side, which will produce hyper-responsive web applications for your users.

So let’s begin our journey to the new world of async Python web development!

## Roadmap and Requirements
Let’s take a look at what we will be covering on this course. 

First, we’ll explore the fundamental concepts behind async programming, including coroutines and tasks and look at some of the common pitfalls you will face writing these applications.

We will then get introduced to Quart, the asynchronous version of the popular Flask library and build a basic counter application that will serve as an easy introduction to the concepts.

Then, we will build a more complex Quart application called “QuartFeed”, which will mimic the popular FriendFeed social networking site that was ahead of its time thanks to its dynamic flow and amazing interactivity, leveraging the Server Sent Events protocol.

Next, we will build “Qchat”, a MongoDB powered chat application using web sockets on the javascript side.

Finally, we will explore how to build an API service, based on our previous “Pet Store” example in the API course, using the async paradigm.

In order to get the most out of this course, you will need to have a solid knowledge of the Python language as well as the Flask framework. As you know, I have excellent courses that can teach you everything you need to get the preparation for this course.

You will also need a computer where you can run this code, or use an online development platform, like PythonAnywhere or Cloud9. I won’t cover those platforms in this course, as I teach how to use these resources on my “From Zero to Flask” course.

No matter what platform you use, you will need Python version 3.7 or higher installed

And with that, let’s talk about the real benefits that Asynchronous applications offer you and your users.

## Roadmap and Requirements
Let’s take a look at what we will be covering on this course. 

First, we’ll explore the fundamental concepts behind async programming, including coroutines and tasks and look at some of the common pitfalls you will face writing these applications.

We will then get introduced to Quart, the asynchronous version of the popular Flask library and build a basic counter application that will serve as an easy introduction to the concepts.

Then, we will build a more complex Quart application called “QuartFeed”, which will mimic the popular FriendFeed social networking site that was ahead of its time thanks to its dynamic flow and amazing interactivity, leveraging the Server Sent Events protocol.

Next, we will build “Qchat”, a MongoDB powered chat application using web sockets on the javascript side.

Finally, we will explore how to build an API service, based on our previous “Pet Store” example in the API course, using the async paradigm.

In order to get the most out of this course, you will need to have a solid knowledge of the Python language as well as the Flask framework. As you know, I have excellent courses that can teach you everything you need to get the preparation for this course.

You will also need a computer where you can run this code, or use an online development platform, like PythonAnywhere or Cloud9. I won’t cover those platforms in this course, as I teach how to use these resources on my “From Zero to Flask” course.

No matter what platform you use, you will need Python version 3.7 or higher installed

And with that, let’s talk about the real benefits that Asynchronous applications offer you and your users.

