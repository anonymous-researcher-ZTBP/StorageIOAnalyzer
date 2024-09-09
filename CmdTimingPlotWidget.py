import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QKeyEvent
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
import numpy as np
from pyqtgraph import getConfigOption
from pyqtgraph import functions as fn
import copy
from pyqtgraph import Point
from math import atan2, degrees

class RectItem(pg.GraphicsObject):

    sigPlotChanged = PyQt5.QtCore.pyqtSignal(object)
    sigClicked = PyQt5.QtCore.pyqtSignal(object, object)

    textItem = None
    anchor = None
    rotateAxis = None
    _lastScene = None
    _lastTransform = None

    def __init__(self,*args, **kargs):
        super().__init__()
        self.picture = QtGui.QPicture()
        try:
            self.textItem = pg.QtWidgets.QGraphicsTextItem()
        except:
            self.textItem = pg.Qt.QtWidgets.QGraphicsTextItem()
        self._lastScene = None
        self._lastTransform = None
        self.anchor = None
        self.rotateAxis = None

        self.opts = {
            'shadowPen': None,
            'fillLevel': None,
            'fillOutline': False,
            'brush': None,
            'stepMode': None,
            'name': None,
            'antialias': getConfigOption('antialias'),
            'connect': 'all',
            'mouseWidth': 8, # width of shape responding to mouse click
            'compositionMode': None,
            'skipFiniteCheck': False,
            # 'segmentedLineMode': getConfigOption('segmentedLineMode'),
            'rect':None
        }

        if 'pen' not in kargs:
            self.opts['pen'] = fn.mkPen('w')

        self.setClickable(kargs.get('clickable', True))
        self.setData(*args, **kargs)
        # self._generate_picture()

    def setAngle(self, angle):
        """
        Set the angle of the text in degrees.

        This sets the rotation angle of the text as a whole, measured
        counter-clockwise from the x axis of the parent. Note that this rotation
        angle does not depend on horizontal/vertical scaling of the parent.
        """
        self.angle = angle
        self.updateTransform(force=True)

    @property
    def setrect(self,rect):
        self.opts['rect']=rect

    def setData(self, *args, **kargs):
        # self.clear()  ## clear out all old data
        self.updateData(*args, **kargs)

    def updateData(self, *args, **kargs):
        # if 'compositionMode' in kargs:
        #     self.setCompositionMode(kargs['compositionMode'])
        self.opts['rect'] = kargs['rect']

        # self.invalidateBounds()
        # self.prepareGeometryChange()
        # self.informViewBoundsChanged()

        self.path = None
        self.fillPath = None
        self._fillPathList = None
        self._mouseShape = None
        self._renderSegmentList = None

        if 'name' in kargs:
            self.opts['name'] = kargs['name']
        if 'connect' in kargs:
            self.opts['connect'] = kargs['connect']
        if 'pen' in kargs:
            self.setPen(kargs['pen'])
        if 'shadowPen' in kargs:
            self.setShadowPen(kargs['shadowPen'])
        if 'fillLevel' in kargs:
            self.setFillLevel(kargs['fillLevel'])
        if 'fillOutline' in kargs:
            self.opts['fillOutline'] = kargs['fillOutline']
        if 'bursh' in kargs:
            self.setBrush(kargs['bursh'])
        if 'antialias' in kargs:
            self.opts['antialias'] = kargs['antialias']
        if 'skipFiniteCheck' in kargs:
            self.opts['skipFiniteCheck'] = kargs['skipFiniteCheck']

        if 'pen' not in kargs:
            self.opts['pen'] = fn.mkPen('w')
        if 'bursh' not in kargs:
            self.opts['bursh'] = pg.mkBrush("g")
        self.update()
        self.sigPlotChanged.emit(self)

        self._generate_picture()

    def setClickable(self, s, width=None):
        """Sets whether the item responds to mouse clicks.

        The `width` argument specifies the width in pixels orthogonal to the
        curve that will respond to a mouse click.
        """
        self.clickable = s
        if width is not None:
            self.opts['mouseWidth'] = width
            self._mouseShape = None
            self._boundingRect = None

    def _generate_picture(self):
        painter = QtGui.QPainter(self.picture)
        painter.setPen(self.opts['pen'])
        painter.setBrush(self.opts['bursh'])

        # painter.drawStaticText('right',self.opts['name'])
        for item in self.opts['rect']:

            # painter.drawText(QtCore.QPointF(item.x(),item.y()),self.opts['name'])
            painter.setPen(self.opts['pen'])
            painter.setBrush(self.opts['bursh'])
            painter.drawRect(item)

            # if np.random.randint(100) % 1 == 0 :
            #     painter.save()
            #     painter.setPen(Qt.cyan)
            #     painter.setBrush(self.opts['bursh'])
            #     # painter.rotate(90)
            #     # painter.translate(150,-60)
            #     font = QtGui.QFont()
            #     font.setPointSizeF(1)
            #     painter.setFont(font)
            #     # text_item=pg.QtWidgets.QGraphicsTextItem()
            #     pos=QtCore.QPointF()
            #     pos.setX(item.x())
            #     pos.setY(item.y())
            #     # text_item.setPlainText('test')
            #     # pt = QtGui.QTransform()
            #     # pt.setMatrix(text_item.sceneTransform().m11()
            #     #     ,)
            #     painter.scale(-1,1)
            #     painter.rotate(180)
            #
            #     text_rect = copy.deepcopy(item)
            #     item.setY(item.y()*(-1))
            #     painter.drawText(item, 'Test')
            #     painter.restore()
        painter.end()

    def updateTransform(self, force=False):
        if not self.isVisible():
            return

        # update transform such that this item has the correct orientation
        # and scaling relative to the scene, but inherits its position from its
        # parent.
        # This is similar to setting ItemIgnoresTransformations = True, but
        # does not break mouse interaction and collision detection.
        p = self.parentItem()
        if p is None:
            pt = QtGui.QTransform()
        else:
            pt = p.sceneTransform()

        if not force and pt == self._lastTransform:
            return

        t = pt.inverted()[0]
        # reset translation
        t.setMatrix(t.m11(), t.m12(), t.m13(), t.m21(), t.m22(), t.m23(), 0, 0, t.m33())

        # apply rotation
        angle = -self.angle
        if self.rotateAxis is not None:
            d = pt.map(self.rotateAxis) - pt.map(Point(0, 0))
            a = degrees(atan2(d.y(), d.x()))
            angle += a
        t.rotate(angle)
        self.setTransform(t)
        self._lastTransform = pt
        self.updateTextPos()

    def updateTextPos(self):
        # update text position to obey anchor
        try:
            r = self.textItem.boundingRect()
            tl = self.textItem.mapToParent(r.topLeft())
            br = self.textItem.mapToParent(r.bottomRight())
            offset = (br - tl) * self.anchor
            self.textItem.setPos(-offset)
        except:
            None

    def setBrush(self,*args,**kargs):
        if args[0] is None:
            self.opts['bursh'] = None
        else:
            self.opts['bursh'] = pg.mkBrush(args[0])

    def paint(self, painter, option, widget=None):
        painter.drawPicture(0, 0, self.picture)

    def boundingRect(self):
        return QtCore.QRectF(self.picture.boundingRect())

    def name(self):
        return self.opts['name']

    def implements(self, interface=None):
        ints = ['plotData']
        if interface is None:
            return ints
        return interface in ints

    def setPen(self, *args, **kargs):
        """Set the pen used to draw the curve."""
        if args[0] is None:
            self.opts['pen'] = None
        else:
            self.opts['pen'] = fn.mkPen(*args, **kargs)
        self.invalidateBounds()
        self.update()


