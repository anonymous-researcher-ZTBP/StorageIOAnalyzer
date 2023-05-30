import PyQt5.QtGui as designer
from PyQt5.QtCore import Qt
# for parcing and load ebpf type storage IO analysis
import datetime
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import datetime as dt

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler

class SimulationStorageIOType:
    main_workload_context = list()
    workload_label = ''
    opts = dict()

    def __init__(self):
        self.main_workload_context.clear()
        self.workload_label = 'SimulationStorageIOType workload'

    def parcing(self,raw_data=list()):
        return raw_data

    def get_workload_context(self):
        return self,self.main_workload_context

    def get_typeof_symbol(self,cmd):
        col_sym = {
            0x01:{
                'Color':'b',
                'CMDQ_Color':(0,255,255,75),
                'Symbol':'o',
                'NAME':'READ(1)'
            },
            0x10:{
                'Color':'r',
                'CMDQ_Color': (255, 160, 122, 75),
                'Symbol':'t',
                'NAME':'WRITE(10)'
            },
            0x02: {
                'Color': 'c',
                'Symbol': 't',
                'NAME': 'TEST01'
            },
            0x03: {
                'Color': '#800000',
                'Symbol': 't',
                'NAME': 'TEST02'
            },
            0x04: {
                'Color': '#A52A2A',
                'Symbol': 't',
                'NAME': 'TEST03'
            },
            0x9901: {
                'Color': 'r',
                'CMDQ_Color': (153, 255,51, 100),
                'Symbol': 't',
                'NAME': 'tR'
            },
            0x9902: {
                'Color': 'g',
                'CMDQ_Color': (255, 255, 153, 100),
                'Symbol': 't',
                'NAME': 'D.Out'
            },
            0x9903: {
                'Color': 'b',
                'CMDQ_Color': (255, 255, 153, 75),
                'Symbol': 't',
                'NAME': 'D.In'
            },
            0x9904: {
                'Color': 'r',
                'CMDQ_Color': (255, 51, 51, 75),
                'Symbol': 't',
                'NAME': 'tProgo'
            },
            0x9950:{
                'Color': 'r',
                'CMDQ_Color': (50, 51, 51, 75),
                'Symbol': 't',
                'NAME': 'DRAM-LD'
            },
            0x9951: {
                'Color': 'r',
                'CMDQ_Color': (60, 51, 51, 75),
                'Symbol': 't',
                'NAME': 'dram cache hit'
            },
            0x9952: {
                'Color': 'r',
                'CMDQ_Color': (70, 51, 51, 75),
                'Symbol': 't',
                'NAME': 'insert dram cache'
            },
            0x9953: {
                'Color': 'r',
                'CMDQ_Color': (80, 51, 51, 75),
                'Symbol': 't',
                'NAME': 'evict dram cache'
            },

            0x9970: {
                'Color': 'r',
                'CMDQ_Color': (50, 51, 100, 75),
                'Symbol': 't',
                'NAME': 'SRAM-LD'
            },
            0x9971: {
                'Color': 'r',
                'CMDQ_Color': (60, 51, 120, 75),
                'Symbol': 't',
                'NAME': 'SRAM cache hit'
            },
            0x9972: {
                'Color': 'r',
                'CMDQ_Color': (70, 51, 130, 75),
                'Symbol': 't',
                'NAME': 'insert sram cache'
            },
            0x9973: {
                'Color': 'r',
                'CMDQ_Color': (80, 51, 150, 75),
                'Symbol': 't',
                'NAME': 'evict sram cache'
            },
        }
        return col_sym[cmd]


