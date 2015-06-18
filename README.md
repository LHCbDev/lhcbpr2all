# LHCbPR service

## Installation

1. virtualenv venv
1. source venv/bin/activate
1. pip install -r requirements.txt
1. cd site
1. python manage.py migrate
1. python manage.py populate (optional, fill empty database with test data)
1. python manage.py runserver
