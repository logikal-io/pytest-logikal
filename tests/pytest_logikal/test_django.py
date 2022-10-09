from importlib import reload

from pytest_logikal import django as pytest_logikal_django

pytest_logikal_django = reload(pytest_logikal_django)  # ensures coverage captures definitions
