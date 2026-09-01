"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from chores import views as chores_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', chores_views.home, name='home'),
    path(
        'recurring-chores/add/',
        chores_views.add_recurring_chore,
        name='add_recurring_chore',
    ),
    path(
        'one-off-tasks/add/',
        chores_views.add_one_off_task,
        name='add_one_off_task',
    ),
    path(
        'recurring-chores/<int:chore_id>/mark-done/',
        chores_views.mark_recurring_chore_done,
        name='mark_recurring_chore_done',
    ),
    path(
        'one-off-tasks/<int:task_id>/done/',
        chores_views.mark_one_off_task_done,
        name='mark_one_off_task_done',
    ),
    path(
        'one-off-tasks/<int:task_id>/cancel/',
        chores_views.cancel_one_off_task,
        name='cancel_one_off_task',
    ),
    path(
        'recurring-chores/<int:chore_id>/edit/',
        chores_views.edit_recurring_chore,
        name='edit_recurring_chore',
    ),
    path(
        'recurring-chores/<int:chore_id>/cancel-edit/',
        chores_views.cancel_edit_recurring_chore,
        name='cancel_edit_recurring_chore',
    ),
    path(
        'recurring-chores/<int:chore_id>/delete/',
        chores_views.delete_recurring_chore,
        name='delete_recurring_chore',
    ),
]
