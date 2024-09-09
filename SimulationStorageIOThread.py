import math

import PyQt5.QtGui as designer
from PyQt5.QtCore import Qt
# for parcing and load ebpf type storage IO analysis
import datetime
import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, QObject
import datetime as dt
from PyQt5.QtWidgets import QHBoxLayout
import pyqtgraph as pg
import pandas as pd

import threading
import time

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

    finished_signal = pyqtSignal(list,dict,str,dict)
    progressChanged = pyqtSignal(int)

    result_plot_signal = pyqtSignal(list)
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
        dram_cluster_cache_list = np.array([])
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
    result_hit_ratio=dict()

    result_hit_ratio_tracker = list()

    lock = threading.Lock()

    stop_flag = False

    Simulation_job_list = list()

    # signal to indicate thread has finished
    def __init__(self,result_callback,status_bar,ui_widget,simulation_job_list,parent=None):
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
            'slc_mig':None,
            'slc_read_time':None
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
        self.logic_event_tracker['hit_ratio'] = list()

        self.status_bar = status_bar
        self.finished_signal.connect(result_callback)
        self.progressChanged.connect(status_bar)

        self.opts['plot_sim_res_throughput'] = ui_widget[0]
        self.opts['plot_sim_res_hit_ratio'] = ui_widget[1]
        self.opts['txt_sim_result'] = ui_widget[2]

        self.result_plot_signal.connect(self.simulation_result_plot)

        self.init_buffer = self.global_simple_nand_config['write_buffer']
        self.locking_write_buffer = list()

        self.cpu_cache_timer = 0
        self.cpu_cahce_event_tracker.clear()
        self.dram_cache_timer = 0
        self.dram_cahce_event_tracker.clear()

        self.history_on_cpu_cache_list.clear()
        self.history_on_dram_cache_list.clear()

        self.tot_cahce_hit = 0

        self.Simulation_job_list = simulation_job_list

    def run(self):
        for idx in range(0,len(self.Simulation_job_list)):
            self.setData(**self.Simulation_job_list[idx])
            self.run_generate_workload(idx+1)
            self.finished_signal.emit(self.main_workload_context,self.logic_event_tracker,self.file_name,self.die_event_tracker)

        self.finished.emit()
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

        self.opts['slc_mig'] = kwargs['slc_level_migration']
        self.opts['slc_read_time'] = kwargs['slc_read_time']

        self.opts['pattern_workload_idx'] = kwargs['pattern_workload_idx']
        self.opts['cpu_host_interval'] = 1 * 0.001
        self.opts['address_range'] = kwargs['address_range']

        self.opts['simulation_rounds'] = kwargs['simulation_rounds']
        self.opts['address_pattern'] = kwargs['address_pattern']

        self.opts['zone_id']=kwargs['zone_id']
        self.opts['zone_size']=kwargs['zone_size']
        self.opts['db_scan_parameter'] = kwargs['db_scan_parameter']
        self.opts['on_highest_zone_id'] = kwargs['on_highest_zone_id']
        self.opts['zone_intensive_ratio'] = kwargs['zone_intensive_ratio']
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
            try:
                if workload['nand_tech'] == 'slc':
                    self.die_event_tracker[die_num].append(
                        # {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead - t_Dout)})
                        {'cmd': 0x9801, 'start_time': cur_time, 'end_time': cur_time + (overhead)})
            except:
                self.die_event_tracker[die_num].append(
                    # {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead - t_Dout)})
                    {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead)})
            self.die_event_tracker[die_num].append(
                {'cmd': 0x9902, 'start_time': cur_time + (overhead), 'end_time': cur_time + overhead + t_Dout})
            die_access_control[die_num] = cur_time + overhead + t_Dout + 2
            # workload['etc'] = ''
            # return overhead + 2
            return overhead + t_Dout + 2
        else:
            try:
                if workload['nand_tech'] == 'slc':
                    self.die_event_tracker[die_num].append(
                        # {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead - t_Dout)})
                        {'cmd': 0x9801, 'start_time': die_access_control[die_num], 'end_time': die_access_control[die_num] + (overhead)})
            except:
                self.die_event_tracker[die_num].append(
                    # {'cmd': 0x9901, 'start_time': cur_time, 'end_time': cur_time + (overhead - t_Dout)})
                    {'cmd': 0x9901, 'start_time': die_access_control[die_num], 'end_time': die_access_control[die_num] + (overhead)})
            self.die_event_tracker[die_num].append(
                {'cmd': 0x9902, 'start_time': die_access_control[die_num] + (overhead), 'end_time': die_access_control[die_num] + overhead + t_Dout})
            die_access_control[die_num] = die_access_control[die_num] + overhead + t_Dout + 2
            workload['etc'] = 'Die#' + str(die_num) + ': Collision'

            return die_access_control[die_num] - cur_time + 2

    def check_and_overhead_add(self,cur_time,die_access_control=dict(),die_num=int,overhead=int,workload=dict(),write_unit=int):

        t_Dout = self.global_simple_nand_config['t_Dout']
        t_In = self.global_simple_nand_config['t_DIn']

        if workload['cmd'] == 0x1:  # read
            return self.read_overhead_operation(cur_time, die_access_control, die_num, overhead, t_Dout, workload)

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
                        # if workload_item['cluster'] == 1 or workload_item['cluster'] == 2:
                        # if workload_item['cluster'] == -1 :
                            self.dram_cache_list.insert(0, (workload_item['offset'], workload_item['cluster']))
                    except:
                        self.dram_cache_list.insert(0, workload_item['offset'])
                    self.dram_cahce_event_tracker.append(
                        {'cmd': 0x9952, 'start_time': end_time, 'end_time': end_time + 1, 'desc': 'insert dram cache'})
                else:
                    try:
                        # if workload_item['cluster'] == 1 or workload_item['cluster'] == 2:
                        # if workload_item['cluster'] == -1:
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


    def run_generate_workload(self,sim_job_idx):
        #init_time us
        last_time_list = list()
        last_start_time_list = -1
        cmdq_list=[0]*self.opts['max_queue']
        max_complete_time = -1

        self.cpu_cahce_hit = 0
        self.dram_cache_hit = 0

        zone_recognization_num = 5

        try:
            self.dram_cache_list.clear()
        except:
            self.dram_cache_list = np.array([])
            self.dram_cluster_cache_list = np.array([])
        self.cpu_cache_list.clear()

        self.opts['txt_sim_result'].clear()
        self.result_hit_ratio_tracker.clear()

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

        cluster_list = [0, 1, 2, 3, 4]
        highest_zone_id_array = np.array([item[0] for item in self.opts['on_highest_zone_id']])
        zone_real_offset = self.opts['zone_size'] * 1024 * 1024 * 2

        for number in range(self.opts['simulation_rounds']):
            if self.stop_flag:
                return
            if raw_item !='':
                self.baseworkload = raw_item

            # highest_zone_id_array = np.fromstring(self.opts['on_highest_zone_id'],sep=',')

            for workload_item in self.baseworkload:
                if len(self.dram_cache_list) > dram_cache_max_size:
                    try:
                        try:
                            # index = np.where(self.dram_cluster_cache_list[::-1]==-1)[0][0]
                            #
                            # if len(self.dram_cluster_cache_list) != len(self.dram_cache_list):
                            #     Exception("What the fuck")
                            #
                            # zone_id_array = self.dram_cache_list//zone_real_offset
                            # not_in_cache = np.setdiff1d(zone_id_array,highest_zone_id_array,assume_unique=True)
                            # last_index = np.where(zone_id_array[::-1] == not_in_cache[-1])[0][0]
                            last_index= np.where(~np.isin(self.dram_cluster_cache_list,highest_zone_id_array))[0][-1]
                            self.dram_cache_list = np.delete(self.dram_cache_list, [last_index])
                            try:
                                self.dram_cluster_cache_list = np.delete(self.dram_cluster_cache_list, [last_index])
                            except:
                                None
                        except:
                            self.dram_cache_list = np.delete(self.dram_cache_list, [len(self.dram_cache_list) - 1])
                            try:
                                self.dram_cluster_cache_list = np.delete(self.dram_cluster_cache_list, [len(self.dram_cluster_cache_list) - 1])
                            except:
                                None

                    except:
                        self.dram_cache_list = np.delete(self.dram_cache_list, [len(self.dram_cache_list) - 1])
                        #del self.dram_cache_list[len(self.dram_cache_list) - 1]
                else:
                    if self.opts['mem_access_arch'] == 'ZTBP': #clustering based operation...
                        try:
                            try:
                                if np.where(self.dram_cache_list == workload_item['offset'])[0][0]:
                                    index_pop = np.where(self.dram_cache_list == workload_item['offset'])
                                    self.dram_cache_list = np.delete(self.dram_cache_list, [index_pop])
                                    try:
                                        self.dram_cluster_cache_list = np.delete(self.dram_cluster_cache_list, [index_pop])
                                    except:
                                        None
                            except:
                                None
                            self.dram_cache_list = np.insert(self.dram_cache_list,0,workload_item['offset'])
                            try:
                                # self.dram_cluster_cache_list = np.insert(self.dram_cluster_cache_list,0, workload_item['cluster'])
                                self.dram_cluster_cache_list = np.insert(self.dram_cluster_cache_list, 0,workload_item['zone_id'])
                            except:
                                None

                        except: #for list
                            None
                        #     if workload_item['offset'] in self.dram_cache_list:
                        #         self.dram_cache_list.pop(self.dram_cache_list.index(workload_item['offset']))
                        #         self.dram_cluster_cache_list.pop(self.dram_cache_list.index(workload_item['offset']))
                        #     self.dram_cache_list.insert(0, workload_item['offset'])
                        #     self.dram_cluster_cache_list.insert(0,  workload_item['cluster'])
                    else:
                        try:
                            try:
                                if np.where(self.dram_cache_list==workload_item['offset'])[0][0]:
                                    index_pop = np.where(self.dram_cache_list == workload_item['offset'])
                                    self.dram_cache_list = np.delete(self.dram_cache_list,[index_pop])
                            except:
                                None
                            self.dram_cache_list = np.insert(self.dram_cache_list,0,workload_item['offset'])
                        except:
                            None
                            # if workload_item['offset'] in self.dram_cache_list:
                            #     self.dram_cache_list.pop(self.dram_cache_list.index(workload_item['offset']))
                            # self.dram_cache_list.insert(0, workload_item['offset'])

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
                        None
                        # if workload_item['offset'] in self.cpu_cache_list:
                        #     self.cpu_cache_list.pop(self.cpu_cache_list.index(workload_item['offset']))
                        # self.cpu_cache_list.insert(0, workload_item['offset'])

            raw_item,die_event_tracker=self.do_create_base_workload(sim_job_idx)

            # if self.opts['mem_access_arch'] == 'ZTBP':
            #     temp_list = list()
            #     for idx in range(0, len(raw_item)):
            #         temp_list.append([raw_item[idx]['time'], raw_item[idx]['offset']])
            #     scaler = StandardScaler()
            #     scale_data = scaler.fit_transform(temp_list)
            #
            #     try:
            #         val_eps=float(self.opts['db_scan_paramter'].split(',')[0].split('eps:')[1])
            #         val_min_samples = int(self.opts['db_scan_paramter'].split(',')[1].split('min_samples:')[1])
            #     except:
            #         val_eps = 0.022
            #         val_min_samples = 30
            #
            #     dbscan = DBSCAN(eps=val_eps, min_samples=val_min_samples)
            #     clusters = dbscan.fit_predict(scale_data)
            #     clusters_group_offset = dict()
            #     for i in range(scale_data.shape[0]):
            #         if clusters[i] == -1:
            #             raw_item[i]['cluster'] = clusters[i]
            #         if not clusters[i] in clusters_group_offset.keys():
            #             clusters_group_offset[clusters[i]] = [int(raw_item[i]['offset'])]
            #         else:
            #             clusters_group_offset[clusters[i]].append(int(raw_item[i]['offset']))
            #
            #     import collections
            #     temp=collections.OrderedDict(sorted(clusters_group_offset.items()))
            #     del temp[-1]
            #     temp_key = list(temp.keys())
            #     for i in range(0,len(temp_key)):
            #         for j in range(1,len(temp_key)):
            #             if temp[i][0] > temp[j][0]:
            #                 temp[i],temp[j] = temp[j],temp[i]
            #
            #     for i in temp.keys():
            #         temp[i] = np.median(temp[i])
            #
            #     for item_raw in raw_item[:]:
            #         if not 'cluster' in item_raw:
            #             index_list = list()
            #             for i in temp.keys():
            #                 index_list.append(np.abs(item_raw['offset']-temp[i]))
            #             item_raw['cluster'] = list(temp.keys())[index_list.index(np.min(index_list))]

                # for i in range(scale_data.shape[0]):
                #     raw_item[i]['cluster'] = clusters[i]
                # raw_item = sorted(raw_item, key=lambda x: x['time'])
            self.main_workload_context = raw_item
            # self.status_bar.setValue(100)
            self.progressChanged.emit(100)

            if self.opts['mem_access_arch'] == 'ZTBP':

                self.result_hit_ratio['index'] = number
                self.result_hit_ratio['dram len'] = len(self.dram_cache_list)
                self.result_hit_ratio['cluster_list'] = str(cluster_list)
                self.result_hit_ratio['recognization_zid'] = str(highest_zone_id_array)
                print(str(self.result_hit_ratio))
            else:
                self.result_hit_ratio['index'] = number
                self.result_hit_ratio['dram len'] = len(self.dram_cache_list)
                print('LRU',str(self.result_hit_ratio))

            self.result_hit_ratio_tracker.append(self.result_hit_ratio)
            # self.simulation_result_plot(self.logic_event_tracker['hit_ratio'])
            if len(self.result_hit_ratio_tracker) % 3 == 0:
                self.result_plot_signal.emit(self.result_hit_ratio_tracker)
        title = '[RESULT]['+str(dt.datetime.now())+']'
        title = title.replace(':','-')
        if str(self.opts['mem_access_arch']).__contains__('ZTBP'):
            title += '_ZTBP'
        else:
            title += '_NORMAL'

        if self.opts['slc_mig']:
            title +='_SLCMIG'
        title += '_'+str(self.opts['workload_quantity'])
        title += '_'+str(self.opts['mixed_ratio'])
        title += '_'+str(self.opts['max_queue'])
        title += '_'+str(self.opts['host_interval'])

        title += '_'+self.opts['dram_page_fault_policy']
        title += '_'+str(int(self.opts['dram_size'])/1024)+'MB'
        title += '_'+str(self.opts['zone_intensive_ratio'])
        title = title.replace(':', '_')
        with open(str(title)+".txt","w") as file:
            file.write(title)
            file.write('\nPreCondition\n')
            file.write('\n'.join([f"{key}: {value}" for key, value in self.opts.items()]))
            file.write('\nRESULT\n')
            file.write('\n'.join(str(d) for d in self.result_hit_ratio_tracker))
        file.close()
        self.result_plot_signal.emit(self.result_hit_ratio_tracker)
        # rsponse latency calculation..
        self.rsp_latency_calculation()


        return
    def simulation_result_plot(self,raw_data=list()):

        self.lock.acquire()

        self.opts['txt_sim_result'].appendPlainText(str(raw_data[-1]['cur_Sim_round'])+'/'+str(raw_data[-1]['Total_Sim_round']))
        self.opts['txt_sim_result'].appendPlainText(str(raw_data[-1])+'\n')
        dt_raw_data=pd.DataFrame(raw_data)
        result_list = dict()
        for dt_key in dt_raw_data.keys():
            result_list[dt_key] = list(dt_raw_data[dt_key].values)

        timting_list =  result_list['index']
        throuhput_y_list = result_list['throughput(MiB/s)']
        iops_y_list = result_list['iops(KIOPs)']


        self.opts['plot_sim_res_throughput'].showGrid(x=True, y=True)
        self.opts['plot_sim_res_throughput'].addLegend(size=(100,0))

        self.opts['plot_sim_res_throughput'].setLabel("left",text='Throughput(MiB/s)')
        self.opts['plot_sim_res_throughput'].setLabel("right", text='IOPs', units="K")

        left_axis = pg.AxisItem("left")
        right_axis = pg.AxisItem("right")
        self.opts['plot_sim_res_throughput'].clear()
        self.opts['plot_sim_res_hit_ratio'].clear()
        self.opts['plot_sim_res_throughput'].plot(x=timting_list,y=throuhput_y_list,symbol='x',symbolPen='g',symbolBrush=0.2,name='Throughput',axisItems={"left":left_axis})

        # vb2 = pg.ViewBox()
        # vb2.clear()
        # self.opts['plot_sim_res_throughput'].plotItem.scene().addItem(vb2)
        # self.opts['plot_sim_res_throughput'].getAxis('right').linkToView(vb2)
        # vb2.addItem(pg.PlotCurveItem(iops_y_list, symbol='o', symbolPen='r', symbolBrush=0.1, name='IOPs'))
        # vb2.setXLink(self.opts['plot_sim_res_throughput'])

        # def updateViews(self,vb2):
        #     vb2.setGeometry(self.opts['plot_sim_res_throughput'].plotItem.vb.sceneBoundingRect())
        #     vb2.linkedViewChanged(self.opts['plot_sim_res_throughput'].plotItem.vb, vb2.XAxis)
        #
        # updateViews(self,vb2)
        # self.opts['plot_sim_res_throughput'].vb.sigResized.connect(updateViews)
        # vb2.setGeometry(self.opts['plot_sim_res_throughput'].plotItem.vb.sceneBoundingRect())
        # vb2.linkedViewChanged(self.opts['plot_sim_res_throughput'].plotItem.vb, vb2.XAxis)

        self.opts['plot_sim_res_hit_ratio'].addItem(pg.BarGraphItem(x=timting_list, height=result_list['dram_hit'], symbolBrush=0.2, pen='w', width=0.3,brush='r', name='dram_hit'))
        self.opts['plot_sim_res_hit_ratio'].addItem(pg.BarGraphItem(x=[x + 0.3 for x in timting_list] , height=result_list['cpu_hit'], symbolBrush=0.2, pen='w', width=0.3,brush='y', name='cpu_hit'))

        # self.opts['plot_sim_res_throughput'].plot(x=timting_list, y=iops_y_list, symbol='o', symbolPen='r', symbolBrush=0.2,name='IOPs',axisItems={"right":right_axis})
        # self.opts['plot_sim_res_throughput'].setLayout(hbox_throughput)
        # if not self.opts['plot_sim_res_throughput'].layout():
        #     hbox_throughput = QHBoxLayout()
        #     hbox_throughput.addStretch(1)
        #     hbox_throughput.addWidget(thr_iop_plot)
        #      = pg.PlotWidget(self.opts['plot_sim_res_throughput'].setLayout(hbox_throughput))
        # else:
        #     self.opts['plot_sim_res_throughput'].addItem(x=timting_list,y=throuhput_y_list,symbol='x',symbolPen='g',symbolBrush=0.2,name='Throughput')
        #     self.opts['plot_sim_res_throughput'].addItem(x=timting_list, y=iops_y_list, symbol='x', symbolPen='g', symbolBrush=0.2, name='IOPs', axisItems='right')
        # # self.opts['plot_sim_res_hit_ratio'] = kwargs['plot_sim_res_hit_ratio']
        # # self.opts['txt_sim_result'] = kwargs['txt_sim_result']
        self.lock.release()
        return
    def do_create_base_workload(self,sim_job_idx):
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

            self.progressChanged.emit((round((idx / (len(self.baseworkload) * 1.3)) * 100)))
            cpu_host_interval = self.opts['cpu_host_interval']
            host_interval = self.opts['host_interval']
            workload_item['request_arrow'] = 'req'
            workload_item['cmd'] = mixed_cmd[np.random.randint(100)]
            address_rage = float(self.opts['address_range'])
            base_offset = address_rage * 1024 * 1024 * 1024 * 1024 * 2  # 1TB

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

            if str(self.opts['address_pattern']).lower().__contains__('random'):
                workload_item['offset'] = [np.random.randint(address_rage * 1024 * 1024 * 1024 * 1024 * 2)][np.random.randint(1)]
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
            except:
                None


            tot_block_size += workload_item['length']
            tot_cmd_opt += 1
            flag_cache_hit = False
            if self.check_page_in_cache(workload_item, base_current_time):
                base_current_time += cpu_host_interval
                self.tot_cahce_hit += 1
                flag_cache_hit = True
                workload_item['cache_hit'] = 1
                # continue

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
                die_num = int(str(int(workload_item['offset']))[:-5]) % tot_die
            except:
                die_num = 0

            if not flag_cache_hit:
                if self.opts['slc_mig'] & workload_item['zone_id'] in np.array([item[0] for item in self.opts['on_highest_zone_id']]):
                    workload_item['nand_tech'] = 'slc'
                    workload_item['cmd_latency'] = int(self.opts['slc_read_time'])
                    workload_item['cmd_latency'] = self.check_and_overhead_add(workload_item['time'],
                                                                               self.die_allocation_unit,
                                                                               die_num, workload_item['cmd_latency'],
                                                                               workload_item)
                else:
                    workload_item['cmd_latency'] = self.check_and_overhead_add(workload_item['time'],
                                                                               self.die_allocation_unit,
                                                                               die_num, workload_item['cmd_latency'],
                                                                               workload_item)
            else:
                workload_item['cmd_latency'] = 1

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


        self.result_hit_ratio = {
                'Total_Sim_round' : len(self.Simulation_job_list),
                'cur_Sim_round' : sim_job_idx,
                'total_ratio': 1,
                'total_ratio': self.tot_cahce_hit / tot_cmd_opt,
                'dram_hit': round(self.dram_cache_hit / tot_cmd_opt, 2),
                'cpu_hit': round(self.cpu_cahce_hit / tot_cmd_opt, 3),
                'throughput(MiB/s)': int((tot_block_size / 1024 / 1024) / (end_time * 0.000001)),
                'iops(KIOPs)': int((tot_cmd_opt) / (end_time * 0.000001) / 1000),
            }
        try:
            self.cur_dram_cache_list(end_time)
        except:
            None

        return raw_item,self.die_event_tracker

    def rsp_latency_calculation(raw_item):
        pass
        # for item in raw_item:
