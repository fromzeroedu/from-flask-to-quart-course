# Quart API

- Note: Use [Quart-Schema](https://gitlab.com/pgjones/quart-schema)

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
- Added tests

## Store endpoint (step-2)
- Create models
- Create schemas
- Create app decorator
- Create routes
- Create views