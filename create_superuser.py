#!/usr/bin/env python
import os
import sys
import django

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_agent_system.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

# Create superuser
email = 'admin@example.com'
password = 'admin123456'

try:
    if User.objects.filter(email=email).exists():
        print(f"User with email '{email}' already exists.")
        user = User.objects.get(email=email)
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"Password updated for user '{email}'.")
    else:
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        print(f"Superuser created successfully!")

    print("\nCredentials for testing:")
    print(f"Email: {email}")
    print(f"Password: {password}")
    print("\nYou can now log in to the admin panel at: http://localhost:8000/admin/")

except IntegrityError as e:
    print(f"Error creating user: {e}")
except Exception as e:
    print(f"An error occurred: {e}")