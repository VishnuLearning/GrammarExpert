from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic.base import TemplateView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from . import views
from django.conf.urls import url
from django.urls.base import reverse_lazy


urlpatterns = [
    path('', include('django.contrib.auth.urls')),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.update_profile, name='profile'),
    path('activate/<str:uidb64>/<str:token>', views.activate, name='activate'),
    path('attempt/<str:code>', views.attempt, name='attempt'),
    path('questionmanager',views.questionmanager,name='questionmanager'),
    path('questionmanager/del/<int:qid>',views.delete_question, name = 'delete'),
    path('',views.main_view,name='homepage'),
    path('practice/',views.practice,name='practice'),
    path('fetch/',views.fetch_results,name='fetch_results'),
    path('getresult/',views.get_results,name='get_results'),
    path('updatecomment/',views.update_comment,name='update_comment'),
    path('getuserperformance/',views.getuserperformance,name='getuserperformance'),
    path('leaderboard/<int:qid>',views.leaderboard, name = 'leaderboard'),
    path('getuserattemptdata/', views.getuserattemptdata, name='getuserattemptdata'),
    path('analytics/', views.getallusersummary, name='analytics'),
    path('getuserperfdata/<int:uid>',views.getuserperfdata, name = 'getuserperfdata'),
    path('canattempt/<str:code>',views.canattempt, name = 'canattempt'),
    path('deleteattempt/<int:attemptid>',views.deleteattempt, name = 'deleteattempt'),
    path('updatequestion/<int:pk>',views.EditQuestion.as_view(), name = 'updatequestion'),
    path('reset-password/', PasswordResetView.as_view(template_name= 'registration/reset_password.html', success_url= 'done/', email_template_name= 'registration/reset_password_email.html'), name='password_reset'),
    path('reset-password/done/', PasswordResetDoneView.as_view(template_name= 'registration/reset_password_done.html'), name='password_reset_done'), # name as "password_reset_done" because the default 'reset password' view is defined to redirect to view with that name 
    # path('reset-password/confirm/<str:uidb64>/<str:token>/', PasswordResetConfirmView.as_view(template_name= 'registration/reset_password_confirm.html', success_url= 'complete/'), name='password_reset_confirm'),
    url(r'^reset-password/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)/$', PasswordResetConfirmView.as_view(template_name= 'registration/reset_password_confirm.html', success_url= reverse_lazy('password_reset_complete')), name='password_reset_confirm'),
    path('reset-password/complete/', PasswordResetCompleteView.as_view(template_name= 'registration/reset_password_complete.html'), name='password_reset_complete')
]