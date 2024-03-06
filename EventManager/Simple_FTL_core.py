from EventManager.NAND_operation import NAND_operation as nand_config
from EventManager.FTL_Mapping_operation import FTL_Mapping_operation as FTL_MAP
from EventManager.FTL_GC_operation import FTL_GC_operation as FTL_GC
from EventManager.FTL_Write_operation import FTL_Write_operation as FTL_WRITE
from EventManager.Resource_Manager import Resource_Manager as resource

from EventManager.EventCoreProcess import main_event_core as MainCore
from EventManager.Event import Event as Event

# from EventManager.FTL_BUFFER_operation import FTL_GC_operation as FTL_GC
class Simple_FTL_core():
    main_loop_core = ''
    resource =''
    def __init__(self):
        print('NAND config initialize')
        self.resource = resource().simple_nand_operation()
        # self.main_loop_core = MainCore()
        # self.main_loop_core.start()
        return

    def test(self):
        print("test")
        return

    def write(self,**kwargs):

        loop_manger = self.main_loop_core.get_instance_of_host_layer()[0]
        layer_timer = self.main_loop_core.get_instance_of_host_layer()[1]

        options = dict()
        options['name'] = 'HostWrite'
        options['min_start_time'] = 0
        options['layer_time'] = layer_timer
        options['cur_time'] = kwargs['cur_time']
        options['process_time'] = kwargs['overhead']
        options['event'] = None
        options['event_tracker'] = kwargs['event_tracker']
        options['linkevt'] = FTL_WRITE(options, self.main_loop_core)
        evt_hostwrite = Event(options)
        loop_manger.append(evt_hostwrite)

        print('write operation')
        return

    def read(self,**kwargs):
        print('read operation')
        return

    def flush(self,**kwargs):
        print('flush operation')
        return
