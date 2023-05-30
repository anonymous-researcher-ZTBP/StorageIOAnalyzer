import pyqtgraph as pg
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
import numpy as np

class HistogramPlotwidget(pg.PlotWidget):

    workload_instance = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene().sigMouseClicked.connect(self.handledoubleclicked)

        plt = self.getPlotItem()
        plt.showGrid(x=True, y=True)
        plt.addLegend()

        # set properties
        plt.setLabel('left', 'Counts', units='#')
        plt.setLabel('bottom', 'Latency', units='us')

        plt.setMouseEnabled(x=True, y=False)

    def show_plot_item(self,raw_item,scale,rsp_or_req):
        self.clear()
        y_axis_count_range = dict()
        y_axis_modify_count_range = dict()

        if scale == 0:
            scale = 1

        for item in raw_item:
            if rsp_or_req == 'CMD':
                if item['request_arrow'] == 'req':
                    latency=item['cmd_latency']
                    mother = latency//scale
                    cmd = item['cmd']
                    if cmd in y_axis_count_range:
                        if mother in y_axis_count_range[cmd]:
                            y_axis_count_range[cmd][mother] += 1
                        else:
                            y_axis_count_range[cmd][mother] = 1
                    else:
                        if cmd not in y_axis_count_range:
                            y_axis_count_range[cmd]=dict()
                            y_axis_count_range[cmd][mother] = 1
                        if mother not in y_axis_count_range[cmd]:
                            y_axis_count_range[cmd][mother] = 1

            elif rsp_or_req == 'RSP':
                if item['request_arrow'] == 'com':
                    latency = item['rsp_latency']
                    mother = latency // scale
                    cmd = item['cmd']
                    if mother in y_axis_count_range:
                        y_axis_count_range[cmd][mother] += 1
                    else:
                        y_axis_count_range[cmd][mother] = 1

        min_temp_key = 9999
        max_temp_key = -1
        for cmd_idx in y_axis_count_range:
            temp_sorted_yaxis = sorted(y_axis_count_range[cmd_idx])
            if min_temp_key > temp_sorted_yaxis[0]:
                min_temp_key = temp_sorted_yaxis[0]

            if max_temp_key < temp_sorted_yaxis[-1]:
                max_temp_key = temp_sorted_yaxis[-1]

        x_axis_latency_ragne = np.arange(min_temp_key,max_temp_key,scale).tolist()

        for cmd_idx in y_axis_count_range.keys():
            y_axis_modify_count_range[cmd_idx] = dict()
            y_axis_modify_count_range[cmd_idx] = dict(zip(x_axis_latency_ragne, [None]*len(x_axis_latency_ragne)))

        for cmd_idx in y_axis_count_range.keys():
            for sort_key_item in x_axis_latency_ragne:
                try:
                    y_axis_modify_count_range[cmd_idx][sort_key_item] = y_axis_count_range[cmd_idx][sort_key_item]
                except:
                    y_axis_modify_count_range[cmd_idx][sort_key_item] = 0

        for cmd_idx in y_axis_modify_count_range.keys():
            x_latency_group = list(y_axis_modify_count_range[cmd_idx].keys())
            y_count_group = list(y_axis_modify_count_range[cmd_idx].values())
            cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['Color']
            cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
            cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']
            self.addItem(pg.BarGraphItem (x=x_latency_group,height = y_count_group, symbolBrush = 0.2, pen=cmd_color,width=0.6,brush=cmd_color, name=cmd_name))


    def setworkload_instance(self,workload_instacne):
        self.workload_instance = workload_instacne

    def cus_clearallitem(self):
        self.plotItem.clear()
        print('clear all item')

    def handledoubleclicked(self, event: QMouseEvent):
        if event.double():
            self.getPlotItem().getViewBox().autoRange()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Control:
            self.getPlotItem().getViewBox().setMouseMode(1)
            self.getPlotItem().setMouseEnabled(x=False, y=True)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Control:
            self.getPlotItem().getViewBox().setMouseMode(3)
            self.getPlotItem().setMouseEnabled(x=True, y=False)
        else:
            super().keyReleaseEvent(event)