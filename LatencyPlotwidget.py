import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
import numpy as np

class custom_scatterplotItem(pg.ScatterPlotItem):

    painter = ''
    workload_instance = ''


    def __init__(self, *args, **kargs):
        super().__init__(*args,**kargs)

    def set_stem_plot(self):
        self.picture = PyQt5.QtGui.QPicture()
        self.painter = PyQt5.QtGui.QPainter(self.picture)
        self.painter.setPen(pg.mkPen('r',width=10))
        # x_data = args[0]
        # y_data = args[1]
        for item in self.data:
            self.painter.drawLine(PyQt5.QtCore.QPointF(item[1],0),PyQt5.QtCore.QPointF(item[1],item[0]))

    def paint_stem(self):
        self.painter.drawPicture(0,0,self.picture)

class LatencyPlotwidget(pg.PlotWidget):
    raw_item = ''
    input_key_event = ''
    qapp = ''
    summary_box = ''
    latency_marker = ''

    cmd_timing_plot = ''
    main_ui_object = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        # self.parent_widget =
        self.scene().sigMouseClicked.connect(self.handledoubleclicked)

        plt = self.getPlotItem()
        plt.showGrid(x=True, y=True)
        plt.addLegend()

        # set properties
        plt.setLabel('left', 'latency', units='us')
        plt.setLabel('bottom', 'Time', units='us')

        plt.setMouseEnabled(x=True, y=True)

        self.latency_marker = pg.LinearRegionItem()
        self.latency_marker.sigRegionChanged.connect(self.updateMarker)

    def updateMarker(self):
        region = self.latency_marker.getRegion()
        return

    def show_plot_item(self,raw_item,rsp_or_req):
        self.clear()
        x_range_dict = dict()
        y_range_dict = dict()
        self.raw_item = raw_item
        for item in raw_item:
            if rsp_or_req == 'CMD':
                if item['request_arrow'] == 'req':

                    if item['request_arrow'] != 'req':
                        continue

                    latency=item['cmd_latency']
                    cmd = item['cmd']

                    if cmd not in x_range_dict:
                        x_range_dict[cmd] = list()
                        x_range_dict[cmd].append(item['time'])
                    else:
                        x_range_dict[cmd].append(item['time'])

                    if cmd not in y_range_dict:
                        y_range_dict[cmd] = list()
                        y_range_dict[cmd].append(latency)
                    else:
                        y_range_dict[cmd].append(latency)

            elif rsp_or_req == 'RSP':

                if item['request_arrow'] != 'rsp':
                    continue

                latency = item['rsp_latency']
                cmd = item['cmd']

                if cmd not in x_range_dict:
                    x_range_dict[cmd] = list()
                    x_range_dict[cmd].append(item['time'])
                else:
                    x_range_dict[cmd].append(item['time'])

                if cmd not in y_range_dict:
                    y_range_dict[cmd] = list()
                    y_range_dict[cmd].append(latency)
                else:
                    y_range_dict[cmd].append(latency)

        for cmd_idx in x_range_dict.keys():
            x_latency_group = x_range_dict[cmd_idx]
            y_latency_group = y_range_dict[cmd_idx]
            bar_width = (self.getPlotItem().size().width()) / (len(self.raw_item) * 10)

            _x_latency_group = list()
            _y_latency_group = list()
            for x_item in x_latency_group:
                _x_latency_group.append(x_item)
                _x_latency_group.append(x_item)

            for y_item in y_latency_group:
                _y_latency_group.append(y_item)
                _y_latency_group.append(0)

            cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['Color']
            cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
            cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']
            item = pg.PlotDataItem(x_latency_group,y_latency_group,pen=pg.mkPen(color=cmd_color, width=0, style=PyQt5.QtCore.Qt.NoPen),fillLevel = 0,symbol=cmd_symbol,symbolBrush=cmd_color,symbolSize=5 ,name=cmd_name)
            self.plotItem.addItem(item)
            item = pg.PlotCurveItem(x=_x_latency_group,y=_y_latency_group,symbol=cmd_symbol,name=cmd_name,connect='pairs',pen=pg.mkPen(color=cmd_color, width=0))
            self.plotItem.addItem(item)

    def setworkload_instance(self,main_ui_object,workload_instacne,cmd_timing_object):
        self.main_ui_object = main_ui_object
        self.workload_instance = workload_instacne
        try:
            self.cmd_timing_plot = cmd_timing_object
        except:
            None

    def temp_color_symbol_map(self,cmd):
        temp_col_sym = {
            0x01:{
                'Color':'b',
                'Symbol':'o',
                'NAME':'READ(1)'
            },
            0x10:{
                'Color':'r',
                'Symbol':'t',
                'NAME':'WRITE(10)'
            }
        }
        return temp_col_sym[cmd]

    def cus_clearallitem(self):
        self.plotItem.clear()
        print('clear all item')

    def handledoubleclicked(self, event: QMouseEvent):
        if event.double():
            self.getPlotItem().getViewBox().autoRange()
        elif event.button() == Qt.LeftButton:
            try:
                #send pos in x timing value to other widget
                start_value = self.getPlotItem().vb.mapSceneToView(event.scenePos()).x()
                try:
                    end_value = start_value + int(self.main_ui_object.main_ui_object.edt_cmd_timing_scale.text()) * 1000
                except:
                    end_value = start_value + 1000
                try:
                    self.plotItem.removeItem(self.latency_marker)
                except:
                    None
                self.latency_marker=pg.LinearRegionItem(values=(start_value,end_value))
                self.plotItem.addItem(self.latency_marker)

                send_data = {'start':start_value,'end':end_value}
                self.cmd_timing_plot.show_plot_item(send_data)
            except:
                None
        # elif ( event.button() == Qt.LeftButton ) & ( pg.QtWidgets.QApplication.instance().keyboardModifiers() == Qt.ControlModifier ):
        #     print('button',Qt.Key_Control)
        #     self.summary_latency_operation()

    def summary_latency_operation(self):

        x_min, x_max = self.getViewBox().viewRange()[0]
        y_min, y_max = self.getViewBox().viewRange()[1]

        if self.raw_item == '' :
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

        x_start_time = -1
        x_end_time = -1

        tot_collision_probability = 0
        collision_probability = dict()

        for item in self.raw_item:
            if ( item['time'] > x_min ) & ( item['time'] < x_max ):
                if (item['cmd_latency'] > y_min) & (item['cmd_latency'] < y_max):
                    if x_start_time == -1:
                        x_start_time = item['time']
                        x_end_time = item['time']
                    else:
                        if x_end_time < item['time']:
                            x_end_time = item['time']

                    if item['cmd'] not in block_size:
                        block_size[item['cmd']]=dict()
                        block_size[item['cmd']][item['length']] = 1
                    else:
                        if item['length'] not in block_size[item['cmd']]:
                            block_size[item['cmd']][item['length']] = 1
                        else:
                            block_size[item['cmd']][item['length']] += 1
                    try:
                        if item['etc'].lower().__contains__('collision'):
                            tot_collision_probability = tot_collision_probability+1
                            die_num = int(item['etc'].split(':' )[0].split('#')[1])
                            if die_num not in collision_probability.keys():
                                collision_probability[die_num] = 0
                            else:
                                collision_probability[die_num] = collision_probability[die_num]+1
                    except:
                        None

                    if item['cmd'] not in cmd_latency_distribution:
                        cmd_latency_distribution[item['cmd']]=dict()
                        cmd_latency_distribution[item['cmd']][item['cmd_latency']]=1
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
        time_difference = x_end_time - x_start_time
        time_difference = time_difference*0.000001 #us
        summary_data += 'Difference time : '+"{:.6f}".format(time_difference)+'sec'+str("({:.2f}us)").format(time_difference*1000000)+'\n'
        tot_block_size = 0
        tot_io_cnt = 0
        for cmd_idx in block_size:
            each_cmd_block_size = 0
            each_cmd_cnt = 0
            for blk_idx in block_size[cmd_idx]:
                each_cmd_block_size = each_cmd_block_size+( blk_idx * block_size[cmd_idx][blk_idx] )/1024/1024
                each_cmd_cnt += block_size[cmd_idx][blk_idx]
            tot_block_size = tot_block_size + ( each_cmd_block_size )
            tot_io_cnt = tot_io_cnt + each_cmd_cnt
            summary_data += str('CMD[{}] Size: {:.2f} MiB \n'.format(self.temp_color_symbol_map(cmd_idx)['NAME'], each_cmd_block_size ))
            summary_data += str('CMD[{}]: {:.2f} MiB/s \n' .format(self.temp_color_symbol_map(cmd_idx)['NAME'],(each_cmd_block_size/time_difference) ))
            summary_data += str('CMD[{}]: {:.2f} KIOPs \n'.format(self.temp_color_symbol_map(cmd_idx)['NAME'],(each_cmd_cnt / time_difference)/1000))

        summary_data += str('Total Size: {:.2f} MiB \n'.format(tot_block_size))
        summary_data += str('Total Mixed Bandwidth: {:.2f} MiB/s \n'.format(tot_block_size/time_difference) )
        summary_data += str('Total Mixed IOPs: {:.2f} KIOPs \n'.format((tot_io_cnt / time_difference)/1000))
        summary_data += str('Total collsion : {:.2f} % \n'.format((tot_collision_probability / len(self.raw_item)) *100) )

        for i in sorted(collision_probability.keys()):
            summary_data += str('Die {:.2f}:{:.2f} % \n'.format(i,(collision_probability[i] / len(self.raw_item)) * 100))
        summary_data += str()

        # for cmd_idx in cmd_latency_distribution:
        #     for each_lateny_dist_item in cmd_latency_distribution[cmd_idx]:
        #         summary_data += str('Command CMD[{}]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item , cmd_latency_distribution[cmd_idx][each_lateny_dist_item]))
        #
        # for cmd_idx in rsp_latency_distribution:
        #     for each_lateny_dist_item in rsp_latency_distribution[cmd_idx]:
        #         summary_data += str('Response CMD[%d]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item , rsp_latency_distribution[cmd_idx][each_lateny_dist_item]))

        tot_idle_time = 0
        for cmd_idx in idle_list:
            tot_idle_time += cmd_idx
        summary_data += str( 'IDLE : {}us-{}counts \n'.format(tot_idle_time, len(idle_list)) )

        summary = '[Selected range] \n'+'x_min:'+ str(round(x_min,3))+' x_max:'+str(round(x_max,3))+' y_min:'+str(round(y_min,3))+' y_min:'+str(round(y_max,3))
        summary += summary_data
        print(summary)
        self.summary_box.setPlainText(summary)
        return

    def set_Qapplication_instance(self,QApplication_instance,summary_box):
        self.qapp = QApplication_instance
        self.summary_box = summary_box
        return

    def mouseReleaseEvent(self,evt):
        # pass
        try:
            if ( evt.button() == Qt.LeftButton ) & ( self.qapp.keyboardModifiers() == Qt.ControlModifier ):
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

