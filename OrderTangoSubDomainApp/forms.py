import string
from django.core.exceptions import ValidationError

from django import forms
from OrderTangoApp.models import User
from OrderTangoSubDomainApp.models import *


class MainForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(MainForm, self).__init__(*args, **kwargs)





class ResetpasswordForm(MainForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'autofocus': 'autofocus'}), max_length=15,
                                   label='Old Password')
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='New Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Confirm Password')

    class Meta:
        model = User
        fields = ('password',)
        labels = {
            'old_password': ('Old Password'), 'password': ('New Password'), 'confirm_password': ('Confirm Password')
        }

    def __init__(self, *args, **kwargs):
        super(ResetpasswordForm, self).__init__(*args, **kwargs)

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
                raise ValidationError("New Password and Confirm Password does not match")
        return self.cleaned_data




class SubUserFormDetails(MainForm):
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Confirm Password')
    role = forms.ModelChoiceField(label='Role', empty_label="Select", queryset=RolesAndAccess.objects.filter(status=constants.Active).all())
    area = forms.ModelChoiceField(label='Area',
                                     widget=forms.Select(attrs={'onchange': 'load_sites(this.value)'}),
                                     queryset=Area.objects.all(), empty_label="Select")
    site = forms.ModelChoiceField(label='Site', empty_label="Select", queryset=Sites.objects.filter(siteArea_id=1))
    countryCode = forms.ModelChoiceField(label='Country Code', widget=forms.Select(),
                                            queryset=CountryCode.objects.all().order_by('countryCodeName'))
    class Meta:
        model = Subuser
        fields = (
            'firstName', 'lastName', 'userName', 'password', 'designation', 'role', 'email',
            'DOJ', 'contactNo', 'DOD', 'profilepic')

        labels = {
            'firstName': ('First Name'), 'lastName': ('Last Name'), 'userName': ('User Name')
            , 'password': ('Password'), 'designation': ('Designation'),
            'DOJ': ('DOJ'), 'profilepic': ('Profile Image'), 'email': ('Email')
        }

    def __init__(self, *args, **kwargs):
        super(SubUserFormDetails, self).__init__(*args, **kwargs)
        self.fields['email'].required = False
        self.fields['countryCode'].empty_label = "Select"


class EditSubUserFormDetails(MainForm):
    password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Password')
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=15, label='Confirm Password')
    role = forms.ModelChoiceField(label='Role', empty_label="Select", queryset=RolesAndAccess.objects.filter(status=constants.Active).all())
    area = forms.ModelChoiceField(label='Area',
                                  widget=forms.Select(attrs={'onchange': 'load_sitesedit(this.value)'}),
                                  queryset=Area.objects.all(), empty_label="Select")
    site = forms.ChoiceField(label='Site')
    countryCode = forms.ModelChoiceField(label='Country Code', widget=forms.Select(),
                                         queryset=CountryCode.objects.all().order_by('countryCodeName'))

    class Meta:
        model = Subuser
        fields = (
            'firstName', 'lastName', 'userName', 'password', 'designation', 'role', 'email',
            'DOJ', 'contactNo', 'DOD', 'profilepic')

        labels = {
            'firstName': ('First Name'), 'lastName': ('Last Name'), 'userName': ('User Name')
            , 'password': ('Password'), 'designation': ('Designation'), 'email': ('Email'),
            'DOJ': ('DOJ'), 'profilepic': ('Profile Image')
        }

    def __init__(self, *args, **kwargs):
        super(EditSubUserFormDetails, self).__init__(*args, **kwargs)
        self.fields['area'].widget.attrs['id'] = "uarea"
        self.fields['site'].widget.attrs['id'] = "usite"
        self.fields['firstName'].widget.attrs['id'] = "ufirstName"
        self.fields['lastName'].widget.attrs['id'] = "ulastName"
        self.fields['userName'].widget.attrs['id'] = "uuserName"
        self.fields['password'].widget.attrs['id'] = "upassword"
        self.fields['email'].widget.attrs['id'] = "uemail"
        self.fields['confirm_password'].widget.attrs['id'] = "uconfirm_password"
        self.fields['designation'].widget.attrs['id'] = "udesignation"
        self.fields['contactNo'].widget.attrs['id'] = "ucontactNo"
        self.fields['role'].widget.attrs['id'] = "urole"
        self.fields['DOJ'].widget.attrs['id'] = "uDOJ"
        self.fields['DOD'].widget.attrs['id'] = "uDOD"
        self.fields['profilepic'].widget.attrs['id'] = "uprofilepic"
        self.fields['countryCode'].widget.attrs['id'] = "ucountryCode"
        self.fields['email'].required = False


