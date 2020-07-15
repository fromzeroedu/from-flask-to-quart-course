# Fundamental Concepts

## What’s the Real Benefit of Using Asynchronous Applications?
There’s a bit of “voodoo” that surrounds Asynchronous application development, and you might have heard about this among your developer friends, or in Youtube tutorials, and that is that somehow, magically, async applications are super fast.

The truth is that applications written in async fashion are not really faster, but they are more efficient.

Let’s look at an example, specifically with one of the popular web servers for Python called Gunicorn.

When you start Gunicorn you can specify how many “workers” you will spawn. Typically you can have 3 or 4 workers per server.

Each worker handles one HTTP request at a time, processes it and returns it back to the caller, doing this over and over.

Within each request, there are times when the processor is working and other times it’s “asleep”, just waiting for a database request to complete or an external API request to be returned. When the request is completed, the response is sent back and the next request is taken.

But here’s the problem. Let’s say that you have 3 concurrent users visiting your site, with 3 workers, and it takes 10 seconds for each request to fully complete. That means that each additional user visiting could be waiting as much as 10 seconds just to even get started with their request.

So how do you typically scale these applications? By adding web servers on the front layer. But this is costly and inefficient, as each request spends a lot of time asleep, waiting for data to be returned so that it can finish its request.

This is where asynchronous applications come in. Async libraries can spawn hundreds or even thousands of concurrent “pseudo-threads”, which in async parlance are called _coroutines_. These coroutines are supervised by a master scheduler called the _event loop_. A coroutine `A` is started when a request comes in, but when it hits its first I/O point, it is suspended, like a bear hibernating the winter, and the loop is freed to take a new request and start a new coroutine `B`. When the data is delivered to coroutine `A`, it is resumed whenever coroutine `B` is suspended,. At this point coroutine `A` is completed, so the loop is free to take the next request, which spawns coroutine `C`.

Notice that coroutines never work in _parallel_. This is a major misconception of async programming. Coroutines work _concurrently_ and it’s important to understand that they need to have waiting times for them to work together, otherwise a coroutine that never sleeps could take over the whole loop.

With this methodology, each server is now able to fulfill thousands of requests, versus the handful or tens of requests that it would be able to handle if our code was synchronous.

A good real world example of sync versus async applications is the waiter and cook of a busy restaurant.

Let’s say we start with a single process waiter that operates synchronously. When a new customer comes in, he goes to their table and takes the order. The first customer orders a salad. The waiter goes to the kitchen and places the order to the cook for the customer’s salad. He waits until it’s ready and since it’s a salad, it takes little time to deliver the dish back to the customer. 

But then a new customer enters the restaurant. The waiter writes his order — he wants pasta. Pasta is a bit more complicated so he knows it will take longer to prepare. But he goes to the cook and places the order for the pasta and waits for 10 minutes until the pasta is ready. Meanwhile the first customer wants to order his main course after his salad, and a third customer just came in. The waiter continues in the kitchen until the pasta is ready to be taken to the second customer and he rushes to the third customer. Bad news: the third customer wants lobster, and that takes 30 minutes to prepare. He runs to the kitchen and stays there for 30 whole minutes while the first two customers are losing all their patience to place their new orders.

You can see how this story ends badly for that restaurant’s business.

But on the other side of the street, a new restaurant opens with a highly efficient asynchronous waiter. When the first customer comes in and orders the salad, he goes to the kitchen and places the order for the cook. But instead of waiting for the salad to be ready he goes back to the dining area to take care of the new customer that just sat down. He takes his pasta order and takes it to the kitchen, picks up the salad and delivers it to the first customer and then goes to greet the third customer and starts taking his order.

You can see how much more efficient the second waiter is and how he would be able to accommodate much more concurrent customers than the first synchronous waiter.

So the bottom line of the story: async programming doesn’t make code run faster per se, but it does make code run more efficiently and will allow you to serve many more requests per server.

Let’s now go ahead and code the waiter and cook example using our first async program.

## The Waiter and the Cook - Our First Async Project
So let’s try and code the waiter and cook example using regular synchronous Python. This is what it could look like:

{lang=python,line-numbers=on}
```
import time

def waiter():
    cook('Pasta', 8)    
    cook('Caesar Salad', 3)
    cook('Lamb Chops', 16)        

def cook(order, time_to_prepare):
    print(f'Getting {order} order')
    time.sleep(time_to_prepare)
    print(order, 'ready')

if __name__ == '__main__':
    waiter()
```

Save this file as `sync.py`. 

