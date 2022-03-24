from django.contrib import admin
from .models import Group, Messages, Profile
from django_admin_inline_paginator.admin import TabularInlinePaginated

class MessageInline(TabularInlinePaginated):
    model = Messages
    can_delete = False
    fields = ('id','parent_user','message_detail')
    max_num = 0
    readonly_fields = fields
    per_page = 10

class GroupAdmin(admin.ModelAdmin):
    list_display= ["id","group_name","creater",'updated_on']
    search_fields=["id","group_name","creater_username"]
    list_per_page = 10
    list_display_links = list_display
    readonly_fields = ["group_name","creater"]
    inlines = [MessageInline,]
    ordering = ['-updated_on']

class ProfileAdmin(admin.ModelAdmin):
    list_display= ["id","user"]
    search_fields=["id","user__username"]
    list_per_page = 10
    readonly_fields = ["user"]
    list_display_links = list_display

# To register group on admin page
admin.site.register(Group,GroupAdmin)

# To register profile model
admin.site.register(Profile, ProfileAdmin)