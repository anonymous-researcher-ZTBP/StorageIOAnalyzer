import numpy as np

class Resource_Manager:

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
    def __init__(self):
        return

    def initialize(self):
        self.simple_nand_operation()
        self.map_lpn_ppn_table()
        return

    def map_lpn_ppn_table(self):
        self.lpn_table = np.array(self.tot_die_num * self.die_on_bit_num)
        self.ppn_table = np.array(self.tot_die_num * self.die_on_bit_num)

    def set_lpn_ppn_table(self, ppn_index, lpn_index):
        self.lpn_table[lpn_index] = ppn_index
        self.ppn_table[ppn_index] = lpn_index

    def get_global_resource(self):
        return
    def simple_nand_operation(self):
        # 512Gbit 64Gbytes
        self.tot_die_num = 4096 // 64
        self.die_on_bit_num = 64 * 1024 * 1024 // 4
        self.one_die_blk_num = 64 * 1024 // 96
        self.channel = 16
        self.cnt_logical_block = 5461

        self.NAND_BIT_MAP = np.zeros((self.tot_die_num, self.die_on_bit_num))
        self.NAND_BLOCK_MAP = np.zeros((self.tot_die_num, self.one_die_blk_num))

        logic_block_die_range = 8
        logic_block_size = 96 * logic_block_die_range
        logic_block_bit = 96 * 1024 // 4
        logic_tot_block_bit = logic_block_size * 1024 // 4
        nand_bit_dict = np.zeros((self.tot_die_num, 1))
        logic_tot_bit = 0

        for idx in range(self.channel):
            try:
                self.channel_info[idx].append(self.tot_die_num // self.channel)
            except:
                self.channel_info[idx] = list()
                self.channel_info[idx].append(self.tot_die_num // self.channel)

        for i in range(self.cnt_logical_block):
            bit_map_dict = dict()
            cnt_die = 0

            for die in range(0, len(nand_bit_dict)):
                if nand_bit_dict[die] >= self.die_on_bit_num:
                    continue
                start_bit = int(nand_bit_dict[die])
                nand_bit_dict[die] += logic_block_bit
                end_bit = int(nand_bit_dict[die])
                bit_map_dict[die] = self.NAND_BIT_MAP[die][start_bit:end_bit]
                logic_tot_bit += logic_block_bit
                cnt_die += 1
                if logic_tot_bit >= logic_tot_block_bit:
                    print(cnt_die)
                    logical_block_info = {
                        # block_bit_map
                        'block_bit_map': bit_map_dict,
                        # block_erase_count
                        'block_erase_count': 0,
                        # block_nand_read_count
                        'block_nand_read_count': 0,
                        # nand_block_read_count
                        'nand_block_read_count': 0,
                        'erased_block': False,
                        'block_closed': 0,
                        'logical_block_index': i,
                        'user_block': 1 if (i > 30 & i < 5000) else 0,
                        'op_block': 1 if (i > 5000) else 0,
                        'sys_block': 1 if (i < 30) else 0,
                    }
                    self.logical_block_list.append(logical_block_info)
                    logic_tot_bit = 0
                    cnt_die = 0
                    break

        return