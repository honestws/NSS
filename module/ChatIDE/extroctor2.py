import json
import traceback
from multiprocessing import Process
from threading import Timer


class RepeatedTimer(object):
    def __init__(self, interval, function, queue, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.queue = queue[0]
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.queue.put(self.function(*self.args, **self.kwargs))

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


class ExtractorProcess(Process):
    def __init__(self, config_path, reg, bat, ckp_path, data_path, roomid, tim, queue_list, session, ipport, gpuid):
        Process.__init__(self)
        self.config_path = config_path
        self.reg = reg
        self.bat = bat
        self.ckp_path = ckp_path
        self.data_path = data_path
        self.roomid = roomid
        self.tim = tim
        self.queue_para = queue_list[0]
        self.queue_train = queue_list[1]
        self.queue_test = queue_list[2]
        self.queue_grad = queue_list[3]
        self.queue_error = queue_list[4]
        self.queue_ready = queue_list[5]
        self.session = session
        self.ipport = ipport
        self.gpuid = gpuid

    def run(self):
        rt = None
        flag = True
        try:
            file = open(self.config_path).read()
            config = {}
            exec(file, config)
            EXEV = config.get('ExtractorEvaluator')
            exev = EXEV(self.reg, self.bat, self.ckp_path, self.data_path, self.roomid)
            plotname = exev.name
            self.queue_ready.put(plotname)
            rt = RepeatedTimer(self.tim, exev.evaluate, [self.queue_test])
            exev.extractor.send(None)
            r = self.session.post(
                'http://%s/getgpuipportbygpuid/' % self.ipport, data={
                    'gpuid': self.gpuid
                }
            )
            res = json.loads(r.content.decode('utf-8'))
            gpuipport = res['ipport']
            r = self.session.post('http://' + gpuipport + '/parseconfig/',
                                  data={'roomid': self.roomid})

            while True:
                vec_grads, user_lr, train_record = exev.extractor.send(None)
                self.queue_train.put(train_record)
                self.queue_grad.put((vec_grads, user_lr))
                p = self.queue_para.get(block=True)
                exev.apply(p)
                if flag:
                    flag = False
                    self.queue_error.put(None)
        except Exception as e:
            tb = traceback.format_exc()
            self.queue_error.put(tb)
        finally:
            if rt is not None:
                rt.stop()
