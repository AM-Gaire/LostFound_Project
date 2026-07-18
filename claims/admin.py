from django.contrib import admin
from .models import Claim, AuditLog


@admin.register(Claim)
class ClaimAdmin(admin.ModelAdmin):
    list_display = ('id', 'item', 'claimant', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('item__title', 'claimant__username')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action_type', 'performed_by', 'related_item', 'timestamp')
    list_filter = ('action_type',)
    readonly_fields = ('timestamp',)