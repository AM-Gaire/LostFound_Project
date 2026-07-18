from django.test import TestCase, Client
from django.urls import reverse
from .models import User


class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='teststudent', email='teststudent@test.com', password='testpass123', role='student'
        )

    def test_register_creates_user_and_redirects(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'securepass99',
            'confirm_password': 'securepass99',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_register_duplicate_username_shows_error(self):
        response = self.client.post(reverse('register'), {
            'username': 'teststudent',
            'email': 'other@example.com',
            'password': 'securepass99',
            'confirm_password': 'securepass99',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(email='other@example.com').exists())

    def test_login_valid_credentials_redirects(self):
        response = self.client.post(reverse('login'), {
            'email': 'teststudent@test.com',
            'password': 'testpass123',
        })
        self.assertRedirects(response, reverse('dashboard'))

    def test_login_invalid_credentials_stays_on_page(self):
        response = self.client.post(reverse('login'), {
            'email': 'teststudent@test.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"/login/?next={reverse('dashboard')}")

    def test_dashboard_accessible_when_logged_in(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
