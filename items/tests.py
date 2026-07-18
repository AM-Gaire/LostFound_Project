from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from .models import Item


class ItemReportTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='reporter', email='reporter@test.com', password='testpass123', role='student'
        )
        self.client.login(username='reporter', password='testpass123')

    def test_report_item_get_returns_form(self):
        response = self.client.get(reverse('report_item'))
        self.assertEqual(response.status_code, 200)

    def test_report_lost_item_creates_record(self):
        response = self.client.post(reverse('report_item'), {
            'item_type': 'lost',
            'title': 'Blue Laptop Bag',
            'description': 'A blue Samsonite laptop bag left in the library.',
            'category': 'bags',
            'location': 'Main Library, Floor 2',
            'date_reported': '2026-06-20',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Item.objects.filter(title='Blue Laptop Bag').exists())

    def test_report_item_short_title_shows_error(self):
        response = self.client.post(reverse('report_item'), {
            'item_type': 'lost',
            'title': 'AB',
            'description': 'Short title test.',
            'category': 'other',
            'location': 'Library',
            'date_reported': '2026-06-20',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(title='AB').exists())

    def test_search_returns_found_items_only(self):
        Item.objects.create(
            item_type='found', title='Black Keys', description='Found near canteen',
            category='keys', location='Canteen', date_reported='2026-06-20',
            reported_by=self.user,
        )
        Item.objects.create(
            item_type='lost', title='Red Wallet', description='Lost in library',
            category='accessories', location='Library', date_reported='2026-06-20',
            reported_by=self.user,
        )
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)
        items = response.context['items']
        self.assertTrue(all(i.item_type == 'found' for i in items))

    def test_search_filters_by_keyword(self):
        Item.objects.create(
            item_type='found', title='Black Keys', description='Found near canteen',
            category='keys', location='Canteen', date_reported='2026-06-20',
            reported_by=self.user,
        )
        Item.objects.create(
            item_type='found', title='Blue Umbrella', description='Found at entrance',
            category='other', location='Entrance', date_reported='2026-06-20',
            reported_by=self.user,
        )
        response = self.client.get(reverse('search'), {'q': 'keys'})
        items = response.context['items']
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, 'Black Keys')

    def test_student_cannot_report_found_item(self):
        response = self.client.post(reverse('report_item'), {
            'item_type': 'found',
            'title': 'Found Black Wallet',
            'description': 'Found near the main entrance doors on campus.',
            'category': 'accessories',
            'location': 'Main Entrance',
            'date_reported': '2026-06-20',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Item.objects.filter(title='Found Black Wallet').exists())

    def test_staff_can_report_found_item(self):
        staff = User.objects.create_user(username='staffuser', email='staffuser@test.com', password='testpass123', role='staff')
        self.client.login(username='staffuser', password='testpass123')
        response = self.client.post(reverse('report_item'), {
            'item_type': 'found',
            'title': 'Found Black Wallet',
            'description': 'Found near the main entrance doors on campus.',
            'category': 'accessories',
            'location': 'Main Entrance',
            'date_reported': '2026-06-20',
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(Item.objects.filter(title='Found Black Wallet', item_type='found').exists())

    def test_logout_requires_post(self):
        response = self.client.get(reverse('logout'))
        self.assertTrue(self.client.session.get('_auth_user_id'))

    def test_logout_post_clears_session(self):
        response = self.client.post(reverse('logout'))
        self.assertRedirects(response, reverse('home'))
        self.assertFalse(self.client.session.get('_auth_user_id'))
