import random

import PyQt5.QtGui as designer
from PyQt5.QtCore import Qt
# for parcing and load ebpf type storage IO analysis
import datetime
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import datetime as dt
import math
from EventManager.Simple_FTL_core import Simple_FTL_core as FTL

class GnerateWorkloadType:
    main_workload_context = dict()
    workload_label = ''
    opts = dict()

    def __init__(self):
        self.main_workload_context.clear()
        self.workload_label = 'Generated Types of Workload'

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
            0x9801: {
                'Color': 'r',
                'CMDQ_Color': (100, 155, 51, 23),
                'Symbol': 't',
                'NAME': 'SLC-tR'
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
        }
        return col_sym[cmd]


class GnerateWorkload(QThread):
    main_workload_context = dict()
    workload_label = ''
    opts = dict()
    finished_signal = pyqtSignal(list,dict,str)
    progressChagned = pyqtSignal(int)

    file_name = ''
    status_bar =''
    die_event_tracker = dict()
    plane_event_tracker = dict()
    global_simple_nand_config = dict()
    init_buffer = 0

    die_allocation_unit = dict()
    plane_allocation_unit = dict()

    locking_write_buffer = (int,int)
    # signal to indicate thread has finished
    def __init__(self,result_callback,status_bar,parent=None):
        super().__init__(parent=parent)
        self.opts = {
            'workload_quantity':None,
            'cmd_type':None,
            'mixed_ratio':None,
            'address_pattern':None,
            'address_range':None,
            'idle_duration':None,
            'idle_time':None,
            'max_queue':None,
            'read_distribution':None,
            'write_distribution':None,

            'host_if':None,
            'host_interval':None,
            'host_worker':None,
            'context_id':None,
            'context_line':None,
            'context_id':None,
            'name':None
        }
        self.status_bar = status_bar
        self.finished_signal.connect(result_callback)
        self.progressChagned.connect(status_bar)

        self.global_simple_nand_config = {
            't_Dout': 3,
            't_DIn': 3 * 48,
            # 'write_buffer': 2304 ,
            'write_buffer': 23040 ,
            'buffing_overhead':1000,
            'cur_prog_nand_num':0,
            'num_die':32,
            'num_plane':4,
            'flush_units':192*4,
            'oneshot_units':192,
        }
        self.init_buffer = self.global_simple_nand_config['write_buffer']
        self.locking_write_buffer = list()

    def run(self):
        self.run_generate_workload()
        self.finished_signal.emit(self.main_workload_context,self.die_event_tracker,self.file_name)
        return

    def setData(self,**kwargs):
        self.opts['workload_quantity'] = kwargs['workload_quantity']
        self.opts['cmd_type'] = kwargs['cmd_type']
        self.opts['mixed_ratio'] = kwargs['mixed_ratio']
        self.opts['address_pattern'] = kwargs['address_pattern']
        self.opts['address_range'] = kwargs['address_range']
        self.opts['idle_duration'] = kwargs['idle_duration']
        self.opts['idle_time'] = kwargs['idle_time']
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
        self.opts['context_id'] = kwargs['context_id']

        self.opts['zone_id'] = kwargs['zone_id']
        self.opts['zone_intensive_ratio'] = kwargs['zone_intensive_ratio']
        self.opts['zone_size'] = kwargs['zone_size']

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

    def read_overhead_operation(self,cur_time,die_access_control,die_num,overhead,t_Dout,workload):
        if cur_time > die_access_control[die_num]:
            self.die_event_tracker[die_num].append(
                {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead - t_Dout)})
            self.die_event_tracker[die_num].append(
                {'cmd': 0x9902, 'start_time': cur_time + (overhead - t_Dout), 'end_time': cur_time + overhead})
            die_access_control[die_num] = cur_time + overhead + 2
            # workload['etc'] = ''
            return overhead + 2
        else:
            self.die_event_tracker[die_num].append({'cmd': 0x9901, 'start_time': die_access_control[die_num],
                                                    'end_time': die_access_control[die_num] + (overhead - t_Dout)})
            self.die_event_tracker[die_num].append(
                {'cmd': 0x9902, 'start_time': die_access_control[die_num] + (overhead - t_Dout),
                 'end_time': die_access_control[die_num] + overhead})
            die_access_control[die_num] = die_access_control[die_num] + overhead + 2
            workload['etc'] = 'Die#' + str(die_num) + ': Collision'
            return die_access_control[die_num] - cur_time + 2

    def check_and_overhead_add(self,cur_time,die_access_control=dict(),die_num=int,overhead=int,workload=dict(),write_unit=int):

        # return overhead+2
        t_Dout = self.global_simple_nand_config['t_Dout']
        t_In = self.global_simple_nand_config['t_DIn']

        if workload['cmd'] == 0x1:  # read

            # split_4k_length = workload['length'] // 4096
            # cmd_latency_list=list()
            # if split_4k_length > 1:
            #     for idx in range(split_4k_length):
            #         # die_num=np.random.randint(self.global_simple_nand_config['num_die'])
            #         cmd_latency_list.append(self.read_overhead_operation(cur_time, die_access_control, die_num, overhead, t_Dout, workload))
            #     return np.max(cmd_latency_list)
            # else:
            return self.read_overhead_operation(cur_time, die_access_control, die_num, overhead, t_Dout, workload)

        elif workload['cmd'] == 0x10:
            # workload['etc'] = ''
            write_bffer = self.global_simple_nand_config['write_buffer']

            #free
            for item in self.locking_write_buffer[:]:
                if cur_time >=  item[0]:
                    self.global_simple_nand_config['write_buffer'] = write_bffer + item[1]
                    self.locking_write_buffer.remove(item)

            self.global_simple_nand_config['write_buffer'] = write_bffer - workload['length'] / 1024

            #event based operation
            # cmd_latency = FTL()

            #simple NAND modeling
            cmd_latency = self.check_nand_program(cur_time, -1, die_access_control, overhead, workload, -1, -1)

            return cmd_latency-cur_time

    def run_generate_workload(self):
        # FTL()
        #init_time us
        last_time_list = list()
        last_start_time_list = -1
        cmdq_list=[0]*self.opts['max_queue']
        max_complete_time = -1

        self.file_name = 'MQ['+str(self.opts['max_queue'])+']_'

        mixed_cmd = list()
        for write_cmd in range(0,100-self.opts['mixed_ratio']):
            mixed_cmd.append(0x10)
        for read_cmd in range(0, self.opts['mixed_ratio']):
            mixed_cmd.append(0x1)
        self.file_name += 'Mixed[' + str(self.opts['mixed_ratio']) + ']_'


        tot_die = self.global_simple_nand_config['num_die']
        tot_plane = self.global_simple_nand_config['num_plane']

        for i in range(0,tot_die):
            self.die_allocation_unit[i] = -1
            self.die_event_tracker[i] = list()

        for i in range(0, tot_die):
            self.plane_event_tracker[i] = dict()
            for idx_plane in range(0, tot_plane):
                self.plane_event_tracker[i][idx_plane] = list()

        seq_offset = 0
        raw_item = list()
        # list_divide_num = 20
        # num_idx_tot = self.opts['workload_quantity'] *2 // list_divide_num
        # raw_item_dict = dict()
        # for i in range(0,list_divide_num):
        #     raw_item_dict[i] = list()
        list_num = 0
        self.file_name += '' + str(self.opts['address_range']) + 'TB_'
        self.file_name += 'Pattern[' + str(self.opts['address_pattern']) + ']_'
        zns_info = dict()
        zns_before_info = dict()
        for idx in range(0,self.opts['workload_quantity']):

            # if idx % num_idx_tot == 0:
            #     raw_item = raw_item_dict[list_num]
            #     list_num +=1

            # self.status_bar.setValue
            self.progressChagned.emit(round((idx/(self.opts['workload_quantity']*1.3))*100))
            host_interval = self.opts['host_interval']
            workload_item = dict()
            workload_item['request_arrow'] = 'req'
            workload_item['cmd'] = mixed_cmd[np.random.randint(100)]
            address_rage = float(self.opts['address_range'])

            if workload_item['cmd'] == 0x1:
                workload_item['length'] = self.opts['read_block_size'][np.random.randint(len(self.opts['read_block_size']))]
                lsb = int(self.opts['read_distribution'][0])
                csb = int(self.opts['read_distribution'][1])
                msb = int(self.opts['read_distribution'][2])
                overhead = abs(int([np.random.normal(lsb, 10, 1)[0], np.random.normal(msb, 10, 1)[0], np.random.normal(csb, 10, 1)[0]][np.random.randint(100) % 3]))
                workload_item['cmd_latency'] = overhead

            elif workload_item['cmd'] == 0x10:
                workload_item['length'] = self.opts['write_block_size'][np.random.randint(len(self.opts['write_block_size']))]
                min = int(self.opts['write_distribution'][0])
                median = int(self.opts['write_distribution'][1])
                worst = int(self.opts['write_distribution'][2])
                workload_item['cmd_latency'] = abs(int([np.random.normal(min, 10, 1)[0], np.random.normal(median, 10, 1)[0], np.random.normal(median, 10, 1)[0], np.random.normal(median, 10, 1)[0], np.random.normal(worst, 10, 1)[0]][ np.random.randint(100) % 3]))

            if str(self.opts['address_pattern']).lower().__contains__('random'):
                workload_item['offset'] = [np.random.randint(address_rage*1024*1024*1024*1024*2)][np.random.randint(1)]
            elif str(self.opts['address_pattern']).lower().__contains__('sequentail'):
                workload_item['offset'] = seq_offset
                seq_offset = seq_offset + workload_item['length'] * 2
            elif str(self.opts['address_pattern']).lower().__contains__('streamwritepattern') | str(self.opts['address_pattern']).lower().__contains__('zns'):
                base_offset = address_rage * 1024 * 1024 * 1024 * 1024 * 2 #1TB
                normal_dist = 100  * 1 * 1 * 1024 * 1024 * 2 #100MB
                max_zone_id = int(base_offset // (self.opts['zone_size'] * 1024 * 1024 * 2))
                zone_real_offset = self.opts['zone_size'] * 1024 * 1024 * 2
                low_bound = 0
                high_bound = base_offset
                noraml_address_workload = list()
                zns_address_workload = list()

                noraml_address_workload.append(np.random.uniform(low=low_bound,high=high_bound,size=1))
                for zone_id_idx in self.opts['zone_id']:
                    if int(zone_id_idx) > max_zone_id:
                        zone_id_idx = max_zone_id
                    median_offset = zone_real_offset * int(zone_id_idx) + 0.5 * zone_real_offset
                    zns_offset = np.random.normal(median_offset, (1/5)*zone_real_offset, 1)[0] //(1024*8)*(1024*8)
                    zns_address_workload.append(zns_offset)
                normal_probablity = int(self.opts['zone_intensive_ratio'].split(':')[0])
                random_value = np.random.randint(0,100)
                if random_value < normal_probablity:
                    workload_item['offset'] = noraml_address_workload[0]
                else:
                    workload_item['offset'] = zns_address_workload[np.random.randint(len(zns_address_workload))]

            workload_item['offset'] = int((workload_item['offset'] //(1024*8))*(1024*8)) #4KB page mapping
            try:
                workload_item['zone_id'] = int(workload_item['offset'] // zone_real_offset)
                # try:
                #     zns_info[workload_item['zone_id']] +=1
                # except:
                #     zns_info[workload_item['zone_id']] = 0
            except:
                None


            try:
                workload_item['idle'] = self.opts['idle_time'] if idx % self.opts['idle_duration'] == 0 else 0
            except:
                workload_item['idle'] = 0
            if workload_item['idle'] > 0:
                workload_item['time'] = max_complete_time + workload_item['idle']
            else:
                try:
                    if ( cmdq_list.index(0) >= 0 ):#cmdq has room
                        workload_item['time'] = host_interval
                        if last_start_time_list!=-1:
                            last_time_list.sort()
                            initial_start_time = last_start_time_list + host_interval
                            lastcheck_start_time = host_interval+last_time_list[0][0]
                            if lastcheck_start_time < initial_start_time:
                                workload_item['time'] = lastcheck_start_time
                            else:
                                workload_item['time'] = initial_start_time
                except:
                    last_time_list.sort()
                    workload_item['time'] = host_interval + last_time_list[0][0]
                    if last_start_time_list >= workload_item['time']:
                        workload_item['time'] = host_interval + last_time_list[0][0]

            #check die collision
            try:
                die_num = int(str(int(workload_item['offset']))[:-5])%tot_die
            except:
                die_num = 0
            # print(die_num)

            workload_item['cmd_latency'] = self.check_and_overhead_add(workload_item['time'],self.die_allocation_unit,die_num,workload_item['cmd_latency'],workload_item)

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
                    for idx in range(0,len(delete_item_list)):
                        del last_time_list[last_time_list.index(delete_item_list[idx])]

            # workload_item['length'] = [1024,4096,16384,131072,262144,524288][np.random.randint(100)%6]
            workload_item['cmdq'] = cmdq_list.index(0)
            cmdq_list[workload_item['cmdq']] = 1
            workload_item['rsp_latency'] = 0

            complete_time = workload_item['time'] + workload_item['cmd_latency']
            if max_complete_time < complete_time:
                max_complete_time = complete_time

            last_time_list.append((complete_time,workload_item['cmdq']))

            # complete log
            # com_workload_item = dict()
            # com_workload_item['request_arrow'] = 'com'
            # com_workload_item['cmd'] = workload_item['cmd']
            # com_workload_item['offset'] = workload_item['offset']
            # com_workload_item['time'] = workload_item['time']+workload_item['cmd_latency']
            #
            # com_workload_item['length'] = workload_item['length']
            # com_workload_item['cmdq'] = workload_item['cmdq']
            # com_workload_item['cmd_latency'] = 0
            # com_workload_item['rsp_latency'] = -1
            # com_workload_item['idle'] = -1

            raw_item.append(workload_item)
            # raw_item.append(com_workload_item)

        # merge_raw_item = raw_item_dict[0]
        # for i in range(1,list_divide_num):
        #     merge_raw_item.extend(raw_item_dict[i])

        self.file_name += 'Pattern[' + str(self.opts['address_pattern']) + ']_'
        self.file_name += str(dt.datetime.now())

        # raw_item = sorted(raw_item, key=lambda x: x['time'])
        self.main_workload_context = raw_item
        # self.status_bar.setValue(100)
        # print(sorted(zns_info.items(), key=lambda x:x[1],reverse=True)[:5])
        self.progressChagned.emit(100)

        # rsponse latency calculation..
        self.rsp_latency_calculation()

        return

    def rsp_latency_calculation(raw_item):
        pass
        # for item in raw_item:
