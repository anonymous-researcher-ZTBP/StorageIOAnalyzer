import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QKeyEvent
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
import numpy as np


class AddressDuplicatedPlotWidget(pg.PlotWidget):
    raw_item = ''
    input_key_event = ''
    qapp = ''
    summary_box = ''
    latency_marker = ''
    workload_instance = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene().sigMouseClicked.connect(self.handledoubleclicked)

        plt = self.getPlotItem()
        plt.showGrid(x=True, y=True)
        plt.addLegend()

        # set properties
        plt.setLabel('left', 'Counts', units='#')
        plt.setLabel('bottom', 'Address', units='B')

        plt.setMouseEnabled(x=True, y=True)

        self.latency_marker = pg.LinearRegionItem()
        self.latency_marker.setZValue(-10)
        plt.addItem(self.latency_marker)
        self.latency_marker.sigRegionChanged.connect(self.updateMarker)

    def updateMarker(self):
        region = self.latency_marker.getRegion()
        return

    def show_plot_item(self, *args):
        self.clear()
        try:
            raw_item = args[0]
            time_x_range = args[1]
        except:
            None

        y_range_dict = dict()
        self.raw_item = raw_item
        x_range_dict = dict()
        MB_10 = 2 * 1024 * 1024* 10
        MB_1 = 2 * 1024 * 1024 * 1
        MB_4k = (2 * 1024 * 1024 * 1)//256
        for item in raw_item:

            if item['request_arrow'] == 'req':
                if item['request_arrow'] != 'req':
                    continue
                offset = item['offset']//2
                # offset = offset // (MB_4k) #10MB
                # offset = offset * (MB_4k)
                cmd = item['cmd']

                if cmd not in y_range_dict:
                    y_range_dict[cmd] = dict()
                    x_range_dict[cmd] = list()

                    y_range_dict[cmd][offset] = 1
                    x_range_dict[cmd].append(offset)
                else:
                    if offset not in y_range_dict[cmd]:
                        y_range_dict[cmd][offset] = 1
                        x_range_dict[cmd].append(offset)
                    else:
                        y_range_dict[cmd][offset] += 1


        for cmd_idx in y_range_dict.keys():
            y_latency_group = y_range_dict[cmd_idx]
            modify_y_offset_group = list()
            for off_cnt in y_latency_group:
                modify_y_offset_group.append(y_latency_group[off_cnt])

            cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['Color']
            cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
            cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']

            item = pg.ScatterPlotItem(x=x_range_dict[cmd_idx], y=modify_y_offset_group, symbol=cmd_symbol, name=cmd_name,bursh=cmd_color,pen=cmd_color)
            self.plotItem.addItem(item)

    def setworkload_instance(self,workload_instacne):
        self.workload_instance = workload_instacne

    def load(self):
        pass

    def get_rage_of_viewbox(self):
        pass

    def cus_clearallitem(self):
        self.plotItem.clear()
        print('clear all item')

    def handledoubleclicked(self, event: QMouseEvent):
        if event.double():
            self.getPlotItem().getViewBox().autoRange()


    def summary_latency_operation(self):

        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]

        if self.raw_item == '':
            # self.summayr_text_box.setPlainText('Initialize.....')
            print('initilzae')
            return
        if len(self.raw_item) == 0:
            # self.summayr_text_box.setPlainText('Initialize.....')
            print('initilzae')
            return

        block_size = dict()
        cmd_latency_distribution = dict()
        rsp_latency_distribution = dict()
        idle_list = list()

        for item in self.raw_item:
            if (item['time'] > x_min) & (item['time'] < x_max):
                if (item['cmd_latency'] > y_min) & (item['cmd_latency'] < y_max):

                    if item['cmd'] not in block_size:
                        block_size[item['cmd']] = dict()
                        block_size[item['cmd']][item['length']] = 1
                    else:
                        if item['length'] not in block_size[item['cmd']]:
                            block_size[item['cmd']][item['length']] = 1
                        else:
                            block_size[item['cmd']][item['length']] += 1

                    if item['cmd'] not in cmd_latency_distribution:
                        cmd_latency_distribution[item['cmd']] = dict()
                        cmd_latency_distribution[item['cmd']][item['cmd_latency']] = 1
                    else:
                        if item['length'] not in cmd_latency_distribution[item['cmd']]:
                            cmd_latency_distribution[item['cmd']][item['cmd_latency']] = 1
                        else:
                            cmd_latency_distribution[item['cmd']][item['cmd_latency']] += 1

                    if item['idle'] > 0:
                        idle_list.append(item['idle'])

                elif (item['rsp_latency'] > y_min) & (item['rsp_latency'] < y_max):
                    if item['cmd'] not in block_size:
                        block_size[item['cmd']] = dict()
                        block_size[item['cmd']][item['length']] = 1
                    else:
                        if item['length'] not in block_size[item['cmd']]:
                            block_size[item['cmd']][item['length']] = 1
                        else:
                            block_size[item['cmd']][item['length']] += 1

                    if item['cmd'] not in rsp_latency_distribution:
                        rsp_latency_distribution[item['cmd']] = dict()
                        rsp_latency_distribution[item['cmd']][item['cmd_latency']] = 1
                    else:
                        if item['length'] not in rsp_latency_distribution[item['cmd']]:
                            rsp_latency_distribution[item['cmd']][item['cmd_latency']] = 1
                        else:
                            rsp_latency_distribution[item['cmd']][item['cmd_latency']] += 1

                    if item['idle'] > 0:
                        idle_list.append(item['idle'])

        summary_data = ''
        time_difference = x_max - x_min
        summary_data += 'Difference time : ' + str(time_difference) + 'sec\n'
        tot_block_size = 0
        for cmd_idx in block_size:
            each_cmd_block_size = 0
            for blk_idx in block_size[cmd_idx]:
                each_cmd_block_size += blk_idx * block_size[cmd_idx][blk_idx]
            tot_block_size += each_cmd_block_size
            each_cmd_block_size = each_cmd_block_size / 1024
            summary_data += str('CMD[{}]: {:.2f} MiB/s \n'.format(cmd_idx, (each_cmd_block_size / time_difference)))
        summary_data += str('CMD[{}]: {:.2f} MiB/s \n'.format(cmd_idx, each_cmd_block_size / time_difference))

        for cmd_idx in cmd_latency_distribution:
            for each_lateny_dist_item in cmd_latency_distribution[cmd_idx]:
                summary_data += str('Command CMD[{}]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item,
                                                                                   cmd_latency_distribution[cmd_idx][
                                                                                       each_lateny_dist_item]))

        for cmd_idx in rsp_latency_distribution:
            for each_lateny_dist_item in rsp_latency_distribution[cmd_idx]:
                summary_data += str('Response CMD[%d]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item,
                                                                                    rsp_latency_distribution[cmd_idx][
                                                                                        each_lateny_dist_item]))

        tot_idle_time = 0
        for cmd_idx in idle_list:
            tot_idle_time += idle_list[cmd_idx]
        summary_data += str('IDLE : {}us-{}counts \n'.format(tot_idle_time, len(idle_list)))

        summary = '[Selected range] \n' + 'x_min:' + str(round(x_min, 3)) + ' x_max:' + str(
            round(x_max, 3)) + ' y_min:' + str(round(y_min, 3)) + ' y_min:' + str(round(y_max, 3))
        summary += summary_data
        print(summary)
        self.summary_box.setPlainText(summary)
        return

    def set_Qapplication_instance(self, QApplication_instance, summary_box):
        self.qapp = QApplication_instance
        self.summary_box = summary_box
        return

    def mouseReleaseEvent(self, evt):
        # pass
        try:
            if (evt.button() == Qt.LeftButton) & (self.qapp.keyboardModifiers() == Qt.ControlModifier):
                self.summary_latency_operation()

                super().mouseReleaseEvent(evt)
                if not self.mouseEnabled:
                    return
                self.sigMouseReleased.emit(evt)
                self.lastButtonReleased = evt.button()
            else:
                super().mouseReleaseEvent(evt)
                if not self.mouseEnabled:
                    return
                self.sigMouseReleased.emit(evt)
                self.lastButtonReleased = evt.button()
        except:
            super().mouseReleaseEvent(evt)
            if not self.mouseEnabled:
                return
            self.sigMouseReleased.emit(evt)
            self.lastButtonReleased = evt.button()

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Control:
            self.getPlotItem().getViewBox().setMouseMode(1)
            self.getPlotItem().setMouseEnabled(x=False, y=True)
        elif event.key() == Qt.Key_Alt:
            self.getPlotItem().getViewBox().setMouseMode(1)
            self.getPlotItem().setMouseEnabled(x=True, y=False)
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        self.getPlotItem().getViewBox().setMouseMode(3)
        self.getPlotItem().setMouseEnabled(x=True, y=True)
        super().keyReleaseEvent(event)

