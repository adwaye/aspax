import os.path

from PyQt5.QtWidgets import *


from profiles import *
import shutil
import numpy as np
import cv2
from data_utils import find_bone_annotations, find_joint_annotations


# Global variables to flag what tab needs to be navigated back to after creating new scoring sheet
import platform
# if platform.system() == "Windows":
#     DEFAULT_OUTPUT_LOC ="C:/Users/amr62/Documents/aspax_studies_small/aspax_studies_small"#todo: change this so that people can choose what this is at installation, or maybe just store it in some metadata
# else:
DEFAULT_OUTPUT_LOC = "saved_data"
review_scoring_sheet_flag = 0
inspect_x_rays_flag = 0
zoom_tracker = 1
image_file_list = []
distance_edit_flag = 0
coordinate_count = 0
xray_image = 0



from menu_widgets import AreaMenuWidget,ScoreMenuWidget, \
    XRaySelectionMenu, XrayDataCreationDialog,  XRayCreationWindow, XrayData, NameSignature,output_annotation_name,\
    save_csv, load_csv
from PyQt5.QtGui import QFont, QFontMetrics
from imaging_widgets import ImageHandler
from diagnostic_widgets import PlotWindow


class InspectXRays(QMainWindow):

    """Main class for aspax annotator

    :param ctx: fbs Application Context for fbs compilation
    :type ctx: fbs_runtime.application_context.PyQt5.ApplicationContext


    :ivar ctx: fbs application context of application
    :vartype ctx: fbs_runtime.application_context.PyQt5.ApplicationContext
    :ivar output_loc: location where annotations should be saved. This is the folder where the studies should be saved
                      see https://people.bath.ac.uk/amr62/Projects/malard/software/aspax.html for more information on aspax
                      file structure
    :vartype output_loc: str
    :ivar xray_selection_menu:
    :vartype:
    :ivar
    :vartype
    :ivar
    :vartype
    :ivar
    :vartype
    :ivar
    :vartype

    """
    def __init__(self,ctx):

        super(InspectXRays,self).__init__()
        self.sizeObject = QDesktopWidget().screenGeometry(-1)

        #self.showMaximized()
        self.ctx = ctx
        self._panels = []
        self.output_loc = DEFAULT_OUTPUT_LOC
        self.initialise_left_panel()   #initialises self.menu_tabs and adds it to self._panels
        self.initialise_right_panel()  #initialises self.image_scene and adds it to self._panels


        # self.merge_layouts()
        self.split_layouts()
        self.setCentralWidget(self.main_widget)

        self.connect_sub_buttons()
        self.initialise_xray_record()
        self.xray_selection_menu.wd_info.setText(os.path.abspath(self.output_loc))
        self.load_new_score_sheet()




    def initialise_left_panel(self):
        """Initialises the left panel which relates to

        :return:
        :rtype:
        """
        layout = QVBoxLayout()
        self.xray_selection_menu = XRaySelectionMenu()
        self.xray_selection_menu.setMinimumWidth(500)
        self.xray_selection_menu.setMaximumWidth(500)
        # self.XRaySelectionMenu.setMaximumHeight(280)
        # self.XRaySelectionMenu.setMinimumHeight(280)
        # score_profiles = [f.split('.')[0] for f in os.listdir(self.ctx.profiles) if f.split('.')[-1]=='h5']
        score_profiles = [keys for keys,_ in self.ctx.score_profiles.items()]
        self.xray_selection_menu.score_selector.addItems(score_profiles)
        scrollbar3 = QScrollArea(widgetResizable=True)
        scrollbar3.setMaximumHeight(300)
        scrollbar3.setWidget(self.xray_selection_menu)




        layout.addWidget(scrollbar3)

        self.menu_tabs = QTabWidget()
        self.menu_tabs.setMinimumWidth(500)
        self.menu_tabs.setMaximumHeight(self.sizeObject.width()-self.xray_selection_menu.width())
        # self.menu_tabs.setMaximumWidth(500)
        # self.widget_distance_menu = DistanceMenuWidget()
        height_diff = self.height() - self.sizeObject.height()
        self.widget_area_menu     = AreaMenuWidget(self.ctx.joint_list)

        self.widget_score_menu    = ScoreMenuWidget()

        # if height_diff>0:
        #     current_table_size = self.widget_score_menu.tableView.height()
        #     self.widget_score_menu.tableView.setMaximumHeight(int((current_table_size-height_diff)*0.85))
        #     current_table_size = self.widget_score_menu.tableView.height()
        #     self.widget_area_menu.tableView.setMaximumHeight(int((current_table_size - height_diff) * 0.85))
        # self.widget_label_menu    = label_extraction_menu_widget()
        # self.menu_tabs.addTab(self.widget_distance_menu,'Distance')
        scrollbar1 = QScrollArea(widgetResizable=False)
        scrollbar1.setMaximumHeight(self.sizeObject.height()-scrollbar3.height()-20)

        scrollbar1.setWidget(self.widget_area_menu)
        self.menu_tabs.addTab(self.widget_area_menu,'Annotation')
        scrollbar2 = QScrollArea(widgetResizable=False)
        scrollbar2.setWidget(self.widget_score_menu)

        self.menu_tabs.addTab(scrollbar2,'Score')

        # self.menu_tabs.addTab(self.widget_label_menu,'Label')
        layout.addWidget(self.menu_tabs)
        self.left_panel = QWidget()
        self.left_panel.setLayout(layout)
        self._panels = self._panels+[self.left_panel]

        self.xray_record = None


    def load_new_score_sheet(self):
        """Loads a new score sheet based on the dropdown selection in self.score_selector

        :return:
        :rtype:
        """
        # profile_loc = os.path.join('score_profiles',str(self.XRaySelectionMenu.score_selector.currentText())+'.h5')
        # profile_loc = self.ctx.score_profiles[str(self.XRaySelectionMenu.score_selector.currentText())]
        profile_loc = self.ctx.score_profiles[str(self.xray_selection_menu.score_selector.currentText())]
        #print("======================")

        #print(profile_loc)
        #print("======================")
        try:
            profile = load_profile(profile_loc)
        except:
            profile = {}
        profile['score_technique'] = str(self.xray_selection_menu.score_selector.currentText())
        self.menu_tabs.removeTab(1)
        self.widget_score_menu = ScoreMenuWidget(profile=profile)
        height_diff = self.height()-self.sizeObject.height()
        # if height_diff>0:
        #     current_table_size = self.widget_score_menu.tableView.height()
        #     self.widget_score_menu.tableView.setMaximumHeight(int((current_table_size-height_diff)*0.85))
        self.widget_score_menu.tableView.setMinimumHeight(300)

        scrollbar2 = QScrollArea(widgetResizable=True)
        scrollbar2.setMaximumHeight(self.sizeObject.height() - 300-20)
        scrollbar2.setWidget(self.widget_score_menu)




        self.menu_tabs.addTab(scrollbar2,self.widget_score_menu.score_technique)
        # self.menu_tabs.addTab(self.widget_score_menu,self.widget_score_menu.score_technique)
        self.connect_score_menu_buttons()



        date, organ = self._get_image_info()
        #self.xray_record.meta_table[]
        file_loc = os.path.join(self.output_loc,'scores')
        #print(file_loc)
        file_loc = os.path.join(file_loc,date)
        file_name = os.path.join(file_loc,self.widget_score_menu.score_technique + '.csv')

        if os.path.isfile(file_name):
            my_dict = load_csv(file_name)
            self.widget_score_menu.load_table_view(my_dict)

        file_loc  = os.path.join(self.output_loc)
        file_name = os.path.join(file_loc,"annotation_tracking_"+date+".csv")
        if os.path.isfile(file_name):
            my_dict = load_csv(file_name)
            self.widget_area_menu.load_table_view(my_dict)

        #print("looking for score path")
        score_path = self.make_score_path()
        if os.path.isfile(score_path):
            #print("found score path at "+score_path)
            my_dict = load_csv(score_path)
            self.widget_score_menu.load_table_view(my_dict)
        else:
            print("did not find csv at "+score_path)
        score_path = self.make_score_path()
        self.widget_score_menu.tableView_lineEdit.setText(score_path)


    def initialise_right_panel(self):
        """Creates the image handling widget

        :return:
        :rtype:
        """

        # Creating toolbar

        # Toolbar settings - guidance on https://www.learnpyqt.com/courses/start/actions-toolbars-menus/
        self.image_widget = ImageHandler(self.ctx.image_handler_icons,self.output_loc)
        self.image_widget.setMaximumWidth(self.sizeObject.width()-500)
        self._panels = self._panels + [self.image_widget]




    def open_output_folder_selector_old(self):
        """deprecated

        :return:
        :rtype:
        """
        #print("yes man")
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.Directory)
        if dlg.exec_():
            folder_names = dlg.selectedFiles()
            self.output_loc = os.path.join(os.sep,folder_names[0])
            self.image_widget.output_loc = self.output_loc
            if not os.path.isdir(self.output_loc):
                os.makedirs(self.output_loc)
            self.xray_selection_menu.wd_info.setText(self.output_loc)
            self.xray_selection_menu.combobox_xrayid.clear()
            self.xray_selection_menu.combobox_studyid.clear()
            self.display_studies()
            #self.display_xrays()


    def getDirectory(self):

        response = QFileDialog.getExistingDirectory(
            self,
            caption='Select a folder'
        )
        return response


    def open_output_folder_selector(self):
        #print("yes man")
        # response = QFileDialog.getOpenFileName(
        #     parent=self,
        #     caption='Select a data file',
        #     directory=os.getcwd(),
        #     filter=file_filter,
        #     initialFilter='Excel File (*.xlsx *.xls)'
        # )
        # QFileDialog.getExistingDirectory(self, 'Select Folder')
        # response = QFileDialog.getExistingDirectory(self, "Open Directory",
        #                                "/home",
        #                                QFileDialog.ShowDirsOnly
        #                                | QFileDialog.DontResolveSymlinks)
        response = self.getDirectory()
        #print(response)

        folder_names = response
        self.output_loc = os.path.join(os.sep,folder_names)
        self.image_widget.output_loc = self.output_loc
        if not os.path.isdir(self.output_loc):
            os.makedirs(self.output_loc)
        self.xray_selection_menu.wd_info.setText(self.output_loc)
        self.xray_selection_menu.combobox_xrayid.clear()
        self.xray_selection_menu.combobox_studyid.clear()
        self.display_studies()
            #self.display_xrays()

    def change_wd(self):
        """Method that allows one to change the working directory. Will open a dialogue for the user to interact with
        and sets the working directory name in self.xray_selection_menu.wd_info. Connected to
        self.xray_selection_menu.set_wdir_button

        :return:
        :rtype:
        """
        self.output_loc = self.xray_selection_menu.wd_info.text()
        self.image_widget.output_loc = self.output_loc
        if not os.path.isdir(self.output_loc):
            os.makedirs(self.output_loc)
        # self.XRaySelectionMenu.wd_info.setText(self.output_loc)
        self.xray_selection_menu.combobox_xrayid.clear()
        self.xray_selection_menu.combobox_studyid.clear()
        self.display_studies()


    def open_study_creator(self):
        """Opens a dialogue that allows one to create a new study by loading up an xray. Connected to
        self.xray_selection_menu.new_study_button

        :return:
        :rtype:
        """
        #print('function triggered')
        filename = self.xray_selection_menu.temp_name
        #print('filename fed to mainwindow is ')
        #print(filename)
        # f = open(filenames[0],'r')
        self.image_widget.load_image(file_name=filename)
        self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(1)
        #print("Image quality is ={:}".format(int(self.image_widget.image_quality_flag)))


        # self.create_image_menu = XrayDataCreationDialog()
        # if QMessageBox.Yes:
        self.create_xray_window = XRayCreationWindow()
        self.create_xray_window.show()
        self.name_sig = NameSignature(filename)

        # self.name_sig  = NameSignature(fileName=filename.split('/')[-1].split('.')[0])
        #print(self.name_sig.year)
        self.create_xray_window.xray_creation_options.save_button.clicked.connect(
            lambda:self.create_xray_data(filename))

        self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].setText(self.name_sig.year)
        self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(self.name_sig.id)
        self.create_xray_window.xray_creation_options.qline_edits['Body Part'].setText(self.name_sig.organ)
        self.create_xray_window.xray_creation_options.discard_button.clicked.connect(
            lambda:self.create_xray_window.close())

    def open_study_creator_old(self):
        """deprecated

        :return:
        :rtype:
        """
        #print('function triggered')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # dlg.setFilter("Text files (*.txt)")
        filenames =[]# QStringList()

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            # f = open(filenames[0],'r')
            self.image_widget.load_image(file_name=filenames[0])
            self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(1)
            #print("Image quality is ={:}".format(int(self.image_widget.image_quality_flag)))

            self.create_image_menu = XrayDataCreationDialog()
            if QMessageBox.Yes:
                self.create_xray_window = XRayCreationWindow()
                self.create_xray_window.show()
                # self.name_sig  = NameSignature(fileName=filenames[0].split('/')[-1].split('.')[0])
                self.name_sig = NameSignature(fileName=filenames[0].split('/')[-1])
                #print(self.name_sig.year)
                self.create_xray_window.xray_creation_options.save_button.clicked.connect(
                    lambda:self.create_xray_data(filenames[0]))

                self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].setText(self.name_sig.year)

                self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(self.name_sig.id)
                self.create_xray_window.xray_creation_options.qline_edits['Body Part'].setText(self.name_sig.organ)


                self.create_xray_window.xray_creation_options.discard_button.clicked.connect(
                    lambda:self.create_xray_window.close())

    def open_xray_adder(self):
        """opens up a file dialog that allows the
        Connected to self.xray_selection_menu.addXrayToStudy_button

        :return:
        :rtype:
        """
        #print('function triggered')

        filename = self.xray_selection_menu.temp_name
        # f = open(filenames[0],'r')
        self.image_widget.load_image(file_name=filename)
        self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(1)
        #print("Image quality is ={:}".format(int(self.image_widget.image_quality_flag)))


        # self.create_image_menu = XrayDataCreationDialog()
        # if QMessageBox.Yes:
        self.create_xray_window = XRayCreationWindow()

        self.create_xray_window.show()
        # self.name_sig  = NameSignature(fileName=filename.split('/')[-1].split('.')[0])
        self.name_sig = NameSignature(fileName=filename)
        #print(self.name_sig.year)
        self.create_xray_window.xray_creation_options.save_button.clicked.connect(
            lambda:self.add_xray_to_study(filename))


        self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].setText(self.name_sig.year)

        self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(self.name_sig.id)
        self.create_xray_window.xray_creation_options.qline_edits['Body Part'].setText(self.name_sig.organ)
        id_text = self.xray_selection_menu.combobox_studyid.currentText()
        if id_text is not None or id_text!='':
            self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(id_text)
        self.create_xray_window.xray_creation_options.discard_button.clicked.connect(
            lambda:self.create_xray_window.close())

    def open_xray_adder_old(self):
        """deprecated

        """
        #print('function triggered')
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.AnyFile)
        # dlg.setFilter("Text files (*.txt)")
        filenames =[]# QStringList()

        if dlg.exec_():
            filenames = dlg.selectedFiles()
            # f = open(filenames[0],'r')
            self.image_widget.load_image(file_name=filenames[0])
            self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(1)
            #print("Image quality is ={:}".format(int(self.image_widget.image_quality_flag)))


            self.create_image_menu = XrayDataCreationDialog()
            if QMessageBox.Yes:
                self.create_xray_window = XRayCreationWindow()

                self.create_xray_window.show()
                # self.name_sig  = NameSignature(fileName=filenames[0].split('/')[-1].split('.')[0])
                self.name_sig = NameSignature(fileName=filenames[0].split('/')[-1])
                #print(self.name_sig.year)
                self.create_xray_window.xray_creation_options.save_button.clicked.connect(
                    lambda:self.add_xray_to_study(filenames[0]))


                self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].setText(self.name_sig.year)

                self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(self.name_sig.id)
                self.create_xray_window.xray_creation_options.qline_edits['Body Part'].setText(self.name_sig.organ)
                id_text = self.xray_selection_menu.combobox_studyid.currentText()
                if id_text is not None or id_text!='':
                    self.create_xray_window.xray_creation_options.qline_edits['Study id'].setText(id_text)


                self.create_xray_window.xray_creation_options.discard_button.clicked.connect(
                    lambda:self.create_xray_window.close())


    def create_xray_data(self,filename):
        """Gets called when a new study is created. It creates a metadata table containing info about the xray. See
        menu_widgets.XrayData for information on how this is done.

        :param filename: path to the image corresponding to the xray being added to a study
        :type filename: str
        :return:
        :rtype:
        """
        # self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date','Xray id','Xray Location']
        # self.name_sig = NameSignature(fileName=filenames[0].split('/')[-1])

        acquisition_date = self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].text()
        Xray_id          = self.create_xray_window.xray_creation_options.qline_edits['Study id'].text()
        organ_name       = self.create_xray_window.xray_creation_options.qline_edits['Body Part'].text()


        if os.path.isdir(os.path.join(self.output_loc,Xray_id)):
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Study with same Id already exists, please change the id or "
                                                    "select add x-ray to id instead." ,
                                                    QMessageBox.Ok)
            return -1

        self.xray_record = XrayData(image_name=filename.split('/')[-1],xray_id=Xray_id,acquisition_date=acquisition_date,\
                                                                                  organ_name=organ_name,
                                    save_loc=self.output_loc)

        shutil.copyfile(self.image_widget.image_filename,os.path.join(self.xray_record.save_loc,
                                                                  self.image_widget.image_filename.split(
            '/')[-1] ) )
        # print(self.xray_record.save_loc)
        self.create_xray_window.close()
        self.xray_selection_menu.combobox_studyid.addItem(Xray_id)
        print('adding '+Xray_id+' to dropdown')
        self.xray_selection_menu.combobox_studyid.setCurrentIndex(self.xray_selection_menu.combobox_studyid.count() - 1)


    def add_xray_to_study(self,filename):
        """

        :param filename:
        :type filename:
        :return:
        :rtype:
        """
        acquisition_date = self.create_xray_window.xray_creation_options.qline_edits['Acquisition Date'].text()
        Xray_id          = self.create_xray_window.xray_creation_options.qline_edits['Study id'].text()
        organ_name       = self.create_xray_window.xray_creation_options.qline_edits['Body Part'].text()

        self.xray_record.add_xray(image_name=filename.split('/')[-1],xray_id=Xray_id,acquisition_date=acquisition_date,
                             save_loc=self.output_loc,
                             organ_name=organ_name)
        shutil.copyfile(self.image_widget.image_filename,os.path.join(self.xray_record.save_loc,
                                                                  self.image_widget.image_filename.split(
            '/')[-1] ) )
        self.xray_selection_menu.combobox_xrayid.addItem(filename.split('/')[-1])
        self.xray_selection_menu.combobox_xrayid.setCurrentIndex(self.xray_selection_menu.combobox_xrayid.count() - 1)

        self.create_xray_window.close()
        self.display_image_info()

    def connect_sub_buttons(self):

        self.display_studies()
        self.xray_selection_menu.wd_info.textChanged.connect(self.change_wd)
        # self.XRaySelectionMenu.set_wdir_button.clicked.connect(self.open_output_folder_selector)
        # self.XRaySelectionMenu.set_wdir_button.clicked.connect(self.open_file_dialog)
        # self.XRaySelectionMenu.new_study_button.clicked.connect(self.open_study_creator)
        self.xray_selection_menu.current_study_info.textChanged.connect(self.open_study_creator)
        self.xray_selection_menu.current_file_info.textChanged.connect(self.open_xray_adder)
        # self.XRaySelectionMenu.addXrayToStudy_button.clicked.connect(self.open_xray_adder)
        self.xray_selection_menu.combobox_studyid.currentIndexChanged.connect(self.display_xrays)
        self.xray_selection_menu.combobox_xrayid.activated.connect(self.load_selected_xrays)
        self.xray_selection_menu.combobox_xrayid.currentIndexChanged.connect(self.load_selected_xrays)
        self.xray_selection_menu.score_selector.currentIndexChanged.connect(self.load_new_score_sheet)
        self.xray_selection_menu.score_selector.activated.connect(self.load_new_score_sheet)
        self.widget_area_menu.save_button.clicked.connect(self.save_annotation)
        self.widget_score_menu.save_button.clicked.connect(self.save_scores)
        self.widget_area_menu.view_button.clicked.connect(self.display_all_current_annotations)
        self.widget_area_menu.unsure_button.clicked.connect(lambda: self.update_tracking_annotation(signal='Unsure'))
        self.widget_score_menu.unsure_button.clicked.connect(self.update_tracking_score)
        self.image_widget.toolbar.buttons['Good Image Quality'].triggered.connect(self.update_image_quality_score)
        self.image_widget.toolbar.buttons['Bad Image Quality'].triggered.connect(self.update_image_quality_score)
        self.image_widget.poly_select_options.dropdown.activated.connect(self.show_selected_annotation_bone)
        self.image_widget.poly_select_options.dropdown.currentIndexChanged.connect(self.show_selected_annotation_bone)
        self.image_widget.rect_select_options.dropdown.activated.connect(self.show_selected_annotation_joint)
        self.image_widget.rect_select_options.dropdown.currentIndexChanged.connect(self.show_selected_annotation_joint)
        self.image_widget.toolbar.buttons['Clear Label'].triggered.connect(self.clear_neasurement)
        self.widget_area_menu.output_button.clicked.connect(self.measure_poly)
        # self.image_widget.annotation_options.delete_poly_button.clicked.connect(self.delete_selected_annotation_bone)

    def connect_score_menu_buttons(self):
        self.widget_score_menu.save_button.clicked.connect(self.save_scores)
        self.widget_score_menu.unsure_button.clicked.connect(self.update_tracking_score)


    def split_layouts(self):
        self.main_widget = QSplitter()
        for panel in self._panels:
            self.main_widget.addWidget(panel)

    def merge_layouts(self):
        self.main_layout = QHBoxLayout()
        self.main_widget = QWidget()

        for panel in self._panels:
            self.main_layout.addWidget(panel)

        self.main_widget.setLayout(self.main_layout)


    def save_annotation(self):
        if self.xray_record is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No xray record loaded. Please create or load an x-ray record "
                                                    "before "
                                                    "saving the "
                                                    "score" ,
                                                    QMessageBox.Ok)
            return -1
        if self.image_widget.image_scene.polyline_annotate_item is None and \
                self.image_widget.image_scene.rect_annotate_item is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No labels drawn, please draw a label before attempting to save "
                                                    "one" ,
                                                    QMessageBox.Ok)
            return -1

        if self.widget_area_menu.line_edit_labels.text() == '':
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select which bone or joint you wish to save" ,
                                                    QMessageBox.Ok)
            return -1

        if self.image_widget.image_scene.polyline_annotate_item is None and \
                self.image_widget.image_scene.rect_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text() == 'Bone':
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select Joint when annotating with a rectangle" ,
                                                    QMessageBox.Ok)
            return -1

        if self.widget_area_menu.side_button_group.checkedButton() is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select the L or R before saving",
                                                    QMessageBox.Ok)

        if self.image_widget.image_scene.polyline_annotate_item is not None and \
                self.image_widget.image_scene.rect_annotate_item is None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text() == 'Joint':
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select Bone when annotating with a polyline" ,
                                                    QMessageBox.Ok)


        dates     = np.array(self.xray_record.meta_table['acquisition_date'])
        filenames = np.array(self.xray_record.meta_table['file_name'])

        id = np.where(filenames == self.xray_selection_menu.combobox_xrayid.currentText())

        # print(self.XRaySelectionMenu.combobox_xrayid.currentText())
        # print(id)
        level1_name = self.xray_record.meta_table['organ'][id[0][0]]

        # level1_name = self.xray_record.meta_table['organ']
        side_name   = self.widget_area_menu.side_button_group.checkedButton().text()
        if side_name=='N/A':
            side_name = 'NA'
        level2_name = side_name
        level3_name = self.widget_area_menu.line_edit_labels.text()

        annotation_id = output_annotation_name(level1_name =level1_name,
                                               level2_name=level2_name,
                                               level3_name=level3_name)
        area_name = level3_name+'_'+side_name
        #print(area_name)
        date = dates[id[0][0]]
        #print(date)
        if self.image_widget.image_scene.polyline_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text()=='Bone':
            self.xray_record.save_bone_outline(bone_id=annotation_id,date=date,
                                               plineItem=self.image_widget.image_scene.polyline_annotate_item)
            # self.widget_area_menu.update_table_view(row_name=area_name,signal='Completed')
            self.update_tracking_annotation(signal='Completed')

        if self.image_widget.image_scene.polyline_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text()=='Tissue':
            self.xray_record.save_tissue_outline(bone_id=annotation_id,date=date,
                                               plineItem=self.image_widget.image_scene.polyline_annotate_item)
            # self.widget_area_menu.update_table_view(row_name=area_name,signal='Completed')
            self.update_tracking_annotation(signal='Completed')

        if self.image_widget.image_scene.rect_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text()=='Joint':
            self.xray_record.save_patch(joint_id=annotation_id,date=date,\
            rectItem=self.image_widget.image_scene.rect_annotate_item)
            # self.widget_area_menu.update_table_view(row_name=area_name,signal='Completed')
            self.update_tracking_annotation(signal='Completed')

        if self.image_widget.image_scene.polyline_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text()=='Phantom':
            annotation_id = 'Phantom'
            self.xray_record.save_phantom_outline(bone_id=annotation_id,date=date,\
            plineItem=self.image_widget.image_scene.polyline_annotate_item)
            # self.widget_area_menu.update_table_view(row_name=area_name,signal='Completed')
            self.update_tracking_annotation(signal='Completed')

        if self.image_widget.image_scene.polyline_annotate_item is not None and \
                self.widget_area_menu.annotation_button_group.checkedButton().text()=='Landmark':

            self.xray_record.save_landmark(landmark_id=annotation_id,date=date,\
            plineItem=self.image_widget.image_scene.polyline_annotate_item)
        self.populate_polylines()#adds the polyline saved for the selected xray in the annotation_options tab
        self.populate_rectItems()#adds the polyline saved for the selected xray in the annotation_options tab

        # file_name = 'annotation_tracking_'+str(date)+'.csv'
        # xray_id = self.XRaySelectionMenu.combobox_studyid.currentText()
        # file_loc = os.path.join(os.path.join(self.output_loc,xray_id),file_name)
        # df = self.widget_area_menu.tableView.model()._data
        # save_csv(df,fileName=file_loc)

    def update_tracking_annotation(self,signal="Unsure"):
        if self.xray_record is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No xray record loaded. Please create or load an x-ray record "
                                                    "before "
                                                    "saving the "
                                                    "score" ,
                                                    QMessageBox.Ok)
            return -1


        if self.widget_area_menu.line_edit_labels.text() == '':
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select which bone or joint you wish to save" ,
                                                    QMessageBox.Ok)
            return -1

        if self.widget_area_menu.side_button_group.checkedButton() is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "Please select the L or R before saving",
                                                    QMessageBox.Ok)


        dates     = np.array(self.xray_record.meta_table['acquisition_date'])
        filenames = np.array(self.xray_record.meta_table['file_name'])

        id = np.where(filenames == self.xray_selection_menu.combobox_xrayid.currentText())

        # print(self.XRaySelectionMenu.combobox_xrayid.currentText())
        # print(id)
        level1_name = self.xray_record.meta_table['organ'][id[0][0]]

        # level1_name = self.xray_record.meta_table['organ']
        side_name   = self.widget_area_menu.side_button_group.checkedButton().text()
        if side_name=='N/A':
            side_name = 'NA'
        level2_name = side_name
        level3_name = self.widget_area_menu.line_edit_labels.text()

        annotation_id = output_annotation_name(level1_name =level1_name,
                                               level2_name=level2_name,
                                               level3_name=level3_name)
        area_name = level3_name+'_'+side_name
        date = dates[id[0][0]]
        self.widget_area_menu.update_table_view(row_name=area_name,signal=signal)
        df = self.widget_area_menu.tableView.model()._data

        file_name = 'annotation_tracking_'+level1_name+'_'+str(date)+'.csv'
        xray_id = self.xray_selection_menu.combobox_studyid.currentText()
        file_loc = os.path.join(os.path.join(self.output_loc,xray_id),file_name)
        save_csv(df,fileName=file_loc)


    def find_tracking_info(self):
        # if self.xray_record is None:
        #     self.popupWindow = QMessageBox.question(self,'Warning!',
        #                                             "No xray record loaded. Please create or load an x-ray record "
        #                                             "before "
        #                                             "saving the "
        #                                             "score" ,
        #                                             QMessageBox.Ok)
        #     return -1

        # if self.widget_area_menu.line_edit_labels.text() == '':
        #     self.popupWindow = QMessageBox.question(self,'Warning!',
        #                                             "Please select which bone or joint you wish to save" ,
        #                                             QMessageBox.Ok)
        #     return -1

        # if self.widget_area_menu.side_button_group.checkedButton() is None:
        #     self.popupWindow = QMessageBox.question(self,'Warning!',
        #                                             "Please select the L or R before saving",
        #                                             QMessageBox.Ok)


        dates     = np.array(self.xray_record.meta_table['acquisition_date'])
        filenames = np.array(self.xray_record.meta_table['file_name'])

        id = np.where(filenames == self.xray_selection_menu.combobox_xrayid.currentText())#loads up the metadata and finds which row it should extract info from
        organ_name = self.xray_record.meta_table['organ'][id[0][0]]#name of the organ
        date = dates[id[0][0]]
        # side_name   = self.widget_area_menu.side_button_group.checkedButton().text()#name of the side
        # if side_name=='N/A':
        #     side_name = 'NA'
        file_name = 'annotation_tracking_'+organ_name+'_'+str(date)+'.csv'
        xray_id = self.xray_selection_menu.combobox_studyid.currentText()
        file_loc = os.path.join(os.path.join(self.output_loc,xray_id),file_name)
        if os.path.isfile(file_loc):
            df = load_csv(file_loc)
            self.widget_area_menu.load_table_view(df)
        else:
            self.widget_area_menu.create_table_view()





    def update_image_quality_score(self):
        if self.xray_record is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No xray record loaded. Please create or load an x-ray record "
                                                    "before "
                                                    "saving the "
                                                    "score" ,
                                                    QMessageBox.Ok)
            return -1



        dates     = np.array(self.xray_record.meta_table['acquisition_date'])
        filenames = np.array(self.xray_record.meta_table['file_name'])

        id = np.where(filenames == self.xray_selection_menu.combobox_xrayid.currentText())
        try:
            image_quality_array = np.array(self.xray_record.meta_table['image_quality'])
        except KeyError:
            image_quality_array = np.ones(dates.shape)


        image_quality_array[id[0][0]] = int(self.image_widget.toolbar.buttons['Good Image Quality'].isChecked())

        self.xray_record.meta_table['image_quality'] = image_quality_array
        self.xray_record.save_metadata()




    def update_tracking_score(self):
        if self.xray_record is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No xray record loaded. Please create or load an x-ray record "
                                                    "before "
                                                    "saving the "
                                                    "score" ,
                                                    QMessageBox.Ok)
            return -1


        if self.widget_score_menu.side_button_group.checkedButton() is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                            "Please select a side to allocate the score" ,
                                                            QMessageBox.Ok)
            return -1



        dates     = np.array(self.xray_record.meta_table['acquisition_date'])
        filenames = np.array(self.xray_record.meta_table['file_name'])

        id = np.where(filenames == self.xray_selection_menu.combobox_xrayid.currentText())

        # print(self.XRaySelectionMenu.combobox_xrayid.currentText())
        # print(id)
        level1_name = self.xray_record.meta_table['organ'][id[0][0]]

        # level1_name = self.xray_record.meta_table['organ']
        side_name   = self.widget_score_menu.side_button_group.checkedButton().text()
        if side_name=='N/A':
            side_name = 'NA'
        level2_name = side_name
        level3_name = self.widget_score_menu.score_area_box.currentText()

        annotation_id = output_annotation_name(level1_name =level1_name,
                                               level2_name=level2_name,
                                               level3_name=level3_name)
        area_name = level3_name+'_'+side_name
        date = dates[id[0][0]]
        self.widget_area_menu.update_table_view(row_name=area_name,signal='Unsure')
        df = self.widget_area_menu.tableView.model()._data

        file_name = 'annotation_tracking_'+str(date)+'.csv'
        xray_id = self.xray_selection_menu.combobox_studyid.currentText()
        file_loc = os.path.join(os.path.join(self.output_loc,xray_id),file_name)
        save_csv(df,fileName=file_loc)

    def save_scores(self):
        if self.xray_record is None:
            self.popupWindow = QMessageBox.question(self,'Warning!',
                                                    "No xray record loaded. Please create or load an x-ray record "
                                                    "before "
                                                    "saving the "
                                                    "score" ,
                                                    QMessageBox.Ok)
        else:
            # date = NameSignature(self.XRaySelectionMenu.combobox_xrayid.currentText()).year
            # date = self.XRaySelectionMenu.xray_info_box_date.text()
            # #self.xray_record.meta_table[]
            # file_loc = os.path.join(self.xray_record.save_loc,'scores')
            # #print(file_loc)
            # file_loc = os.path.join(file_loc,date)
            # file_name = os.path.join(file_loc,self.widget_score_menu.score_technique+'.csv')

            file_name = self.make_score_path()
            file_path = os.path.dirname(file_name)
            if not os.path.isdir(file_path): os.makedirs(file_path)
            #print("saving at "+file_name)
            self.widget_score_menu.save_table_view(file_loc=file_name)


    def display_studies(self):
        if not os.path.isdir(self.output_loc):
            return -1
        studies = [f for f in os.listdir(self.output_loc) if os.path.isdir(os.path.join(self.output_loc,f))]
        for it in studies:
            self.xray_selection_menu.combobox_studyid.addItem(it)
            print('adding ' + it + ' to dropdown')


    def display_xrays(self):
        """
        changes the list in the xray id box to be a list of filenames of images presemt in tehe metaloc of the selected
        study id and loads the last image in that list of file names
        """
        if self.xray_selection_menu.combobox_studyid.count()>0:
            study_name = self.xray_selection_menu.combobox_studyid.currentText()
            meta_loc   = os.path.join(self.output_loc,study_name)
            # meta_data  = pd.read_csv(os.path.join(meta_loc,'metadata.csv'))
            meta_data = load_csv(os.path.join(meta_loc,'metadata.csv'))
            dates      = meta_data['acquisition_date']
            fileNames  = meta_data['file_name']
            self.xray_selection_menu.combobox_xrayid.clear()
            for it in fileNames:
                self.xray_selection_menu.combobox_xrayid.addItem(it)
            meta_loc = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
            self.xray_record = XrayData(image_name=None,xray_id=None,acquisition_date=None,meta_loc=meta_loc)
            self.load_selected_xrays()

    def initialise_xray_record(self):
        if not os.path.isdir(self.output_loc):
            return -1
        if self.xray_selection_menu.combobox_studyid.currentText() is not None:

            meta_loc = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
            if os.path.isfile(meta_loc):
                self.xray_record = XrayData(image_name=None,xray_id=None,acquisition_date=None,meta_loc=meta_loc)
                self.display_xrays()
                self.load_selected_xrays()

    def load_selected_xrays(self):
        """
        method that loads the xray corrsponding the the id being displayed in the study id box and the filename being
        displayed in the xray id box
        will read in the filename being isplyed in xray id and will look for the file in self.output_loc/study_id
        """
        meta_loc = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        # dates = np.array(self.xray_record.meta_table['acquisition_date'],dtype=np.int)
        file_names = np.array(self.xray_record.meta_table['file_name'])
        organs     = np.array(self.xray_record.meta_table['organ'])

        #
        #
        id =np.where(file_names==self.xray_selection_menu.combobox_xrayid.currentText())
        # print(dates)
        # print(self.XRaySelectionMenu.combobox_xrayid.currentText())
        # print(id)
        # image_name = self.xray_record.meta_table['file_name'][id[0][0]]#.to_numpy()[0]
        image_name = self.xray_selection_menu.combobox_xrayid.currentText()

        if os.path.isfile(os.path.join(meta_loc,image_name)):
            self.image_widget.load_image(file_name=os.path.join(meta_loc,image_name))

            #print("Image quality is ={:}".format(int(self.image_widget.image_quality_flag)))
            self.display_image_info()
            self.find_tracking_info()


        self.populate_polylines()#adds the polyline saved for the selected xray in the annotation_options tab
        self.populate_rectItems()#adds the polyline saved for the selected xray in the annotation_options tab



        score_path = self.make_score_path()
        self.widget_score_menu.tableView_lineEdit.setText(score_path)

        if os.path.isfile(score_path):
            my_dict = load_csv(score_path)
            self.widget_score_menu.load_table_view(my_dict)
        else:
            self.widget_score_menu.create_table_view()

        try:
            image_quality_array = np.array(self.xray_record.meta_table['image_quality'])
            image_qual_bool     = bool(int(float(image_quality_array[id[0][0]])))
            #print(image_qual_bool)
            self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(image_qual_bool)
            self.image_widget.toolbar.buttons['Bad Image Quality'].setChecked(not image_qual_bool)
        except KeyError:
            self.image_widget.toolbar.buttons['Good Image Quality'].setChecked(1)
            #print("No image quality info present in metadata")

        #print(image_name)



    def make_score_path(self):
        meta_loc = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        score_path = os.path.join(meta_loc,'scores')
        date = self.xray_selection_menu.xray_info_box_date.text()
        score_path = os.path.join(score_path,date)

        score_path = os.path.join(score_path,self.widget_score_menu.score_technique + '.csv')

        return score_path


    def _get_image_info(self):
        if self.xray_record is not None:
            dates = np.array(self.xray_record.meta_table['acquisition_date'])
            file_names = np.array(self.xray_record.meta_table['file_name'])
            organs     = np.array(self.xray_record.meta_table['organ'])
            #
            #
            id =np.where(file_names==self.xray_selection_menu.combobox_xrayid.currentText())
            if len(id)!=0:
                date = str(dates[id[0][0]])
                organ = str( organs[id[0][0]] )

            else:
                date=""
                organ=""
        else:
            date = ""
            organ = ""
        return date, organ

    def display_image_info(self):
        dates = np.array(self.xray_record.meta_table['acquisition_date'])
        file_names = np.array(self.xray_record.meta_table['file_name'])
        organs     = np.array(self.xray_record.meta_table['organ'])
        #
        #
        id =np.where(file_names==self.xray_selection_menu.combobox_xrayid.currentText())
        if len(id)!=0:
            if len(id[0])!=0:
                self.xray_selection_menu.xray_info_box_date.setText(str(dates[id[0][0]]))
                self.xray_selection_menu.xray_info_box_organ.setText(organs[id[0][0]])
            else:
                ('empty array for the id where the filenames = the combobox content')


    def display_all_current_annotations(self):
        im_loc = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        # date = NameSignature(self.XRaySelectionMenu.combobox_xrayid.currentText()).year
        date = self.xray_selection_menu.xray_info_box_date.text()
        im_name = self.xray_selection_menu.combobox_xrayid.currentText()
        # self.xray_record.meta_table[]
        joint_loc = os.path.join(self.xray_record.save_loc, 'joint')
        joint_loc = os.path.join(joint_loc, date)
        bones_loc = os.path.join(self.xray_record.save_loc, 'bone')
        bones_loc = os.path.join(bones_loc, date)

        rects = [os.path.join(joint_loc, f) for f in os.listdir(joint_loc) if f.split('.')[-1]=='txt']
        polys = [os.path.join(bones_loc, f) for f in os.listdir(bones_loc) if f.split('.')[-1]=='txt']
        self.display_window = PlotWindow()
        #print("rectitems:")
        #print(joint_loc)
        #print(rects)
        for rect in rects:
            #print(rect)
            x = np.loadtxt(rect)
            self.display_window.plot(np.append(x[:, 0], x[0, 0]), np.append(x[:, 1], x[0, 1]))

        for poly in polys:
            #print(poly)
            x = np.loadtxt(poly)
            self.display_window.plot(x[:, 0], x[:, 1])

        im = cv2.imread(os.path.join(im_loc,im_name))
        self.display_window.imshow(im)
        self.display_window.show()


    def populate_polylines(self):
        study_id = self.xray_selection_menu.combobox_studyid.currentText()
        target_loc = os.path.join(self.output_loc,study_id)#todo: link this to current date so that only the current
        _loc,x = find_bone_annotations(target_folder=self.output_loc,xray_id=study_id,date=self.xray_selection_menu.xray_info_box_date.text())
        # self.image_widget.annotation_options.poly_loc_line_edit.setText(_loc)
        self.image_widget.poly_select_options.loc_line_edit.setText(_loc)

        anatomical_structure = self.xray_selection_menu.xray_info_box_organ.text()
        x_filtered = [f for f in x if anatomical_structure in f]
        # self.image_widget.annotation_options.polyline_dFdisplayropdown.clear()
        self.image_widget.poly_select_options.dropdown.clear()
        maxlen = 0
        fm = QFontMetrics(self.image_widget.poly_select_options.dropdown.view().font())
        if len(x)>0:
            for f in x:
                if f.split('.')[-1] == 'txt':

                    # self.image_widget.annotation_options.polyline_dropdown.addItem(f.split('.')[0])
                    self.image_widget.poly_select_options.dropdown.addItem(f.split('.')[0])
                    if maxlen<len(f.split('.')[0]): maxlen= fm.width(f.split('.')[0])
            #print("font length")
            #print(maxlen)
            self.image_widget.poly_select_options.dropdown.view().setMinimumWidth(maxlen)#todo: determine the width of the
            # pixel

    def populate_rectItems(self):
        study_id = self.xray_selection_menu.combobox_studyid.currentText()
        target_loc = os.path.join(self.output_loc,
                                  study_id)  # todo: link this to current date so that only the current
        _loc,x = find_joint_annotations(target_folder=self.output_loc, xray_id=study_id,
                                  date=self.xray_selection_menu.xray_info_box_date.text())
        self.image_widget.rect_select_options.loc_line_edit.setText(_loc)

        anatomical_structure = self.xray_selection_menu.xray_info_box_organ.text()
        x_filtered = [f for f in x if anatomical_structure in f]
        self.image_widget.rect_select_options.dropdown.clear()
        maxlen=0
        if len(x) > 0:
            for f in x:
                if f.split('.')[-1] == 'txt':
                    self.image_widget.rect_select_options.dropdown.addItem(f.split('.')[0])
                    if maxlen<len(f.split('.')[0]): maxlen= len(f.split('.')[0])
            fm = self.image_widget.rect_select_options.dropdown.view().font()
            # self.image_widget.annotation_options.rectItem_dropdown.view().setMinimumWidth(maxlen*fm.pixelSize())#todo: determine the width of the pixel


    def show_selected_annotation_bone(self):
        annotation_name = self.image_widget.poly_select_options.dropdown.currentText()
        # print(annotation_name)
        annotation_path = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        annotation_path = os.path.join(annotation_path,'bone')
        annotation_path = os.path.join(annotation_path,self.xray_selection_menu.xray_info_box_date.text())
        annotation_path = os.path.join(annotation_path, annotation_name+'.txt')
        # print(annotation_path)
        if os.path.isfile(annotation_path):
            control_points  = np.loadtxt(annotation_path)
            if self.image_widget.poly_select_options.display_box.isChecked():
                # print("trying to display the poly")
                self.image_widget.image_scene.clear_poly()
                self.image_widget.image_scene.add_polyline(control_points)


    def clear_neasurement(self):
        self.widget_area_menu.output_box.setText('0mm')

    def measure_poly(self):
        if self.image_widget.image_scene.annotation_length>2:
            # self.image_widget.pixel_width = [0.1,0.2]
            array = self.image_widget.image_scene.polyline_annotate_item.control_points
            scaling = np.expand_dims(self.image_widget.pixel_width,0)
            diffs = np.diff(array,axis=0)
            # print(diffs.shape)
            # print(diffs)
            # print('=====pixel spacing:')
            # print((scaling*diffs).shape)
            # print(scaling*diffs)
            distance = np.sqrt(np.sum(np.square(scaling*diffs)))
            self.widget_area_menu.output_box.setText('{:.4f} mm'.format(distance))

        if self.image_widget.image_scene.rect_annotate_item is not None:
            h = self.image_widget.image_scene.rect_annotate_item.model.height*self.image_widget.pixel_width[0]
            w = self.image_widget.image_scene.rect_annotate_item.model.width*self.image_widget.pixel_width[1]
            area = h*w
            self.widget_area_menu.output_box.setText('{:.2f} mm sq.'.format(area))



    def show_selected_annotation_joint(self):
        annotation_name = self.image_widget.rect_select_options.dropdown.currentText()
        # print(annotation_name)
        annotation_path = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        annotation_path = os.path.join(annotation_path,'joint')
        annotation_path = os.path.join(annotation_path,self.xray_selection_menu.xray_info_box_date.text())
        annotation_path = os.path.join(annotation_path, annotation_name+'.txt')
        if os.path.isfile(annotation_path):
            control_points  = np.loadtxt(annotation_path)
            x = np.min(control_points[:,0])
            w = np.max(control_points[:,0])-np.min(control_points[:,0])
            y = np.min(control_points[:,1])
            h = np.max(control_points[:,1])-np.min(control_points[:,1])
            diff = control_points[0,:]-control_points[1,:]
            angle = np.arctan(diff[1]/diff[0])
            if self.image_widget.rect_select_options.display_box.isChecked():

                self.image_widget.image_scene.clear_poly()
                self.image_widget.image_scene.add_rectItem(x,y,w,h,angle)


    def delete_selected_annotation_bone(self):
        annotation_name = self.image_widget.annotation_options.polyline_dropdown.currentText()
        # print(annotation_name)
        annotation_path = os.path.join(self.output_loc,self.xray_selection_menu.combobox_studyid.currentText())
        annotation_path = os.path.join(annotation_path,'joint')
        annotation_path = os.path.join(annotation_path,self.xray_selection_menu.xray_info_box_date.text())
        # annotation_path = os.path.join(annotation_path, annotation_name+'.txt')
        # popupWindow = QMessageBox.question(self, 'Warning!',
        #                                         "Are you sure you want to delete "+annotation_name+"?",QMessageBox.No,
        #                                         QMessageBox.Ok)
        self.image_widget.annotation_options.delete_selected_poly(file_loc=annotation_path)
        # qm = QMessageBox
        # ret = qm.question(self, '', "Are you sure to reset all the values?", qm.Yes | qm.No)
        # if  ret == qm.Yes:
        #     print("deleting " +annotation_path)
        # else:
        #     print("keeping " + annotation_path)
        # if QMessageBox.Ok:

        # if os.path.isfile(filename):
        #     self.msg = QMessageBox()
        #     self.msg.setIcon(QMessageBox.Information)
        #     self.msg.setText("Saved annotation under")
        #     self.msg.setInformativeText(organ)
        #     self.msg.setDetailedText("Save location \n"+filename)
        #     self.msg.setStandardButtons(QMessageBox.Ok)
        #     self.msg.show()
        # os.remove(annotation_path)
        # control_points  = np.loadtxt(annotation_path)
        # x = np.min(control_points[:,0])
        # w = np.max(control_points[:,0])-np.min(control_points[:,0])
        # y = np.min(control_points[:,1])
        # h = np.max(control_points[:,1])-np.min(control_points[:,1])
        # if self.image_widget.annotation_options.display_rectItem_box.isChecked():
        #
        #     self.image_widget.image_scene.clear_poly()
        #     self.image_widget.image_scene.add_rectItem(x,y,w,h)






def main():
    app = QApplication([])
    window = InspectXRays()
    window.show()
    app.exec_()


if __name__=='__main__':
    main()