from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from accounts import views as account_views
from items import views as item_views
from claims import views as claim_views

admin.site.site_header = "Campus Lost & Found Administration"
admin.site.site_title = "Lost & Found Admin"
admin.site.index_title = "Welcome to the Campus Lost & Found Admin Panel"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', account_views.home_view, name='home'),
    path('login/', account_views.login_view, name='login'),
    path('register/', account_views.register_view, name='register'),
    path('logout/', account_views.logout_view, name='logout'),
    path('dashboard/', account_views.dashboard_view, name='dashboard'),
    path('manage-users/', account_views.manage_users_view, name='manage_users'),
    path('manage-users/<int:user_id>/edit/', account_views.edit_user_view, name='edit_user'),
    path('manage-users/<int:user_id>/delete/', account_views.delete_user_view, name='delete_user'),
    path('report/', item_views.report_item_view, name='report_item'),
    path('search/', item_views.search_items_view, name='search'),
    path('claim/<int:item_id>/', claim_views.submit_claim_view, name='submit_claim'),
    path('my-claims/', claim_views.my_claims_view, name='my_claims'),
    path('my-claims/<int:claim_id>/update/', claim_views.update_claim_view, name='update_claim'),
    path('review/', claim_views.claim_review_list_view, name='claim_review_list'),
    path('review/<int:claim_id>/', claim_views.claim_review_detail_view, name='claim_review_detail'),
    path('review/<int:claim_id>/collected/', claim_views.mark_collected_view, name='mark_collected'),
    path('audit-log/', claim_views.audit_log_view, name='audit_log'),
    path('items/all/', item_views.all_items_view, name='all_items'),
    path('items/my-logged/', item_views.my_logged_items_view, name='my_logged_items'),
    path('items/<int:item_id>/manage/', item_views.item_manage_view, name='item_manage'),

    # Forgot password URLs
    path('forgot-password/', auth_views.PasswordResetView.as_view(template_name='accounts/forgot_password.html', email_template_name='registration/password_reset_email.html', html_email_template_name='registration/password_reset_email.html'), name='password_reset'),
    path('forgot-password/done/', auth_views.PasswordResetDoneView.as_view(template_name='accounts/forgot_password_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='accounts/forgot_password_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='accounts/forgot_password_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)