class SimulationStorageIOThread(QThread):
    main_workload_context = dict()
    workload_label = ''
    opts = dict()
    finished_signal = pyqtSignal(list,dict,str)
    file_name = ''
    status_bar =''
    global_simple_nand_config = dict()
    init_buffer = 0

    die_allocation_unit = dict()
    plane_allocation_unit = dict()

    locking_write_buffer = (int,int)
    baseworkload = ''

    cpu_cache_list = list()
    try:
        dram_cache_list = np.array([])
    except:
        dram_cache_list = list()


    cpu_cahce_hit = 0
    dram_cache_hit = 0

    cpu_cache_timer = 0
    cpu_cahce_event_tracker = list()
    dram_cache_timer = 0
    dram_cahce_event_tracker = list()

    history_on_cpu_cache_list = list()
    history_on_dram_cache_list = list()

    die_event_tracker = dict()
    plane_event_tracker = dict()
    logic_event_tracker = dict()
    tot_cahce_hit =0
    # signal to indicate thread has finished
    def __init__(self,result_callback,status_bar,parent=None):
        super().__init__(parent=parent)
        self.opts = {
            'mem_access_arch':None,
            'num_cpu':None,
            'sram_bandwidth':None,
            'sram_size':None,
            'sram_latency':None,
            'sram_page_units': None,

            'dram_page_fault_policy':None,
            'dram_bandwidth':None,
            'dram_latency':None,
            'dram_size':None,
            'dram_page_units': None,
        }
        self.global_simple_nand_config = {
            't_Dout': 7,
            't_DIn': 7 * 48,
            # 'write_buffer': 2304 ,
            'write_buffer': 2304,
            'buffing_overhead': 20,
            'cur_prog_nand_num': 0,
            'num_die': 32,
            'num_plane': 4,
            'flush_units': 192 * 4,
            'oneshot_units': 192,
        }

        self.status_bar = status_bar
        self.finished_signal.connect(result_callback)

        self.init_buffer = self.global_simple_nand_config['write_buffer']
        self.locking_write_buffer = list()

        self.cpu_cache_timer = 0
        self.cpu_cahce_event_tracker.clear()
        self.dram_cache_timer = 0
        self.dram_cahce_event_tracker.clear()

        self.history_on_cpu_cache_list.clear()
        self.history_on_dram_cache_list.clear()

        self.tot_cahce_hit = 0

    def run(self):
        self.run_generate_workload()
        self.finished_signal.emit(self.main_workload_context,self.logic_event_tracker,self.file_name)
        return

    def setData(self,**kwargs):

        self.opts['workload_quantity']=int(kwargs['workload_quantity'])
        self.opts['idle_duration'] = kwargs['idle_duration']
        self.opts['idle_time'] = kwargs['idle_time']

        self.opts['mixed_ratio'] = int(kwargs['mixed_ratio'])
        self.opts['max_queue'] = kwargs['max_queue']
        self.opts['read_distribution'] = kwargs['read_distribution']
        self.opts['read_block_size'] = kwargs['read_block_size']
        self.opts['write_distribution'] = kwargs['write_distribution']

        self.opts['write_block_size'] = kwargs['write_block_size']
        self.opts['host_if'] = kwargs['host_if']
        self.opts['host_interval'] = kwargs['host_interval']
        self.opts['host_worker'] = kwargs['host_worker']
        self.opts['context_id'] = kwargs['context_id']
        self.opts['context_line'] = kwargs['context_line']

        self.opts['mem_access_arch'] = kwargs['mem_access_arch']
        self.opts['num_cpu'] = kwargs['num_cpu']
        self.opts['sram_bandwidth'] = kwargs['sram_bandwidth']
        self.opts['sram_size'] = kwargs['sram_size']
        self.opts['sram_latency'] = kwargs['sram_latency']
        self.opts['sram_page_units'] = kwargs['sram_page_units']
        self.opts['cpu_cache_policy'] = kwargs['cpu_page_fault_policy']

        self.opts['dram_page_fault_policy'] = kwargs['dram_page_fault_policy']
        self.opts['dram_bandwidth'] = kwargs['dram_bandwidth']
        self.opts['dram_latency'] = kwargs['dram_latency']
        self.opts['dram_size'] = kwargs['dram_size']*1024
        self.opts['dram_page_units'] = kwargs['dram_page_units']

        self.opts['cpu_host_interval'] = 1*0.001
        self.opts['address_range'] = kwargs['address_range']

        # self.opts['name'] = kwargs['name']
        return

    def check_nand_program(self,cur_time,die_num,die_access_control,overhead,workload,write_unit,end_time):
        if write_unit == (self.global_simple_nand_config['flush_units'] // self.global_simple_nand_config['oneshot_units'])-1:
            program_overhead = end_time-cur_time+4
            self.locking_write_buffer.append((end_time,self.global_simple_nand_config['flush_units']))

            if self.global_simple_nand_config['write_buffer'] <=0:
                return end_time # 4u each program latency
            else:
                return cur_time + self.global_simple_nand_config['buffing_overhead']

        t_In = self.global_simple_nand_config['t_DIn']/3

        if self.global_simple_nand_config['write_buffer'] % self.global_simple_nand_config['flush_units'] == 0 : #flush
            workload['etc'] = 'buffering on flush'
            if die_num == -1:
                die_num = self.global_simple_nand_config['cur_prog_nand_num'] #init for die operation

            if end_time !=-1:
                old_end_time = end_time

            if cur_time > die_access_control[die_num]:
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': cur_time, 'end_time': cur_time + t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': cur_time + t_In, 'end_time': cur_time + 2*t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': cur_time + 2*t_In, 'end_time': cur_time + 3*t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9904, 'start_time': cur_time + 3*t_In, 'end_time': cur_time + 3*t_In+overhead})
                die_access_control[die_num] = cur_time + 3*t_In+overhead + 2
            else:
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': die_access_control[die_num], 'end_time': die_access_control[die_num] + t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': die_access_control[die_num] + t_In, 'end_time': die_access_control[die_num] + 2*t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9903, 'start_time': die_access_control[die_num] + 2*t_In, 'end_time': die_access_control[die_num] + 3*t_In})
                self.die_event_tracker[die_num].append({'cmd': 0x9904, 'start_time': die_access_control[die_num] + 3*t_In, 'end_time': die_access_control[die_num] + 3*t_In+overhead})
                die_access_control[die_num] = die_access_control[die_num] +3*t_In +overhead + 2

            end_time = die_access_control[die_num]
            try:
                if old_end_time > end_time:
                    end_time = old_end_time #last end_time operation
            except:
                None

            die_num = die_num + 1
            if die_num not in self.die_event_tracker:
                die_num = list(self.die_event_tracker.keys())[0]
            self.global_simple_nand_config['cur_prog_nand_num'] = die_num

            write_unit = write_unit + 1

            return self.check_nand_program(cur_time+1,die_num,die_access_control,overhead,workload,write_unit,end_time)

        elif self.global_simple_nand_config['write_buffer'] > 0 :

            self.locking_write_buffer.append((cur_time+self.global_simple_nand_config['buffing_overhead'], workload['length']/1024))
            return cur_time+self.global_simple_nand_config['buffing_overhead'] # buffer is not full
        else:
            while(1):
                # workload['etc'] = 'buffered delayed'
                workload['etc'] = 'Delayed on buffer'
                cur_time = cur_time + 1
                for item in self.locking_write_buffer[:]:
                    if cur_time >= item[0]:
                        self.global_simple_nand_config['write_buffer'] = self.global_simple_nand_config['write_buffer'] + item[1]
                        self.locking_write_buffer.remove(item)

                if self.global_simple_nand_config['write_buffer'] > workload['length']/1024:
                    self.locking_write_buffer.append((cur_time + self.global_simple_nand_config['buffing_overhead'], workload['length'] / 1024))
                    return cur_time + self.global_simple_nand_config['buffing_overhead']


    def check_and_overhead_add(self,cur_time,die_access_control=dict(),die_num=int,overhead=int,workload=dict(),write_unit=int):

        t_Dout = self.global_simple_nand_config['t_Dout']
        t_In = self.global_simple_nand_config['t_DIn']

        if workload['cmd'] == 0x1:  # read
            if cur_time > die_access_control[die_num]:
                self.die_event_tracker[die_num].append({'cmd': 0x9901, 'start_time': cur_time,'end_time': cur_time + (overhead-t_Dout) })
                self.die_event_tracker[die_num].append({'cmd': 0x9902, 'start_time': cur_time + (overhead-t_Dout), 'end_time': cur_time + overhead })
                die_access_control[die_num] = cur_time + overhead + 2
                # workload['etc'] = ''
                return overhead + 2

            else:
                self.die_event_tracker[die_num].append({'cmd': 0x9901, 'start_time': die_access_control[die_num],'end_time': die_access_control[die_num] + (overhead-t_Dout) })
                self.die_event_tracker[die_num].append({'cmd': 0x9902, 'start_time': die_access_control[die_num] +(overhead-t_Dout), 'end_time': die_access_control[die_num] + overhead })
                die_access_control[die_num] = die_access_control[die_num] + overhead + 2
                workload['etc'] = 'Die#' + str(die_num) + ': Collision'
                return die_access_control[die_num] - cur_time + 2

        elif workload['cmd'] == 0x10:
            # workload['etc'] = ''
            write_bffer=self.global_simple_nand_config['write_buffer']

            #free
            for item in self.locking_write_buffer[:]:
                if cur_time >=  item[0]:
                    self.global_simple_nand_config['write_buffer'] = write_bffer + item[1]
                    self.locking_write_buffer.remove(item)

            self.global_simple_nand_config['write_buffer'] = write_bffer - workload['length'] / 1024
            cmd_latency = self.check_nand_program(cur_time, -1, die_access_control, overhead, workload, -1, -1)

            return cmd_latency-cur_time

    def set_base_workload(self,workload):
        self.baseworkload = workload

    def check_cpu_cache(self,offset,cur_time):
        if len(self.cpu_cache_list) == 0:
            return False
        try:
            for cache_item in self.cpu_cache_list:
                if cache_item[0] == offset:
                    cpu_host_interval = self.opts['sram_latency'] * 0.001
                    self.cpu_cache_timer = cur_time + cpu_host_interval
                    self.cpu_cahce_event_tracker.append({'cmd': 0x9970, 'start_time': cur_time, 'end_time': cur_time + cpu_host_interval})
                    return True
        except:
            if offset in self.cpu_cache_list:
                cpu_host_interval = self.opts['sram_latency'] * 0.001
                self.cpu_cache_timer = cur_time + cpu_host_interval
                self.cpu_cahce_event_tracker.append({'cmd': 0x9970, 'start_time': cur_time, 'end_time': cur_time + cpu_host_interval})
                return True
            else:
                return False

        return False
    def cur_dram_cache_list(self,cur_time):

        self.history_on_dram_cache_list=sorted(self.history_on_dram_cache_list)

        for histor_dram_item in self.history_on_dram_cache_list[:]:
            end_time = histor_dram_item[0]
            workload_item = dict()
            if end_time > cur_time:
                break
            try:
                workload_item['offset'] = histor_dram_item[1][0]
                workload_item['cluster'] = histor_dram_item[1][1]
            except:
                workload_item['offset'] = histor_dram_item[1]
            if end_time <= cur_time:
                if len(self.dram_cache_list) != 0:
                    try:
                        if workload_item['cluster'] == 1 or workload_item['cluster'] == 2:
                            self.dram_cache_list.insert(0, (workload_item['offset'], workload_item['cluster']))
                    except:
                        self.dram_cache_list.insert(0, workload_item['offset'])
                    self.dram_cahce_event_tracker.append(
                        {'cmd': 0x9952, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert dram cache'})
                else:
                    try:
                        if workload_item['cluster'] == 1 or workload_item['cluster'] == 2:
                            self.dram_cache_list.insert(0, (workload_item['offset'], workload_item['cluster']))
                    except:
                        self.dram_cache_list.insert(0, workload_item['offset'])
                    # self.history_on_dram_cache_list.append((end_time, self.dram_cache_list))
                    self.dram_cahce_event_tracker.append(
                        {'cmd': 0x9952, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert dram cache'})

                dram_cache_max_size = self.opts['dram_size'] // self.opts['dram_page_units']
                if len(self.dram_cache_list) > dram_cache_max_size:
                    while (1):
                        if len(self.dram_cache_list) == dram_cache_max_size:
                            break
                        else:
                            try:
                                flag_pop = False
                                for item in self.dram_cache_list[::-1]:
                                    if item[1] == -1:
                                        self.dram_cache_list.pop(self.dram_cache_list.index(item))
                                        flag_pop = True
                                        break
                                if flag_pop == False:
                                    self.dram_cache_list.pop(len(self.dram_cache_list) - 1)
                            except:
                                self.dram_cache_list.pop(len(self.dram_cache_list) - 1)
                            self.dram_cahce_event_tracker.append(
                                {'cmd': 0x9953, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'evict dram cache'})

                self.history_on_dram_cache_list.remove(histor_dram_item)

    def check_dram_cache(self,offset,cur_time):

        # self.cur_dram_cache_list(cur_time)

        if len(self.dram_cache_list) == 0:
            return False
        try:
            for cache_item in self.dram_cache_list:
                if cache_item[0] == offset:
                    cpu_host_interval = self.opts['dram_latency'] * 0.001
                    if cur_time > self.dram_cache_timer:
                        self.dram_cache_timer = cur_time + cpu_host_interval
                        self.dram_cahce_event_tracker.append({'cmd': 0x9950, 'start_time': cur_time, 'end_time': self.dram_cache_timer})
                    else:
                        self.dram_cache_timer = self.dram_cache_timer + cpu_host_interval + cpu_host_interval
                        self.dram_cahce_event_tracker.append({'cmd': 0x9950, 'start_time': self.dram_cache_timer, 'end_time': self.dram_cache_timer-cpu_host_interval})
                    return True
        except:
            try:
                try:
                    if np.where(self.dram_cache_list==offset)[0][0]:
                        dram_host_interval = self.opts['dram_latency'] * 0.001
                        self.dram_cache_timer = cur_time + dram_host_interval
                        self.dram_cahce_event_tracker.append({'cmd': 0x9950, 'start_time': cur_time, 'end_time': cur_time + dram_host_interval})
                        return True
                except:
                    return False
            except:
                if offset in self.dram_cache_list:
                    dram_host_interval = self.opts['dram_latency'] * 0.001
                    self.dram_cache_timer = cur_time + dram_host_interval
                    self.dram_cahce_event_tracker.append({'cmd': 0x9950, 'start_time': cur_time, 'end_time': cur_time + dram_host_interval})
                    return True
                else:
                    return False

        return False

    def check_page_in_cache(self,workload_item,cur_time):

        # self.cpu_cache_list, self.dram_cache_list = self.history_current_cache_list_check(cur_time)

        if self.check_cpu_cache(workload_item['offset'],cur_time):
            self.cpu_cahce_hit += 1
            return True


        if self.check_dram_cache(workload_item['offset'],cur_time):
            self.dram_cache_hit += 1
            return True

        return False

    def history_current_cache_list_check(self,cur_time):
        last_cpu_cache_list = list()
        last_dram_cache_list = list()

        self.history_on_cpu_cache_list = sorted(self.history_on_cpu_cache_list)
        self.history_on_dram_cache_list = sorted(self.history_on_dram_cache_list)

        for item in self.history_on_cpu_cache_list[:]:
            if (item[0] < cur_time):
                last_cpu_cache_list = item[1]
                self.history_on_cpu_cache_list.remove(item)

        if len(last_cpu_cache_list) > 0:
            self.history_on_cpu_cache_list.append((cur_time,last_cpu_cache_list))

        for item in self.history_on_dram_cache_list[:]:
            if (item[0] < cur_time):
                last_dram_cache_list = item[1]
                self.history_on_dram_cache_list.remove(item)

        if len(last_dram_cache_list) > 0:
            self.history_on_dram_cache_list.append((cur_time,last_cpu_cache_list))

        return last_cpu_cache_list,last_dram_cache_list

    def history_end_cache_list_check(self,end_time,workload_item):

        last_cpu_cache_list = list()
        last_dram_cache_list = list()

        self.history_on_cpu_cache_list = sorted(self.history_on_cpu_cache_list)
        self.history_on_dram_cache_list = sorted(self.history_on_dram_cache_list)

        for item in self.history_on_cpu_cache_list[:]:
            # if ( item[0] < cur_time ) & ( not workload_item['offset'] in item[1] ):
            if (item[0] < end_time):
                for idx in item[1][::-1]:
                    last_cpu_cache_list.insert(0,idx)
                self.history_on_cpu_cache_list.remove(item)
        if len(last_cpu_cache_list) > 0:
            self.history_on_cpu_cache_list.append((end_time,last_cpu_cache_list))

        for item in self.history_on_dram_cache_list[:]:
            # if ( item[0] < cur_time ) & ( not workload_item['offset'] in item[1] ):
            if (item[0] < end_time):
                for idx in item[1][::-1]:
                    last_dram_cache_list.insert(0,idx)
                self.history_on_dram_cache_list.remove(item)
        if len(last_dram_cache_list) > 0:
            self.history_on_dram_cache_list.append((end_time, last_dram_cache_list))

        return last_cpu_cache_list,last_dram_cache_list

    # def append_cache_workload(self,workload_item,end_time):
    #     #LRU
    #     # self.cpu_cache_list,self.dram_cache_list = self.history_current_cache_list_check(end_time)
    #
    #     if self.opts['cpu_cache_policy'] == 'LRU':
    #         if len(self.cpu_cache_list) != 0:
    #             try:
    #                 self.cpu_cache_list.insert(0,(workload_item['offset'],workload_item['cluster']))
    #             except:
    #                 self.cpu_cache_list.insert(0, workload_item['offset'])
    #
    #             # self.history_end_cache_list_check(end_time,workload_item)
    #             # self.history_on_cpu_cache_list.append((end_time, self.cpu_cache_list))
    #             self.cpu_cahce_event_tracker.append({'cmd': 0x9972, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert cpu cache'})
    #         else:
    #             try:
    #                 self.cpu_cache_list.insert(0, (workload_item['offset'],workload_item['cluster']))
    #             except:
    #                 self.cpu_cache_list.insert(0,  workload_item['offset'])
    #             self.history_on_cpu_cache_list.append((end_time, self.cpu_cache_list))
    #             self.cpu_cahce_event_tracker.append({'cmd': 0x9972, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert cpu cache'})
    #
    #         cpu_cache_max_size = self.opts['sram_size'] // self.opts['sram_page_units']
    #         if len(self.cpu_cache_list) > cpu_cache_max_size :
    #             while(1):
    #                 if len(self.cpu_cache_list) == cpu_cache_max_size :
    #                     break
    #                 else:
    #                     try:
    #                         flag_pop = False
    #                         for item in self.cpu_cache_list[::-1]:
    #                             if item[1] == -1:
    #                                 self.cpu_cache_list.pop(self.cpu_cache_list.index(item))
    #                                 flag_pop = True
    #                                 break
    #                         if flag_pop == False:
    #                             self.cpu_cache_list.pop(len(self.cpu_cache_list) - 1)
    #                     except:
    #                         self.cpu_cache_list.pop(len(self.cpu_cache_list) - 1)
    #                     self.cpu_cahce_event_tracker.append({'cmd': 0x9973, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'evict cpu cache'})
    #                     # self.history_on_cpu_cache_list.append((end_time, self.cpu_cache_list))
    #                     # print('evict the last one')
    #
    #     if self.opts['dram_page_fault_policy'] == 'LRU':
    #         # try:
    #         #     self.history_on_dram_cache_list.append((end_time, (workload_item['offset'],workload_item['cluster'])))
    #         # except:
    #         #     self.history_on_dram_cache_list.append((end_time, workload_item['offset']))
    #
    #         self.dram_cahce_event_tracker.append({'cmd': 0x9952, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert dram cache'})


    def run_generate_workload(self):
        #init_time us
        last_time_list = list()
        last_start_time_list = -1
        cmdq_list=[0]*self.opts['max_queue']
        max_complete_time = -1

        self.cpu_cahce_hit = 0
        self.dram_cache_hit = 0

        try:
            self.dram_cache_list.clear()
        except:
            self.dram_cache_list = np.array([])
        self.cpu_cache_list.clear()

        self.file_name = 'MQ['+str(self.opts['max_queue'])+']_'

        tot_die = self.global_simple_nand_config['num_die']
        tot_plane = self.global_simple_nand_config['num_plane']

        for i in range(0,tot_die):
            self.die_allocation_unit[i] = -1
            self.die_event_tracker[i] = list()

        for i in range(0, tot_die):
            self.plane_event_tracker[i] = dict()
            for idx_plane in range(0, tot_plane):
                self.plane_event_tracker[i][idx_plane] = list()

        self.logic_event_tracker['die'] = self.die_event_tracker
        self.logic_event_tracker['plane'] = self.plane_event_tracker
        self.logic_event_tracker['sram'] = self.cpu_cahce_event_tracker
        self.logic_event_tracker['dram'] = self.dram_cahce_event_tracker


        self.file_name += '' + str(self.opts['address_range']) + 'TB_'
        try:
            self.file_name += 'Pattern[' + str(self.opts['pattern_workload_idx']['name']) + ']_'
        except:
            None
        self.file_name += str(dt.datetime.now())

        #cache store

        dram_cache_max_size = self.opts['dram_size'] // self.opts['dram_page_units']
        sram_cache_max_size = self.opts['sram_size'] // self.opts['sram_page_units']

        raw_item = ''

        for number in range(1000):
            if raw_item !='':
                self.baseworkload = raw_item

            cluster_list = [0,1,2,3,4]

            for workload_item in self.baseworkload:
                if len(self.dram_cache_list) > dram_cache_max_size:
                    try:
                        self.dram_cache_list = np.delete(self.dram_cache_list, [len(self.dram_cache_list) - 1])
                    except:
                        del self.dram_cache_list[len(self.dram_cache_list) - 1]
                else:
                    try:
                        if workload_item['cluster'] in cluster_list:
                            # self.dram_cache_list.insert(0,(workload_item['offset'],workload_item['cluster']))
                            try:
                                try:
                                    if np.where(self.dram_cache_list == workload_item['offset'])[0][0]:
                                        index_pop = np.where(self.dram_cache_list == workload_item['offset'])
                                        self.dram_cache_list = np.delete(self.dram_cache_list, [index_pop])
                                except:
                                    None
                                self.dram_cache_list = np.insert(self.dram_cache_list,0,workload_item['offset'])
                            except:
                                if workload_item['offset'] in self.dram_cache_list:
                                    self.dram_cache_list.pop(self.dram_cache_list.index(workload_item['offset']))
                                self.dram_cache_list.insert(0, workload_item['offset'])
                    except:
                        try:
                            try:
                                if np.where(self.dram_cache_list==workload_item['offset'])[0][0]:
                                    index_pop = np.where(self.dram_cache_list == workload_item['offset'])
                                    self.dram_cache_list = np.delete(self.dram_cache_list,[index_pop])
                            except:
                                None
                            self.dram_cache_list = np.insert(self.dram_cache_list,0,workload_item['offset'])
                        except:
                            if workload_item['offset'] in self.dram_cache_list:
                                self.dram_cache_list.pop(self.dram_cache_list.index(workload_item['offset']))
                            self.dram_cache_list.insert(0, workload_item['offset'])

                if len(self.cpu_cache_list) > sram_cache_max_size:
                    del self.cpu_cache_list[len(self.cpu_cache_list)-1]
                else:
                    try:
                        if workload_item['cluster'] in cluster_list:
                            # self.cpu_cache_list.insert(0,(workload_item['offset'],workload_item['cluster']))
                            if workload_item['offset'] in self.cpu_cache_list:
                                self.cpu_cache_list.pop(self.cpu_cache_list.index(workload_item['offset']))
                            self.cpu_cache_list.insert(0, workload_item['offset'])
                    except:
                        if workload_item['offset'] in self.cpu_cache_list:
                            self.cpu_cache_list.pop(self.cpu_cache_list.index(workload_item['offset']))
                        self.cpu_cache_list.insert(0, workload_item['offset'])

            raw_item=self.do_create_base_workload()

            if self.opts['mem_access_arch'] == 'NUMA':
                temp_list = list()
                for idx in range(0, len(raw_item)):
                    temp_list.append([raw_item[idx]['time'], raw_item[idx]['offset']])
                scaler = StandardScaler()
                scale_data = scaler.fit_transform(temp_list)

                val_eps = 0.05
                val_min_samples = 20

                dbscan = DBSCAN(eps=val_eps, min_samples=val_min_samples)
                clusters = dbscan.fit_predict(scale_data)
                clusters_group_offset = dict()
                for i in range(scale_data.shape[0]):
                    if clusters[i] == -1:
                        raw_item[i]['cluster'] = clusters[i]
                    if not clusters[i] in clusters_group_offset.keys():
                        clusters_group_offset[clusters[i]] = [int(raw_item[i]['offset'])]
                    else:
                        clusters_group_offset[clusters[i]].append(int(raw_item[i]['offset']))

                import collections
                temp=collections.OrderedDict(sorted(clusters_group_offset.items()))
                del temp[-1]
                temp_key = list(temp.keys())
                for i in range(0,len(temp_key)):
                    for j in range(1,len(temp_key)):
                        if temp[i][0] > temp[j][0]:
                            temp[i],temp[j] = temp[j],temp[i]

                for i in temp.keys():
                    temp[i] = np.median(temp[i])

                for item_raw in raw_item[:]:
                    if not 'cluster' in item_raw:
                        index_list = list()
                        for i in temp.keys():
                            index_list.append(np.abs(item_raw['offset']-temp[i]))
                        item_raw['cluster'] = list(temp.keys())[index_list.index(np.min(index_list))]

                # for i in range(scale_data.shape[0]):
                #     raw_item[i]['cluster'] = clusters[i]
                # raw_item = sorted(raw_item, key=lambda x: x['time'])
            self.main_workload_context = raw_item
            self.status_bar.setValue(100)

            if self.opts['mem_access_arch'] == 'NUMA':
                print(number,'dram len:' + str(len(self.dram_cache_list)),'cluster_list:'+str(cluster_list),str(self.logic_event_tracker['hit_ratio']))
            else:
                print(number, 'dram len:' + str(len(self.dram_cache_list)), 'LRU',str(self.logic_event_tracker['hit_ratio']))

        # rsponse latency calculation..
        self.rsp_latency_calculation()

        return

    def do_create_base_workload(self):
        base_current_time = 0
        raw_item = list()
        last_time_list = list()
        last_start_time_list = -1
        cmdq_list = [0] * self.opts['max_queue']
        max_complete_time = -1

        self.cpu_cahce_hit = 0
        self.dram_cache_hit = 0

        self.file_name = 'MQ[' + str(self.opts['max_queue']) + ']_'

        tot_die = self.global_simple_nand_config['num_die']
        tot_plane = self.global_simple_nand_config['num_plane']

        for i in range(0, tot_die):
            self.die_allocation_unit[i] = -1
            self.die_event_tracker[i] = list()

        for i in range(0, tot_die):
            self.plane_event_tracker[i] = dict()
            for idx_plane in range(0, tot_plane):
                self.plane_event_tracker[i][idx_plane] = list()

        self.cpu_cahce_event_tracker.clear()
        self.dram_cahce_event_tracker.clear()
        self.logic_event_tracker['die'] = self.die_event_tracker
        self.logic_event_tracker['plane'] = self.plane_event_tracker
        self.logic_event_tracker['sram'] = self.cpu_cahce_event_tracker
        self.logic_event_tracker['dram'] = self.dram_cahce_event_tracker

        seq_offset = 0
        base_current_time = 0
        mixed_cmd = list()
        for write_cmd in range(0,100-self.opts['mixed_ratio']):
            mixed_cmd.append(0x10)
        for read_cmd in range(0, self.opts['mixed_ratio']):
            mixed_cmd.append(0x1)

        tot_block_size = 0
        tot_cmd_opt = 0
        for idx in range(self.opts['workload_quantity']):

            workload_item = dict()
            workload_item['request_arrow'] = 'req'
            self.status_bar.setValue(round((idx / (len(self.baseworkload) * 1.3)) * 100))

            cpu_host_interval = self.opts['cpu_host_interval']
            host_interval = self.opts['host_interval']
            address_rage = float(self.opts['address_range'])
            base_offset = address_rage * 1024 * 1024 * 1024 *1024* 2 #1TB
            normal_dist = (address_rage/4)* 0.1 * 1024 *  1024 * 1024 *2 #0.1GB
            workload_item['offset'] = [np.random.randint(int(base_offset))
                                       ,np.random.randint(int(base_offset))
                                       ,np.random.randint(int(base_offset))
                                       ,np.random.normal(0.1 * base_offset, normal_dist, 1)[0]
                                       ,np.random.normal(0.2 * base_offset, normal_dist, 1)[0]
                                       ,np.random.normal(0.5 * base_offset, normal_dist, 1)[0]
                                       ,np.random.normal(0.7 * base_offset, normal_dist, 1)[0]
                                       ,np.random.normal(0.9 * base_offset, normal_dist, 1)[0]][np.random.randint(8)]
            workload_item['offset'] = int((workload_item['offset'] //(8*1024))*(8*1024))
            workload_item['cmd'] = mixed_cmd[np.random.randint(100)]
            if workload_item['cmd'] == 0x1:
                workload_item['length'] = self.opts['read_block_size'][
                    np.random.randint(len(self.opts['read_block_size']))]
                lsb = int(self.opts['read_distribution'][0])
                csb = int(self.opts['read_distribution'][1])
                msb = int(self.opts['read_distribution'][2])
                overhead = abs(int(
                    [np.random.normal(lsb, 10, 1)[0], np.random.normal(msb, 10, 1)[0], np.random.normal(csb, 10, 1)[0]][
                        np.random.randint(100) % 3]))
                workload_item['cmd_latency'] = overhead

            elif workload_item['cmd'] == 0x10:
                workload_item['length'] = self.opts['write_block_size'][
                    np.random.randint(len(self.opts['read_block_size']))]
                min = int(self.opts['write_distribution'][0])
                median = int(self.opts['write_distribution'][1])
                worst = int(self.opts['write_distribution'][2])
                workload_item['cmd_latency'] = abs(int(
                    [np.random.normal(min, 10, 1)[0], np.random.normal(median, 10, 1)[0],
                     np.random.normal(median, 10, 1)[0], np.random.normal(median, 10, 1)[0],
                     np.random.normal(worst, 10, 1)[0]][np.random.randint(100) % 3]))

            tot_block_size += workload_item['length']
            tot_cmd_opt +=1
            if self.check_page_in_cache(workload_item, base_current_time):
                base_current_time += cpu_host_interval
                self.tot_cahce_hit += 1
                continue

            workload_item['idle'] = self.opts['idle_time']

            if workload_item['idle'] > 0:
                workload_item['time'] = max_complete_time + workload_item['idle']
            else:
                try:
                    if (cmdq_list.index(0) >= 0):  # cmdq has room
                        workload_item['time'] = host_interval
                        if last_start_time_list != -1:
                            last_time_list.sort()
                            initial_start_time = last_start_time_list + host_interval
                            lastcheck_start_time = host_interval + last_time_list[0][0]
                            if lastcheck_start_time < initial_start_time:
                                workload_item['time'] = lastcheck_start_time
                            else:
                                workload_item['time'] = initial_start_time
                except:
                    last_time_list.sort()
                    workload_item['time'] = host_interval + last_time_list[0][0]
                    if last_start_time_list >= workload_item['time']:
                        workload_item['time'] = host_interval + last_time_list[0][0]

            # check die collision
            try:
                die_num = int(str(int(workload_item['offset']))[:-5])%tot_die
            except:
                die_num = 0
            workload_item['cmd_latency'] = self.check_and_overhead_add(workload_item['time'], self.die_allocation_unit,
                                                                       die_num, workload_item['cmd_latency'],
                                                                       workload_item)
            if workload_item['time'] > last_start_time_list:
                last_start_time_list = workload_item['time']

            if (len(last_time_list) > 0):
                delete_item_list = list()
                for last_time_item in last_time_list:
                    if workload_item['time'] > last_time_item[0]:
                        cmdq_list[last_time_item[1]] = 0
                        delete_item_list.append(last_time_item)
                    else:
                        break

                if delete_item_list.__len__() > 0:
                    for idx in range(0, len(delete_item_list)):
                        del last_time_list[last_time_list.index(delete_item_list[idx])]

            workload_item['cmdq'] = cmdq_list.index(0)
            cmdq_list[workload_item['cmdq']] = 1
            workload_item['rsp_latency'] = 0

            complete_time = workload_item['time'] + workload_item['cmd_latency']
            if max_complete_time < complete_time:
                max_complete_time = complete_time

            last_time_list.append((complete_time, workload_item['cmdq']))

            # complete log
            # com_workload_item = dict()
            # com_workload_item['request_arrow'] = 'com'
            # com_workload_item['cmd'] = workload_item['cmd']
            # com_workload_item['offset'] = workload_item['offset']
            # com_workload_item['time'] = workload_item['time'] + workload_item['cmd_latency']
            #
            # com_workload_item['length'] = workload_item['length']
            # com_workload_item['cmdq'] = workload_item['cmdq']
            # com_workload_item['cmd_latency'] = 0
            # com_workload_item['rsp_latency'] = -1
            # com_workload_item['idle'] = -1
            raw_item.append(workload_item)
            # raw_item.append(com_workload_item)

            end_time = workload_item['cmd_latency'] + workload_item['time']
            # sync async
            # base_current_time = end_time
            # self.append_cache_workload(workload_item, end_time)
        try:
            self.cur_dram_cache_list(end_time)
        except:
            None

        self.logic_event_tracker['hit_ratio'] = {
            'total_ratio':self.tot_cahce_hit/tot_cmd_opt,
            'dram_hit':self.dram_cache_hit,
            'cpu_hit':self.cpu_cahce_hit,
            'throughput(MiB/s)':int((tot_block_size/1024/1024)/(end_time*0.000001)),
            'iops(KIOPs)':int((tot_cmd_opt)/(end_time*0.000001)/1000),
        }

        return raw_item

    def rsp_latency_calculation(raw_item):
        pass
        # for item in raw_item:
