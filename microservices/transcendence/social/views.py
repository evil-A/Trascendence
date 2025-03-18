from django.shortcuts import render
from oauth.utils import jwtManager, jwt_login_required, jwt_refresh
from oauth.models import User
from oauth import views as oauth
from .models import Friendship, Ban
from django.db.models import Q
from social import utils as utils

# Create your views here.

@jwt_refresh
@jwt_login_required
def social_view(request):
    manager = jwtManager()
    requests = Friendship.objects.filter(Q(user_to = request.user) & Q(status = 'P')).count()
    response = render(request, 'social.html', {'requests': requests})
    new_jwt =  new_jwt = manager.refresh_token(request.COOKIES.get('jwt'))
    response.set_cookie('jwt', new_jwt)
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return oauth.profile_view(request, content)
    return response

@jwt_refresh
@jwt_login_required
def search(request):
    manager = jwtManager()
    banning_users = Ban.objects.filter(user_to=request.user).values_list("user_from", flat=True)
    valid_users = User.objects.exclude(id__in=banning_users).filter(username__icontains = request.POST.get('search'))[:10]
    context = {
        'results': valid_users}
    response = render(request, 'user_search.html', context)
    new_jwt =  new_jwt = manager.refresh_token(request.COOKIES.get('jwt'))
    response.set_cookie('jwt', new_jwt)
    return response

@jwt_refresh
@jwt_login_required
def applications(request):
    manager = jwtManager()
    applications = Friendship.objects.filter(user_to = request.user, status = 'P')
    context = {
        'applications': applications 
    }
    response = render(request, "social_applications.html", context)
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return social_view(request, content)
    return response

@jwt_refresh
@jwt_login_required
def friends(request):
    manager = jwtManager()
    friends = Friendship.objects.filter(status = 'A').filter(Q(user_from = request.user) | Q(user_to = request.user))
    context = {
        'me': request.user,
        'friends': friends
    }
    response = render(request, "social_friends.html", context)
    if not request.headers.get('Hx-Request'):
        content = response.content.decode("utf-8")
        return social_view(request, content)
    return response

@jwt_refresh
@jwt_login_required
def apply(request):
    user_from = request.user
    user_to = request.GET.get("id")
    if utils.can_apply(request.user.id, user_to):
        Friendship.objects.create(user_from = user_from, user_to = User.objects.get(pk = user_to))
    return(oauth.profile_view(request))

@jwt_refresh
@jwt_login_required
def accept(request):
    friendship = Friendship.objects.get(pk = request.GET.get('id'))
    friendship.status = 'A'
    friendship.save()
    return applications(request)

@jwt_refresh
@jwt_login_required
def reject(request):
    friendship = Friendship.objects.get(pk = request.GET.get('id')).delete()
    return applications(request)

@jwt_refresh
@jwt_login_required
def friend_remove(request):
    Friendship.objects.get(pk = request.GET.get('id')).delete()
    return(friends(request))

