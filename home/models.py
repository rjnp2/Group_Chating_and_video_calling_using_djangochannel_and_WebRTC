from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.auth.models import User
from django.urls import reverse
import uuid

class Profile(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name = 'profile_detail')

class Group(models.Model):
    group_name = models.SlugField(max_length=20)
    creater = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name="all_groups")
    updated_on = models.DateTimeField(auto_now = True)

    def __str__(self):
        return self.group_name
    
    @property
    def room_group_name(self):
        return f'group_chat_{self.group_name}'

class Messages(models.Model):
    id = models.UUIDField(primary_key = True,editable = False)
    parent_group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="messages")
    parent_user = models.ForeignKey(User, verbose_name='message_sender',  on_delete=models.CASCADE)
    message_detail = models.JSONField()

    class Meta:
        ordering = ['-message_detail__timestamp']
    
    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)
        Group.objects.get(id = self.parent_group.id).save()   # Update Group TimeStampe

    def __str__(self):
        return '%s' %(self.message_detail["timestamp"])

    def get_absolute_url(self):
        return reverse("home:group", kwargs={"grp_name": self.parent_group})
