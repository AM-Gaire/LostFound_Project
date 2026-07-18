from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from .models import User
from .forms import RegisterForm, LoginForm, CreateStaffForm, ChangePasswordForm
from items.models import Item
from claims.models import Claim, AuditLog


def home_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    recent_found = Item.objects.filter(item_type='found').order_by('-created_at')[:3]
    grid_found = Item.objects.filter(item_type='found').order_by('-created_at')[:4]
    return render(request, 'home.html', {'recent_found': recent_found, 'grid_found': grid_found})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password.')

    return render(request, 'accounts/login.html', {'form': form})


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            role='student',
        )
        messages.success(request, 'Account created successfully. Please log in.')
        return redirect('login')

    return render(request, 'accounts/register.html', {'form': form})


def logout_view(request):
    if request.method == 'POST':
        logout(request)
    return redirect('home')


@login_required
def dashboard_view(request):
    user = request.user

    if user.role == 'admin':
        context = {
            'total_items': Item.objects.count(),
            'total_lost': Item.objects.filter(item_type='lost').count(),
            'total_found': Item.objects.filter(item_type='found').count(),
            'pending_claims': Claim.objects.filter(status__in=('pending', 'info_requested')).count(),
            'total_users': User.objects.count(),
            'recent_claims': Claim.objects.select_related('item', 'claimant').filter(
                status__in=('pending', 'info_requested')
            ).order_by('-submitted_at')[:5],
            'recent_audit': AuditLog.objects.select_related('performed_by', 'related_item').order_by('-timestamp')[:5],
        }
        return render(request, 'accounts/dashboard_admin.html', context)

    if user.role == 'staff':
        my_logged_items = Item.objects.filter(item_type='found', reported_by=user).order_by('-created_at')
        approved_pickups = Claim.objects.select_related('item', 'claimant').filter(
            item__reported_by=user,
            status='approved',
        ).order_by('-reviewed_at')[:5]
        context = {
            'total_logged': my_logged_items.count(),
            'open_logged': my_logged_items.filter(status='open').count(),
            'awaiting_pickup': approved_pickups.count(),
            'my_logged_items': my_logged_items[:5],
            'approved_pickups': approved_pickups,
        }
        return render(request, 'accounts/dashboard_staff.html', context)

    # Student

    context = {
        'my_lost_reports': Item.objects.filter(item_type='lost', reported_by=user).count(),
        'my_claims': Claim.objects.filter(claimant=user).count(),
        'pending_claims': Claim.objects.filter(claimant=user, status='pending').count(),
        'available_found': Item.objects.filter(item_type='found', status='open').count(),
        'recent_found': Item.objects.filter(item_type='found', status='open').order_by('-created_at')[:5],
        'my_recent_claims': Claim.objects.select_related('item').filter(claimant=user).order_by('-submitted_at')[:5],
    }
    return render(request, 'accounts/dashboard_student.html', context)


@login_required
def manage_users_view(request):
    if request.user.role != 'admin':
        raise PermissionDenied

    form = CreateStaffForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        User.objects.create_user(
            username=form.cleaned_data['username'],
            email=form.cleaned_data['email'],
            password=form.cleaned_data['password'],
            role='staff',
        )
        AuditLog.objects.create(
            action_type='STAFF_ACCOUNT_CREATED',
            performed_by=request.user,
            details=f'Staff account created for {form.cleaned_data["username"]}',
        )
        messages.success(request, f'Staff account for "{form.cleaned_data["username"]}" created successfully.')
        return redirect('manage_users')

    staff_users = User.objects.filter(role='staff').order_by('username')
    student_users = User.objects.filter(role='student').order_by('username')
    return render(request, 'accounts/manage_users.html', {
        'form': form,
        'staff_users': staff_users,
        'student_users': student_users,
    })


@login_required
def edit_user_view(request, user_id):
    if request.user.role != 'admin':
        raise PermissionDenied

    from django.shortcuts import get_object_or_404
    target = get_object_or_404(User, id=user_id)

    if target.role == 'admin' and target != request.user:
        messages.error(request, 'You cannot edit another admin account.')
        return redirect('manage_users')

    form = ChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        target.set_password(form.cleaned_data['new_password'])
        target.save()
        AuditLog.objects.create(
            action_type='PASSWORD_CHANGED',
            performed_by=request.user,
            details=f'Password changed for user "{target.username}" ({target.get_role_display()})',
        )
        messages.success(request, f'Password for "{target.username}" updated successfully.')
        return redirect('manage_users')

    return render(request, 'accounts/edit_user.html', {'form': form, 'target': target})


@login_required
def delete_user_view(request, user_id):
    if request.user.role != 'admin':
        raise PermissionDenied

    from django.shortcuts import get_object_or_404
    target = get_object_or_404(User, id=user_id)

    if target == request.user:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('manage_users')

    if target.role == 'admin':
        messages.error(request, 'Admin accounts cannot be deleted here.')
        return redirect('manage_users')

    if request.method == 'POST':
        username = target.username
        target.delete()
        AuditLog.objects.create(
            action_type='USER_DELETED',
            performed_by=request.user,
            details=f'User account "{username}" deleted',
        )
        messages.success(request, f'Account "{username}" has been deleted.')
        return redirect('manage_users')

    return render(request, 'accounts/confirm_delete_user.html', {'target': target})
