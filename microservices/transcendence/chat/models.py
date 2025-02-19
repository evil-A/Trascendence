from django.db import models
from django.conf import settings
#from oauth.models import User

class ChatMessage(models.Model):
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_sent_messages"
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_received_messages",
        null=True,
        blank=True
    )
    message =  models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    channel = models.CharField(default="general", max_length=255)

    def  is_private(self):
        return self.recipient is not None
    
    def __str__(self):
        if self.is_private():
            return f"[PRIVATE] {self.sender.username} → {self.recipient.username}: {self.message[:20]}"
        return f"{self.sender.username} ({self.channel}): {self.message[:20]}"   