from django.contrib import admin
from .models import Agent, Artifact, EventLog, Message

admin.site.register(Agent)
admin.site.register(Artifact)
admin.site.register(EventLog)
admin.site.register(Message)
