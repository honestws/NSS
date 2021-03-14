import random
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import logout
from django.core.cache import cache
from django.core.mail import send_mail
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone as datetime
from NSS.settings import DEFAULT_FROM_EMAIL
from .models import Account, Dataset, GPU, RoomDB, ConfigFile, DatasetServer


def log_in(request):
    username = request.POST['username']
    userpwd = request.POST['password']
    user = authenticate(username=username, password=userpwd)
    if user:
        login(request, user)
        return JsonResponse({'status': 1})
    else:
        return JsonResponse({'status': 0})


def auth_code():
    ret = ''
    for i in range(random.randint(5, 15)):
        num = random.randint(0, 9)
        up_alf = chr(random.randint(65, 90))
        lo_alf = chr(random.randint(97, 122))
        num_alf = str(random.choice([num, up_alf, lo_alf]))
        ret += num_alf
    return ret


def authcode_send(request):
    email = request.POST.get('email')
    account = request.POST.get('account')
    authcode = auth_code()
    if email:
        cache.set(email + "authcode", authcode, 5 * 60)
    if account:
        user = Account.objects.get(username=account)
        email = user.email
        cache.set(account + "authcode", authcode, 5 * 60)

    msg = 'Dear user, you received this email because you requested to register an account or reset your password at ' \
          'the NSS User Management Center. To verify the validity of your email, please enter the following ' \
          'authentication code: %s for email verification, ' \
          'and the authentication code will expire in five minutes!' % authcode
    send_mail('NSS Authentication Code', msg, DEFAULT_FROM_EMAIL, [email])
    return JsonResponse({'status': 1})


def signup(request):
    email = request.POST['email']
    authcode = request.POST['authcode']
    if authcode == cache.get(email + 'authcode'):
        user = Account.objects.create(email=email)
        username = 'P%010d' % user.account
        user.username = username
        pwd = auth_code()
        user.set_password(pwd)
        user.save()
        msg = 'Dear user, you received this email because you have registered an account successfully at ' \
              'the NSS User Management Center. Please log in to NSS with the account: %s and temporary password: %s '\
              'For account security, please change the password in the account center in time' % (username, pwd)
        send_mail('Sign Up', msg, DEFAULT_FROM_EMAIL, [email])

        return JsonResponse({'status': 1})
    else:
        return JsonResponse({'status': 0})


def reset(request):
    account = request.POST['account']
    authcode = request.POST['authcode']
    if authcode == cache.get(account + "authcode"):
        user = Account.objects.get(username=account)
        pwd = auth_code()
        user.set_password(pwd)
        email = user.email
        user.save()
        msg = 'Dear user, you received this email because you requested for the password reset at ' \
              'the NSS User Management Center. Please log in to NSS with the account: %s and temporary password: %s ' \
              'For account security, please change the password in the account center in time' % (account, pwd)
        send_mail('Password Reset', msg, DEFAULT_FROM_EMAIL, [email])
        return JsonResponse({'status': 1})
    else:
        return JsonResponse({'status': 0})


@login_required()
def log_out(request):
    logout(request)
    return JsonResponse({'status': 1})


@login_required()
def preupload(request):
    datasetname = request.POST['datasetname']
    m = float(request.POST['money'])
    account = Account.objects.get(username=request.user)
    dataset = Dataset.objects.filter(name=datasetname)
    if m > account.wallet:
        return JsonResponse({'status': -1})
    elif dataset:
        return JsonResponse({'status': 0})
    else:
        return JsonResponse({'status': 1})


# @login_required()
# def datasetrcv(request):
#     price = float(request.POST['price'])
#     description = request.POST['description']
#     cbtype = request.POST['type']
#     mbsize = float(request.POST['size'])
#     file = request.FILES['data']
#     if Dataset.objects.filter(name=file.name):
#         return JsonResponse({'status': 0})
#
#     dataset = Dataset.objects.create(
#         name=file.name, file=file, description=description, size=mbsize,
#         price=price, cbtype=cbtype, owner=request.user,
#         expire_time=datetime.datetime.now()+datetime.timedelta(days=365))
#     dataset.save()
#
#     account = Account.objects.get(username=request.user)
#     account.accessdataset.add(dataset)
#     account.save()
#     datasets = Dataset.objects.filter(expire_time__lt=datetime.datetime.now())
#     for d in datasets:
#         d.verified = 0
#         d.save()
#     return JsonResponse({'status': 1})


