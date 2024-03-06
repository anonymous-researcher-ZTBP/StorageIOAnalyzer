from EventManager.Event import Event
import numpy as np
class NAND_operation(Event):

    NAND_BIT_MAP = ''
    NAND_BLOCK_MAP = ''

    tot_die_num = ''
    die_on_bit_num = ''
    one_die_blk_num = ''
    channel = ''
    cnt_logical_block = ''
    logical_block_list = list()
    channel_info = dict()
    map_table = ''
    lpn_table = ''
    ppn_table = ''


    def map_read_operation(self):
        pass

    def map_write_operation(self):
        pass

    def get_open_block(self):

        pass

    def get_nand_operation(self):

        pass