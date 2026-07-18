from django.contrib import admin
from .models import Item


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'item_type', 'category', 'status', 'reported_by', 'date_reported')
    list_filter = ('item_type', 'category', 'status')
    search_fields = ('title', 'description', 'location')