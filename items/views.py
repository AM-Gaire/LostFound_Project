from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import Item
from .forms import ItemReportForm
from claims.models import AuditLog


@login_required
def report_item_view(request):
    user = request.user
    can_report_found = user.role in ('staff', 'admin')

    form = ItemReportForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        item_type = form.cleaned_data['item_type']
        if item_type == 'found' and not can_report_found:
            messages.error(request, 'Only staff members can report found items.')
            return render(request, 'items/report_item.html', {
                'form': form, 'can_report_found': can_report_found
            })
        item = form.save(commit=False)
        item.reported_by = user
        item.save()
        AuditLog.objects.create(
            action_type='ITEM_REPORTED',
            performed_by=user,
            related_item=item,
            details=f'{item.get_item_type_display()} item reported: {item.title}',
        )
        messages.success(request, 'Item reported successfully.')
        return redirect('dashboard')

    return render(request, 'items/report_item.html', {
        'form': form, 'can_report_found': can_report_found
    })


@login_required
def search_items_view(request):
    items = Item.objects.filter(item_type='found').order_by('-created_at')

    query = request.GET.get('q', '')
    category = request.GET.get('category', '')

    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(location__icontains=query)
        )
    if category:
        items = items.filter(category=category)

    context = {
        'items': items,
        'query': query,
        'selected_category': category,
        'categories': Item.Category.choices,
    }
    return render(request, 'items/search.html', context)


@login_required
def item_manage_view(request, item_id):
    if request.user.role != 'admin':
        raise PermissionDenied

    item = get_object_or_404(Item, id=item_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(Item.Status.choices):
            old_status = item.status
            item.status = new_status
            item.save()
            AuditLog.objects.create(
                action_type='ITEM_STATUS_UPDATED',
                performed_by=request.user,
                related_item=item,
                details=f'Status changed from {old_status} to {new_status} on "{item.title}"',
            )
            messages.success(request, f'Item status updated to {item.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')
        return redirect('item_manage', item_id=item.id)

    return render(request, 'items/item_manage.html', {
        'item': item,
        'statuses': Item.Status.choices,
    })


@login_required
def my_logged_items_view(request):
    if request.user.role != 'staff':
        raise PermissionDenied

    items = Item.objects.filter(
        item_type='found', reported_by=request.user
    ).prefetch_related('claims').order_by('-created_at')

    return render(request, 'items/my_logged_items.html', {'items': items})


@login_required
def all_items_view(request):
    if request.user.role != 'admin':
        raise PermissionDenied

    items = Item.objects.select_related('reported_by').order_by('-created_at')

    filter_type = request.GET.get('type', '')
    filter_status = request.GET.get('status', '')

    if filter_type:
        items = items.filter(item_type=filter_type)
    if filter_status:
        items = items.filter(status=filter_status)

    context = {
        'items': items,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'statuses': Item.Status.choices,
    }
    return render(request, 'items/all_items.html', context)
