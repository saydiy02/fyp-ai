from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserData(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    goal = models.IntegerField(choices=[(0, 'Web-application'), (1, 'API'), (2, 'Mobile-app')])
    attackT = models.IntegerField(choices=[(0, 'Reflected'), (1, 'Stored'), (2, 'Dom-based')])
    skill = models.IntegerField(choices=[(0, 'Beginner'), (1, 'Intermediate'), (2, 'Advanced')])
    automation = models.IntegerField(choices=[(0, 'No'), (1, 'Yes')])
    platform = models.IntegerField(choices=[(0, 'Windows'), (1, 'Linux'), (2, 'MacOS')])
    suggest = models.IntegerField(choices=[(0, 'Nmap & PwnXSS'), (1, 'Nmap & XSStrike'), (2, 'Nmap & Burp Suite'), (3, 'Nmap & OWASP ZAP')])
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.user.username} - {self.goal}'

class ToolResult(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    tool_name = models.CharField(max_length=50)
    target = models.CharField(max_length=255)
    result = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    user_data = models.ForeignKey(UserData, on_delete=models.CASCADE)
    agree = models.BooleanField()
    preferred_suggestion = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return f'Feedback for {self.user_data.user.username} - Agree: {self.agree}'