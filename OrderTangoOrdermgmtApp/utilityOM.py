from OrderTangoOrdermgmtApp.models import *

def getPdfBasedOnOrderNo(orderNo):
    try:
        pdf = pdfDetailsForPlacedOrder.objects.get(ordNumber__iexact=orderNo)
    except:
        pdf = None
    return pdf