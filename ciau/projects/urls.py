from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path('login/',   views.login_view,  name='login'),
    path('logout/',  views.logout_view, name='logout'),

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Projects
    path('projects/new/',                                         views.project_create,      name='project_create'),
    path('projects/<int:pk>/',                                    views.project_detail,      name='project_detail'),
    path('projects/<int:pk>/edit/',                               views.project_edit,        name='project_edit'),
    path('projects/<int:pk>/archive/',                            views.project_archive,     name='project_archive'),
    path('projects/<int:pk>/delete/',                             views.project_delete,      name='project_delete'),

    # Deliverables
    path('projects/<int:pk>/deliverables/add/',                   views.deliverable_add,     name='deliverable_add'),
    path('projects/<int:pk>/deliverables/<int:did>/edit/',        views.deliverable_edit,    name='deliverable_edit'),
    path('projects/<int:pk>/deliverables/<int:did>/upload/',      views.deliverable_upload,  name='deliverable_upload'),
    path('projects/<int:pk>/deliverables/<int:did>/delete/',      views.deliverable_delete,  name='deliverable_delete'),

    # Payments
    path('projects/<int:pk>/payments/add/',                       views.payment_add,         name='payment_add'),
    path('projects/<int:pk>/payments/<int:pid>/collect/',         views.payment_collect,     name='payment_collect'),
    path('projects/<int:pk>/payments/<int:pid>/edit/',            views.payment_edit,        name='payment_edit'),
    path('projects/<int:pk>/payments/<int:pid>/delete/',          views.payment_delete,      name='payment_delete'),

    # References
    path('projects/<int:pk>/references/add/',                     views.reference_add,       name='reference_add'),
    path('projects/<int:pk>/references/<int:rid>/delete/',        views.reference_delete,    name='reference_delete'),

    # Weekly activities
    path('activities/',              views.activities_week,  name='activities_week'),
    path('activities/<int:aid>/delete/', views.activity_delete, name='activity_delete'),

    # Contracts & Archives
    path('contracts/', views.contracts_list, name='contracts_list'),
    path('archives/',  views.archives_list,  name='archives_list'),
]
