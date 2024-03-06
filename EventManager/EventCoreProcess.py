import time

from EventManager.Event import Event as evt
from PyQt5.QtCore import QThread,QThreadPool, pyqtSignal, QObject, QRunnable
class Signals(QObject):
    started = pyqtSignal(int)
    completed = pyqtSignal(int)
class evt_worker_manager(QRunnable):
    def __init__(self):
        super().__init__()
        self.signals = Signals()

    def set_option_data(self,**kwargs):
        self.kwargs = kwargs
        return
    def run(self):
        cpu_list_name = list(self.kwargs['evt_worker_manager'].keys())
        key_idx = 0
        loop_while = 0

        while 1:
            if key_idx == len(cpu_list_name):
                key_idx = 0

            if len(self.kwargs['evt_worker_manager'][cpu_list_name[key_idx]]) == 0:
                key_idx +=1
                loop_while +=1
                if loop_while == 1000:
                    time.sleep(1)
                    print(self.kwargs['name'], ' manger does not have any event')
                    break
                continue
            else:
                loop_while = 0

            for evt_item in self.kwargs['evt_worker_manager'][cpu_list_name[key_idx]]:
                if evt(evt_item).get_min_start_time() > 0:
                    evt(evt_item).state_check(self.kwargs['current_time'])

        self.signals.completed.emit(0)

class main_event_core(QThread):

    event_manager_queue = dict()
    layer_manager_timer = dict()
    opts = dict()

    def __init__(self,**kwargs):
        super().__init__()
        try:
            self.opts['hil_cpu'] = kwargs['hil_cpu']
            self.opts['ftl_cpu'] = kwargs['ftl_cpu']
            self.opts['fil_cpu'] = kwargs['fil_cpu']
            self.opts['host_cpu'] = kwargs['host_cpu']

            self.opts['plane_arch'] = kwargs['plane_arch']
            self.opts['die_arch'] = kwargs['die_arch']
        except:
            self.opts['hil_cpu'] = 1
            self.opts['ftl_cpu'] = 1
            self.opts['fil_cpu'] = 1
            self.opts['host_cpu'] = 2

            self.opts['plane_arch'] = -1
            self.opts['die_arch'] = 32

        self.event_manager_queue['hil_layer_queue'] = dict()
        self.layer_manager_timer['hil_layer_queue'] = dict()
        for idx in range(0,self.opts['hil_cpu']):
            self.event_manager_queue['hil_layer_queue'][idx] = list()
            self.layer_manager_timer['hil_layer_queue'][idx] = 0

        self.event_manager_queue['ftl_layer_queue'] = dict()
        self.layer_manager_timer['ftl_layer_queue'] = dict()
        for idx in range(0, self.opts['ftl_cpu']):
            self.event_manager_queue['ftl_layer_queue'][idx] = list()
            self.layer_manager_timer['ftl_layer_queue'][idx] = 0

        self.event_manager_queue['fil_layer_queue'] = dict()
        self.layer_manager_timer['fil_layer_queue'] = dict()
        for idx in range(0, self.opts['fil_cpu']):
            self.event_manager_queue['fil_layer_queue'][idx] = list()
            self.layer_manager_timer['fil_layer_queue'][idx] = 0

        self.event_manager_queue['host_layer_queue'] = dict()
        self.layer_manager_timer['host_layer_queue'] = dict()
        for idx in range(0, self.opts['host_cpu']):
            self.event_manager_queue['host_layer_queue'][idx] = list()
            self.layer_manager_timer['host_layer_queue'][idx] = 0

        self.event_manager_queue['nand_layer_queue'] = dict()
        self.layer_manager_timer['nand_layer_queue'] = dict()
        for idx in range(0, self.opts['die_arch']):
            self.event_manager_queue['nand_layer_queue'][idx] = list()
            self.layer_manager_timer['nand_layer_queue'][idx] = 0

        return
    def get_instance_of_nand_layer(self):
        return self.event_manager_queue['nand_layer_queue'] , self.layer_manager_timer['nand_layer_queue'], 'nand'
    def get_instance_of_fil_layer(self):
        return self.event_manager_queue['fil_layer_queue'], self.layer_manager_timer['fil_layer_queue'], 'fil'
    def get_instance_of_ftl_layer(self):
        return self.event_manager_queue['ftl_layer_queue'], self.layer_manager_timer['ftl_layer_queue'], 'ftl'
    def get_instance_of_hil_layer(self):
        return self.event_manager_queue['hil_layer_queue'], self.layer_manager_timer['hil_layer_queue'] , 'hil'
    def get_instance_of_host_layer(self):
        return self.event_manager_queue['host_layer_queue'], self.layer_manager_timer['host_layer_queue'] ,'host'

    def run(self):
        pool = QThreadPool.globalInstance()

        layer_timer_instance = [
            self.get_instance_of_host_layer,
            self.get_instance_of_hil_layer,
            self.get_instance_of_ftl_layer,
            self.get_instance_of_fil_layer,
            self.get_instance_of_nand_layer
        ]

        for item in layer_timer_instance:
            Event_Manager = evt_worker_manager()
            Event_Manager.set_option_data(evt_worker_manager=item()[0],layer_timer=item()[1],name=item()[2])

            Event_Manager.signals.completed.connect(self.update)
            pool.start(Event_Manager)

        return

    def update(self,n):
        print("completed",n)
        return