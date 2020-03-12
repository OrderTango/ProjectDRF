import string
from django.db import connection
from django import forms
from django.core.exceptions import ValidationError
from . import views
from OrderTangoApp.models import *
from OrderTangoApp import utility
from OrderTangoSubDomainApp.models import UserAddress
from django.conf import settings

class MainForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(MainForm, self).__init__(*args, **kwargs)

class UserForm(MainForm):
    wsid = forms.CharField(widget=forms.HiddenInput())
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Confirm Password')
    countryCode = forms.ModelChoiceField(widget=forms.Select(),queryset=CountryCode.objects.all().order_by('countryCodeName'));
    plan = forms.ModelChoiceField(widget=forms.Select(),
                                     queryset=Plan.objects.all());

    class Meta:

        model = User
        fields = (
            'plan', 'firstName', 'lastName', 'countryCode', 'contactNo', 'email', 'password', 'confirm_password',
            'sec_question', 'sec_answer')
        labels = {
            'plan': ('Subscription Plan'),'firstName': ('First Name'), 'lastName': ('Last Name'), 'countryCode': ('Country Code')
            , 'contactNo': ('Contact No.'), 'email': ('Email'),
            'sec_question': ('Question'), 'sec_answer': ('Answer')
        }

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.fields['plan'].empty_label = None
        self.fields['contactNo'].widget.attrs['class'] = "number"
        self.fields['sec_question'].empty_label = "Select"
        self.fields['countryCode'].empty_label = "Select"
        self.fields['wsid'].required = False

    def clean(self):  # Password and Confirm Password Validation
        email = self.cleaned_data['email'].lower()
        contactNumber = self.cleaned_data['contactNo'].lower()
        userEmail = views.fuzzyEmail(email, "user")
        userContactNumber = views.fuzzyContactNumber(contactNumber)

        if userContactNumber:
            self.add_error('contactNo', "User with this Contact Number already exists.Contact admin")

        elif userEmail:
            self.add_error('email', "User with this Email already exists.Contact admin")
        return self.cleaned_data

    def clean_confirm_password(self):  # Password and Confirm Password Validation
        invalidChars = set(string.punctuation.replace("_", ""))
        passWord = self.cleaned_data['password']
        confirmPassword = self.cleaned_data['confirm_password']
        minLength = 8

        if passWord.isdigit() or not any(x.isupper() for x in passWord) or not any(
                x.islower() for x in passWord) or len(passWord) < minLength or not any(
            x.isdigit() for x in passWord) or not any(
            char in invalidChars for char in passWord):  # Numeric validation

            raise ValidationError(
                "Password should contain at least %d characters with a mix of uppercase,lowercase,special character,numeric " % minLength)

        else:
            if passWord != confirmPassword:  # confirm p    assword validation - password  match validation
                raise ValidationError("Password does not match")
        return self.cleaned_data




class CompanyForm(MainForm):
    country = forms.ModelChoiceField(widget=forms.Select(attrs={'onchange': 'load_states(this.value)'}),
                                     queryset=Country.objects.all().order_by('countryName'))
    companyWsid = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Company
        fields = (
            'companyName',
            'country',
            'address_Line1', 'unit1', 'unit2', 'address_Line2', 'state', 'postalCode')
        labels = {
            'companyName': ('Company Name'),
            'country': ('Country'), 'address_Line1': ('Address 1')
            , 'address_Line2': ('Address 2'), 'state': ('State'), 'postalCode': ('Postal Code'),

        }

    def __init__(self, *args, **kwargs):
        super(CompanyForm, self).__init__(*args, **kwargs)
        #self.fields['postalCode'].widget.attrs['class'] = "number"
        self.fields['country'].queryset = Country.objects.all().order_by('countryName')
        self.fields['state'].queryset = State.objects.filter(country_id=self.data.get('country')).order_by('stateName')
        self.fields['country'].empty_label = "Select"
        self.fields['state'].empty_label = "Select"
        self.fields['companyWsid'].required = False

    def clean(self):
        companyName = self.cleaned_data['companyName'].lower()
        addressLine1 = self.cleaned_data['address_Line1'].lower()
        addressLine2 = self.cleaned_data['address_Line2'].lower()
        country = self.cleaned_data['country']
        state = self.cleaned_data['state']
        pincode = self.cleaned_data['postalCode'].lower()
        unit1 = self.cleaned_data['unit1'].lower()
        unit2 = self.cleaned_data['unit2'].lower()
        userCompanyOrAddress = views.fuzzyCompanyName(companyName, country, state, pincode, unit1, unit2, addressLine1,
                                                      addressLine2, "user")
        try:
            token = self.cleaned_data['companyWsid']
            userwithTokenCompany = User.objects.get(userCompanyId__companyName__iexact=companyName, token=token)
        except:
            userwithTokenCompany = None
        if userCompanyOrAddress[0] and userwithTokenCompany is None:
            self.add_error('companyName', "User with this Company Name already exists.Contact admin")
        elif userCompanyOrAddress[1] and userwithTokenCompany is None:
            self.add_error('postalCode', "User with this Address already exists.Contact admin")

        return self.cleaned_data


