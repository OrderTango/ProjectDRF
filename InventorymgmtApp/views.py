from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from OrderTangoApp.forms import *
from OrderTangoSubDomainApp.forms import *
from OrderTangoApp import utility, constants
from django.shortcuts import render, redirect

def inventory(request):
        if 'user' in request.session or 'subUser' in request.session:
            if 'user' in request.session:
                currentUser = utility.getObjectFromSession(request, 'user')
                subUserProfile = constants.No
                company = currentUser.userCompanyId
                urls = utility.checkRequesURLisPresentForCompany(company, request.path)
                addOnModuleUrls = utility.getUrlsAccessAddonModule(company, request.path)
            else:
                currentUser = utility.getObjectFromSession(request, 'subUser')
                subUserProfile = constants.Yes
                company = utility.getCompanyBySchemaName(connection.schema_name)
                urls = utility.checkRequesURLisPresentForSubUser(currentUser, request.path)
            if urls or addOnModuleUrls:
                return render(request, 'test.html', {})

            else:
                return HttpResponseRedirect('/unauthorize/')
        return HttpResponseRedirect('/login/')

