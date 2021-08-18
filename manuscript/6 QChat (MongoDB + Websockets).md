# Using Websockets

- Quart websockets [tutorial](https://pgjones.gitlab.io/quart/tutorials/websocket_tutorial.html#websocket-tutorial)
- Quart websockets [deeper dive](https://pgjones.gitlab.io/quart/how_to_guides/websockets.html)
- [Motor with Asyncio](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html)
  - [Tutorial with Ayncio](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html)

## Initial Setup (step-0)

- Basic "Hello World" setup
- Important! Renamed home_app to chat_app om step-6

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

- Use Flexbox ([following this tutorial](https://medium.com/quick-code/building-a-chat-application-using-flexbox-e6936c3057ef)) and [this codepen](https://codepen.io/Abhitalks/pen/ZbjNvQ/)
- Setup the navbar and profile images
- Separate the JS into its own file with the message template

## Chat and User Model Refactor (step-6)

- Important! Renamed home_app to chat_app
- Created a proper chat model (before it was wirting messages directly on the chat views.py)
- Refactored user models as well

## Presence (step-7)

- Have another websocket for presence and maybe update their status? (idle, active)
- [Detecting disconnection](https://pgjones.gitlab.io/quart/how_to_guides/websockets.html#detecting-disconnection)

## Testing (step-8)

- Write tests for messages
- [Testing Websockets](https://pgjones.gitlab.io/quart/how_to_guides/websockets.html#testing-websockets)
