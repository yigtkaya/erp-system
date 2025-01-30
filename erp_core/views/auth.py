from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from guardian.shortcuts import assign_perm, get_objects_for_user

from erp_core.models import User, UserProfile, Department, RolePermission
from erp_core.forms import UserRegistrationForm, UserProfileForm
from erp_core.permissions import IsAdminUser, HasDepartmentPermission

class UserRegistrationView(UserPassesTestMixin, CreateView):
    model = User
    form_class = UserRegistrationForm
    template_name = 'erp_core/auth/register.html'
    success_url = reverse_lazy('user_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'ADMIN'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.set_password(form.cleaned_data['password1'])
        user.save()
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            department_id=form.cleaned_data.get('department'),
            employee_id=form.cleaned_data.get('employee_id')
        )
        
        # Assign role-based permissions
        role_permissions = RolePermission.objects.filter(role=user.role)
        for role_perm in role_permissions:
            user.user_permissions.add(role_perm.permission)
        
        messages.success(self.request, f'Account created for {user.username}')
        return super().form_valid(form)

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'erp_core/auth/user_list.html'
    context_object_name = 'users'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'ADMIN'

    def get_queryset(self):
        if self.request.user.is_superuser:
            return User.objects.all()
        return User.objects.filter(departments__in=self.request.user.departments.all())

class UserProfileView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'erp_core/auth/profile.html'
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user.profile

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role,
                'departments': list(user.departments.values_list('id', flat=True))
            }
        return response

@login_required
def logout_view(request):
    logout(request)
    return redirect('login') 