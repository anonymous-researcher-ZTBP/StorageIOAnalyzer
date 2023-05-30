from PyQt5.QtCore import QThread, pyqtSignal, QObject
from WorkloadtypeDictionary import Workload_type_dictionary as Workload_type

class LoadStorageIOThread(QThread):
    finished_signal = pyqtSignal(list,object)  # signal to indicate thread has finished
    raw_workload_context = ''
    raw_workload_type = ''
    workload_list = ''
    progress_bar = ''
    def __init__(self,workload_list, result_callback,progress_bar,parent=None):
        super().__init__(parent=parent)
        self.workload_list = workload_list
        self.progress_bar = progress_bar
        self.finished_signal.connect(result_callback)

    def set_raw_workload_file(self,workload,workload_type):
        self.raw_workload_context = workload
        self.raw_workload_type = workload_type


    def run(self):
        # thread logic goes here
        # this method will be executed in a separate thread

        # emit signal to indicate thread has finished
        tot_workload_item = list()
        for workload_item in self.workload_list:
            workload_type = workload_item['workload_type']
            workload_context = workload_item['workload_context']
            tot_workload_item += self.parseworkload_command(workload_type,workload_context)[1]
            workload_type = self.parseworkload_command(workload_type,workload_context)[0]

        self.finished_signal.emit(tot_workload_item,workload_type)

    def parseworkload_command(self,workload_type,workload_context):

        if workload_type == 'eBPF':
            Workload_type['ebpf']['Workload_Parcing_logic'].parcing(workload_context,self.progress_bar)
            return Workload_type['ebpf']['Workload_Parcing_logic'].get_workload_context()


