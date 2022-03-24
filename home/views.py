from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Group, Messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from .forms import (
    UserRegisterForm,
    MessageCreateForm,
    GroupCreateForm,
    AddMemberForm
)
from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.contrib.auth.models import User
import json
from django.utils.safestring import mark_safe

# Create your views here.    
@login_required
def group(request, grp_name=None):

    groups = request.user.all_groups.all()
    if request.method == "POST":
        g_form = GroupCreateForm(request.POST)

        if g_form.is_valid():
            group = g_form.save(commit=False)
            group.creater = request.user
            group.save()
            group.members.add(request.user)
            return redirect("home:home")
    else:
        g_form = GroupCreateForm()
    
    room_name_json = None
    fetch_all_message= None
    group = ''
    try:
        if grp_name:
            group = request.user.all_groups.get(group_name=grp_name)
            fetch_all_message = Messages.objects.filter(parent_group = group.id).order_by('message_detail__timestamp')

    except Group.DoesNotExist:
        raise Http404("Group Does not exist or You are not member of this group")

    context = {
        'room_name_json': mark_safe(json.dumps(grp_name)),
        'group' : group,
        "groups": groups,
        "g_form" : g_form,
        'fetch_all_message' : fetch_all_message
    }

    return render(request, 'home/home.html', context)

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = UserRegisterForm()

    return render(request, "home/register.html", {"form": form})

@login_required
def add_member(request, grp_name):
    try:
        group = Group.objects.get(group_name=grp_name)
        flag = group.members.get(username=request.user.username)

        #find all suggested friend list
        user_list = [memb.id for memb in group.members.all()]
        all_user = [(user.id, user.username) for user in User.objects.exclude(Q(id__in = list(set(user_list)))) ]
    except Group.DoesNotExist:
        raise Http404("Group Does not exist")

    if flag:
        if request.method == 'POST':           
            if 'users' in request.POST:
                userlist = AddMemberForm(request.POST)
                userlist.fields['users'].choices = all_user

                if userlist.is_valid():
                    print('sucess') 
                    users = userlist.cleaned_data.get('users') 
                    for user in users:
                        print(User.objects.get(id=user), user)
                        group.members.add(User.objects.get(id=user))

                    return redirect('home:group', grp_name=grp_name)
                else:
                    print(userlist.errors.as_text())
        
        userlistform = AddMemberForm()
        userlistform.fields['users'].choices = all_user
        context = {
            "list" : userlistform,
            "group" : group
        }          
        return render(request, "home/add_members.html", context)