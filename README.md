#Getting Started
To use this template to start your own project:

##clone the project

`https://github.com/puuq/Nepalnirvana.git`

##create and start a a virtual environment

`virtualenv env --no-site-packages`
`source env/bin/activate`

##Install the project dependencies:

`pip install -r requirements.txt`

##create a postgres db and add the credentials to settings.py

`DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'db_name',
        'USER': 'name',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '',
    }
}`

##then run

`python manage.py migrate`

##create admin account

`python manage.py createsuperuser`

##then

`python manage.py makemigrations`

##to makemigrations for the app

##then again run

`python manage.py migrate`

##to start the development server

`python manage.py runserver`

##and open localhost:8000 on your browser to view the app.
