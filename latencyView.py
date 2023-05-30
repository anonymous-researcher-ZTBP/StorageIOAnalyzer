import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject, pyqtSignal
from pyqtgraph import ViewBox
from HistogramPlotWidget import HistogramPlotwidget

class LatencyView():

    latency_plot = ''
    latency_marker = ''
    latency_viewbox = ''

    histogram_plot = ''

    summayr_text_box = ''

    raw_item = ''

    def __init__(self, *args,**kwargs):
        # create a plot item
        self.latency_plot = args[0]
        self.summayr_text_box = args[1]
        try:
            self.histogram_plot = args[2]
            histogram_plot = self.histogram_plot
            histogram_plot.cus_clearallitem()
        except:
            None

        # Initialize Plot
        plt = self.latency_plot
        plt.cus_clearallitem()

        summary_box = self.summayr_text_box
        summary_box.clear()


    def load(self, main_ui_object, raw_data_load, workload_instance):

        scale = 1
        rsp_or_req = 'CMD'
        raw_item = raw_data_load

        self.latency_plot.setworkload_instance(main_ui_object, workload_instance, None)
        self.latency_plot.show_plot_item(raw_item, rsp_or_req)

        self.histogram_plot.setworkload_instance(workload_instance)
        self.histogram_plot.show_plot_item(raw_item, scale, rsp_or_req)