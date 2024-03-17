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


CORS_ORIGIN_WHITELIST = [

     '<http://localhost:3000>',  # The default port for create-react-app

]