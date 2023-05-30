import PyQt5.QtGui as designer
from PyQt5.QtCore import Qt
# for parcing and load ebpf type storage IO analysis
import datetime
import numpy as np

class ebpStorageIO:
    main_workload_context = dict()
    workload_label = ''
    status_bar = ''

    def __init__(self):
        self.main_workload_context.clear()
        self.workload_label = 'eBPF Types of Workload'

    def parcing(self, raw_data, status_bar):
        #tempcode
        raw_item = list()
        scale = 1
        rsp_or_req = 'CMD'
        cmdq = 0
        max_qd = 32
        #init_time us
        last_time_list = list()
        last_start_time_list = -1
        cmdq_list=[0]*max_qd
        max_complete_time = -1
        base_timing = 0
        self.status_bar = status_bar

        for idx in range(0, raw_data.count()):
            status_bar.setValue(round((idx / (self.opts['workload_quantity'] * 1.3)) * 100))
            workload_item = dict()
            workload_item['request_arrow'] = str(raw_data[idx]).split(',')[0]
            workload_item['cmd'] = str(raw_data[idx]).split(',')[1]
            workload_item['offset'] = str(raw_data[idx]).split(',')[2]
            workload_item['time'] = str(raw_data[idx]).split(',')[3]
            workload_item['length'] = str(raw_data[idx]).split(',')[4]
            workload_item['cmdq'] = str(raw_data[idx]).split(',')[5]
            workload_item['cmd_latency'] = 0
            workload_item['rsp_latency'] = 0
            workload_item['idle'] = 0

            self.main_workload_context[datetime.datetime.fromtimestamp(workload_item['time'])] = workload_item

        self.main_workload_context = dict(sorted(self.main_workload_context.items(), key=lambda x: datetime.datetime.fromisoformat(x[0])))
        self.main_workload_context = list(self.main_workload_context.values())

        request_timelinse = list()
        complete_timeline = list()
        last_req_time = 0
        for idx in range(0,len(self.main_workload_context)):
            workload_item = self.main_workload_context[idx]
            if workload_item['request_arrow'].lower() == 'req':
                if request_timelinse.count() == 0 and request_timelinse.count() == 0:
                    workload_item['idle'] = workload_item['time'] - last_req_time
                if request_timelinse.count() == 1:
                    request_timelinse.clear()

                request_timelinse.append(idx)
            elif workload_item['request_arrow'].lower() == 'comp':
                complete_timeline.append(idx)
                last_req_time = workload_item['time']

                for req_item_idx in request_timelinse:
                    req_workload_item = self.main_workload_context[req_item_idx]
                    if (workload_item['cmdq'] == req_workload_item['cmdq'] and \
                        workload_item['offset'] == req_workload_item['offset'] and \
                        workload_item['cmd'] == req_workload_item['cmd']):
                        req_workload_item['cmd_latency'] = workload_item['time'] - req_workload_item['time']
                        workload_item['cmd_latency'] = req_workload_item['cmd_latency']

                        try:
                            workload_item['rsp_latency'] = workload_item['time'] - complete_timeline[-2]
                            del complete_timeline[-2]
                        except:
                            workload_item['rsp_latency'] = req_workload_item['cmd_latency']

        status_bar.setValue(0)
        return

    def get_workload_context(self):
        return self,self.main_workload_context

    def get_typeof_symbol(self,cmd):
        col_sym = {
            0x01:{
                'Color':'b',
                'Symbol':'o',
                'NAME':'READ(1)'
            },
            0x10:{
                'Color':'r',
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
            }
        }
        return col_sym[cmd]
