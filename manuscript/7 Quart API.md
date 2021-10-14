# Quart API

## Initial setup (step-0)
- Clone the `qapi` repo @ step-0
- Explain the overall structure of the counter app

## API Auth (step-1)
- Add the views, models for the app API routes, expaling the Quart MethodView
- We need to reinit alembic
    - Backup the `migrations/env.py` to the root folder as `env.py.bak`
    - Delete the migration folder
    - Run `poetry run alembic init migrations`
    - Copy the `env.py.bak` to the `/migrations` folder
    - Run `poetry run alembic revision --autogenerate -m "create qapi tables"`
- Added tests EXCEPT token expired test
    - The token expired test is added on Store GET stores (step-4) below
    - Pleae note that I created a test fixtures folder with common pytest functions

## Store POST endpoint (step-2)
- Create model
- Create schema
- Create POST route
- Create POST view
- Auth decorator
- Test

## Store GET store endpoint (step-3)
- Add route for specific store
- Add view for specific store
- Add store GET test

## Store GET stores endpoint (step-4)
- Add routes and View
- Pagination
- Tests
    - Add app token expire test

## Store PUT endpoint (step-5)
- Add routes and view
- Tests

## Store DELETE endpoint (step-6)
- Add routes and view
- Tests

## Pet POST endpoint (step-7)
- Create model with foreign key
- Do alembic revision
- Create schema with load-only store id
- Create POST route
- Create POST view
- Tests

## Pet GET endpoint (step-8)
- Write the individual pet endpoint
- For the pets in a store, add to the store endpoint to follow best practices, as there is no use case of all pets across the company because a pet can't exist without a store [ref](https://www.moesif.com/blog/technical/api-design/REST-API-Design-Best-Practices-for-Sub-and-Nested-Resources/)