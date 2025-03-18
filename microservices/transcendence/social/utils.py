from .models import Friendship, Ban

def is_friend(from_id, to_id) -> bool:
    return Friendship.objects.filter(user_from__pk = from_id, user_to__pk = to_id, status = 'A').count()

def is_banned(from_id, to_id) -> bool:
    return Ban.objects.filter(user_from__pk = from_id, user_to__pk = to_id).count()

def can_apply(from_id, to_id) -> bool:
     return not (Friendship.objects.filter(user_from__pk = from_id, user_to__pk = to_id).count() + Friendship.objects.filter(user_from__pk = to_id, user_to__pk = from_id).count())


def delete_friendship(user_to, user_from):
    Friendship.objects.filter(user_to = user_to, user_from = user_from).delete()
    Friendship.objects.filter(user_to = user_from, user_from = user_to).delete()