@login_required()
def getdatasets(request):
    datasets = Dataset.objects.all()
    data_dict = {}
    for d in datasets:
        data_dict[d.name] = {
            'size': d.size, 'cbtype': d.cbtype, 'description': d.description,
            'price': d.price, 'verified': d.verified, 'times': d.times}

    return JsonResponse(data_dict)


@login_required()
def getdatasetserveripport(request):
    datasetserver = DatasetServer.objects.first()
    ipport = datasetserver.ipport
    return JsonResponse({'ipport': ipport})


# @login_required()
# def downloaddataset(request):
#     datasetname = request.GET['datasetname']
#     pay = float(request.GET['pay'])
#     dataset = Dataset.objects.get(name=datasetname)
#     owner = dataset.owner
#     owner.wallet += pay*0.9
#     owner.save()
#     nss_account = Account.objects.get(email='519109033@qq.com')
#     nss_account.wallet += pay*0.1
#     nss_account.save()
#     account = Account.objects.get(username=request.user)
#     account.accessdataset.add(dataset)
#     account.save()
#     dataset.times += 1
#     dataset.save()
#     path = os.path.join(MEDIA_ROOT, dataset.file.path)
#     with open(path, 'rb') as file:
#         response = FileResponse(file)
#         response['Content-Type'] = 'application/octet-stream'
#         response['Content-Disposition'] = 'attachment;filename=%s.zip' % datasetname
#         response['Content-Length'] = str(dataset.size * 1024 * 1024)
#         return response


@login_required()
def datasetsize(request):
    datasetname = request.GET['datasetname']
    dataset = Dataset.objects.get(name=datasetname)
    return JsonResponse({'size': dataset.size*1024*1024})


@login_required()
def accesseddataset(request):
    datasets = Dataset.objects.filter(account__username=request.user)
    data_dict = {}
    for d in datasets:
        data_dict[d.name] = {
            'size': d.size, 'cbtype': d.cbtype, 'description': d.description,
            'price': d.price, 'verified': d.verified}

    return JsonResponse(data_dict)


@login_required()
def datasettype(request):
    types = {'datasettype': ['Image recognition', 'Image segmentation', 'Object detection']}
    return JsonResponse(types)


@login_required()
def gputype(request):
    types = {'gputype': ['RTX 2080 (24219MB 25000RMB)']}
    return JsonResponse(types)


@login_required()
def prereserve(request):
    gpus = GPU.objects.filter(master=request.user)
    account = Account.objects.get(username=request.user)
    if account.wallet < 500 * (len(gpus)+1):
        return JsonResponse({'wallet': 0, 'pay': 500*(len(gpus)+1)})
    else:
        return JsonResponse({'wallet': 1, 'pay': 500*(len(gpus)+1)})


@login_required()
def reserve(request):
    gpu = request.POST['gpu'].split('(')
    gpu_type = gpu[0].strip(' ')
    gpuinfo = gpu[1].replace(')', '').split(' ')
    memory = int(gpuinfo[0].replace('MB', ''))
    price = float(gpuinfo[1].replace('RMB', ''))
    gpu = GPU.objects.create(master=request.user, gputype=gpu_type, memory=memory, price=price,
                             expire_time=datetime.datetime.now()+datetime.timedelta(days=365))
    gpu.save()
    gpus = GPU.objects.filter(expire_time__lt=datetime.datetime.now())
    for g in gpus:
        g.status = 0
        g.save()

    return JsonResponse({'username': request.user.username, 'gpuid': str(gpu)})


@login_required()
def getgpus(request):
    gpus = GPU.objects.filter(master=request.user)
    gpu_dict = {}

    for idx, g in enumerate(gpus):
        gpu_dict[str(g)] = {'gputype': g.gputype, 'memory': g.memory, 'gpuid': g.id,
                            'price': g.price, 'master': str(g.master), 'status': g.status,
                            'location': '%s, %s, %s, %s' % (
                                g.district, g.city, g.province, g.nation), 'ctime': g.create_time.date(),
                            'mtime': g.modify_time.date(), 'etime': g.expire_time.date()}

    return JsonResponse(gpu_dict)


