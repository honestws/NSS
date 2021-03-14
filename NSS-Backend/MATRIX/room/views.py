import json
import os
import random
import re
import sys
import time
import traceback
import numpy as np
import psutil
import pynvml
import requests
from threading import Lock
from PyQt5.QtCore import QCoreApplication, QThread, pyqtSignal, pyqtSlot
from django.db import connection
from django.http import JsonResponse, FileResponse
from multiprocessing import Process, Queue
from MATRIX.settings import BASE_DIR, MEDIA_ROOT
from pypinyin import lazy_pinyin
from .nssproto import res, req
from .models import RoomDB, GPU, Account, ConfigFile
from PyQt5 import QtCore, QtWebSockets
from PyQt5.QtNetwork import QHostAddress

room_instances = dict()
chat_instances = dict()
lock = Lock()


def inigpu():
    ipport = sys.argv[2]
    gpuid = int(sys.argv[4])
    cuda = int(sys.argv[6])
    pynvml.nvmlInit()
    handle = pynvml.nvmlDeviceGetHandleByIndex(cuda)
    info = pynvml.nvmlDeviceGetMemoryInfo(handle)
    memory = info.total/1024/1024
    r = requests.get(
        'https://apis.map.qq.com/ws/location/v1/ip?key=N3TBZ-TTJC4-PKCUD-DX27T-SDFNS-63BAD')
    response = json.loads(r.content.decode('utf-8'))
    lat = response['result']['location']['lat']
    lng = response['result']['location']['lng']
    nation = response['result']['ad_info']['nation']
    nation = ''.join(lazy_pinyin(nation)).capitalize()
    nation = nation.replace('Zhongguo', 'China')
    province = response['result']['ad_info']['province']
    province = ''.join(lazy_pinyin(province)).capitalize()
    province = re.sub('sheng$', '', province)

    city = response['result']['ad_info']['city']
    city = ''.join(lazy_pinyin(city)).capitalize()
    city = city.strip('shi')
    district = response['result']['ad_info']['district']
    district = ''.join(lazy_pinyin(district)).capitalize()
    district = district.strip('qu')
    adcode = response['result']['ad_info']['adcode']
    gpu = GPU.objects.get(id=gpuid)
    # if gpu.status:
    #     raise RuntimeError('The status of the specified GPU was available.')
    gpu.cuda = cuda
    gpu.memory = memory
    gpu.lat = lat
    gpu.lng = lng
    gpu.nation = nation
    gpu.province = province
    gpu.city = city
    gpu.district = district
    gpu.adcode = adcode
    gpu.ipport = ipport
    gpu.status = 1
    gpu.save()
    connection.close()


inigpu()


def getfreeport():
    pscmd = "netstat -ntl |grep -v Active| grep -v Proto|awk '{print $4}'|awk -F: '{print $NF}'"
    procs = os.popen(pscmd).read()
    procarr = procs.split("\n")
    t = str(random.randint(15000, 20000))
    if t not in procarr:
        return t
    else:
        return getfreeport()


class RoomEditThread(QThread):
    to_socket_roomedit = pyqtSignal(tuple)

    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue[0]

    def run(self):
        while True:
            e = self.queue.get(block=True)
            self.to_socket_roomedit.emit(e)


class DoorReverseThread(QThread):
    to_socket_doorreverse = pyqtSignal()

    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue[0]

    def run(self):
        while True:
            _ = self.queue.get(block=True)
            self.to_socket_doorreverse.emit()


class ParseConfigThread(QThread):
    to_socket_parseconfig = pyqtSignal()

    def __init__(self, queue):
        QThread.__init__(self)
        self.queue = queue[0]

    def run(self):
        while True:
            _ = self.queue.get(block=True)
            self.to_socket_parseconfig.emit()


