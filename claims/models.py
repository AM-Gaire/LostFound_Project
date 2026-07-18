from django.db import models
from django.conf import settings
from items.models import Item


class Claim(models.Model):
    """
    A claim submitted by a user against a found item,
    requiring identifying verification answers and admin approval.
    """

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        INFO_REQUESTED = 'info_requested', 'More Info Requested'

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='claims',
    )
    claimant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='claims',
    )
    verification_answers = models.TextField(
        help_text='Claimant answers to identifying verification questions.'
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_claims',
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Claim #{self.id} on {self.item.title} ({self.get_status_display()})"


class AuditLog(models.Model):
    """
    Records key system actions for accountability and traceability.
    """

    action_type = models.CharField(max_length=100)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_logs',
    )
    related_item = models.ForeignKey(
        Item,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
    )
    details = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action_type} by {self.performed_by} at {self.timestamp}"