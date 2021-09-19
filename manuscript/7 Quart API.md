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
    - That one is added on Store GET store (step-3) below

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
- Add app token expire text

## Store GET stores endpoint (step-4)
- Pagination (see [this](https://github.com/wizeline/sqlalchemy-pagination/blob/master/sqlalchemy_pagination/__init__.py))
- Fixtures