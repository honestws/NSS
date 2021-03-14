import os
import sys

from DATASET.settings import MEDIA_ROOT
from django.utils import timezone as datetime
from django.http import JsonResponse, FileResponse
from .models import Dataset, Account, DatasetServer


def inidatasetserver():
    ipport = sys.argv[2]
    datasetservers = DatasetServer.objects.all()
    for d in datasetservers:
        d.delete()
    datasetserver = DatasetServer.objects.create(ipport=ipport)
    datasetserver.save()


inidatasetserver()


def datasetrcv(request):
    price = float(request.POST['price'])
    description = request.POST['description']
    username = request.POST['username']
    cbtype = request.POST['type']
    mbsize = float(request.POST['size'])
    file = request.FILES['data']
    if Dataset.objects.filter(name=file.name):
        return JsonResponse({'status': 0})

    account = Account.objects.get(username=username)

    dataset = Dataset.objects.create(
        name=file.name, file=file, description=description, size=mbsize,
        price=price, cbtype=cbtype, owner=account,
        expire_time=datetime.datetime.now()+datetime.timedelta(days=365))
    dataset.save()

    account.accessdataset.add(dataset)
    account.save()
    datasets = Dataset.objects.filter(expire_time__lt=datetime.datetime.now())
    for d in datasets:
        d.verified = -1
        d.save()
    return JsonResponse({'status': 1})


def downloaddataset(request):
    datasetname = request.GET['datasetname']
    username = request.GET['username']
    pay = float(request.GET['pay'])
    dataset = Dataset.objects.get(name=datasetname)
    owner = dataset.owner
    owner.wallet += pay*0.9
    owner.save()
    nss_account = Account.objects.get(email='519109033@qq.com')
    nss_account.wallet += pay*0.1
    nss_account.save()
    account = Account.objects.get(username=username)
    account.accessdataset.add(dataset)
    account.wallet -= pay
    account.save()
    dataset.times += 1
    dataset.save()
    path = os.path.join(MEDIA_ROOT, dataset.file.path)
    print(path)
    print(datasetname)
    file = open(path, 'rb')
    response = FileResponse(file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename=%s' % datasetname
    response['Content-Length'] = str(dataset.size * 1024 * 1024)
    return response