class AreaAddForm(MainForm):
    areaDesc = forms.CharField(widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}), label='Area Description')
    areaSla = forms.ModelChoiceField(label='Area SLA',
                                     queryset=serviceLevelAgreement.objects.filter(status=constants.Active).all(),
                                     empty_label="Select")

    class Meta:
        model = Area
        fields = (
            'areaName', 'areaDesc')
        labels = {
            'areaName': ('Area Name')
        }

    def __init__(self, *args, **kwargs):
        super(AreaAddForm, self).__init__(*args, **kwargs)


class AreaEditForm(MainForm):
    areaId = forms.CharField(widget=forms.HiddenInput())
    areaDesc = forms.CharField(widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}), label='Area Description')
    areaSla = forms.ModelChoiceField(label='Area SLA',
                                     queryset=serviceLevelAgreement.objects.filter(status=constants.Active).all(),
                                     empty_label="Select")

    class Meta:
        model = Area
        fields = (
            'areaId', 'areaName', 'areaDesc')
        labels = {
            'areaName': ('Area Name')
        }

    def __init__(self, *args, **kwargs):
        super(AreaEditForm, self).__init__(*args, **kwargs)
        self.fields['areaId'].widget.attrs['id'] = "eAreaId"
        self.fields['areaName'].widget.attrs['id'] = "eAreaName"
        self.fields['areaDesc'].widget.attrs['id'] = "eAreaDesc"
        self.fields['areaSla'].widget.attrs['id'] = "eAreaSla"


class AddSiteForm(MainForm):
    siteArea = forms.ModelChoiceField(label='Site Area', queryset=Area.objects.filter(status=constants.Active).all(),
                                      empty_label="Select")
    siteType = forms.ModelChoiceField(label='Site Type',
                                      queryset=TypeOfSites.objects.all(),
                                      empty_label="Select")
    siteName = forms.CharField(label='Site Name',max_length=50)
    siteDesc = forms.CharField(label='Site Description', widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}))
    country = forms.ModelChoiceField(label='Country',
                                     widget=forms.Select(attrs={'onchange': 'load_states(this.value)'}),
                                     queryset=Country.objects.all(), empty_label="Select")
    state = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    address_Line1 = forms.CharField(label='Address 1',max_length=100)
    address_Line2 = forms.CharField(label='Address 2',max_length=100)
    unit1 = forms.CharField(label='Unit1',max_length=2)
    unit2 = forms.CharField(label='Unit2',max_length=2)
    postalCode = forms.CharField(label='Postal Code',max_length=7)

    class Meta:
        model = Sites
        exclude = {}

    def __init__(self, *args, **kwargs):
        super(AddSiteForm, self).__init__(*args, **kwargs)


class EditSiteForm(MainForm):
    siteArea = forms.ModelChoiceField(label='Site Area', queryset=Area.objects.filter(status=constants.Active).all(),
                                      empty_label="Select")
    siteType = forms.ModelChoiceField(label='Site Type',
                                      queryset=TypeOfSites.objects.all(),
                                      empty_label="Select")
    siteName = forms.CharField(label='Site Name',max_length=50)
    siteDesc = forms.CharField(label='Site Description', widget=forms.Textarea(attrs={'cols': 30, 'rows': 5}))
    country = forms.ModelChoiceField(label='Country',
                                     widget=forms.Select(attrs={'onchange': 'load_edit_states(this.value)'}),
                                     queryset=Country.objects.all(), empty_label="Select")
    state = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    address_Line1 = forms.CharField(label='Address 1',max_length=100)
    address_Line2 = forms.CharField(label='Address 2',max_length=100)
    unit1 = forms.CharField(label='Unit1',max_length=2)
    unit2 = forms.CharField(label='Unit2',max_length=2)
    postalCode = forms.CharField(label='Postal Code',max_length=7)

    class Meta:
        model = Sites
        exclude = {}

    def __init__(self, *args, **kwargs):
        super(EditSiteForm, self).__init__(*args, **kwargs)
        self.fields['siteArea'].widget.attrs['id'] = "siteArea"
        self.fields['siteType'].widget.attrs['id'] = "siteType"
        self.fields['siteName'].widget.attrs['id'] = "siteName"
        self.fields['siteDesc'].widget.attrs['id'] = "siteDesc"
        self.fields['country'].widget.attrs['id'] = "editcountry"
        self.fields['state'].widget.attrs['id'] = "editstate"
        self.fields['address_Line1'].widget.attrs['id'] = "editaddress_Line1"
        self.fields['address_Line2'].widget.attrs['id'] = "editaddress_Line2"
        self.fields['unit1'].widget.attrs['id'] = "editunit1"
        self.fields['unit2'].widget.attrs['id'] = "editunit2"
        self.fields['postalCode'].widget.attrs['id'] = "editpostalCode"


class CustomerManualAddingForm(MainForm):
    cusCountryCode = forms. ModelChoiceField(label='Country Code',widget=forms.Select(),queryset=CountryCode.objects.all().order_by('countryCodeName'));
    cusCountry = forms.ModelChoiceField(label='Country',
                                     widget=forms.Select(attrs={'onchange': 'load_states(this.value)'}),
                                     queryset=Country.objects.all(), empty_label="Select")
    cusState = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    cusSameEmail = forms.BooleanField(label='Same Email', widget=forms.CheckboxInput, initial=False)

    class Meta:
        model = Customer
        fields = (
            'cusCompanyName', 'cusEmail', 'cusContactNo', 'cusAddress_Line1','cusCommunicationEmail',
            'cusAddress_Line2','cusUnit1','cusUnit2','cusPostalCode','contactPerson','cusAlterNateEmail',
        )

        labels = {
            'cusCompanyName': ('Company Name'), 'cusEmail': ('Email'), 'cusCommunicationEmail': ('Communication Email'),
             'cusContactNo': ('Contact No.'), 'cusAddress_Line1': ('Address 1'),'cusAlterNateEmail':('Alternate Email'),
            'cusAddress_Line2': ('Address 2'),'cusPostalCode':('Postal Code'),'contactPerson':('Contact Person')
        }

    def __init__(self, *args, **kwargs):
        super(CustomerManualAddingForm, self).__init__(*args, **kwargs)
        self.fields['cusContactNo'].widget.attrs['class'] = "number"
        self.fields['cusCountryCode'].empty_label = "Select"

class CustomerShippingAddressForm(MainForm):
    cusShipCountry = forms.ModelChoiceField(label='Country',
                                        widget=forms.Select(attrs={'onchange': 'load_shipping_states(this.value)'}),
                                        queryset=Country.objects.all(), empty_label="Select")
    cusShipState = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    emailSent = forms.BooleanField(label='Send Invitation', widget=forms.CheckboxInput, initial=False)
    sameAddress = forms.BooleanField(label='Same as Company Address', widget=forms.CheckboxInput, initial=False)

    class Meta:
        model = CustomerShippingAddress
        fields = (
            'cusShipAddress_Line1', 'cusShipAddress_Line2', 'cusShipUnit1', 'cusShipUnit2','cusShipPostalCode',
        )

        labels = {'cusShipAddress_Line1': ('Address 1'),
            'cusShipAddress_Line2': ('Address 2'),'cusShipPostalCode':('Postal Code')
        }

    def __init__(self, *args, **kwargs):
        super(CustomerShippingAddressForm, self).__init__(*args, **kwargs)



class SupplierManualAddingForm(MainForm):
    supCountryCode = forms. ModelChoiceField(label='Country Code',widget=forms.Select(),queryset=CountryCode.objects.all().order_by('countryCodeName'));
    supCountry = forms.ModelChoiceField(label='Country',
                                     widget=forms.Select(attrs={'onchange': 'load_supplier_states(this.value)'}),
                                     queryset=Country.objects.all(), empty_label="Select")
    supState = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    supContactPerson = forms.CharField(max_length=30,label='Contact Person')
    supSameEmail = forms.BooleanField(label='Same Email', widget=forms.CheckboxInput, initial=False)
    class Meta:
        model = Supplier
        fields = (
            'supCompanyName', 'supEmail', 'supContactNo', 'supAddress_Line1','supCommunicationEmail',
            'supAddress_Line2','supUnit1','supUnit2','supPostalCode','supAlterNateEmail'
        )

        labels = {
            'supCompanyName': ('Company Name'), 'supEmail': ('Email'), 'supCommunicationEmail': ('Communication Email'),
            'supContactNo': ('Contact No.'), 'supAddress_Line1': ('Address 1'),
            'supAddress_Line2': ('Address 2'),'supPostalCode':('Postal Code'),'supAlterNateEmail':('Alternate Email')
        }

    def __init__(self, *args, **kwargs):
        super(SupplierManualAddingForm, self).__init__(*args, **kwargs)
        self.fields['supContactNo'].widget.attrs['class'] = "number"
        self.fields['supCountryCode'].empty_label = "Select"


class SupplierShippingAddressForm(MainForm):
    supShipCountry = forms.ModelChoiceField(label='Country',
                                        widget=forms.Select(attrs={'onchange': 'load_supShipping_states(this.value)'}),
                                        queryset=Country.objects.all(), empty_label="Select")
    supShipState = forms.ModelChoiceField(label='State', empty_label="Select", queryset=State.objects.filter(country_id=1))
    supEmailSent = forms.BooleanField(label='Send Invitation', widget=forms.CheckboxInput, initial=False)
    supSameAddress = forms.BooleanField(label='Same as Company Address', widget=forms.CheckboxInput, initial=False)

    class Meta:
        model = SupplierShippingAddress
        fields = (
            'supShipAddress_Line1', 'supShipAddress_Line2', 'supShipUnit1', 'supShipUnit2','supShipPostalCode',
        )

        labels = {'supShipAddress_Line1': ('Address 1'),
            'supShipAddress_Line2': ('Address 2'),'supShipPostalCode':('Postal Code')
        }

    def __init__(self, *args, **kwargs):
        super(SupplierShippingAddressForm, self).__init__(*args, **kwargs)


class ItemMasterManualForm(MainForm):
    articleType = forms.ModelChoiceField(label='Article Type',empty_label='Select',queryset=typeOfArticle.objects.all())
    itemCategory = forms.ModelChoiceField(label='Product Category',empty_label='Select',queryset=productCategory.objects.all())
    itemMerchantCategory = forms.ModelChoiceField(label='Merchandise Category',empty_label='Select',queryset=merchantCategory.objects.all())
    itemMerchantCategoryOne = forms.ModelChoiceField(label='Merchandise Sub-Category L1',empty_label='Select',queryset=merchantSubCategoryOne.objects.all())
    itemMerchantCategoryTwo = forms.ModelChoiceField(label='Merchandise Sub-Category L2',empty_label='Select',queryset=merchantSubCategoryTwo.objects.all())
    itemStorageCondition = forms.ModelChoiceField(label='Storage Conditions',empty_label='Select',queryset=storageConditions.objects.all())
    baseUom = forms.ModelChoiceField(label='Base Unit of Measure',empty_label='Select',queryset=QuantityType.objects.all())
    selfManufacturing =  forms.BooleanField(label='Self-Manufactured Product?', widget=forms.CheckboxInput, initial=False)

    class Meta:
        model = ItemMaster
        exclude = {}

        fields = (
            'itemCode', 'itemName', 'alterItemCode', 'alterItemName', 'brandName','itemDesc','packingUnit', 'manufacturingLeadTime',
        )

        labels = {'itemName': ('Product Name'),
                  'itemCode': ('Product Code'), 'alterItemName': ('Alternate Product Name'),
                  'alterItemCode': ('Alternate Produce Code'), 'brandName': ('Brand name'),
                  'itemDesc': ('Product Description'), 'packingUnit': ('Packing Unit'),
                  'manufacturingLeadTime': ('Manufacturing Lead Time')
                  }

    def __init__(self, *args, **kwargs):
        super(ItemMasterManualForm, self).__init__(*args, **kwargs)
        self.fields['itemName'].widget.attrs['class'] = "required"
        self.fields['itemCode'].widget.attrs['class'] = "required"
        self.fields['brandName'].widget.attrs['class'] = "required"
        self.fields['itemDesc'].widget.attrs['class'] = "required"
        self.fields['articleType'].widget.attrs['class'] = "required"
        self.fields['itemStorageCondition'].widget.attrs['class'] = "required"
        self.fields['itemCategory'].widget.attrs['class'] = "required"
        self.fields['baseUom'].widget.attrs['class'] = "required"
        choices = [(constants.Both, constants.Both), (constants.Purchase, constants.Purchase),(constants.Sale, constants.Sale)]
        self.fields['productDetail'] = forms.ChoiceField(
            label=('Product For'),
            choices=choices,

        )

class productAttributeForm(MainForm):
    class Meta:
        model = productAttribute
        exclude = {}

        fields = (
            'attributeColor', 'attributeSize', 'attributeDesign', 'attributeStyle', 'attributeOther',
        )

        labels = {'attributeColor': ('Color'),
                  'attributeSize': ('Size'), 'attributeDesign': ('Design'),
                  'attributeStyle': ('Style/ Pattern'), 'attributeOther': ('Other Attribute'),}

    def __init__(self, *args, **kwargs):
        super(productAttributeForm, self).__init__(*args, **kwargs)

