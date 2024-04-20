import os

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import FastAPI
from fastapi import Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse

from apps.jwt import CREDENTIALS_EXCEPTION
from apps.jwt import create_token
from apps.jwt import valid_email_from_db
from config import get_settings

# Create the auth app
auth_app = FastAPI()
settings = get_settings()

# Set up the middleware to read the request session
SECRET_KEY = settings.SECRET_KEY
GOOGLE_CLIENT_ID = settings.GOOGLE_CLIENT_ID
GOOGLE_CLIENT_SECRET = settings.GOOGLE_CLIENT_SECRET

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
auth_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Frontend URL:
FRONTEND_URL = os.environ.get('FRONTEND_URL') or 'http://127.0.0.1:8000/token'


@auth_app.route('/login')
async def login(request: Request):
    redirect_uri = FRONTEND_URL  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, redirect_uri)


@auth_app.route('/token')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise CREDENTIALS_EXCEPTION
    user_data = await oauth.google.parse_id_token(request, access_token)
    if valid_email_from_db(user_data['email']):
        return JSONResponse({'result': True, 'access_token': create_token(user_data['email'])})
    raise CREDENTIALS_EXCEPTION
