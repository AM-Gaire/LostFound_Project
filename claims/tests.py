from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from items.models import Item
from .models import Claim, AuditLog


class ClaimTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.student = User.objects.create_user(
            username='student1', email='student1@test.com', password='testpass123', role='student'
        )
        self.admin = User.objects.create_user(
            username='admin1', email='admin1@test.com', password='testpass123', role='admin'
        )
        self.found_item = Item.objects.create(
            item_type='found', title='Found Wallet', description='Brown leather wallet found near reception',
            category='accessories', location='Reception', date_reported='2026-06-20',
            reported_by=self.admin,
        )

    def test_submit_claim_creates_record_and_audit_log(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('submit_claim', args=[self.found_item.id]),
            {'verification_answers': 'It has my student ID card inside and a blue sticky note on the cover.'}
        )
        self.assertRedirects(response, reverse('my_claims'))
        self.assertEqual(Claim.objects.filter(claimant=self.student).count(), 1)
        self.assertTrue(AuditLog.objects.filter(action_type='CLAIM_SUBMITTED').exists())

    def test_submit_claim_too_short_shows_error(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(
            reverse('submit_claim', args=[self.found_item.id]),
            {'verification_answers': 'Too short'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Claim.objects.count(), 0)

    def test_my_claims_only_shows_own_claims(self):
        other = User.objects.create_user(username='other', email='other@test.com', password='testpass123', role='student')
        Claim.objects.create(item=self.found_item, claimant=other, verification_answers='Other user claim details here')
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('my_claims'))
        self.assertEqual(len(response.context['claims']), 0)

    def test_admin_can_approve_claim(self):
        claim = Claim.objects.create(
            item=self.found_item, claimant=self.student,
            verification_answers='Brown wallet with my name engraved on the inside clasp.'
        )
        self.client.login(username='admin1', password='testpass123')
        response = self.client.post(
            reverse('claim_review_detail', args=[claim.id]),
            {'decision': 'approve', 'admin_notes': 'Answers match.'}
        )
        self.assertRedirects(response, reverse('claim_review_list'))
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'approved')
        self.assertTrue(AuditLog.objects.filter(action_type='CLAIM_APPROVED').exists())

    def test_admin_can_reject_claim(self):
        claim = Claim.objects.create(
            item=self.found_item, claimant=self.student,
            verification_answers='Cannot describe the item properly at all.'
        )
        self.client.login(username='admin1', password='testpass123')
        self.client.post(
            reverse('claim_review_detail', args=[claim.id]),
            {'decision': 'reject', 'admin_notes': 'Answers do not match.'}
        )
        claim.refresh_from_db()
        self.assertEqual(claim.status, 'rejected')

    def test_non_admin_cannot_access_review_panel(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('claim_review_list'))
        self.assertEqual(response.status_code, 403)

    def test_audit_log_accessible_to_admin(self):
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('audit_log'))
        self.assertEqual(response.status_code, 200)

    def test_audit_log_blocked_for_student(self):
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('audit_log'))
        self.assertEqual(response.status_code, 403)

    def test_cannot_claim_own_reported_item(self):
        own_item = Item.objects.create(
            item_type='found', title='My Own Item', description='I reported this myself.',
            category='other', location='Canteen', date_reported='2026-06-20',
            reported_by=self.student,
        )
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('submit_claim', args=[own_item.id]))
        self.assertRedirects(response, reverse('search'))
        self.assertEqual(Claim.objects.count(), 0)

    def test_cannot_claim_returned_item(self):
        self.found_item.status = 'returned'
        self.found_item.save()
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('submit_claim', args=[self.found_item.id]))
        self.assertRedirects(response, reverse('search'))

    def test_cannot_submit_duplicate_claim(self):
        self.client.login(username='student1', password='testpass123')
        Claim.objects.create(
            item=self.found_item, claimant=self.student,
            verification_answers='First claim with sufficient identifying detail provided here.'
        )
        response = self.client.post(
            reverse('submit_claim', args=[self.found_item.id]),
            {'verification_answers': 'Trying to submit a second claim for the same item again.'}
        )
        self.assertRedirects(response, reverse('my_claims'))
        self.assertEqual(Claim.objects.filter(claimant=self.student).count(), 1)
