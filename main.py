from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem,QSizePolicy
from PyQt5.QtCore import Qt
# import qwt
import sys
from StorageIO_main import Ui_MainWindow
from LoadStorageIOThread import LoadStorageIOThread
from latencyView import LatencyView
from CmdtimingView import CmdTimingView
from AddressView import AddressView
from SimulationTimingView import SimTimingView

from GenerateWorkload import GnerateWorkloadType
from GenerateWorkload import GnerateWorkload

from SimulationStorageIOThread import SimulationStorageIOType
from SimulationStorageIOThread import SimulationStorageIOThread

class MainWindow(QMainWindow):
    main_ui_object = ''

    latency_plot_class = ''
    timing_plot_class = ''
    address_plot_class = ''

    thread_list = list()
    raw_workload_list = ''
    workload_instance = ''

    _die_event_tracer = ''

    simulation_plot_class = ''
    logic_event_tracer = ''

    def __init__(self):
        super().__init__()
        main_ui = Ui_MainWindow()
        self.main_ui_object = main_ui
        main_ui.setupUi(self)
        self.setWindowTitle("Storage IO Analyzer v0.1")

        #Workload Gnerator
        self.main_ui_object.btnl_load.clicked.connect(self.on_load_button_clicked)
        self.main_ui_object.btn_delete.clicked.connect(self.on_delete_button_clicked)
        self.main_ui_object.btn_workload_gen.clicked.connect(self.on_workload_gen_clicked)

        #Viewer
        self.main_ui_object.btn_load_latency_view.clicked.connect(self.on_latency_view_clicked)
        self.main_ui_object.btn_load_TimingView.clicked.connect(self.on_timing_view_clicked)
        self.main_ui_object.btn_load_Address.clicked.connect(self.on_address_view_clicked)

        self.main_ui_object.latencyViewWidget.set_Qapplication_instance(QApplication,self.main_ui_object.summary_latency)
        self.main_ui_object.cmdLatencyWidget.set_Qapplication_instance(QApplication,self.main_ui_object.summary_timing)
        self.main_ui_object.AddressWidget.set_Qapplication_instance(QApplication,self.main_ui_object.summary_Address)
        self.main_ui_object.simulation_latency_widget.set_Qapplication_instance(QApplication,self.main_ui_object.simulation_summary_timing_)

        self.main_ui_object.btn_address_test01.clicked.connect(self.on_db_scan_clicked)

        self.main_ui_object.btn_refresh_2.clicked.connect(self.on_cmd_plot_refreshed)

        # self.main_ui_object.latencyViewWidget.scene().sigMouseClicked.connect(self.mouse_clicked)

        self.main_ui_object.btn_simulation_execute.clicked.connect(self.on_simulation_btn_clicked)
        self.main_ui_object.btn_simulation_plot.clicked.connect(self.on_simulation_workload_plot)

        self.setAcceptDrops(True)
        self.show()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            name = f.split('/')[-1].split('.')[0]
            tbl_row_cnt = self.main_ui_object.LogListView.rowCount()
            self.main_ui_object.LogListView.insertRow(tbl_row_cnt)
            print(f,tbl_row_cnt)
            checked_item=QTableWidgetItem()
            checked_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            checked_item.setCheckState(Qt.Checked)
            self.main_ui_object.LogListView.setItem(tbl_row_cnt, 0, checked_item )
            self.main_ui_object.LogListView.setItem(tbl_row_cnt, 1, QTableWidgetItem(str(tbl_row_cnt)))
            self.main_ui_object.LogListView.setItem(tbl_row_cnt, 2, QTableWidgetItem(name))
            self.main_ui_object.LogListView.setItem(tbl_row_cnt, 3, QTableWidgetItem('eBPF'))
            self.main_ui_object.LogListView.setItem(tbl_row_cnt, 4, QTableWidgetItem(f))

    def on_load_button_clicked(self):
        file_counts=self.main_ui_object.LogListView.rowCount()
        workload_file_thread_list = list()
        for idx in range(0,file_counts):
            if self.main_ui_object.LogListView.item(idx,0).checkState():
                workload_item = dict()
                type = self.main_ui_object.LogListView.item(idx,3).text()
                read_workload = self.on_raw_file_read(self.main_ui_object.LogListView.item(idx,4).text())
                workload_item['workload_type'] = type
                workload_item['workload_context'] = read_workload
                workload_file_thread_list.append(workload_item)

        Workload_thread = LoadStorageIOThread(workload_file_thread_list,self.get_workload,parent=self)
        self.thread_list.append(Workload_thread)
        # Workload_thread.finished.connect(self.get_workload)
        Workload_thread.start()

    def on_workload_gen_clicked(self):
        genworkload_class=GnerateWorkload(self.get_gen_workload,self.main_ui_object.bar_progress_load,parent=self)

        genworkload_class.setData(
            workload_quantity=int(self.main_ui_object.edt_workload_quantity.text()),
            cmd_type=self.main_ui_object.edt_workload_cmd_type.text().split(','),
            mixed_ratio=int(self.main_ui_object.edt_workload_mixed_ratio.text()),
            address_pattern=self.main_ui_object.cmb_workload_address_pattern.currentText(),
            address_range=self.main_ui_object.edt_workload_address_range.text(),
            idle_duration=int(self.main_ui_object.edt_workload_idle_duration.text()),
            idle_time=int(self.main_ui_object.edt_workload_idle_time.text()),
            max_queue=int(self.main_ui_object.edt_workload_max_queue.text()),
            read_distribution=[int(i) for i in self.main_ui_object.edt_workload_read_distribution.text().split(',')],
            read_block_size=[int(i) for i in self.main_ui_object.edt_workload_read_block.text().split(',')],
            write_distribution=[int(i) for i in self.main_ui_object.edt_workload_write_distribution.text().split(',')],
            write_block_size=[int(i) for i in self.main_ui_object.edt_workload_write_block_size.text().split(',')],
            host_if=self.main_ui_object.cmb_workload_host_if.currentText(),
            host_interval=int(self.main_ui_object.edt_workload_host_interval.text()),
            host_worker=int(self.main_ui_object.edt_workload_host_worker.text()),
            context_id=bool(self.main_ui_object.chk_workload_context_id.isChecked()),
            context_line=int(self.main_ui_object.edt_workload_context_line.text()),
        )

        genworkload_class.start()
        return

    def get_gen_workload(self,raw_workload,die_event_tracker,gen_name):
        self.main_ui_object.edt_workload_name.setText(gen_name)
        name = self.main_ui_object.edt_workload_name.text()
        print('Generated workload thread finished .....',name)

        tbl_row_cnt = self.main_ui_object.LogListView.rowCount()
        self.main_ui_object.LogListView.insertRow(tbl_row_cnt)
        checked_item = QTableWidgetItem()
        checked_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checked_item.setCheckState(Qt.Checked)
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 0, checked_item)
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 1, QTableWidgetItem(str(tbl_row_cnt)))
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 2, QTableWidgetItem(name))
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 3, QTableWidgetItem('Generated'))

        self.raw_workload_list = raw_workload
        self._die_event_tracer = die_event_tracker
        self.workload_instance = GnerateWorkloadType()
        self.show_log_item()
        self.main_ui_object.bar_progress_load.setValue(0)
        return self.raw_workload_list


    def get_workload(self,raw_workload,workload_instance):
        print('thread finished .....')
        self.raw_workload_list = raw_workload
        self.workload_instance = workload_instance
        self.show_log_item()
        return self.raw_workload_list

    def show_log_item(self):

        view=self.main_ui_object.LogitemView
        view.clear()
        view.reset()
        view.setRowCount(0)
        view.setColumnCount(7)
        headerlable = ['TIME','REQ','CMD','ADDRESS','TASK_ID','LENGTH','CMD_LATENCY','RSP_LATENCY','IDLE']
        view.setHorizontalHeaderLabels(headerlable)
        for idx in range(0,len(self.raw_workload_list)):
            view.insertRow(view.rowCount())
            view.setItem(view.rowCount() - 1, 0, QTableWidgetItem(str(self.raw_workload_list[idx]['time'])+'us'))
            view.setItem(view.rowCount() - 1, 1, QTableWidgetItem(str(self.raw_workload_list[idx]['request_arrow'])))

            name = self.workload_instance.get_typeof_symbol(self.raw_workload_list[idx]['cmd'])['NAME']
            view.setItem(view.rowCount() - 1, 2, QTableWidgetItem(name))

            address = str('{:.4f}').format(self.raw_workload_list[idx]['offset']/2/1024/1024/1024)+str('GB')
            view.setItem(view.rowCount() - 1, 3, QTableWidgetItem(address))
            view.setItem(view.rowCount() - 1, 4, QTableWidgetItem(str(self.raw_workload_list[idx]['cmdq'])))
            view.setItem(view.rowCount() - 1, 5, QTableWidgetItem(str(self.raw_workload_list[idx]['length']/1024)+'KB'))
            view.setItem(view.rowCount() - 1, 6, QTableWidgetItem(str(self.raw_workload_list[idx]['cmd_latency'])+'us'))
            view.setItem(view.rowCount() - 1, 7, QTableWidgetItem(str(self.raw_workload_list[idx]['rsp_latency'])+'us'))
            view.setItem(view.rowCount() - 1, 8, QTableWidgetItem(str(self.raw_workload_list[idx]['idle'])+'us'))

            color = self.workload_instance.get_typeof_symbol(self.raw_workload_list[idx]['cmd'])['Color']

            if color == 'b':
                color = Qt.blue
            elif color == 'r':
                color = Qt.red
            else:
                color = Qt.cyan

            for j in range(0,len(headerlable)):
                try:
                    view.item(view.rowCount() - 1,j).setBackground(color)
                    view.item(view.rowCount() - 1, j).setForeground(Qt.white)
                except:
                    None


    def on_raw_file_read(self,path):
        with open(path,'r') as file:
            content = file.readline()
        return content

    def on_delete_button_clicked(self):
        file_counts=self.main_ui_object.LogListView.rowCount()
        for idx in range(0,file_counts):
            try:
                if self.main_ui_object.LogListView.item(idx,0).checkState():
                    self.main_ui_object.LogListView.removeRow(idx)
            except:
                None
        for idx in reversed(range(0,file_counts)):
            try:
                if self.main_ui_object.LogListView.item(idx,0).checkState():
                    self.main_ui_object.LogListView.removeRow(idx)
            except:
                None


    def on_latency_view_clicked(self):
        try:
            self.latency_plot_class = LatencyView(self.main_ui_object.latencyViewWidget,self.main_ui_object.summary_latency,self.main_ui_object.HistogramViewWidget)
            self.latency_plot_class.load(self,self.raw_workload_list,self.workload_instance)
        except:
            self.main_ui_object.summary_latency.setPlainText('Not Ready')
            None

        return

    def on_timing_view_clicked(self):
        try:
            self.timing_plot_class = CmdTimingView(self.main_ui_object.cmdLatencyWidget,self.main_ui_object.summary_timing,self.main_ui_object.TimingWidget)
            self.timing_plot_class.load(self,self.raw_workload_list,self.workload_instance,self._die_event_tracer)
        except:
            self.main_ui_object.summary_timing.setPlainText('Not Ready')


    def on_address_view_clicked(self):
        try:
            self.address_plot_class = AddressView(self.main_ui_object.AddressWidget,
                                                    self.main_ui_object.summary_Address,
                                                    self.main_ui_object.AddressFrequencyWidget)
            self.address_plot_class.load(self.raw_workload_list,self.workload_instance)

        except:
            self.main_ui_object.summary_timing.setPlainText('Not Ready')

    def on_db_scan_clicked(self):
        try:
            self.address_plot_class.test_dbscan_pattern_recoginization(self.main_ui_object.bar_progress_load,self.main_ui_object.lineEdit_4.text())
        except:
            None

    def on_cmd_plot_refreshed(self):
        try:
            self.timing_plot_class.clear_plot_and_replot()
        except:
            None

    def check_res_pattern_model_result(self):
        try:
            #check status verify
            {'name':'dbscan_0_0'}
            return self.main_ui_object.tbl_pattern_model_result_2.item()
        except:
            return 0

    def on_simulation_btn_clicked(self):

        try:
            Simulation_class = SimulationStorageIOThread(self.get_simulation_workload, self.main_ui_object.bar_progress_load,
                                                parent=self)
            Simulation_class.set_base_workload(self.raw_workload_list)
            Simulation_class.setData(
                mixed_ratio = int(self.main_ui_object.edt_workload_mixed_ratio.text()),
                workload_quantity=int(self.main_ui_object.edt_workload_quantity.text()),
                idle_duration=int(self.main_ui_object.edt_workload_idle_duration.text()),
                idle_time=int(self.main_ui_object.edt_workload_idle_time.text()),
                max_queue=int(self.main_ui_object.edt_workload_max_queue.text()),
                read_distribution=[int(i) for i in
                                   self.main_ui_object.edt_workload_read_distribution.text().split(',')],
                read_block_size=[int(i) for i in self.main_ui_object.edt_workload_read_block.text().split(',')],
                write_distribution=[int(i) for i in
                                    self.main_ui_object.edt_workload_write_distribution.text().split(',')],
                write_block_size=[int(i) for i in self.main_ui_object.edt_workload_write_block_size.text().split(',')],
                host_if=self.main_ui_object.cmb_workload_host_if.currentText(),
                host_interval=int(self.main_ui_object.edt_workload_host_interval.text()),
                host_worker=int(self.main_ui_object.edt_workload_host_worker.text()),
                context_id=bool(self.main_ui_object.chk_workload_context_id.isChecked()),
                context_line=int(self.main_ui_object.edt_workload_context_line.text()),

                mem_access_arch=self.main_ui_object.cmb_cpu_architecture.currentText(),
                num_cpu = int(self.main_ui_object.edt_cpu_number.text()),
                sram_bandwidth = int(self.main_ui_object.edt_sram_bandwidth.text()),
                sram_size = int(self.main_ui_object.edt_sram_length.text()),
                sram_latency = int(self.main_ui_object.edt_sram_latency.text())*0.001,
                sram_page_units= int(self.main_ui_object.edt_cpu_sram_page_unit.text()),
                cpu_page_fault_policy = self.main_ui_object.cmb_cpu_cahce_policy.currentText(),

                dram_page_fault_policy = self.main_ui_object.cmb_dram_page_fault_policy.currentText(),
                dram_bandwidth = int(self.main_ui_object.edt_dram__bandwidth.text()),
                dram_latency = int(self.main_ui_object.edt_dram_latency.text()),
                dram_size = float(self.main_ui_object.edt_dram_length.text()),
                dram_page_units = int(self.main_ui_object.edt_dram_cache_page_unit.text()),

                pattern_workload_idx = self.check_res_pattern_model_result(),

                address_range = self.main_ui_object.edt_workload_address_range.text(),

            )
            Simulation_class.start()
        except:
            None

    def get_simulation_workload(self,raw_workload,logic_evt_tracker,name):
        print('Generated workload thread finished .....',name)

        tbl_row_cnt = self.main_ui_object.tbl_simulation_workload.rowCount()
        self.main_ui_object.tbl_simulation_workload.insertRow(tbl_row_cnt)
        checked_item = QTableWidgetItem()
        checked_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        checked_item.setCheckState(Qt.Checked)
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 0, checked_item)
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 1, QTableWidgetItem(str(tbl_row_cnt)))
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 2, QTableWidgetItem(name))
        self.main_ui_object.LogListView.setItem(tbl_row_cnt, 3, QTableWidgetItem('SimulatedWorkload'))

        self.raw_workload_list = raw_workload
        self.logic_event_tracer = logic_evt_tracker
        self.workload_instance = SimulationStorageIOType()
        self.show_log_item()
        self.main_ui_object.bar_progress_load.setValue(0)
        return self.raw_workload_list

    def on_simulation_workload_plot(self):
        try:
            self.timing_plot_class = SimTimingView(self.main_ui_object.simulation_latency_widget,self.main_ui_object.simulation_summary_timing_,self.main_ui_object.simulation_timing_widget)
            self.timing_plot_class.load(self,self.raw_workload_list,self.workload_instance,self.logic_event_tracer)
        except:
            self.main_ui_object.summary_timing.setPlainText('Not Ready')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWin = MainWindow()
    sys.exit(app.exec_())