class newpasswordForm(MainForm):
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='New Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Confirm Password')

    class Meta:
        model = User
        fields = ('password',)
        labels = {
            'password': ('New Password'),
        }

    def __init__(self, *args, **kwargs):
        super(newpasswordForm, self).__init__(*args, **kwargs)

    def clean_confirm_password(self):  # Password and Confirm Password Validation
        invalidChars = set(string.punctuation.replace("_", ""))
        passWord = self.cleaned_data['password']
        confirmPassword = self.cleaned_data['confirm_password']
        minLength = 8

        if passWord.isdigit() or not any(x.isupper() for x in passWord) or not any(
                x.islower() for x in passWord) or len(passWord) < minLength or not any(
            x.isdigit() for x in passWord) or not any(
            char in invalidChars for char in passWord):  # Numeric validation

            raise ValidationError(
                "Password should contain at least %d characters with a mix of uppercase,lowercase,special character,numeric " % minLength)

        else:
            if passWord != confirmPassword:  # confirm p    assword validation - password  match validation
                raise ValidationError("Password does not match")
        return self.cleaned_data


class securityQuestionForm(forms.Form):
    sec_answer = forms.CharField(label='sec_answer', max_length=15)


class LoginForm(forms.Form):
    email = forms.CharField(max_length=100, label='Username')
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Password')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(LoginForm, self).__init__(*args, **kwargs)


class ForgetpasswordForm(MainForm):
    class Meta:
        model = User
        fields = ('email',)
        labels = {'email': ('Email'), }

    def clean(self):
        try:
            uName = self.cleaned_data['email'].lower()
        except:
            uName = None
        if uName is not None:
            user = utility.getUserByEmail(uName)
            if user is None:
                self.add_error('email', 'User not found')
            elif user is not None and user.userCompanyId.verificationStatus != constants.Active:
                self.add_error('email', 'Please activate your account')
        return self.cleaned_data




class UserShippingAddressForm(MainForm):
    usradd_country = forms.ModelChoiceField(label='Country',
                                            widget=forms.Select(attrs={'onchange': 'load_shipping_states(this.value)'}),
                                            queryset=Country.objects.all().order_by('countryName'), empty_label="Select");
    usradd_state = forms.ModelChoiceField(label='State', empty_label="Select",
                                          queryset=State.objects.filter(country_id=1))
    emailSent = forms.BooleanField(label='Send Invitation', widget=forms.CheckboxInput, initial=False)
    sameAddress = forms.BooleanField(label='Same as Company Address', widget=forms.CheckboxInput, initial=False)

    class Meta:
        model = UserAddress
        fields = (
            'usradd_country', 'usradd_address_Line1', 'usradd_address_Line2', 'usradd_unit1', 'usradd_unit2',
            'usradd_state',
            'usradd_postalCode', 'usradd_addressType', 'emailSent', 'sameAddress')
        labels = {
            'usradd_address_Line1': ('Address 1')
            , 'usradd_address_Line2': ('Address 2'), 'usradd_postalCode': ('Postal Code'), 'usradd_addressType': ('Address Type')
        }

        def __init__(self, *args, **kwargs):
            super(UserShippingAddressForm, self).__init__(*args, **kwargs)
            self.fields['usradd_postalCode'].widget.attrs['class'] = "number"
            self.fields['usradd_state'].required = False
            self.fields['emailSent'].required = False


