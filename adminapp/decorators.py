# adminapp/decorators.py
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout

def secure_admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. Basic Auth Check
        if not request.user.is_authenticated:
            return redirect('admin_login')
        
        # 2. Superuser Check
        if not request.user.is_superuser:
            messages.error(request, "Access Denied.")
            return redirect('home') # Adjust 'home' to your public homepage URL name
            
        # 3. 2FA Session Flag Check
        if not request.session.get('is_admin_2fa_verified', False):
            # Valid credentials, but skipped OTP. Force logout.
            logout(request)
            messages.warning(request, "Two-step verification required.")
            return redirect('admin_login')

        return view_func(request, *args, **kwargs)
    return _wrapped_view