class NssChatSocket(QtCore.QObject):
    def __init__(self, parent, roomid, mbs):
        QtCore.QObject.__init__(self, parent)
        self.chat_clients = []
        self.roomid = roomid
        self.mbs = mbs
        print("server name: {}".format(parent.serverName()))
        self.server = QtWebSockets.QWebSocketServer(parent.serverName(), parent.secureMode(), parent)
        self.port = getfreeport()
        if self.server.listen(QHostAddress(sys.argv[2].split(':')[0]), int(self.port)):
            roomdb = RoomDB.objects.get(id=self.roomid)
            roomdb.chatipport = sys.argv[2].split(':')[0] + ':' + self.port
            roomdb.save()
            connection.close()
            print('Listening: {}:{}:{}'.format(
                self.server.serverName(), self.server.serverAddress().toString(),
                str(self.server.serverPort())))
        else:
            print('error')
        self.server.acceptError.connect(self.onAcceptError)
        self.server.newConnection.connect(self.onNewConnection)
        self.clientConnection = None
        print(self.server.isListening())

    @staticmethod
    def onAcceptError(accept_error):
        print("Accept Error: {}".format(accept_error))

    def onNewConnection(self):
        print('chatter new connection')
        self.clientConnection = self.server.nextPendingConnection()
        self.clientConnection.textMessageReceived.connect(self.processTextMessage)
        self.clientConnection.disconnected.connect(self.socketDisconnected)
        self.chat_clients.append(self.clientConnection)

    def processTextMessage(self, message):
        if self.clientConnection:
            for client in self.chat_clients:
                client.sendTextMessage(message)

    def socketDisconnected(self):
        print("chatsocketDisconnected")
        if self.clientConnection:
            self.chat_clients.remove(self.clientConnection)
            self.clientConnection.deleteLater()