class purchasingItemsForm(MainForm):
    purchasingUom = forms.ModelChoiceField(label='Order Unit', queryset=QuantityType.objects.all())
    purchasingTax = forms.ModelChoiceField(label='Tax Code', queryset=taxCode.objects.all())
    purchasingCurrency = forms.ModelChoiceField(label='Currency Key', queryset=CurrencyType.objects.all())
    purchasingUomForKg = forms.ModelChoiceField(label='Purchase Order Price Unit', queryset=CurrencyType.objects.all())

    class Meta:
        model = purchasingItems
        exclude = {}

        fields = (
            'purchasingPrice', 'purchasingPriceUnit', 'purchasingOrderText',
        )

        labels = {'purchasingPrice': ('Purchase Price'),
                  'purchasingPriceUnit': ('Price Unit'), 'purchasingOrderText': ('Purchase Order Text'),}

    def __init__(self, *args, **kwargs):
        super(purchasingItemsForm, self).__init__(*args, **kwargs)
        self.fields['purchasingUom'].empty_label = "Select"
        self.fields['purchasingTax'].empty_label = "Select"
        self.fields['purchasingCurrency'].empty_label = "Select"
        self.fields['purchasingUomForKg'].empty_label = "Select"
        self.fields['purchasingPrice'].widget.attrs['class'] = "required"
        self.fields['purchasingPriceUnit'].widget.attrs['class'] = "required"
        self.fields['purchasingOrderText'].widget.attrs['class'] = "required"
        self.fields['purchasingUom'].widget.attrs['class'] = "required"
        self.fields['purchasingTax'].widget.attrs['class'] = "required"
        self.fields['purchasingCurrency'].widget.attrs['class'] = "required"
        self.fields['purchasingUomForKg'].widget.attrs['class'] = "required"

class salesItemsForm(MainForm):
    salesUom = forms.ModelChoiceField(label='Sales Unit', queryset=QuantityType.objects.all())
    salesTax = forms.ModelChoiceField(label='Tax Code', queryset=taxCode.objects.all())
    salesCurrency = forms.ModelChoiceField(label='Currency Key', queryset=CurrencyType.objects.all())
    salesUomForKg = forms.ModelChoiceField(label='Selling Price Unit',
                                                queryset=CurrencyType.objects.all())
    class Meta:
        model = salesItems
        exclude = {}

        fields = (
            'salesCategoryGrp', 'salesOrderText', 'salesPrice','salesPriceUnit',
        )

        labels = {'salesCategoryGrp': ('Item Category Group '),
                  'salesOrderText': ('Sales Text'), 'salesPrice': ('Selling Price'),
                  'salesPriceUnit': ('Price Unit'), }

    def __init__(self, *args, **kwargs):
        super(salesItemsForm, self).__init__(*args, **kwargs)
        self.fields['salesUom'].empty_label = "Select"
        self.fields['salesTax'].empty_label = "Select"
        self.fields['salesCurrency'].empty_label = "Select"
        self.fields['salesUomForKg'].empty_label = "Select"
        self.fields['salesUom'].widget.attrs['class'] = "required"
        self.fields['salesTax'].widget.attrs['class'] = "required"
        self.fields['salesPrice'].widget.attrs['class'] = "required"
        self.fields['salesCurrency'].widget.attrs['class'] = "required"


class itemMeasurementForm(MainForm):
    measurementDimensionUnit = forms.ModelChoiceField(label='Dimension Unit', queryset=itemDimension.objects.all())
    measurementWeightUnit = forms.ModelChoiceField(label='Weight Unit', queryset=weightUnit.objects.all())
    class Meta:
        model = itemMeasurement
        exclude = {}

        fields = (
            'measurementDimension', 'measurementLength', 'measurementWidth', 'measurementHeight',
            'measurementWeight',
        )

        labels = {'measurementDimension': ('Dimension'),
                  'measurementLength': ('Length'), 'measurementWidth': ('Width'),
                  'measurementHeight': ('Height'), 'measurementWeight': ('Weight'),}

    def __init__(self, *args, **kwargs):
        super(itemMeasurementForm, self).__init__(*args, **kwargs)
        self.fields['measurementDimensionUnit'].empty_label = "Select"
        self.fields['measurementWeightUnit'].empty_label = "Select"

class itemStorageForm(MainForm):
    storageDept = forms.ModelChoiceField(label='Department', queryset=itemDepartment.objects.all())
    class Meta:
        model = itemStorage
        exclude = {}

        fields = (
            'storageShelfLife', 'storageCase', 'storageTier', 'storagePallet',
            'storageRack',
        )

        labels = {'storageShelfLife': ('Shelf Life (Days)'),
                  'storageCase': ('Case/Tier'), 'storageTier': ('Tier/Pallet'),
                  'storagePallet': ('Case/Pallet'),
                  'storageRack':('Rack')}

    def __init__(self, *args, **kwargs):
        super(itemStorageForm, self).__init__(*args, **kwargs)
        self.fields['storageDept'].empty_label = "Select"

class itemParameterForm(MainForm):
    class Meta:
        model = itemParameter
        exclude = {}

        fields = (
            'alterNateParamOne', 'alterNateParamTwo', 'alterNateParamThree', 'alterNateParamFour',
        )

        labels = {'alterNateParamOne': ('Alternate Parameter 1'),
                  'alterNateParamTwo': ('Alternate Parameter 2'), 'alterNateParamThree': ('Alternate Parameter 3'),
                  'alterNateParamFour':('Alternate Parameter 4')}

    def __init__(self, *args, **kwargs):
        super(itemParameterForm, self).__init__(*args, **kwargs)


class EditItemMasterManualForm(MainForm):
    articleType = forms.ModelChoiceField(label='Article Type', empty_label='Select',
                                         queryset=typeOfArticle.objects.all())
    itemCategory = forms.ModelChoiceField(label='Product Category', empty_label='Select',
                                          queryset=productCategory.objects.all())
    itemMerchantCategory = forms.ModelChoiceField(label='Merchandise Category', empty_label='Select',
                                                  queryset=merchantCategory.objects.all())
    itemMerchantCategoryOne = forms.ModelChoiceField(label='Merchandise Sub-Category L1', empty_label='Select',
                                                     queryset=merchantSubCategoryOne.objects.all())
    itemMerchantCategoryTwo = forms.ModelChoiceField(label='Merchandise Sub-Category L2', empty_label='Select',
                                                     queryset=merchantSubCategoryTwo.objects.all())
    itemStorageCondition = forms.ModelChoiceField(label='Storage Conditions', empty_label='Select',
                                                  queryset=storageConditions.objects.all())
    baseUom = forms.ModelChoiceField(label='Base Unit of Measure', empty_label='Select',
                                     queryset=QuantityType.objects.all())
    selfManufacturing = forms.BooleanField(label='Self-Manufactured Product?', widget=forms.CheckboxInput,
                                           initial=False)

    class Meta:
        model = ItemMaster
        exclude = {}

        fields = (
            'itemCode', 'itemName', 'alterItemCode', 'alterItemName', 'brandName', 'itemDesc', 'packingUnit',
            'manufacturingLeadTime',
        )

        labels = {'itemName': ('Product Name'),
                  'itemCode': ('Product Code'), 'alterItemName': ('Alternate Product Name'),
                  'alterItemCode': ('Alternate Produce Code'), 'brandName': ('Brand name'),
                  'itemDesc': ('Product Description'), 'packingUnit': ('Packing Unit'),
                  'manufacturingLeadTime': ('Manufacturing Lead Time')
                  }

    def __init__(self, *args, **kwargs):
        super(EditItemMasterManualForm, self).__init__(*args, **kwargs)
        choices = [(constants.Both, constants.Both), (constants.Purchase, constants.Purchase),
                   (constants.Sale, constants.Sale)]
        self.fields['productDetail'] = forms.ChoiceField(
            label=('Product For'),
            choices=choices,

        )
        self.fields['itemName'].widget.attrs['class'] = "required"
        self.fields['itemCode'].widget.attrs['class'] = "required"
        self.fields['brandName'].widget.attrs['class'] = "required"
        self.fields['itemDesc'].widget.attrs['class'] = "required"
        self.fields['articleType'].widget.attrs['class'] = "required"
        self.fields['itemStorageCondition'].widget.attrs['class'] = "required"
        self.fields['baseUom'].widget.attrs['class'] = "required"
        self.fields['itemName'].widget.attrs['id'] = "pitemName"
        self.fields['itemCode'].widget.attrs['id'] = "pitemCode"
        self.fields['alterItemCode'].widget.attrs['id'] = "palterItemCode"
        self.fields['alterItemName'].widget.attrs['id'] = "palterItemName"
        self.fields['brandName'].widget.attrs['id'] = "pbrandName"
        self.fields['itemDesc'].widget.attrs['id'] = "pitemDesc"
        self.fields['articleType'].widget.attrs['id'] = "particleType"
        self.fields['itemCategory'].widget.attrs['id'] = "pitemCategory"
        self.fields['itemMerchantCategory'].widget.attrs['id'] = "pitemMerchantCategory"
        self.fields['itemMerchantCategoryOne'].widget.attrs['id'] = "pitemMerchantCategoryOne"
        self.fields['itemMerchantCategoryTwo'].widget.attrs['id'] = "pitemMerchantCategoryTwo"
        self.fields['itemStorageCondition'].widget.attrs['id'] = "pitemStorageCondition"
        self.fields['baseUom'].widget.attrs['id'] = "pbaseUom"
        self.fields['packingUnit'].widget.attrs['id'] = "ppackingUnit"
        self.fields['selfManufacturing'].widget.attrs['id'] = "pselfManufacturing"
        self.fields['manufacturingLeadTime'].widget.attrs['id'] = "pmanufacturingLeadTime"
        self.fields['productDetail'].widget.attrs['id'] = "pproductDetail"


class EditproductAttributeForm(MainForm):
    class Meta:
        model = productAttribute
        exclude = {}

        fields = (
            'attributeColor', 'attributeSize', 'attributeDesign', 'attributeStyle', 'attributeOther',
        )

        labels = {'attributeColor': ('Color'),
                  'attributeSize': ('Size'), 'attributeDesign': ('Design'),
                  'attributeStyle': ('Style/ Pattern'), 'attributeOther': ('Other Attribute'),}

    def __init__(self, *args, **kwargs):
        super(EditproductAttributeForm, self).__init__(*args, **kwargs)
        self.fields['attributeColor'].widget.attrs['id'] = "pattributeColor"
        self.fields['attributeSize'].widget.attrs['id'] = "pattributeSize"
        self.fields['attributeDesign'].widget.attrs['id'] = "pattributeDesign"
        self.fields['attributeStyle'].widget.attrs['id'] = "pattributeStyle"
        self.fields['attributeOther'].widget.attrs['id'] = "pattributeOther"



class EditpurchasingItemsForm(MainForm):
    purchasingUom = forms.ModelChoiceField(label='Order Unit', queryset=QuantityType.objects.all())
    purchasingTax = forms.ModelChoiceField(label='Tax Code', queryset=taxCode.objects.all())
    purchasingCurrency = forms.ModelChoiceField(label='Currency Key', queryset=CurrencyType.objects.all())
    purchasingUomForKg = forms.ModelChoiceField(label='Purchase Order Price Unit', queryset=CurrencyType.objects.all())

    class Meta:
        model = purchasingItems
        exclude = {}

        fields = (
            'purchasingPrice', 'purchasingPriceUnit', 'purchasingOrderText',
        )

        labels = {'purchasingPrice': ('Purchase Price'),
                  'purchasingPriceUnit': ('Price Unit'), 'purchasingOrderText': ('Purchase Order Text'),}

    def __init__(self, *args, **kwargs):
        super(EditpurchasingItemsForm, self).__init__(*args, **kwargs)
        self.fields['purchasingUom'].empty_label = "Select"
        self.fields['purchasingTax'].empty_label = "Select"
        self.fields['purchasingCurrency'].empty_label = "Select"
        self.fields['purchasingUomForKg'].empty_label = "Select"
        self.fields['purchasingPrice'].widget.attrs['class'] = "required"
        self.fields['purchasingPriceUnit'].widget.attrs['class'] = "required"
        self.fields['purchasingOrderText'].widget.attrs['class'] = "required"
        self.fields['purchasingUom'].widget.attrs['class'] = "required"
        self.fields['purchasingTax'].widget.attrs['class'] = "required"
        self.fields['purchasingCurrency'].widget.attrs['class'] = "required"
        self.fields['purchasingUomForKg'].widget.attrs['class'] = "required"
        self.fields['purchasingUom'].widget.attrs['id'] = "ppurchasingUom"
        self.fields['purchasingTax'].widget.attrs['id'] = "ppurchasingTax"
        self.fields['purchasingCurrency'].widget.attrs['id'] = "ppurchasingCurrency"
        self.fields['purchasingUomForKg'].widget.attrs['id'] = "ppurchasingUomForKg"
        self.fields['purchasingPrice'].widget.attrs['id'] = "ppurchasingPrice"
        self.fields['purchasingPriceUnit'].widget.attrs['id'] = "ppurchasingPriceUnit"
        self.fields['purchasingOrderText'].widget.attrs['id'] = "ppurchasingOrderText"


class EditsalesItemsForm(MainForm):
    salesUom = forms.ModelChoiceField(label='Sales Unit', queryset=QuantityType.objects.all())
    salesTax = forms.ModelChoiceField(label='Tax Code', queryset=taxCode.objects.all())
    salesCurrency = forms.ModelChoiceField(label='Currency Key', queryset=CurrencyType.objects.all())
    salesUomForKg = forms.ModelChoiceField(label='Selling Price Unit',
                                                queryset=CurrencyType.objects.all())
    class Meta:
        model = salesItems
        exclude = {}

        fields = (
            'salesCategoryGrp', 'salesOrderText', 'salesPrice','salesPriceUnit',
        )

        labels = {'salesCategoryGrp': ('Item Category Group '),
                  'salesOrderText': ('Sales Text'), 'salesPrice': ('Selling Price'),
                  'salesPriceUnit': ('Price Unit'), }

    def __init__(self, *args, **kwargs):
        super(EditsalesItemsForm, self).__init__(*args, **kwargs)
        self.fields['salesUom'].empty_label = "Select"
        self.fields['salesTax'].empty_label = "Select"
        self.fields['salesCurrency'].empty_label = "Select"
        self.fields['salesUomForKg'].empty_label = "Select"
        self.fields['salesUom'].widget.attrs['class'] = "required"
        self.fields['salesTax'].widget.attrs['class'] = "required"
        self.fields['salesPrice'].widget.attrs['class'] = "required"
        self.fields['salesCurrency'].widget.attrs['class'] = "required"
        self.fields['salesUom'].widget.attrs['id'] = "psalesUom"
        self.fields['salesTax'].widget.attrs['id'] = "psalesTax"
        self.fields['salesCurrency'].widget.attrs['id'] = "psalesCurrency"
        self.fields['salesUomForKg'].widget.attrs['id'] = "psalesUomForKg"
        self.fields['salesCategoryGrp'].widget.attrs['id'] = "psalesCategoryGrp"
        self.fields['salesOrderText'].widget.attrs['id'] = "psalesOrderText"
        self.fields['salesPrice'].widget.attrs['id'] = "psalesPrice"
        self.fields['salesPriceUnit'].widget.attrs['id'] = "psalesPriceUnit"