class UserProfileForm(MainForm):
    token = forms.CharField(widget=forms.HiddenInput())
    countryCode = forms.ModelChoiceField(widget=forms.Select(),label='Country Code', queryset=CountryCode.objects.all().order_by('countryCodeName'));

    class Meta:
        model = User
        fields = ('token',
                  'firstName', 'lastName', 'sec_question', 'sec_answer','email','contactNo')
        labels = {
            'firstName': ('First Name'), 'lastName': ('Last Name'), 'contactNo': ('Contact No'),
            'sec_question': ('Question'), 'sec_answer': ('Answer')
        }

    def __init__(self, *args, **kwargs):
        super(UserProfileForm, self).__init__(*args, **kwargs)
        self.fields['firstName'].widget.attrs['id'] = "firstName"
        self.fields['lastName'].widget.attrs['id'] = "lastName"
        self.fields['sec_answer'].widget.attrs['id'] = "sec_answer"
        self.fields['sec_question'].widget.attrs['id'] = "question"
        self.fields['email'].widget.attrs['id'] = "email"
        self.fields['contactNo'].widget.attrs['id'] = "contactNo"
        self.fields['countryCode'].widget.attrs['id'] = "countryCode"
        self.fields['sec_question'].widget.attrs['name'] = "question"
        self.fields['sec_question'].empty_label = "Select"
        self.fields['token'].required = False
        self.fields['countryCode'].empty_label = "Select"

class CompanyProfileForm(MainForm):
    country = forms.ModelChoiceField(widget=forms.Select(attrs={'onchange': 'load_states1(this.value)'}),
                                     queryset=Country.objects.all().order_by('countryName'))

    class Meta:
        model = Company
        fields = (
            'country',
            'address_Line1', 'unit1', 'unit2', 'address_Line2', 'state', 'postalCode','companyName')
        labels = {

            'country': ('Country'), 'address_Line1': ('Address 1')
            , 'address_Line2': ('Address 2'), 'state': ('State'), 'postalCode': ('Postal Code'),
            'companyName': ('Company Name'),

        }

    def __init__(self, *args, **kwargs):
        super(CompanyProfileForm, self).__init__(*args, **kwargs)
        self.fields['country'].widget.attrs['id'] = "country"
        self.fields['state'].widget.attrs['id'] = "state"
        self.fields['address_Line1'].widget.attrs['id'] = "address_Line1"
        self.fields['address_Line2'].widget.attrs['id'] = "address_Line2"
        self.fields['postalCode'].widget.attrs['id'] = "postalCode"
        self.fields['unit1'].widget.attrs['id'] = "unit1"
        self.fields['unit2'].widget.attrs['id'] = "unit2"
        self.fields['companyName'].widget.attrs['id'] = "companyName"
        self.fields['postalCode'].widget.attrs['class'] = "number"
        self.fields['country'].queryset = Country.objects.all().order_by('countryName')
        self.fields['state'].queryset = State.objects.filter(country_id=self.data.get('country')).order_by('stateName')
        self.fields['country'].empty_label = "Select"
        self.fields['state'].empty_label = "Select"
        self.fields['state'].required = False

