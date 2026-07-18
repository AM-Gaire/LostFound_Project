from django.db import models
from django.conf import settings


class Item(models.Model):
    """
    Represents a lost or found item reported in the system.
    Covers both LostItem and FoundItem from the ER diagram via a 'item_type' field.
    """

    class ItemType(models.TextChoices):
        LOST = 'lost', 'Lost'
        FOUND = 'found', 'Found'

    class Category(models.TextChoices):
        ELECTRONICS = 'electronics', 'Electronics'
        BAGS = 'bags', 'Bags'
        KEYS = 'keys', 'Keys'
        ACCESSORIES = 'accessories', 'Accessories'
        BOOKS = 'books', 'Books'
        CLOTHING = 'clothing', 'Clothing'
        OTHER = 'other', 'Other'

    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        UNDER_REVIEW = 'under_review', 'Under Review'
        CLAIMED = 'claimed', 'Claimed'
        RETURNED = 'returned', 'Returned'

    item_type = models.CharField(max_length=10, choices=ItemType.choices)
    title = models.CharField(max_length=150)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    location = models.CharField(max_length=200)
    date_reported = models.DateField()
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reported_items',
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_item_type_display()}: {self.title}"