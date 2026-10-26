from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import CustomUser
from .forms import (
    UserLoginForm,
    UserRegistrationForm,
    UserProfileForm,
    UserAdminForm,
    CustomPasswordChangeForm
)
from .decorators import role_required, admin_required
from audit.utils import log_audit_action

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username} ({user.get_role_display()}).")
            log_audit_action(
                user=user,
                action='LOGIN',
                entity_type='User',
                entity_id=str(user.id),
                summary=f"User {user.username} logged in successfully",
                request=request
            )
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard:index')
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = UserLoginForm()

    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        user = request.user
        log_audit_action(
            user=user,
            action='LOGOUT',
            entity_type='User',
            entity_id=str(user.id),
            summary=f"User {username} logged out",
            request=request
        )
        logout(request)
        messages.info(request, "You have been logged out of SkyShield.")
    return redirect('accounts:login')

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful! You may now sign in with your credentials.")
            log_audit_action(
                user=user,
                action='CREATE',
                entity_type='User',
                entity_id=str(user.id),
                summary=f"New user {user.username} registered with role REPORTER",
                request=request
            )
            return redirect('accounts:login')
        else:
            messages.error(request, "Please correct the errors in the registration form below.")
    else:
        form = UserRegistrationForm()

    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='User',
                entity_id=str(request.user.id),
                summary=f"User {request.user.username} updated their profile",
                request=request
            )
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def password_change_view(request):
    if request.method == 'POST':
        form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='User',
                entity_id=str(user.id),
                summary=f"User {user.username} changed their password",
                request=request
            )
            return redirect('accounts:profile')
        else:
            messages.error(request, "Please fix the errors below to change your password.")
    else:
        form = CustomPasswordChangeForm(user=request.user)

    return render(request, 'accounts/password_change.html', {'form': form})

@login_required
@admin_required
def user_list_view(request):
    search_query = request.GET.get('q', '').strip()
    role_filter = request.GET.get('role', '').strip()
    dept_filter = request.GET.get('department', '').strip()

    users = CustomUser.objects.all().order_by('username')

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(employee_id__icontains=search_query)
        )

    if role_filter:
        users = users.filter(role=role_filter)

    if dept_filter:
        users = users.filter(department=dept_filter)

    paginator = Paginator(users, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/user_list.html', {
        'page_obj': page_obj,
        'search_query': search_query,
        'role_filter': role_filter,
        'dept_filter': dept_filter,
        'role_choices': CustomUser.ROLE_CHOICES,
        'dept_choices': CustomUser.DEPARTMENT_CHOICES,
    })

@login_required
@admin_required
def user_edit_view(request, user_id):
    target_user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserAdminForm(request.POST, instance=target_user)
        if form.is_valid():
            form.save()
            messages.success(request, f"User '{target_user.username}' updated successfully.")
            log_audit_action(
                user=request.user,
                action='UPDATE',
                entity_type='User',
                entity_id=str(target_user.id),
                summary=f"Admin updated user {target_user.username} (Role: {target_user.role})",
                request=request
            )
            return redirect('accounts:user_list')
    else:
        form = UserAdminForm(instance=target_user)

    return render(request, 'accounts/user_form.html', {
        'form': form,
        'target_user': target_user,
        'is_edit': True,
    })

@login_required
@admin_required
def user_toggle_status_view(request, user_id):
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('accounts:user_list')

    target_user = get_object_or_404(CustomUser, id=user_id)
    if target_user == request.user:
        messages.error(request, "Security violation: You cannot deactivate your own active session account.")
        return redirect('accounts:user_list')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User account '{target_user.username}' has been {status_str}.")
    log_audit_action(
        user=request.user,
        action='UPDATE',
        entity_type='User',
        entity_id=str(target_user.id),
        summary=f"Admin {status_str} user {target_user.username}",
        request=request
    )
    return redirect('accounts:user_list')

def error_403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def error_404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def error_500(request):
    return render(request, 'errors/500.html', status=500)