class NSSGradSocket(QtCore.QObject):
    def __init__(self, parent, roomid, cuda, max_memory, mbs, queue_list, master):
        QtCore.QObject.__init__(self, parent)
        self.grad_clients = []
        self.roomid = roomid
        self.cuda = cuda
        self.mbs = mbs
        self.max_memory = max_memory
        self.opendoor = True
        self.stack_a = None
        self.device = None
        self.torch = None
        self.stack_b = None
        self.max_num_grad = 0
        self.s = None
        self.variables = None
        self.vars_shape = None
        self.begin = 0
        self.end = None
        self.ind1 = None
        self.ind2 = None
        self.master = master
        self.inisolution()

        room_edit_thread = RoomEditThread([queue_list[0]])
        door_reverse_thread = DoorReverseThread([queue_list[1]])
        parse_config_thread = ParseConfigThread([queue_list[2]])
        room_edit_thread.start()
        door_reverse_thread.start()
        parse_config_thread.start()
        room_edit_thread.to_socket_roomedit.connect(self.roomedit)
        door_reverse_thread.to_socket_doorreverse.connect(self.doorreverse)
        parse_config_thread.to_socket_parseconfig.connect(self.parseconfig)

        print("server name: {}".format(parent.serverName()))
        self.server = QtWebSockets.QWebSocketServer(parent.serverName(), parent.secureMode(), parent)
        self.port = getfreeport()
        if self.server.listen(QHostAddress(sys.argv[2].split(':')[0]), int(self.port)):
            roomdb = RoomDB.objects.get(id=self.roomid)
            roomdb.gradipport = sys.argv[2].split(':')[0] + ':' + self.port
            roomdb.save()
            connection.close()
            print('Listening: {}:{}:{}'.format(
                self.server.serverName(), self.server.serverAddress().toString(),
                str(self.server.serverPort())))
        else:
            print('error')
        self.server.acceptError.connect(self.onAcceptError)
        self.server.newConnection.connect(self.onNewConnection)
        self.clientConnection = None

    def inisolution(self):
        torch = __import__('torch')
        self.torch = torch
        self.device = torch.device('cuda:' + str(self.cuda))

        class Solution(torch.nn.Module):
            def __init__(self):
                super(Solution, self).__init__()

            def forward(self, a, b):
                inverse_matrix = torch.inverse(torch.matmul(a, a.permute(1, 0)))
                solution = torch.matmul(torch.matmul(a.permute(1, 0), inverse_matrix), b)
                return solution
        self.s = Solution().to(self.device)

    def get_vec_params(self, varis):
        _vars_size = [int(self.torch.prod(self.torch.tensor(list(var.size()))).item()) for var in varis]
        vec_vars_set = [self.torch.reshape(var, (-1, _vars_size[i])) for i, var in enumerate(varis)]
        vec_params = self.torch.cat([vec_vars_set[i] for i in range(len(_vars_size))], dim=1)
        return vec_params.detach().numpy()

    def recover_shape(self, _vec_params, _vars_shape, _ind1, _ind2):
        vec_params_tensor = self.torch.from_numpy(_vec_params)
        _recovered_vars = [
            self.torch.reshape(vec_params_tensor[0][ind[0]:ind[1]], shape=tuple(_vars_shape[k]))
            for k, ind in enumerate(zip(_ind1, _ind2))]
        return _recovered_vars

    @staticmethod
    def onAcceptError(accept_error):
        print("Accept Error: {}".format(accept_error))

    def onNewConnection(self):
        print('grad new connection')
        self.clientConnection = self.server.nextPendingConnection()
        self.clientConnection.binaryMessageReceived.connect(self.processBinaryMessage)
        self.clientConnection.disconnected.connect(self.socketDisconnected)

    def processBinaryMessage(self, buf):
        username, msgtype, msg, grad, user_lr = req(buf)
        if msg == 'ini':
            if self.opendoor or username == self.master:
                while self.variables is None:
                    time.sleep(0.2)
                vec_params = self.get_vec_params(self.variables)
                nss_proto = res('*', 'sync', 'sync', vec_params, user_lr).SerializeToString()
                self.clientConnection.sendBinaryMessage(nss_proto)
                self.grad_clients.append(self.clientConnection)
            else:
                message = 'The room has been closed by its master! You can not enter the room now!'
                nss_proto = res(
                    '*', 'roomclosed', message, user_lr, user_lr).SerializeToString()
                self.clientConnection.sendBinaryMessage(nss_proto)
        else:
            try:
                self.stack_a = np.concatenate([self.stack_a, grad], axis=0)
                self.stack_b = np.concatenate([self.stack_b, user_lr], axis=0)
            except ValueError:
                self.stack_a = grad
                self.stack_b = user_lr
            if self.stack_a is not None and self.stack_a.shape[0] >= len(self.grad_clients):
                a = self.torch.from_numpy(self.stack_a[:, self.begin:self.end])
                b = self.torch.from_numpy(self.stack_b)
                a = a.to(self.device)
                b = b.to(self.device)
                with self.torch.no_grad():
                    solution = self.s(a, b).cpu().numpy()
                if self.max_num_grad < len(self.grad_clients):
                    self.max_num_grad = len(self.grad_clients)
                    lux = "nvidia-smi |grep %s| sed 's/  */ /g'|cut -f6 -d' '|tr -cd '[0-9]'" % str(os.getpid())
                    m = float(os.popen(lux).read())
                    roomdb = RoomDB.objects.get(id=self.roomid)
                    if m >= roomdb.max_memory:
                        message = 'The process has exceeded the maximum ' \
                                  'room memory limitation! The room has been terminated.' \
                                  ' destroyed and rebuilt! Please exit the IDE, and reenter the room again.'
                        nss_proto = res(
                            '*', 'roomerror', message, user_lr, user_lr).SerializeToString()
                        for so in self.grad_clients:
                            so.sendBinaryMessage(nss_proto)
                        roomdb.running = False
                        roomdb.save()
                        connection.close()
                        QCoreApplication.quit()
                    else:
                        message = 'Room memory usage: %d/%d=%.2f' % (int(m), roomdb.max_memory,
                                                                     m / roomdb.max_memory * 100) + '%'
                        nss_proto = res(
                            '*', 'roomstatus', message, user_lr, user_lr).SerializeToString()
                        for so in self.grad_clients:
                            so.sendBinaryMessage(nss_proto)
                vec_params = self.get_vec_params(self.variables)
                vec_params[0, self.begin:self.end] += solution[:, 0]
                recovered_params = self.recover_shape(vec_params, self.vars_shape, self.ind1, self.ind2)

                for i, param in enumerate(self.variables):
                    param.data = recovered_params[i]
                vec_params = self.get_vec_params(self.variables)
                nss_proto = res('*', 'sync', 'sync', vec_params, user_lr).SerializeToString()
                self.stack_a = None
                self.stack_b = None
                for so in self.grad_clients:
                    so.sendBinaryMessage(nss_proto)

    def socketDisconnected(self):
        print("gradsocketDisconnected")
        if self.clientConnection:
            try:
                self.grad_clients.remove(self.clientConnection)
                self.max_num_grad -= 1
                self.clientConnection.deleteLater()
            except:
                pass

    @pyqtSlot()
    def roomedit(self, e):
        self.max_memory = e[0]
        self.mbs = e[1]

    @pyqtSlot()
    def doorreverse(self):
        roomdb = RoomDB.objects.get(id=self.roomid)
        if roomdb.closed:
            roomdb.closed = False
            self.opendoor = True
        else:
            roomdb.closed = True
            self.opendoor = False
        roomdb.save()
        connection.close()

    @pyqtSlot()
    def parseconfig(self):
        try:
            path = os.path.join(BASE_DIR, 'configs/R%010d.py' % self.roomid)
            config = {}
            file = open(path).read()
            exec(file, config)
            Model = config.get('DeepNet')
            if Model is None:
                raise RuntimeError('File parsing failed. DeepNet module not found.')
            else:
                model = Model()
            self.variables = list(model.parameters())
            self.vars_shape = [list(var.size()) for var in self.variables]
            vars_size = [self.torch.prod(self.torch.tensor(list(var.size()))).item() for var in self.variables]
            self.begin = 0
            self.end = sum(vars_size)
            self.ind2 = [sum(vars_size[:i + 1]) for i in range(len(self.variables))]
            self.ind1 = [0] + self.ind2[:-1]
        except Exception as e:
            tb = traceback.format_exc()
            print((e, tb))


