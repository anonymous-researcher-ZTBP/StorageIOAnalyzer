

class AddressView():

    Address_plot = ''
    Address_marker = ''
    Address_viewbox = ''

    Duplicated_plot = ''

    summary_text_box = ''

    raw_item = ''

    def __init__(self, *args,**kwargs):
        # create a plot item
        self.Address_plot = args[0]
        self.summary_text_box = args[1]
        self.Duplicated_plot = args[2]

        # Initialize Plot
        self.Address_plot.cus_clearallitem()
        self.Duplicated_plot.cus_clearallitem()

        summary_box = self.summary_text_box
        summary_box.setPlainText('')

    def load(self,raw_data_load,workload_instance):

        self.raw_item = raw_data_load
        self.Address_plot.setworkload_instance(workload_instance)
        self.Address_plot.show_plot_item(self.raw_item)

        self.Duplicated_plot.setworkload_instance(workload_instance)
        self.Duplicated_plot.show_plot_item(self.raw_item)

    def test_dbscan_pattern_recoginization(self,status_bar,txt):
        summary_text = self.Address_plot.test_pattern_recognization(status_bar, txt)
        self.summary_text_box.setPlainText(str(summary_text))
        return summary_text

