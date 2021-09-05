# Quart API

- Note: Use [Quart-Schema](https://gitlab.com/pgjones/quart-schema)

## Initial setup (step-0)
- Clone the `qapi` repo @ step-0
- Explain the overall structure of the counter app

## API Auth (step-1)
- Add the views, models, expaling the Quart MethodView
- We need to reinit alembic
    - Delete the migration folder
    - Run `poetry run alembic init migrations`
    - Copy the `env.py.bak` to the `/migrations` folder
    
