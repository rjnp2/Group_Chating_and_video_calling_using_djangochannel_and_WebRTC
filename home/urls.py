from django.urls import path
from . import views


app_name = "home"
urlpatterns = [
    path("", views.group, name="home"),
    path("<slug:grp_name>", views.group, name="group"),
    path("<slug:grp_name>/add_members", views.add_member, name="add_members"),
]
