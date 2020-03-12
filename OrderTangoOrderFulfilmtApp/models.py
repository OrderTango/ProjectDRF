from django.db import models
from OrderTangoApp import constants
from OrderTangoSubDomainApp.models import Customer,Sites
from OrderTangoApp.models import CurrencyType,QuantityType,Country,State

# Create your models here.


class OrderPlacementfromCustomer(models.Model):
    ordFrmCusId = models.AutoField(primary_key=True)
    ordNumber = models.CharField(max_length=255)
    totalQuantity = models.CharField(max_length=50,null=True)
    totalPrice = models.CharField(max_length=50, default='0')
    totalPriceUnit = models.CharField(max_length=50, default="USD")
    ordstatus = models.CharField(max_length=50, default=constants.Pending)
    customerId = models.ForeignKey(Customer, on_delete=models.CASCADE)
    customer_country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)
    customer_address_Line1 = models.CharField(max_length=100)
    customer_address_Line2 = models.CharField(max_length=100)
    customer_unit1 = models.CharField(max_length=2)
    customer_unit2 = models.CharField(max_length=2)
    customer_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True)
    customer_postalCode = models.CharField(max_length=7)
    expectedDate = models.CharField(max_length=50)
    expectedTime = models.CharField(max_length=50)
    orderDate = models.DateField()
    pdfField = models.BinaryField(null=True)
    siteId = models.ForeignKey(Sites, on_delete=models.SET_NULL, null=True)
    connectedStatus = models.BooleanField(default=False)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.ordFrmCusId

    class Meta:
        db_table = 'OrderPlacementfromCustomer'

class OrderDetails(models.Model):
    ordDetailId = models.AutoField(primary_key=True)
    ordNumber =  models.ForeignKey(OrderPlacementfromCustomer,related_name="orderdetail", on_delete=models.CASCADE)
    itemCode = models.CharField(max_length=50)
    itemName = models.CharField(max_length=50)
    itemCategory = models.CharField(max_length=50, default=constants.Uncategorized)
    quantity = models.CharField(max_length=50)
    actualQuantity = models.CharField(max_length=50,null=True)
    price = models.CharField(max_length=50)
    priceUnit = models.ForeignKey(CurrencyType, on_delete=models.CASCADE)
    uOm = models.ForeignKey(QuantityType, on_delete=models.CASCADE)
    ordstatus = models.CharField(max_length=50, default=constants.Pending)
    comment = models.TextField()
    goodsIssue = models.CharField(max_length=50)
    goodsReceive = models.CharField(max_length=50)
    pickUpList= models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __int__(self):
        return self.ordDetailId

    class Meta:
        db_table = 'OrderDetails'