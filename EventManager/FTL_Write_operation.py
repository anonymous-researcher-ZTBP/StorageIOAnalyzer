from EventManager.Event import Event
from EventManager.FTL_Mapping_operation import FTL_Mapping_operation as FTL_MAP_WRITE
class FTL_Write_operation(Event):
    _layer_manager=''
    _options = ''
    def __init__(self,options,layer_mgr):
        super().__init__(self)
        self.child_method_operation = self.FTL_write
        self._options = options
        self._layer_manager = layer_mgr
        return

    def FTL_write(self):
        #Map Update
        self.map_update_operation()
        # check_gc_operation
        self.check_gc_operation()
        #block_close_erase
        self.block_close_erase()
        #set_open_block
        self.set_open_block()

        return
    def map_update_operation(self):
        options = dict()
        options['name'] = 'ftl_map_update'
        options['min_start_time'] = 0
        options['layer_time'] = self._layer_manager.get_instance_of_ftl_layer()[1]
        options['cur_time'] = self._options['cur_time']
        options['process_time'] = self._options['overhead']
        options['event'] = None
        options['event_tracker'] = self._options['event_tracker']
        options['linkevt'] = None
        self._layer_manager.get_instance_of_ftl_layer()[0].append(FTL_MAP_WRITE(self._options))

        return
    def block_close_erase(self):
        pass

    def set_open_block(self):
        pass

    def check_gc_operation(self):
        pass

