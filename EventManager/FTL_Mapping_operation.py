import numpy as np
from EventManager.NAND_operation import NAND_operation as nand_op
from EventManager.Event import Event
class FTL_Mapping_operation(Event):

    ppn_map_buffer_on_read_buffer = np.array(1)
    lpn_map_buffer_on_write_buffer = dict()
    def __init__(self):
        super().__init__(self)
        return

    def check_on_map_write_buffer(self,lpn,ppn):
        if lpn in self.lpn_map_buffer_on_write_buffer.keys():
            self.lpn_map_buffer_on_write_buffer[lpn] = ppn
        else:
            self.lpn_map_buffer_on_write_buffer[lpn] = ppn
        if len(self.lpn_map_buffer_on_write_buffer) == 32768:
            return True
        else:
            return False
    def map_write(self,lpn,ppn):
        #check map dram on map
        if not self.check_on_map_write_buffer(lpn,ppn):
            self.nand_map_write_operation()
        else:
            print('on buffer modifying')
        return

    def check_on_map_read_buffer(self,lpn):
        try:
            return self.get_ppn_map_buffer_on_read_buffer[lpn]
        except:
            return None
    def map_read(self,lpn):
        #check on map dram
        ppn = self.check_on_map_read_buffer(lpn)
        if ppn is None:
            self.nand_map_read_operation(lpn)
        else:
            return ppn

    def nand_map_write_operation(self):
        nand_op.map_write_operation()
        return

    def nand_map_read_operation(self,lpn):
        nand_op.map_read_operation()

        nand_block_and_bit = 96*1024//4
        np.delete(self.ppn_map_buffer_on_read_buffer,range(len(self.ppn_map_buffer_on_read_buffer)-nand_block_and_bit,len(self.ppn_map_buffer_on_read_buffer)) )
        np.insert(self.ppn_map_buffer_on_read_buffer,self.get_range_of_map_data(lpn))
        self.ppn_map_buffer_on_read_buffer
        return
    def get_range_of_map_data(self,lpn):
        nand_block_and_bit = 96 * 1024 // 4
        temp = np.array(nand_block_and_bit)
        return temp
    def map_update_operation(self):
        return

    def map_search_operation(self):
        return

    def map_gc_operation(self):
        return

    def map_erase_operation(self):
        return
