from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.contrib.auth import authenticate
from web.instances.models import Instance
from web.accounts.models import UserProfile
from web.accounts.models import UserProfileEducation
from web.accounts.models import UserProfileIncomes
from web.accounts.models import UserProfileLiving
from web.accounts.models import UserProfileGender
from web.accounts.models import UserProfileRace
from web.accounts.models import UserProfileStake

class RegisterForm(forms.Form):

    firstName = forms.CharField(required=True, max_length=30, label=_("First Name"))
    lastName = forms.CharField(required=True, max_length=30, label=_("Last Name"))
    email = forms.EmailField(required=True, label=_("Email:"))
    password = forms.CharField(required=True, label=_("Password"), widget=forms.PasswordInput(render_value=False))
    passwordAgain = forms.CharField(required=True, label=_("Password Again"), widget=forms.PasswordInput(render_value=False))
    instance = forms.ModelChoiceField(queryset=Instance.objects.active(), label=_('Community'))
    preferred_language = forms.ChoiceField(choices=settings.LANGUAGES)

    # Ensure that a user has not already registered an account with that email address.
    def clean_email(self):
        email = self.cleaned_data['email']
        if (User.objects.filter(email=email).count() != 0):
            raise forms.ValidationError(_('Account already exists, please use a different email address.'))
        else:
            return email
    
    def clean_firstName(self):
        firstName = self.cleaned_data['firstName']
        if (len(firstName.strip()) == 0):
            raise forms.ValidationError(_('Please provide your first name.'))
        else:
            return firstName
        
    def clean_lastName(self):
        lastName = self.cleaned_data['lastName']
        if (len(lastName.strip()) == 0):
            raise forms.ValidationError(_('Please provide your last name.'))
        else:
            return lastName
        
    def clean_password(self):
        password = self.cleaned_data['password']
        if (len(password.strip()) == 0):
            raise forms.ValidationError(_('Please provide a password.'))
        else:
            return password
    
    def clean_passwordAgain(self):
        passwordAgain = self.cleaned_data['passwordAgain']
        if (len(passwordAgain.strip()) == 0):
            raise forms.ValidationError(_('Please type the password again.'))
        if (passwordAgain != self.cleaned_data['password']):
            raise forms.ValidationError(_('The passwords do not match.'))
        else:
            return passwordAgain
    
    #def clean_instance(self):
    #    if (self.cleaned_data['instance'] == ""):
    #        instance = None
    #    else:
    #        instance = Instance.objects.get(id = self.cleaned_data['instance'])
    #    return instance
    
class ActivationForm(forms.Form):
    accepted_term = forms.BooleanField(required=True, label=_("I have have read the <a href=\"/label/\">Terms of Use.</a>"))
    accepted_research = forms.BooleanField(required=True, label=_("Accepted research"))

class ForgotForm(forms.Form):
    email = forms.EmailField()

    # Ensure that the email address is in the system otherwise no need to send a password reset.
    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            user = User.objects.get(email=email)
            return email
        except User.DoesNotExist:
            raise forms.ValidationError(_('Email not found in our system'))

class ChangePasswordForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm = forms.CharField(widget=forms.PasswordInput)

    # Ensure that both passwords match.
    def clean_confirm(self):
        password = self.cleaned_data['password']
        confirm = self.cleaned_data['confirm']
        if not password == confirm:
            raise forms.ValidationError(_('Passwords must match'))

        return confirm

class UserProfileForm(forms.ModelForm):
    # Required fields
    first_name = forms.CharField(max_length=30, required=True,)
    last_name = forms.CharField(max_length=30, required=True,)
    email = forms.CharField(max_length=255, required=True, help_text="(Private)",)

    # Non-required fields
    gen = []
    gen.append((0, '------'))
    for x in UserProfileGender.objects.all().order_by("pos"):
        gen.append((x.id, x.gender))
    gender = forms.ChoiceField(required=False, choices=gen)
    
    ra = []
    ra.append((0, '------'))
    for x in UserProfileRace.objects.all().order_by("pos"):
        ra.append((x.id, x.race))
    race = forms.ChoiceField(required=False, choices=ra)
    
    st = []
    st.append((0, '------'))
    for x in UserProfileStake.objects.all().order_by("pos"):
        st.append((x.id, x.stake))
    stake = forms.ChoiceField(required=False, choices=st)
    
    birth_year = forms.CharField(max_length=30, label='Age', help_text='Private',required=False)
    phone_number = forms.CharField(max_length=30, help_text='Private',required=False)
    myInstance = forms.ModelChoiceField(queryset=Instance.objects.all(), required=False, label=_('Community'))
    affiliations = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2, "cols": 40}), 
                                   help_text = "Please place a comma between each affiliation (ie: YMCA, James Memorial Highschool, Gardening Club).")
    edu = []
    edu.append((0, '------'))
    for x in UserProfileEducation.objects.all().order_by("pos"):
        edu.append((x.id, x.eduLevel))
    education = forms.ChoiceField(required=False, choices=edu)
    
    inc = []
    inc.append((0, '------'))
    for x in UserProfileIncomes.objects.all().order_by("pos"):
        inc.append((x.id, x.income))
    income = forms.ChoiceField(required=False, choices=inc)
    
    liv = []
    liv.append((0, '------'))
    for x in UserProfileLiving.objects.all().order_by("pos"):
        liv.append((x.id, x.livingSituation))
    living = forms.ChoiceField(required=False, choices=liv)
    
    avatar = forms.ImageField(required=False)
    
    def clean_instance(self):
        try:
            return Instance.objects.get(id=self.cleaned_data['instance'])
        except:
            return None
    
    def clean_gender(self):
        try:
            return UserProfileGender.objects.get(pos=self.cleaned_data['gender'])
        except:
            return None
    
    def clean_race(self):
        try:
            return UserProfileRace.objects.get(pos=self.cleaned_data['race'])
        except:
            return None
    
    def clean_stake(self):
        try:
            return UserProfileStake.objects.get(pos=self.cleaned_data['stake'])
        except:
            return None
    
    def clean_education(self):
        try:
            return UserProfileEducation.objects.get(pos=self.cleaned_data['education'])
        except:
            return None
    
    def clean_income(self):
        try:
            return UserProfileIncomes.objects.get(pos=self.cleaned_data['income'])
        except:
            return None
    
    def clean_living(self):
        try:
            return UserProfileLiving.objects.get(pos=self.cleaned_data['living'])
        except:
            return None
    
    class Meta:
        model = UserProfile
        #Adding to Meta.fields will display default settings in the browser and link it to the correct model object. 
        fields = ( 'email', 'first_name', 'last_name', 'stake', 'birth_year', 'gender', 'race', 'phone_number', 'myInstance', 'affiliations',
                   'education', 'income', 'living' )