As you can see, we’re simulating the cook as a function that takes an order and how long it takes to prepare it. It then simulates the cooking by doing a `time.sleep` and then prints that the order is ready.

The waiter is another function that is taking the order from the customers and _synchronously_ passes them to the cook.

Make sure you have at least Python 3.7 installed by doing `python3 --version` on the Mac or `python --version` on Windows. If you get less than 3.7, go ahead and upgrade using Homebrew on the Mac or Chocolatey on Windows.

So run the example and you will see slowly, but surely, all the plates come out.

{lang=bash}
```
$ python3 sync.py
Getting Pasta order
Pasta ready
Getting Caesar Salad order
Caesar Salad ready
Getting Lamb Chops order
Lamb Chops ready
```

Those lamb chops take a long time for sure!

## Our First Async Program
So now, we’ll convert this program to use the `asyncio` library and get a feel of how to write this code asynchronously. So let’s copy the `sync.py` file on a new file called `coros.py` with the following code.

{lang=python,line-numbers=on}
```
import asyncio
import time


async def waiter() -> None:
    cook("Pasta", 8)
    cook("Caesar Salad", 3)
    cook("Lamb Chops", 16)


async def cook(order: str, time_to_prepare: int) -> None:
    print(f"Getting {order} order")
    time.sleep(time_to_prepare)
    print(order, "ready")


asyncio.run(waiter())
```

First, we’ll need to import the `asyncio` Python standard library so that we can use the asynchronous features.

All the way at the bottom we’ll replace the `if __name__ == '__main__'` conditional and Instead use this new `run` method from the `asyncio` module. So what does `run` do?

_Run_ essentially grabs a low level `asyncio` pseudo-server called the _running loop_. This loop is the master coordinator that oversees the suspension and resuming of tasks that are running in our code. In our example, the “cook pasta” call is a task that will run but will be paused for eight seconds. So when a request comes in and goes to that line, the loop suspends that task for eight seconds, making a note of it, and goes on to take another incoming request to start from the beginning When the call to pasta finishes for the first request, the loop resumes execution on the next line, which would be the Caesar salad line.

The run command needs a function to execute , so we pass the `waiter` function, which is the main function on this code.

_Run_ also takes care of the cleanup, so when the whole code is run, it will gracefully disconnect from the loop.

These changes are not enough to make our code asynchronous, though. We need to tell `asyncio` what functions and what tasks will be run asynchronously. So let’s change the`waiter` function as follows.

{lang=python}
```
async def waiter() -> None:
    await cook("Pasta", 8)
    await cook("Caesar Salad", 3)
    await cook("Lamb Chops", 16)
```

We declare the `waiter` as an asynchronous function by prepending it with he `async` keyword. Once we do that, we are then able to tell `asyncio` what asynchronous tasks will happen inside the function by prepending them with the `await` keyword.

So you could read this code as “call the `cook` function and `await` its result before moving to the next line”. But this is not a blocking waiting process, this tells the loop, “if you have other requests to tend to, you can do that while we wait, go ahead and we’ll let you know when this is done”.

Just remember that if you have any `await` tasks, you need to define that function as `async`.

You might be wondering, “what about the cook function?”. Well, we need to make that asynchronous as well, so we could change it to the following.

{lang=python}
```
async def cook(order, time_to_prepare):
    print(f'Getting {order} order')
    await time.sleep(time_to_prepare)
    print(order, 'ready')
```

Here’s an issue though. If we use the regular `time.sleep` function, it will block the whole execution, rendering the asynchronous program useless. In this case we need to use asyncio’s `sleep` function instead.

{lang=python}
```
async def cook(order, time_to_prepare):
    print(f'Getting {order} order')
    await asyncio.sleep(time_to_prepare)
    print(order, 'ready')
```

Now we’re guaranteeing that while the `cook` function is asleep for those number of seconds, the program can take other incoming requests.

Now if we run the program we get the following:

{lang=bash}
```
$ python3 coros.py
Getting Pasta order
Pasta ready
Getting Caesar Salad order
Caesar Salad ready
Getting Lamb Chops order
Lamb Chops ready
```

But wait, there’s no difference with the synchronous execution. You were expecting this to run faster right? Well, that’s one of the misconceptions about asynchronous code, that it runs faster. But this program is better already in a way that you can’t really tell with this usage.

If we were running this program as part of a website, we could be able to serve hundreds or thousands of visitors at the same time on the same server without any time outs. If we ran the synchronous code instead, we could only serve maybe a dozen of users before the others would start to get timeout errors since the server’s CPU would get overwhelmed.
