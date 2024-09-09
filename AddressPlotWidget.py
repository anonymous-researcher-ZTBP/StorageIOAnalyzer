import PyQt5
import pyqtgraph as pg
from PyQt5.QtGui import QKeyEvent
import PyQt5.QtGui as QtGui
import PyQt5.QtCore as QtCore
from PyQt5.QtCore import Qt,pyqtSignal
from PyQt5.QtGui import QMouseEvent
import numpy as np

from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
from sklearn.metrics import silhouette_score

class AddressPlotWidget(pg.PlotWidget):
    raw_item = ''
    input_key_event = ''
    qapp = ''
    summary_box = ''
    latency_marker = ''
    workload_instance = ''

    y_range_dict = dict()
    x_range_dict = dict()
    progressChanged = pyqtSignal(int)


    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene().sigMouseClicked.connect(self.handledoubleclicked)

        plt = self.getPlotItem()
        plt.showGrid(x=True, y=True)
        plt.addLegend()

        # set properties
        plt.setLabel('left', 'Offset', units='B')
        plt.setLabel('bottom', 'Accumulated Size', units='Bytes')

        plt.setMouseEnabled(x=True, y=True)

        self.latency_marker = pg.LinearRegionItem()
        self.latency_marker.setZValue(-10)
        plt.addItem(self.latency_marker)
        self.latency_marker.sigRegionChanged.connect(self.updateMarker)

    def updateMarker(self):
        region = self.latency_marker.getRegion()
        return

    def kfold_operation(self,scale_data):

        # Assuming X is your dataset with 50000 samples
        # For demonstration purposes, we're generating random data
        X = scale_data
        # Define k-fold cross-validation
        kf = KFold(n_splits=5)

        # Placeholder for the best parameters
        best_eps = None
        best_min_samples = None
        best_silhouette = -1

        # Parameter grid (These ranges are arbitrary for demonstration and should be adjusted based on EDA)
        eps_values = np.arange(0.01, 0.05, 0.01)  # Example range for eps
        min_samples_values = np.arange(20, 50, 10)  # Example range for min_samples
        prgress = 0
        # Iterate over all possible combinations of eps and min_samples
        for eps in eps_values:
            for min_samples in min_samples_values:
                silhouette_avg = []
                # Perform k-fold CV
                for train_index, test_index in kf.split(X):
                    # Split the data into training and testing sets
                    X_train, X_test = X[train_index], X[test_index]

                    # Apply DBSCAN to the training set
                    db = DBSCAN(eps=eps, min_samples=min_samples).fit(X_train)
                    test_labels = db.fit_predict(X_test)
                    prgress += 1
                    self.progressChanged.emit(round((prgress / (len(eps_values) * len(min_samples_values) * 5)) * 100))

                    # Evaluate the clustering performance on the test set
                    # Silhouette score can only be computed if there are more than one cluster present, and not noise
                    if len(np.unique(test_labels)) > 1:
                        score = silhouette_score(X_test, test_labels)
                        silhouette_avg.append(score)

                # Calculate the average silhouette score for the current parameters
                if silhouette_avg:
                    silhouette_avg_score = np.mean(silhouette_avg)
                    # Update best parameters if current ones are better
                    if silhouette_avg_score > best_silhouette:
                        best_eps = eps
                        best_min_samples = min_samples
                        best_silhouette = silhouette_avg_score

        # Print the best parameters found
        print(f'Best eps: {best_eps}, Best min_samples: {best_min_samples}, Best silhouette score: {best_silhouette}')

        return best_eps,best_min_samples

    def test_pattern_recognization(self,status_bar,txt):
        self.progressChanged.connect(status_bar)
        if len(self.raw_item) == 0:
            print('None of raw data')
            return
        else:
            self.clear()
            print('DB Scan Enable')
            for cmd_idx in self.y_range_dict.keys():
                y_latency_group = self.y_range_dict[cmd_idx]
                x_range_group = self.x_range_dict[cmd_idx]
                temp_list = list()
                for idx in range(0, len(x_range_group)):
                    temp_list.append([x_range_group[idx], y_latency_group[idx]])
                scaler=StandardScaler()
                scale_data=scaler.fit_transform(temp_list)

                try:
                    val_eps=float(txt.split(',')[0].split('eps:')[1])
                    val_min_samples = int(txt.split(',')[1].split('min_samples:')[1])
                except:
                    val_eps = 0.05
                    val_min_samples = 20

                # val_eps, val_min_samples = self.kfold_operation(scale_data)
                dbscan = DBSCAN(eps=val_eps, min_samples=val_min_samples)
                clusters = dbscan.fit_predict(scale_data)

                color_list = ['r', 'g', 'b', 'c', 'm', 'y', 'w', 'k']
                cmap = {label: np.random.choice(color_list) for label in set(clusters)}

                clusters_group = dict()
                zone_freq_info = dict()
                for i in range(scale_data.shape[0]):
                    self.raw_item[i]['cluster'] = clusters[i]
                    #second filter
                    if clusters[i] !=-1:
                        try:
                            zone_freq_info[self.raw_item[i]['zone_id']] += 1
                        except:
                            zone_freq_info[self.raw_item[i]['zone_id']] = 1

                    if not  clusters[i] in clusters_group:
                        clusters_group[clusters[i]] = {'x':[scale_data[i, 0]],'y':[scale_data[i, 1]]}

                    else:
                        clusters_group[clusters[i]]['x'].append(scale_data[i, 0])
                        clusters_group[clusters[i]]['y'].append(scale_data[i, 1])
                    # scatter.addPoints(x=[scale_data[i, 0]], y=[scale_data[i, 1]], brush=brush)
                    # status_bar.setValue(round((i/(scale_data.shape[0]*1.0))*100))
                    self.progressChanged.emit(round((i/(scale_data.shape[0]*1.0))*100))

                # print(sorted(zone_freq_info.items(), key=lambda x: x[1], reverse=True)[:5])

                for group_idx in clusters_group.keys():
                    cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME'] + 'DB_SCAN_' +str(group_idx)
                    cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']
                    color = cmap[group_idx]
                    brush = pg.mkBrush(color)
                    scatter = pg.ScatterPlotItem(symbol=cmd_symbol, name=cmd_name,x=clusters_group[group_idx]['x'],y=clusters_group[group_idx]['y'],brush=brush)
                    self.plotItem.addItem(scatter)

                # status_bar.setValue(0)
                self.progressChanged.emit(0)
            threshould_intensive_zone = scale_data.shape[0] / 100

            return sorted([(k, v) for k, v in zone_freq_info.items() if v > threshould_intensive_zone ], key=lambda x: x[1], reverse=True)

    def show_plot_item(self,*args):
        self.clear()
        try:
            raw_item=args[0]
        except:
            None
        self.raw_item = raw_item

        self.y_range_dict.clear()
        self.x_range_dict.clear()

        accumulated_size = 0
        for item in raw_item:
            if item['request_arrow'] == 'req':
                if item['request_arrow'] != 'req':
                    continue
                address = item['offset']
                # address = address / 2 / 1024 / 1024 #GB Units
                address = address / 2 #Byte Units
                cmd = item['cmd']

                try:
                    cluster = item['cluster']
                    cmd = str(cmd)+'cluster'+str(cluster)
                except:
                    None

                if cmd not in self.y_range_dict:
                    self.y_range_dict[cmd] = list()
                    self.y_range_dict[cmd].append(address)
                    self.x_range_dict[cmd] = list()
                    self.x_range_dict[cmd].append(item['length'])
                    # x_range_dict[cmd].append(item['time'])
                else:
                    self.y_range_dict[cmd].append(address)
                    self.x_range_dict[cmd].append(self.x_range_dict[cmd][-1]+item['length'])
                    # x_range_dict[cmd].append(item['time'])

        for cmd_idx in self.y_range_dict.keys():

            y_latency_group = self.y_range_dict[cmd_idx]
            x_range_group = self.x_range_dict[cmd_idx]

            try:
                cmd_color = self.workload_instance.get_typeof_symbol(cmd_idx)['Color']
                cmd_name = self.workload_instance.get_typeof_symbol(cmd_idx)['NAME']
                cmd_symbol = self.workload_instance.get_typeof_symbol(cmd_idx)['Symbol']
            except:
                cmd_color = 'b'
                cmd_name = cmd_idx
                cmd_symbol ='o'
            item = pg.ScatterPlotItem(x=x_range_group,y=y_latency_group,symbol=cmd_symbol,name=cmd_name,bursh=cmd_color,pen=cmd_color)
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

