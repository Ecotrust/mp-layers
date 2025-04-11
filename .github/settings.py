INSTALLED_APPS = [

    # ...

    'corsheaders',

    # ...

]


MIDDLEWARE = [

    # ...

    'corsheaders.middleware.CorsMiddleware',

    # ...

]

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Add the port your React app runs on
]

CORS_ORIGIN_WHITELIST = [
    'http://localhost:3000',  # The default port for create-react-app
]