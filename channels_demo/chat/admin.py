from django.contrib import admin

from .models import Org, Speaker, Bulletin, Message


admin.site.register([Org, Speaker, Bulletin, Message])