@login_required()
def getroomsbygpuid(request):
    gpuid = request.POST['gpuid']
    gpu = GPU.objects.get(id=int(gpuid))
    rooms = RoomDB.objects.filter(gpu=gpu)
    room_dict = dict()
    for r in rooms:
        members = r.members.all()
        room_dict[str(r)] = {'roomid': r.id, 'max_memory': r.max_memory, 'num_members': len(members), 'gpuid': gpu.id}
    return JsonResponse(room_dict)


@login_required()
def getgpuipportbygpuid(request):
    gpuid = request.POST['gpuid']
    gpu = GPU.objects.get(id=int(gpuid))
    return JsonResponse({'ipport': gpu.ipport})


@login_required()
def getroombyroomid(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    members = room.members.all()
    memberlist = ''
    for m in members:
        memberlist += m.username + ';\n'
    memory = room.max_memory
    dataset = room.dataset
    current_dataset = str(dataset)
    return JsonResponse({'memberlist': memberlist, 'memory': memory, 'current_dataset': current_dataset})


@login_required()
def getnickbyroomid(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    members = room.members.all()
    master = GPU.objects.get(rooms=room).master

    usernick = dict()
    for m in members:
        if m.nickname is None:
            nickname = ''
        else:
            nickname = m.nickname
        if m.locate == room:
            status = 'joined'
        elif m.locate != room:
            status = 'leaved'

        if m == master:
            usernick[m.username] = '%s ' % status + nickname + ' (master)'
        else:
            usernick[m.username] = '%s ' % status + nickname
    return JsonResponse(usernick)


@login_required()
def setnickname(request):
    username = request.POST['username']
    nickname = request.POST['nickname']
    account = Account.objects.get(username=username)
    account.nickname = nickname
    account.save()
    return JsonResponse({'status': 1})


@login_required()
def getaccessdata(request):
    account = Account.objects.get(username=request.user)
    datasets = account.accessdataset.all()
    dataset_list = [str(d) for d in datasets]
    return JsonResponse({'datasetlist': dataset_list})


@login_required()
def getroomdata(request):
    roomid = int(request.POST['roomid'])
    room = RoomDB.objects.get(id=roomid)
    roomdata = room.dataset
    return JsonResponse({'roomdataset': str(roomdata)})


@login_required()
def getmaxmemory(request):
    gpuid = int(request.POST['gpuid'])
    gpu = GPU.objects.get(id=gpuid)
    gpu_memory = gpu.memory
    rooms = RoomDB.objects.filter(gpu=gpu)
    acc_memory = 0
    for r in rooms:
        acc_memory += r.max_memory
    maxmemory = gpu_memory-acc_memory
    return JsonResponse({'maxmemory': maxmemory})


@login_required()
def roomadd(request):
    gpuid = int(request.POST['gpuid'])
    gpu = GPU.objects.get(id=gpuid)
    memory = int(request.POST['memory'])
    datasetname = request.POST['datasetname']
    gpu_memory = gpu.memory
    rooms = RoomDB.objects.filter(gpu=gpu)
    acc_memory = 0
    for r in rooms:
        acc_memory += r.max_memory
    maxmemory = gpu_memory - acc_memory
    if maxmemory < memory:
        memory = int(maxmemory)
    if memory < 5120:
        memory = 5120
    if len(rooms) >= 4:
        return JsonResponse({'roomid': -1})
    dataset = Dataset.objects.get(name=datasetname + '.zip')
    dataset.save()
    room = RoomDB.objects.create(max_memory=memory, dataset=dataset)
    room.save()
    gpu.rooms.add(room)
    gpu.save()
    mbs = request.POST['members'].replace('\n', '').split(';')[:-1]
    for m in mbs:
        account = Account.objects.filter(username=m)
        if account:
            room.members.add(account[0])
            room.save()
            account[0].accessroom.add(room)
            account[0].save()
        else:
            room.delete()
            return JsonResponse({'roomid': 0, 'username': m})
    return JsonResponse({'roomid': room.id})


@login_required()
def deleteroom(request):
    roomid = int(request.POST['roomid'])
    room = RoomDB.objects.get(id=roomid)
    room.delete()
    return JsonResponse({'status': 1})


@login_required()
def roomedit(request):
    memory = int(request.POST['memory'])
    roomid = int(request.POST['roomid'])
    datasetname = request.POST['datasetname']
    room = RoomDB.objects.get(id=roomid)
    gpuid = int(request.POST['gpuid'])
    gpu = GPU.objects.get(id=gpuid)
    gpu_memory = gpu.memory
    rooms = RoomDB.objects.filter(gpu=gpu)
    acc_memory = 0
    for r in rooms:
        acc_memory += r.max_memory
    maxmemory = gpu_memory - acc_memory
    if maxmemory < memory:
        memory = int(maxmemory + room.max_memory)
    if memory < 5120:
        memory = 5120
    room.max_memory = memory
    old_mbs = room.members.all()
    for m in old_mbs:
        room.members.remove(m)
    room.save()
    mbs = request.POST['members'].replace('\n', '').split(';')[:-1]
    for m in mbs:
        account = Account.objects.filter(username=m)
        if account:
            room.members.add(account[0])
            room.save()
            account[0].accessroom.add(room)
            account[0].save()
        else:
            return JsonResponse({'status': 0, 'username': m})
    dataset = Dataset.objects.get(name=datasetname + '.zip')
    room.dataset = dataset
    dataset.save()
    room.save()
    return JsonResponse({'status': 1})


@login_required()
def roomremove(request):
    gpuid = int(request.POST['gpuid'])
    gpu = GPU.objects.get(id=gpuid)
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    config = ConfigFile.objects.filter(room=room)
    if config:
        config.delete()
    gpu.rooms.remove(room)
    gpu.save()
    room.delete()
    return JsonResponse({'status': 1})


@login_required()
def getroomsbymember(request):
    account = Account.objects.get(username=request.user)
    locate = account.locate
    rooms = account.accessroom.all()
    room_dict = dict()
    for r in rooms:
        members = r.members.all()
        gpu = GPU.objects.filter(Q(rooms=r) & Q(expire_time__gt=datetime.datetime.now()))
        if not gpu:
            continue
        room_dict[str(r)] = {'roomid': r.id, 'max_memory': r.max_memory, 'datasetname': str(r.dataset),
                             'num_members': len(members), 'gpuid': gpu[0].id, 'status': int(r.running),
                             'location': str(locate), 'master': str(gpu[0].master), 'gpuaddr': gpu[0].ipport}
    return JsonResponse(room_dict)


@login_required()
def getlocation(request):
    account = Account.objects.get(username=request.user)
    return JsonResponse({'location': str(account.locate)})


@login_required()
def getroomchataddr(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=roomid)
    return JsonResponse({'addr': room.chatipport})


@login_required()
def getroomgradaddr(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=roomid)
    return JsonResponse({'addr': room.gradipport})


@login_required()
def setlocation(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    account = Account.objects.get(username=request.user)
    account.locate = room
    account.save()
    return JsonResponse({'location': str(account.locate)})


@login_required()
def clearlocation(request):
    account = Account.objects.get(username=request.user)
    account.locate = None
    account.save()
    return JsonResponse({'status': 1})


@login_required()
def getroommaster(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    gpu = GPU.objects.get(rooms=room)
    if gpu.master.username == request.user.username:
        return JsonResponse({'status': 1})
    else:
        return JsonResponse({'status': 0})


@login_required()
def getrequestuser(request):
    account = Account.objects.get(username=request.user)
    return JsonResponse({'username': request.user.username, 'nickname': str(account.nickname)})


@login_required()
def getroomstatus(request):
    roomid = request.POST['roomid']
    room = RoomDB.objects.get(id=int(roomid))
    room_status_dict = {'closed': int(room.closed)}
    return JsonResponse(room_status_dict)


@login_required()
def setroomstatus(request):
    roomid = request.POST['roomid']
    account = Account.objects.get(username=request.user)
    room = RoomDB.objects.get(id=int(roomid))
    room_status_dict = {'running': int(room.running), 'closed': int(room.closed)}
    return JsonResponse(room_status_dict)

