from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import posts, auth, billing
from tortoise.contrib.fastapi import register_tortoise
from config import APIConfig

app = FastAPI(title='Shortdiary API')
app.add_middleware(
	CORSMiddleware,
	allow_origins=APIConfig().cors_origins,
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)

app.include_router(auth.router, prefix='/auth', tags=['auth'])
app.include_router(posts.router, prefix='/posts', tags=['posts'])
app.include_router(billing.router, prefix='/billing', tags=['billing'])

TORTOISE_ORM = {
	'connections': {'default': APIConfig().database},
	'apps': {
		'models': {
			'models': ['models', 'aerich.models'],
			'default_connection': 'default',
		},
	},
}

register_tortoise(
	app,
	db_url=APIConfig().database,
	modules={'models': ['models', 'aerich.models']},
	generate_schemas=False,
	add_exception_handlers=True,
)