class UserShippingAddressEditForm(MainForm):
   usradd_addressId = forms.CharField(widget=forms.HiddenInput())
   usradd_country = forms.ModelChoiceField(label='Country',
                                           widget=forms.Select(attrs={'onchange': 'load_shipping_states(this.value)'}),
                                           queryset=Country.objects.all().order_by('countryName'), empty_label="Select");
   usradd_state = forms.ModelChoiceField(label='State', empty_label="Select",
                                         queryset=State.objects.filter(country_id=1))
   emailSent = forms.BooleanField(label='Send Invitation', widget=forms.CheckboxInput, initial=False)
   sameAddress = forms.BooleanField(label='Same as Company Address', widget=forms.CheckboxInput, initial=False)

   class Meta:
       model = UserAddress
       fields = (
           'usradd_country', 'usradd_address_Line1', 'usradd_address_Line2', 'usradd_unit1', 'usradd_unit2',
           'usradd_state',
           'usradd_postalCode', 'usradd_addressType', 'emailSent', 'sameAddress')
       labels = {
           'usradd_addressId': ('Address Id'), 'usradd_addressType': ('Address Type'), 'usradd_address_Line1': ('Address 1')
           , 'usradd_address_Line2': ('Address 2'), 'usradd_postalCode': ('Postal Code')
       }

   def __init__(self, *args, **kwargs):
       super(UserShippingAddressEditForm, self).__init__(*args, **kwargs)
       self.fields['usradd_addressType'].widget.attrs['id'] = "uusradd_addressType"
       self.fields['usradd_addressId'].widget.attrs['id'] = "uusradd_addressId"
       self.fields['usradd_country'].widget.attrs['id'] = "uusradd_country"
       self.fields['usradd_address_Line1'].widget.attrs['id'] = "uusradd_address_Line1"
       self.fields['usradd_address_Line2'].widget.attrs['id'] = "uusradd_address_Line2"
       self.fields['usradd_unit1'].widget.attrs['id'] = "uusradd_unit1"
       self.fields['usradd_unit2'].widget.attrs['id'] = "uusradd_unit2"
       self.fields['usradd_state'].widget.attrs['id'] = "uusradd_state"
       self.fields['usradd_postalCode'].widget.attrs['id'] = "uusradd_postalCode"
       #self.fields['addressId'].required = False


class AcceptTraderForm(MainForm):
    countryCode = forms.CharField()
    relId = forms.CharField(widget=forms.HiddenInput())
    type = forms.CharField(widget=forms.HiddenInput())

    class Meta:

        model = User
        fields = (
            'relId','type','firstName', 'lastName', 'countryCode', 'contactNo', 'email',
           )
        labels = {
           'firstName': ('First Name'), 'lastName': ('Last Name'), 'countryCode': ('Country Code')
            , 'contactNo': ('Contact No.'), 'email': ('Email'),

        }

    def __init__(self, *args, **kwargs):
        super(AcceptTraderForm, self).__init__(*args, **kwargs)
        self.fields['firstName'].widget.attrs['readonly'] = True
        self.fields['lastName'].widget.attrs['readonly'] = True
        self.fields['countryCode'].widget.attrs['readonly'] = True
        self.fields['contactNo'].widget.attrs['readonly'] = True
        self.fields['email'].widget.attrs['readonly'] = True

class AcceptTraderCompanyForm(MainForm):
    country = forms.CharField()
    state = forms.CharField()

    class Meta:
        model = Company
        fields = (
            'companyName',
            'country',
            'address_Line1', 'unit1', 'unit2', 'address_Line2', 'state', 'postalCode')
        labels = {
            'companyName': ('Company Name'),
            'country': ('Country'), 'address_Line1': ('Address 1')
            , 'address_Line2': ('Address 2'), 'state': ('State'), 'postalCode': ('Postal Code'),

        }

    def __init__(self, *args, **kwargs):
        super(AcceptTraderCompanyForm, self).__init__(*args, **kwargs)
        self.fields['companyName'].widget.attrs['readonly'] = True
        self.fields['country'].widget.attrs['readonly'] = True
        self.fields['address_Line1'].widget.attrs['readonly'] = True
        self.fields['address_Line2'].widget.attrs['readonly'] = True
        self.fields['unit1'].widget.attrs['readonly'] = True
        self.fields['unit2'].widget.attrs['readonly'] = True
        self.fields['postalCode'].widget.attrs['readonly'] = True
        self.fields['state'].widget.attrs['readonly'] = True


