from EventManager.NAND_operation import NAND_operation as nand_op
from EventManager.FTL_Write_operation import FTL_Write_operation as FTL_WRITE
from EventManager.Event import Event
class FTL_GC_operation(Event):

    opts=dict()

    def __init__(self, *args,**kwargs):
        self.set_initial_condition(kwargs)
        return

    def set_initial_condition(self,kwargs):
        self.opts['trigger_freeblock'] = kwargs['trigger_freeblock']
        self.opts['victim_ratio'] = kwargs['victim_ratio']

    def gc_enable_or_not(self):
        #freeblock
        free_block = nand_op.logical_block_list()
        if self.opts['trigger_freeblock'] >= free_block:
            #gc_trigger
            self.gc_trigger()

        return

    def swl_enable_or_not(self):


        return

    def gc_trigger(self):

        while(1):
            free_block = nand_op.logical_block_list()
            if self.opts['trigger_freeblock'] <= free_block:
                break

            block_list=self.select_victim_block()
            for idx in range(0,len(block_list)):
                FTL_WRITE(block_list)
                #FTL write operation event trigger


    def select_victim_block(self):
        victim_block_list = list()

        for block_idx in range(0,len(nand_op.logical_block_list)):
            if nand_op.logical_block_list[block_idx]['block_closed'] == 1:
                if nand_op.logical_block_list[block_idx]['block_bit_ratio'] < 50:
                    victim_block_list(nand_op.logical_block_list[block_idx])

        return victim_block_list