class EdititemMeasurementForm(MainForm):
    measurementDimensionUnit = forms.ModelChoiceField(label='Dimension Unit', queryset=itemDimension.objects.all())
    measurementWeightUnit = forms.ModelChoiceField(label='Weight Unit', queryset=weightUnit.objects.all())
    class Meta:
        model = itemMeasurement
        exclude = {}

        fields = (
            'measurementDimension', 'measurementLength', 'measurementWidth', 'measurementHeight',
            'measurementWeight',
        )

        labels = {'measurementDimension': ('Dimension'),
                  'measurementLength': ('Length'), 'measurementWidth': ('Width'),
                  'measurementHeight': ('Height'), 'measurementWeight': ('Weight'),}

    def __init__(self, *args, **kwargs):
        super(EdititemMeasurementForm, self).__init__(*args, **kwargs)
        self.fields['measurementDimensionUnit'].empty_label = "Select"
        self.fields['measurementWeightUnit'].empty_label = "Select"
        self.fields['measurementDimensionUnit'].widget.attrs['id'] = "pmeasurementDimensionUnit"
        self.fields['measurementWeightUnit'].widget.attrs['id'] = "pmeasurementWeightUnit"
        self.fields['measurementDimension'].widget.attrs['id'] = "pmeasurementDimension"
        self.fields['measurementLength'].widget.attrs['id'] = "pmeasurementLength"
        self.fields['measurementWidth'].widget.attrs['id'] = "pmeasurementWidth"
        self.fields['measurementHeight'].widget.attrs['id'] = "pmeasurementHeight"
        self.fields['measurementWeight'].widget.attrs['id'] = "pmeasurementWeight"

class EdititemStorageForm(MainForm):
    storageDept = forms.ModelChoiceField(label='Department', queryset=itemDepartment.objects.all())
    class Meta:
        model = itemStorage
        exclude = {}

        fields = (
            'storageShelfLife', 'storageCase', 'storageTier', 'storagePallet',
            'storageRack',
        )

        labels = {'storageShelfLife': ('Shelf Life (Days)'),
                  'storageCase': ('Case/Tier'), 'storageTier': ('Tier/Pallet'),
                  'storagePallet': ('Case/Pallet'),
                  'storageRack':('Rack')}

    def __init__(self, *args, **kwargs):
        super(EdititemStorageForm, self).__init__(*args, **kwargs)
        self.fields['storageDept'].empty_label = "Select"
        self.fields['storageDept'].widget.attrs['id'] = "pstorageDept"
        self.fields['storageShelfLife'].widget.attrs['id'] = "pstorageShelfLife"
        self.fields['storageCase'].widget.attrs['id'] = "pstorageCase"
        self.fields['storageTier'].widget.attrs['id'] = "pstorageTier"
        self.fields['storagePallet'].widget.attrs['id'] = "pstoragePallet"
        self.fields['storageRack'].widget.attrs['id'] = "pstorageRack"

class EdititemParameterForm(MainForm):
    class Meta:
        model = itemParameter
        exclude = {}

        fields = (
            'alterNateParamOne', 'alterNateParamTwo', 'alterNateParamThree', 'alterNateParamFour',
        )

        labels = {'alterNateParamOne': ('Alternate Parameter 1'),
                  'alterNateParamTwo': ('Alternate Parameter 2'), 'alterNateParamThree': ('Alternate Parameter 3'),
                  'alterNateParamFour':('Alternate Parameter 4')}

    def __init__(self, *args, **kwargs):
        super(EdititemParameterForm, self).__init__(*args, **kwargs)
        self.fields['alterNateParamOne'].widget.attrs['id'] = "palterNateParamOne"
        self.fields['alterNateParamTwo'].widget.attrs['id'] = "palterNateParamTwo"
        self.fields['alterNateParamThree'].widget.attrs['id'] = "palterNateParamThree"
        self.fields['alterNateParamFour'].widget.attrs['id'] = "palterNateParamFour"