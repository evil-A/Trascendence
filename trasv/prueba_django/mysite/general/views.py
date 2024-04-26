
#from django.shortcuts import render
from django.utils.translation import activate

def activate_language(request):
    myLanguage = request.session.get('myLanguage')
    if not (myLanguage is None):
        activate(myLanguage)
