from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile, Group, Messages
from crispy_forms.helper import FormHelper, Layout
from crispy_forms.layout import Submit
from crispy_forms.layout import Field


class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["username", "password1", "password2"]

class GroupCreateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):

        super(GroupCreateForm, self).__init__(*args, **kwargs)

        self.fields["group_name"].label = "Group Name :"
        self.fields["group_name"].widget.attrs["placeholder"] = "Enter Group Name..."

        self.helper = FormHelper()
        self.helper.form_class = "form-horizontal form-class"
        self.helper.label_class = "form-group col-lg-2"
        self.helper.field_class = "input-class col-lg-10"
        self.helper.layout = Layout(
            "group_name", Submit("submit", "Create", css_class="col-lg-2")
        )

    class Meta:
        model = Group
        fields = ["group_name"]

class MessageCreateForm(forms.ModelForm):
    message_text = forms.CharField()

    class Meta:
        model = Messages
        fields = ["message_text"]

class AddMemberForm(forms.Form):
    users = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple, label="Select users to add : "
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = "form-class"
        self.helper.field_class = "form-field-class"
        self.helper.layout = Layout(
            "users", Submit("submit", "Add To Group", css_class="col-lg-2")
        )

