# Using Websockets

- Quart websockets [tutorial](https://pgjones.gitlab.io/quart/tutorials/websocket_tutorial.html#websocket-tutorial)
- Quart websockets [deeper dive](https://pgjones.gitlab.io/quart/how_to_guides/websockets.html)
- [Motor with Asyncio](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html)
  - [Tutorial with Ayncio](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html)

## Initial Setup (step-0)

- Basic "Hello World" setup

## User Crud (step-1)

- Login and registration

## User tests (step-2)

- Full tests

## Websocket initial setup (step-3)

- Get websocket initial form
- Problem is that first user to get to the message, deletes it

## User Cursors (step-4)

- Work out a solution to have an initial history of the messages and a cursor per user

## Look and Feel (step-5)

- Use Flexbox ([following this tutorial](https://medium.com/quick-code/building-a-chat-application-using-flexbox-e6936c3057ef))
- Setup the navbar and profile images
- Separate the JS into its own file with the message template

## Presence (step-6)

- Have another websocket for presence and maybe update their status? (idle, active)
- [Detecting disconnection](https://pgjones.gitlab.io/quart/how_to_guides/websockets.html#detecting-disconnection)

## Rooms (step-7)

- Create the concept of rooms
