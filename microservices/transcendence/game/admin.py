from django.contrib import admin
from .models import *

# Register your models here.

class GameAdmin(admin.ModelAdmin):
    readonly_fields = ('date',)

admin.site.register(Game, GameAdmin)