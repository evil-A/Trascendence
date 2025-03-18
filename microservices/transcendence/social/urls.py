from django.urls import path
from social import views

urlpatterns = [
    path("", views.social_view  , name = "social"),
    path("search/", views.search, name = "search"),
    path("applications/", views.applications, name = "applications"),
    path("friend/", views.friends, name='friends'),
    path("friend/apply/", views.apply, name="friend_app"),
    path("friend/accept", views.accept, name ="accept_friend"),
    path("friend/reject", views.reject, name ="reject_friend"),
    path("friend/remove", views.friend_remove, name ="remove_friend"),
]