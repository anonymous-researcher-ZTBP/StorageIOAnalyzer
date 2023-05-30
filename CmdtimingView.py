import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtSignal
from pyqtgraph import ViewBox
from HistogramPlotWidget import HistogramPlotwidget

class CmdTimingView():

    latency_plot = ''
    latency_marker = ''
    latency_viewbox = ''

    cmdtiming_plot = ''

    summary_text_box = ''

    raw_item = ''

    def __init__(self, *args,**kwargs):
        # create a plot item
        self.latency_plot = args[0]
        self.summary_text_box = args[1]
        self.cmdtiming_plot = args[2]

        # Initialize Plot
        plt = self.latency_plot
        plt.cus_clearallitem()

        # self.cmdtiming_plot.cus_clearallitem()

        summary_box = self.summary_text_box
        summary_box.setPlainText('')

    def clear_plot_and_replot(self):
        try:
            self.cmdtiming_plot.cus_clearallitem()
        except:
            self.summary_text_box.setText('plot load first')


    def load(self,main_ui_object,raw_data_load,workload_instance,die_event_tracker):
        scale = 1
        rsp_or_req = 'CMD'
        raw_item = raw_data_load

        self.latency_plot.setworkload_instance(main_ui_object,workload_instance,self.cmdtiming_plot)
        self.latency_plot.show_plot_item(raw_item,rsp_or_req)

        self.cmdtiming_plot.setworkload_instance(workload_instance)
        self.cmdtiming_plot.set_workload_item(raw_item)
        try:
            self.cmdtiming_plot.set_event_tracer_item(die_event_tracker)
        except:
            None
        self.cmdtiming_plot.show_plot_item({'start':0,'end':1000})
