from django.contrib import admin
from .models import Balance, Hotel, Game, Location

# Register your models here.
admin.site.register(Location)
admin.site.register(Balance)
admin.site.register(Hotel)
admin.site.register(Game)