class CmdTimingPlotwidget(pg.PlotWidget):
    raw_item = ''
    input_key_event = ''
    qapp = ''
    summary_box = ''
    latency_marker = ''
    workload_instance = ''
    die_event_tracker = ''

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene().sigMouseClicked.connect(self.handledoubleclicked)

        plt = self.getPlotItem()
        plt.showGrid(x=True, y=True)
        plt.addLegend()

        # set properties
        plt.setLabel('left', 'Task ID', units='#')
        plt.setLabel('bottom', 'Time', units='us')

        plt.setMouseEnabled(x=True, y=True)
        task_item = list()
        for idx in range(128):
            task_item.append((idx,'Task #'+str(idx)))

        for idx in range(32):
            task_item.append((-1*idx+-1, 'Die #' + str(idx)))

        self.getAxis('left').setTicks([task_item])

        self.latency_marker = pg.LinearRegionItem()
        self.latency_marker.setZValue(-10)
        plt.addItem(self.latency_marker)
        self.latency_marker.sigRegionChanged.connect(self.updateMarker)

    def updateMarker(self):
        region = self.latency_marker.getRegion()
        return

    def set_workload_item(self,raw_item):
        self.raw_item = raw_item

    def set_event_tracer_item(self,die_evt_tracker):
        self.die_event_tracker = die_evt_tracker

    def show_plot_item(self,*args):

        self.clear()
        time_x_range=args[0]
        y_range_dict = dict()
        x_range_dict = list()

        for item in self.raw_item:

            if (item['time'] >= time_x_range['start']) & (item['time'] < time_x_range['end']):
                if item['request_arrow'] == 'req':
                    if item['request_arrow'] != 'req':
                        continue
                    latency = item['cmd_latency']
                    cmdq = item['cmdq']
                    cmd = item['cmd']

                    x_range_dict.append(item['time'])
                    x_range_dict.append(item['time']+(item['cmd_latency']))
                    x_start_time = item['time']

                    try:
                        if item['etc'].lower().__contains__('collision'):
                            text_item=pg.TextItem(item['etc'],(255,160,122))
                            text_item.setPos(item['time'],cmdq+1)
                            text_item.setFont(QtGui.QFont('Times',10))
                            # text_item.setTextWidth(4)
                            self.plotItem.addItem(text_item)
                    except:
                        None

                    try:
                        if item['etc'] != '':
                            text_item=pg.TextItem(item['etc'],(255,160,122))
                            text_item.setPos(item['time'],cmdq+1)
                            text_item.setFont(QtGui.QFont('Times',10))
                            # text_item.setTextWidth(4)
                            self.plotItem.addItem(text_item)
                    except:
                        None

                    item = QtCore.QRectF(x_start_time, cmdq, latency, 0.9)
                    if cmd not in y_range_dict:
                        y_range_dict[cmd] = list()
                        y_range_dict[cmd].append(item)
                    else:
                        y_range_dict[cmd].append(item)

        for cmd_idx in y_range_dict.keys():

            y_latency_group = y_range_dict[cmd_idx]
            cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['CMDQ_Color']
            cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
            cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']

            item = RectItem(x=x_range_dict,rect=y_latency_group,symbol=cmd_symbol,name=cmd_name,bursh=cmd_color)
            self.plotItem.addItem(item)

        y_range_dict = dict()
        x_range_dict = list()

        for die_num in self.die_event_tracker.keys():

            for item in self.die_event_tracker[die_num]:

                if (item['start_time'] >= time_x_range['start']) & (item['start_time'] < time_x_range['end']):
                    latency = item['end_time'] - item['start_time']
                    cmd = item['cmd']

                    x_range_dict.append(item['start_time'])
                    x_range_dict.append(item['end_time'])
                    x_start_time = item['start_time']
                    item = QtCore.QRectF(x_start_time, die_num*(-1)-2, latency, 0.9)
                    if cmd not in y_range_dict:
                        y_range_dict[cmd] = list()
                        y_range_dict[cmd].append(item)
                    else:
                        y_range_dict[cmd].append(item)

        for cmd_idx in y_range_dict.keys():

            y_latency_group = y_range_dict[cmd_idx]

            cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['CMDQ_Color']
            # cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']+str(die_num)
            cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
            cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']

            item = RectItem(x=x_range_dict,rect=y_latency_group,symbol=cmd_symbol,name=cmd_name,bursh=(cmd_color))

            self.plotItem.addItem(item)


    def setworkload_instance(self,workload_instacne):
        self.workload_instance = workload_instacne

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


    def load(self):
        pass

    def get_rage_of_viewbox(self):
        pass

    def cus_clearallitem(self):
        self.plotItem.clear()
        self.scene().clear()
        print('clear all item')

    def handledoubleclicked(self, event: QMouseEvent):
        if event.double():
            self.getPlotItem().getViewBox().autoRange()
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

        for item in self.raw_item:
            if ( item['time'] > x_min ) & ( item['time'] < x_max ):
                if (item['cmd_latency'] > y_min) & (item['cmd_latency'] < y_max):

                    if item['cmd'] not in block_size:
                        block_size[item['cmd']]=dict()
                        block_size[item['cmd']][item['length']] = 1
                    else:
                        if item['length'] not in block_size[item['cmd']]:
                            block_size[item['cmd']][item['length']] = 1
                        else:
                            block_size[item['cmd']][item['length']] += 1

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
        time_difference = x_max - x_min
        summary_data += 'Difference time : '+str(time_difference)+'sec\n'
        tot_block_size = 0
        for cmd_idx in block_size:
            each_cmd_block_size = 0
            for blk_idx in block_size[cmd_idx]:
                each_cmd_block_size += blk_idx * block_size[cmd_idx][blk_idx]
            tot_block_size +=each_cmd_block_size
            each_cmd_block_size = each_cmd_block_size/1024
            summary_data += str('CMD[{}]: {:.2f} MiB/s \n' .format(cmd_idx,(each_cmd_block_size/time_difference) ))
        summary_data += str('CMD[{}]: {:.2f} MiB/s \n'.format(cmd_idx,each_cmd_block_size/time_difference) )

        for cmd_idx in cmd_latency_distribution:
            for each_lateny_dist_item in cmd_latency_distribution[cmd_idx]:
                summary_data += str('Command CMD[{}]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item , cmd_latency_distribution[cmd_idx][each_lateny_dist_item]))

        for cmd_idx in rsp_latency_distribution:
            for each_lateny_dist_item in rsp_latency_distribution[cmd_idx]:
                summary_data += str('Response CMD[%d]: {:.2f}us-{}counts \n'.format(cmd_idx, each_lateny_dist_item , rsp_latency_distribution[cmd_idx][each_lateny_dist_item]))

        tot_idle_time = 0
        for cmd_idx in idle_list:
            tot_idle_time += idle_list[cmd_idx]
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

