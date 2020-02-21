from django.db import models
from OrderTangoApp import constants
from OrderTangoSubDomainApp.models import SupplierProductCatalog,Sites
from OrderTangoApp.models import CurrencyType,QuantityType
# Create your models here.


class ShoppingCart(models.Model):
    shoppingCartId = models.AutoField(primary_key=True)
    status = models.CharField(max_length=50, default=constants.Pending)
    totalPrice = models.CharField(max_length=50, default='0')
    totalPriceUnit = models.CharField(max_length=50, default="USD")
    expectedDate = models.CharField(max_length=50)
    expectedTime =  models.CharField(max_length=50)
    deliveryLocation = models.ForeignKey(Sites, on_delete=models.CASCADE)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.shoppingCartId

    class Meta:
        db_table = 'ShoppingCart'

class OrderPlacementtoSupplier(models.Model):
    ordToSupId = models.AutoField(primary_key=True)
    ordNumber = models.CharField(max_length=255)
    productId = models.ForeignKey(SupplierProductCatalog, on_delete=models.CASCADE)
    shopCartId = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE)
    quantity = models.CharField(max_length=50)
    actualQuantity = models.CharField(max_length=50, null=True)
    price = models.CharField(max_length=50)
    priceUnit = models.ForeignKey(CurrencyType, on_delete=models.CASCADE)
    uOm = models.ForeignKey(QuantityType, on_delete=models.CASCADE)
    ordstatus = models.CharField(max_length=50, default=constants.Pending)
    orderDate = models.DateField()
    comment = models.TextField()
    goodsIssue = models.CharField(max_length=50)
    goodsReceive = models.CharField(max_length=50)
    pickUpList = models.CharField(max_length=50)
    status = models.CharField(max_length=50, default=constants.Active)
    connectedStatus = models.BooleanField(default=False)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ordToSupId

    class Meta:
        db_table = 'OrderPlacementtoSupplier'


class pdfDetailsForPlacedOrder(models.Model):
    pdfId = models.AutoField(primary_key=True)
    ordNumber = models.CharField(max_length=255)
    pdfField = models.BinaryField(blank=True)
    status = models.CharField(max_length=50, default=constants.Active)
    createdDateTime = models.DateTimeField(auto_now_add=True)
    updatedDateTime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pdfId

    class Meta:
        db_table = 'pdfDetailsForPlacedOrder'