class NSSChatSocketProcess(Process):
    def __init__(self, roomid, mbs):
        Process.__init__(self)
        self.roomid = roomid
        self.mbs = mbs
        self.port = None
        self.ip = sys.argv[2].split(':')[0]

    def run(self):
        app = QCoreApplication(sys.argv)
        serverObject = QtWebSockets.QWebSocketServer('Chatter', QtWebSockets.QWebSocketServer.NonSecureMode)
        chattersocket = NssChatSocket(serverObject, self.roomid, self.mbs)
        self.port = chattersocket.port
        serverObject.closed.connect(app.quit)
        app.exec_()


class NSSGradSocketProcess(Process):
    def __init__(self, roomid, cuda, max_memory, mbs, master):
        Process.__init__(self)
        self.roomid = roomid
        self.cuda = cuda
        self.max_memory = max_memory
        self.mbs = mbs
        self.queue_list = []
        self.master = master
        for _ in range(3):
            self.queue_list.append(Queue())

    def run(self):
        app = QCoreApplication(sys.argv)
        serverObject = QtWebSockets.QWebSocketServer('Gradient Processor',
                                                     QtWebSockets.QWebSocketServer.NonSecureMode)
        _ = NSSGradSocket(serverObject, self.roomid, self.cuda, self.max_memory, self.mbs, self.queue_list, self.master)
        serverObject.closed.connect(app.quit)
        app.exec_()

    def roomremove(self):
        p = psutil.Process(self.pid)
        p.terminate()


def parseconfig(request):
    roomid = int(request.POST['roomid'])
    room = room_instances[roomid]
    queue = room.queue_list[2]
    queue.put(None)
    return JsonResponse({'status': 1})


def roomadd(request):
    cuda = int(sys.argv[6])
    roomid = int(request.POST['roomid'])
    max_memory = int(request.POST['max_memory'])
    mbs = request.POST['members']
    master = request.POST['master']
    room_instances[roomid] = NSSGradSocketProcess(roomid, cuda, max_memory, mbs, master)
    chat_instances[roomid] = NSSChatSocketProcess(roomid, mbs)
    room = room_instances[roomid]
    room.start()
    chat = chat_instances[roomid]
    chat.start()
    return JsonResponse({'status': 1})


def roomedit(request):
    roomid = int(request.POST['roomid'])
    max_memory = int(request.POST['max_memory'])
    mbs = request.POST['members']
    room = room_instances[roomid]
    queue = room.queue_list[0]
    queue.put((max_memory, mbs))
    return JsonResponse({'status': 1})


def roomremove(request):
    roomid = int(request.POST['roomid'])
    room = room_instances.get(roomid)
    if not room:
        return JsonResponse({'status': 1})
    room.roomremove()
    del room_instances[roomid]
    return JsonResponse({'status': 1})


def roomrestart(request):
    roomid = int(request.POST['roomid'])
    room = room_instances.get(roomid)
    if not room:
        return JsonResponse({'status': 1})
    room.roomremove()
    cuda = room.cuda
    max_memory = room.max_memory
    mbs = room.mbs
    master = room.master
    del room_instances[roomid]
    room_instances[roomid] = NSSGradSocketProcess(roomid, cuda, max_memory, mbs, master)
    room = room_instances[roomid]
    room.start()
    return JsonResponse({'status': 1})


def doorreverse(request):
    roomid = int(request.POST['roomid'])
    room = room_instances[roomid]
    queue = room.queue_list[1]
    queue.put(None)
    return JsonResponse({'status': 1})


def filercv(request):
    roomid = int(request.POST['roomid'])
    file = request.FILES['data']
    room = RoomDB.objects.get(id=roomid)
    config = ConfigFile.objects.filter(room=room)
    if not config:
        config = ConfigFile.objects.create(room=room, file=file)
        config.save()
    else:
        path = os.path.join(MEDIA_ROOT, config[0].file.path)
        if os.path.exists(path):
            os.remove(path)
        config[0].file = file
        config[0].save()
    return JsonResponse({'status': 1})


def downloadfile(request):
    roomid = int(request.GET['roomid'])
    room = RoomDB.objects.get(id=roomid)
    config = ConfigFile.objects.filter(room=room)

    if config:
        path = os.path.join(MEDIA_ROOT, config[0].file.path)
        file = open(path, 'rb')
        response = FileResponse(file)
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename=%s' % config[0].file.name
        response['status'] = 1
        return response
    else:
        return JsonResponse({'status': 0})
