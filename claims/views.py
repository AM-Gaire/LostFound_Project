from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone
from items.models import Item
from .models import Claim, AuditLog
from .forms import ClaimSubmitForm


# NOTE: Claim review is intentionally restricted to admin accounts only (staff cannot review claims).
def admin_required(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
def submit_claim_view(request, item_id):
    item = get_object_or_404(Item, id=item_id, item_type='found')

    if request.user.role != 'student':
        messages.error(request, 'Only students can submit claims.')
        return redirect('search')

    if item.reported_by == request.user:
        messages.error(request, 'You cannot claim an item you reported yourself.')
        return redirect('search')

    if item.status not in ('open', 'under_review'):
        messages.error(request, 'This item is no longer available to claim.')
        return redirect('search')

    if Claim.objects.filter(item=item, claimant=request.user).exists():
        messages.error(request, 'You have already submitted a claim for this item.')
        return redirect('my_claims')

    form = ClaimSubmitForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            claim = Claim.objects.create(
                item=item,
                claimant=request.user,
                verification_answers=form.cleaned_data['verification_answers'],
            )
            item.status = 'under_review'
            item.save()
            AuditLog.objects.create(
                action_type='CLAIM_SUBMITTED',
                performed_by=request.user,
                related_item=item,
                details=f'Claim submitted on {item.title}',
            )
        messages.success(request, 'Your claim has been submitted for review.')
        return redirect('my_claims')

    return render(request, 'claims/submit_claim.html', {'item': item, 'form': form})


@login_required
def my_claims_view(request):
    claims = Claim.objects.select_related('item').filter(claimant=request.user).order_by('-submitted_at')
    lost_reports = Item.objects.filter(reported_by=request.user, item_type='lost').order_by('-created_at')
    return render(request, 'claims/my_claims.html', {'claims': claims, 'lost_reports': lost_reports})


@login_required
def update_claim_view(request, claim_id):
    claim = get_object_or_404(Claim, id=claim_id, claimant=request.user)

    if claim.status != 'info_requested':
        messages.error(request, 'This claim does not require additional information.')
        return redirect('my_claims')

    if request.method == 'POST':
        additional = request.POST.get('additional_info', '').strip()
        if not additional:
            messages.error(request, 'Please provide additional details before submitting.')
            return redirect('my_claims')

        claim.verification_answers = (
            claim.verification_answers
            + '\n\n--- Student Follow-up ---\n'
            + additional
        )
        claim.status = 'pending'
        claim.save()

        AuditLog.objects.create(
            action_type='CLAIM_UPDATED',
            performed_by=request.user,
            related_item=claim.item,
            details=f'Student provided additional info for claim #{claim.id} on "{claim.item.title}"',
        )
        messages.success(request, 'Your additional details have been submitted. The admin will review your claim again.')
        return redirect('my_claims')

    return redirect('my_claims')


@login_required
def claim_review_list_view(request):
    if not admin_required(request.user):
        raise PermissionDenied

    claims = Claim.objects.select_related('item', 'claimant').filter(
        status__in=('pending', 'info_requested')
    ).order_by('-submitted_at')

    approved_claims = Claim.objects.select_related('item', 'claimant').filter(
        status='approved'
    ).order_by('-submitted_at')

    # Found items with no claim yet — reported but nobody has claimed them
    claimed_item_ids = Claim.objects.exclude(status='rejected').values_list('item_id', flat=True)
    unclaimed_found = Item.objects.select_related('reported_by').filter(
        item_type='found', status='open'
    ).exclude(id__in=claimed_item_ids).order_by('-created_at')

    # Lost item reports waiting to be matched
    lost_reports = Item.objects.select_related('reported_by').filter(
        item_type='lost'
    ).order_by('-created_at')

    context = {
        'claims': claims,
        'approved_claims': approved_claims,
        'unclaimed_found': unclaimed_found,
        'lost_reports': lost_reports,
    }
    return render(request, 'claims/review_list.html', context)


@login_required
def claim_review_detail_view(request, claim_id):
    if not admin_required(request.user):
        raise PermissionDenied

    claim = get_object_or_404(Claim, id=claim_id)

    if request.method == 'POST':
        decision = request.POST.get('decision')
        notes = request.POST.get('admin_notes', '')

        if decision not in ('approve', 'reject', 'request_info'):
            messages.error(request, 'Invalid decision.')
            return redirect('claim_review_detail', claim_id=claim.id)

        with transaction.atomic():
            if decision == 'approve':
                claim.status = 'approved'
                claim.item.status = 'claimed'
                claim.item.save()
                action = 'CLAIM_APPROVED'
            elif decision == 'reject':
                claim.status = 'rejected'
                claim.item.status = 'open'
                claim.item.save()
                action = 'CLAIM_REJECTED'
            else:
                claim.status = 'info_requested'
                action = 'CLAIM_INFO_REQUESTED'

            claim.admin_notes = notes
            claim.reviewed_by = request.user
            claim.reviewed_at = timezone.now()
            claim.save()

            AuditLog.objects.create(
                action_type=action,
                performed_by=request.user,
                related_item=claim.item,
                details=f'{action.replace("_", " ").title()} for claim #{claim.id} on {claim.item.title}',
            )

        messages.success(request, f'Claim {claim.get_status_display().lower()}.')
        return redirect('claim_review_list')

    return render(request, 'claims/review_detail.html', {'claim': claim})


@login_required
def mark_collected_view(request, claim_id):
    if not (request.user.role in ('admin', 'staff')):
        raise PermissionDenied
    claim = get_object_or_404(Claim, id=claim_id, status='approved')
    if request.method == 'POST':
        if claim.item.status == 'returned':
            messages.error(request, 'This item has already been marked as collected.')
            if request.user.role == 'admin':
                return redirect('claim_review_list')
            return redirect('my_logged_items')
        claim.item.status = 'returned'
        claim.item.save()
        AuditLog.objects.create(
            action_type='ITEM_COLLECTED',
            performed_by=request.user,
            related_item=claim.item,
            details=f'Item "{claim.item.title}" marked as collected by {claim.claimant.username} (claim #{claim.id})',
        )
        messages.success(request, f'"{claim.item.title}" marked as collected.')
    if request.user.role == 'admin':
        return redirect('claim_review_list')
    return redirect('my_logged_items')


@login_required
def audit_log_view(request):
    if not admin_required(request.user):
        raise PermissionDenied

    logs = AuditLog.objects.select_related('performed_by', 'related_item').order_by('-timestamp')
    return render(request, 'claims/audit_log.html', {'logs': logs})
