import uuid
from django.db import models

class Agent(models.fields.UUIDField):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=50, choices=[
        ('Running', 'Running'),
        ('Waiting', 'Waiting'),
        ('Idle', 'Idle'),
        ('Complete', 'Complete'),
        ('Error', 'Error'),
    ], default='Waiting')
    scope = models.CharField(max_length=255, default='general')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.status})"

class Artifact(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='artifacts')
    file_path = models.CharField(max_length=512)
    content = models.TextField()
    status = models.CharField(max_length=50, choices=[
        ('Proposed', 'Proposed'),
        ('Committed', 'Committed'),
    ], default='Proposed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file_path} - {self.status}"

class EventLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=100)
    payload = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} at {self.timestamp}"

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=50, choices=[
        ('user', 'User'),
        ('model', 'Model'),
        ('system', 'System')
    ])
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role}: {self.content[:20]}"
