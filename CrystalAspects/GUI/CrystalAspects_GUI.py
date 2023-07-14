# PyQT5 imports
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, \
    QShortcut, QTableWidgetItem, QTableWidget,\
    QAction, QMenu, QMenuBar, QFileDialog, \
    QInputDialog, QCheckBox, QComboBox, \
    QVBoxLayout, QLabel, QDialog, \
    QDialogButtonBox
from PyQt5.QtCore import Qt, QThreadPool
from PyQt5.QtGui import QKeySequence, QKeyEvent
from qt_material import apply_stylesheet

# General imports
import os, sys, subprocess
import pandas as pd
from collections import namedtuple
from pathlib import Path

# Project Module imports
from CrystalAspects.GUI.load_GUI import Ui_MainWindow
from CrystalAspects.data.find_data import Find
from CrystalAspects.data.growth_rates import GrowthRate
from CrystalAspects.tools.shape_analysis import CrystalShape, AspectRatioCalc
from CrystalAspects.tools.visualiser import Visualiser
#from CrystalAspects.tools.AspectRatioXYZ import CrystalShape
from CrystalAspects.tools.crystal_slider import create_slider
from CrystalAspects.visualisation.replotting import Replotting, PlotWindow
from CrystalAspects.GUI.gui_threads import Worker_XYZ, Worker_Calc, Worker_Movies
from CrystalAspects.visualisation.plot_data import Plotting
from CrystalAspects.data.aspect_ratios import AspectRatio
from CrystalAspects.visualisation.Tables import TableDialog
from CrystalAspects.data.CalculateAspectRatios import AnalysisOptionsDialog

basedir = os.path.dirname(__file__)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        apply_stylesheet(app, theme="dark_cyan.xml")

        self.setupUi(self)
        self.statusBar().showMessage("CrystalGrower Data Processor v1.0")

        self.growth = GrowthRate()
        self.shape = CrystalShape()
        self.threadpool = QThreadPool()
        self.change_style(theme_main="dark", theme_colour="teal")

        self.welcome_message()
        self.key_shortcuts()
        self.connect_buttons()
        self.init_parameters()
        self.MenuBar()

    def MenuBar(self):
        # Create a menu bar
        menu_bar = self.menuBar()

        # Create two menus
        file_menu = QMenu("File", self)
        edit_menu = QMenu("Edit", self)
        CrystalAspects_menu = QMenu("CrystalAspects", self)

        # Add menus to the menu bar
        menu_bar.addMenu(file_menu)
        menu_bar.addMenu(edit_menu)
        menu_bar.addMenu(CrystalAspects_menu)

        # Create actions for the File menu
        new_action = QAction("New", self)
        open_action = QAction("Open", self)
        save_action = QAction("Save", self)
        exit_action = QAction("Exit", self)

        # Add actions to the File menu
        file_menu.addAction(new_action)
        file_menu.addAction(open_action)
        file_menu.addAction(save_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        # Create actions for the Edit menu
        cut_action = QAction("Cut", self)
        copy_action = QAction("Copy", self)
        paste_action = QAction("Paste", self)

        # Add actions to the Edit menu
        edit_menu.addAction(cut_action)
        edit_menu.addAction(copy_action)
        edit_menu.addAction(paste_action)

        # Create actions to the Calculate menu
        aspect_ratio_action = QAction("Aspect Ratio", self)
        growth_rate_action = QAction("Growth Rates", self)
        plotting_action = QAction("Plotting", self)
        calculate_action = QAction("Calculate", self)

        # Add actions and Submenu to CrystalAspects menu
        calculate_menu = CrystalAspects_menu.addMenu("Calculate")
        calculate_menu.addAction(aspect_ratio_action)
        calculate_menu.addAction(growth_rate_action)
        CrystalAspects_menu.addAction(plotting_action)

        # Connect the aspect_ratio_action to a custom slot
        aspect_ratio_action.triggered.connect(self.calculate_aspect_ratio)

        # Connect the growth_rate_action to a custom function
        growth_rate_action.triggered.connect(self.calculate_growth_rates)

    def change_style(self, theme_main, theme_colour, density=-1):

        extra = {
            # Font
            "font_family": "Roboto",
            # Density Scale
            "density_scale": str(density),
        }

        apply_stylesheet(
            app, f"{theme_main}_{theme_colour}.xml", invert_secondary=False, extra=extra
        )

    def init_parameters(self):

        self.checked_directions = []
        self.selected_directions = []
        self.checkboxnames = []
        self.checkboxes = []
        self.growthrates = False
        self.aspectratio = False
        self.growthmod = False
        self.cda = False
        self.pca = False
        self.sa_vol = False
        self.screwdislocations = []
        self.folder_path = ""
        self.folders = []
        self.mode = 1
        self.plot = False
        self.vis = False
        self.xyz = None
        self.xyz_list = []
        self.xyz_result = ()
        self.frame_list = []
        self.plot_list = []
        self.equation_list = []

        self.summary_csv = None
        self.replot_info = None
        self.replot_folder = None
        self.AR_csv = None
        self.SAVAR_csv = None
        self.GrowthRate_csv = None
        self.select_plots = []
        self.progressBar.setValue(0)

    def key_shortcuts(self):
        # Create a QShortcut with the specified key sequence
        close = QShortcut(QKeySequence("Ctrl+Q"), self)
        # Connect the activated signal of the shortcut to the close() method
        close.activated.connect(self.close)
        # Open read folder
        self.openKS = QShortcut(QKeySequence("Ctrl+O"), self)
        try:
            self.openKS.activated.connect(lambda: self.read_folder(self.mode))
        except IndexError:
            pass
        # Open output folder
        self.open_outKS = QShortcut(QKeySequence("Ctrl+Shift+O"), self)
        try:
            self.open_outKS.activated.connect(self.output_folder_button)
        except IndexError:
            pass
        # Reset everything
        self.resetKS = QShortcut(QKeySequence("Ctrl+R"), self)
        self.resetKS.activated.connect(self.reset_button_function)
        '''self.applyKS = QShortcut(QKeySequence("Ctrl+A"), self)
        # self.applyKS.activated.connect(self.apply_clicked)'''

    def welcome_message(self):
        print("############################################")
        print("####        CrystalAspects v1.00        ####")
        print("############################################")

    def connect_buttons(self):

        self.tabWidget.currentChanged.connect(self.tabChanged)

        # Open Folder
        try:
            self.simFolder_Button.clicked.connect(lambda: self.read_folder(self.mode))
        except IndexError:
            pass

        self.growthRate_checkBox.stateChanged.connect(self.growth_rate_check)
        self.plot_checkBox.stateChanged.connect(self.plot_check)
        self.run_calc_button.clicked.connect(self.run_calc)

        # Checkboxes
        self.aspectRatio_checkBox.stateChanged.connect(self.aspect_ratio_checked)
        self.pca_checkBox.stateChanged.connect(self.pca_checked)
        self.cda_checkBox.stateChanged.connect(self.cda_checked)
        #self.sa_vol_checkBox.stateChanged.connect(self.sa_vol_checked)
        self.reset_button.clicked.connect(self.reset_button_function)
        self.plot_checkBox.setEnabled(True)
        self.outFolder_Button.clicked.connect(self.output_folder_button)
        # self.count_checkBox.stateChanged.connect(self.count_check)
        # self.aspect_range_checkBox.stateChanged.connect(self.range_check)

        # Plotting buttons
        self.AR_browse_button.clicked.connect(self.replot_AR_read)
        self.subplot_button.clicked.connect(lambda: self.subplotting())
        self.threeD_plotting_button.clicked.connect(lambda: self.threeD_plotting())
        self.clearPlots.clicked.connect(lambda: self.clearPlotting())
        self.PlottingOptions.currentTextChanged.connect(lambda: self.plotting_choices(whole_plot_list=self.plot_list))
        self.GeneratePlots.clicked.connect(lambda: self.call_replot())
        self.clearPlots.clicked.connect(lambda: self.clearPlotting())

        # Visualisation Buttons
        self.select_summary_slider_button.clicked.connect(lambda: self.read_summary_vis())

    def calculate_aspect_ratio(self):
        # Example function to calculate aspect ratio

        # Prompt the user to select the folder
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "./", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        find = Find()
        # Check if the user selected a folder

        if folder:
            # Perform calculations using the selected folder

            # Read the information from the selected folder
            information = find.find_info(folder)

            # Get the directions from the information
            checked_directions = information.directions
            print(checked_directions)

            # Create the analysis options dialog
            dialog = AnalysisOptionsDialog(checked_directions)
            if dialog.exec_() == QDialog.Accepted:
                # Retrieve the selected options
                selected_aspect_ratio, selected_cda, selected_directions, selected_direction_aspect_ratio, auto_plotting = dialog.get_options()

                # Display the information in a QMessageBox
                QMessageBox.information(self, "Options",
                                        f"Selected Aspect Ratio: {selected_aspect_ratio}\n"
                                        f"Selected CDA: {selected_cda}\n"
                                        f"Selected Directions: {selected_directions}\n"
                                        f"Selected Direction Aspect Ratio: {selected_direction_aspect_ratio}\n"
                                        f"Auto Plotting: {auto_plotting}")

                AspectXYZ = AspectRatioCalc()
                aspect_ratio = AspectRatio()
                plotting = Plotting()
                save_folder = find.create_aspects_folder(folder)
                file_info = find.find_info(folder)
                summary_file = file_info.summary_file
                folders = file_info.folders

                if selected_aspect_ratio:
                    xyz_df = AspectXYZ.collect_all(folder=folder)
                    xyz_df_final = find.summary_compare(
                        summary_csv=summary_file,
                        aspect_df=xyz_df
                    )
                    xyz_df_final_csv = f"{save_folder}/AspectRatio.csv"
                    xyz_df_final.to_csv(xyz_df_final_csv, index=None)
                    AspectXYZ.shape_number_percentage(
                        df=xyz_df_final,
                        savefolder=save_folder
                    )
                    if auto_plotting is True:
                        plotting.build_PCAZingg(df=xyz_df_final,
                                                folderpath=save_folder)
                        plotting.plot_OBA(df=xyz_df_final,
                                          folderpath=save_folder)
                    '''if selected_aspect_ratio is False:
                        self.ShowData(xyz_df_final)'''
                if selected_cda:
                    cda_df = aspect_ratio.build_AR_CDA(
                        folderpath=folder,
                        folders=folders,
                        directions=selected_directions,
                        selected=selected_direction_aspect_ratio,
                        savefolder=save_folder,
                    )
                    zn_df = aspect_ratio.defining_equation(
                        directions=selected_direction_aspect_ratio,
                        ar_df=cda_df,
                        filepath=save_folder,
                    )
                    zn_df_final = find.summary_compare(
                        summary_csv=summary_file,
                        aspect_df=zn_df
                    )
                    zn_df_final_csv = f"{save_folder}/CDA.csv"
                    zn_df_final.to_csv(zn_df_final_csv, index=None)

                    if selected_aspect_ratio and selected_cda:
                        combined_df = find.combine_XYZ_CDA(
                            CDA_df=zn_df,
                            XYZ_df=xyz_df
                        )
                        final_cda_xyz = find.summary_compare(
                            summary_csv=summary_file,
                            aspect_df=combined_df
                        )
                        final_cda_xyz_csv = f"{save_folder}/CrystalAspects.csv"
                        final_cda_xyz.to_csv(final_cda_xyz_csv, index=None)
                        #self.ShowData(final_cda_xyz)
                        aspect_ratio.CDA_Shape_Percentage(
                            df=final_cda_xyz,
                            savefolder=save_folder
                        )

    def calculate_growth_rates(self):
        # Example function to calculate growth rates

        # Prompt the user to select the folder
        folder = QFileDialog.getExistingDirectory(self, "Select Folder", "./", QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        # Check if the user selected a folder
        if folder:
            # Perform calculations using the selected folder
            QMessageBox.information(self, "Result", f"Growth rates calculated for the folder: {folder}")
            




    def read_summary_vis(self):
        print('Entering Reading Summary file')
        create_slider.read_summary(self)

    def read_folder(self, mode):
        find = Find()

        if self.mode == 2:
            slider = create_slider()
            self.folder_path, self.xyz_list = slider.read_crystals()
            find.create_aspects_folder(self.folder_path)
            print(f"Initial XYZ list: {self.xyz_list}")
            Visualiser.initGUI(self, self.xyz_list)
            self.select_summary_slider_button.setEnabled(True)

        if self.mode == 1:

            self.folder_path = Path(
                QtWidgets.QFileDialog.getExistingDirectory(
                    None, "Select CrystalGrower Output Folder"
                )
            )
            checkboxes = []
            check_box_names = []

            file_info = find.find_info(self.folder_path)

            self.summary_file = file_info.summary_file

            self.folders = file_info.folders

            if file_info.size_files:
                self.growthrates = True
                self.growthRate_checkBox.setChecked(True)

            if self.growthrates is False:
                self.growthRate_checkBox.setEnabled(False)

            num_directions = len(file_info.directions)
            print("Number of Directions:", num_directions)

            # Deletes current directions
            for chk_box in self.facet_gBox.findChildren(QtWidgets.QCheckBox):
                chk_box.deleteLater()

            for i in range(num_directions):
                chk_box_name = file_info.directions[i]
                self.chk_box_direction = QtWidgets.QCheckBox(self.facet_gBox)
                check_box_names.append(chk_box_name)
                checkboxes.append(self.chk_box_direction)

                self.chk_box_direction.setEnabled(True)
                self.chk_box_direction.stateChanged.connect(self.check_facet)
                sizePolicy = QtWidgets.QSizePolicy(
                    QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
                )
                sizePolicy.setHorizontalStretch(0)
                sizePolicy.setVerticalStretch(1)
                sizePolicy.setHeightForWidth(
                    self.chk_box_direction.sizePolicy().hasHeightForWidth()
                )
                self.chk_box_direction.setSizePolicy(sizePolicy)
                font = QtGui.QFont()
                font.setFamily("Arial")
                font.setPointSize(10)
                self.chk_box_direction.setFont(font)
                self.chk_box_direction.setText(chk_box_name)

                self.verticalLayout_2.addWidget(self.chk_box_direction)

            self.checkboxnames = check_box_names
            self.checkboxes = checkboxes
            print(self.checkboxnames)

    def check_facet(self, state):
        if state == Qt.Checked:
            chk_box = self.sender()
            print(chk_box)
            for box in self.checkboxes:
                if chk_box == box:
                    # print(box)
                    checked_facet = self.checkboxnames[self.checkboxes.index(box)]
                    if checked_facet not in self.checked_directions:
                        self.checked_directions.append(checked_facet)

                    # Turns on and off the second aspect ratio fields
                    if (
                        len(self.checked_directions) >= 3
                        and self.aspectRatio_checkBox.isChecked()
                    ):
                        if self.mode == 1:
                            self.short_facet.setEnabled(True)
                            if self.aspect_range_checkBox.isChecked():
                                self.ms_range_input.setEnabled(True)
                                self.ms_plusminus_label.setEnabled(True)
                                self.ms_spinBox.setEnabled(True)
                                self.ms_percent_label.setEnabled(True)

        else:
            chk_box = self.sender()
            for box in self.checkboxes:
                if chk_box == box:
                    checked_facet = self.checkboxnames[self.checkboxes.index(box)]

                    try:
                        self.checked_directions.remove(checked_facet)
                        print(self.checked_directions)

                    except NameError:
                        print(self.checked_directions)

                    # Turns on and off the second aspect ratio fields
                    if len(self.checked_directions) < 3:
                        if self.mode == 1:
                            self.short_facet.setEnabled(False)
                            # self.short_facet_label.setEnabled(False)
                            self.ms_range_input.clear()
                            self.ms_spinBox.setValue(0)
                            self.ms_range_input.setEnabled(False)
                            self.ms_plusminus_label.setEnabled(False)
                            self.ms_spinBox.setEnabled(False)
                            self.ms_percent_label.setEnabled(False)

        # Adds directions (updates) to the drop down lists
        if self.mode == 1:
            self.long_facet.clear()
            self.medium_facet.clear()
            self.short_facet.clear()
            for item in self.checked_directions:
                self.long_facet.addItem(item)
                self.medium_facet.addItem(item)
                self.short_facet.addItem(item)

    def aspect_ratio_checked(self, state):

        if state == Qt.Checked:
            self.aspectratio = True
            self.pca_checkBox.setEnabled(True)
            self.cda_checkBox.setEnabled(True)

            if self.cda:
                self.long_facet.setEnabled(True)
                self.medium_facet.setEnabled(True)
                self.aspect_range_checkBox.setEnabled(True)
                # self.count_checkBox.setEnabled(True)
                self.ratio_label1.setEnabled(True)

                if len(self.checked_directions) >= 3:
                    self.short_facet.setEnabled(True)
                    self.ratio_label2.setEnabled(True)

        else:
            # Clear
            self.pca_checkBox.setEnabled(False)
            self.cda_checkBox.setEnabled(False)
            self.long_facet.setEnabled(False)
            self.medium_facet.setEnabled(False)
            self.short_facet.setEnabled(False)
            self.lm_range_input.clear()
            self.ms_range_input.clear()
            self.lm_spinBox.setValue(0)
            self.ms_spinBox.setValue(0)
            self.aspect_range_checkBox.setChecked(False)
            self.aspect_range_checkBox.setEnabled(False)
            self.ratio_label1.setEnabled(False)
            self.ratio_label2.setEnabled(False)
            self.count_checkBox.setChecked(False)
            self.count_checkBox.setEnabled(False)

    def reset_button_function(self):

        self.init_parameters()

        # Initialise Progressbar
        self.progressBar.setValue(0)

        if self.mode == 1:
            # Unchecks selected facets
            for chkBox in self.facet_gBox.findChildren(QtWidgets.QCheckBox):
                chkBox.setChecked(False)
                chkBox.deleteLater()
            # Unchecks Checkboxes and clears the fields
            self.growthRate_checkBox.setChecked(False)
            self.aspectRatio_checkBox.setChecked(False)
            self.cda_checkBox.setChecked(False)
            self.pca_checkBox.setChecked(False)
            self.plot_checkBox.setChecked(False)
            self.long_facet.setEnabled(False)
            self.medium_facet.setEnabled(False)
            self.short_facet.setEnabled(False)
            self.lm_range_input.clear()
            self.ms_range_input.clear()
            self.lm_spinBox.setValue(0)
            self.ms_spinBox.setValue(0)
            self.lm_range_input.setEnabled(False)
            self.lm_plusminus_label.setEnabled(False)
            self.lm_spinBox.setEnabled(False)
            self.lm_percent_label.setEnabled(False)
            self.ms_range_input.setEnabled(False)
            self.ms_plusminus_label.setEnabled(False)
            self.ms_spinBox.setEnabled(False)
            self.ms_percent_label.setEnabled(False)
            self.aspect_range_checkBox.setChecked(False)

        self.summary_cs_label.setEnabled(False)
        self.ar_lineEdit.clear()
        self.summaryfile_lineEdit.setEnabled(False)
        self.summaryfile_browse_button.setEnabled(False)
        #self.ARExtra_browse_button.setEnable(False)
        #self.CAExtra_lineEdit.setEnable(False)
        self.SelectPlots.setEnabled(False)
        self.GeneratePlots.setEnabled(False)

    def clearPlotting(self):
        print('Clearing Figure')

    def input_directions(self, directions):
        check_box_names = []
        checkboxes = []

        num_directions = len(directions)
        # Deletes current directions
        for chk_box in self.facet_gBox.findChildren(QtWidgets.QCheckBox):
            chk_box.deleteLater()

        for i in range(num_directions):
            chk_box_name = directions[i]
            self.chk_box_direction = QtWidgets.QCheckBox(self.facet_gBox)
            check_box_names.append(chk_box_name)
            checkboxes.append(self.chk_box_direction)

            self.chk_box_direction.setEnabled(True)
            self.chk_box_direction.stateChanged.connect(self.check_facet)
            sizePolicy = QtWidgets.QSizePolicy(
                QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
            )
            sizePolicy.setHorizontalStretch(0)
            sizePolicy.setVerticalStretch(1)
            sizePolicy.setHeightForWidth(
                self.chk_box_direction.sizePolicy().hasHeightForWidth()
            )
            self.chk_box_direction.setSizePolicy(sizePolicy)
            font = QtGui.QFont()
            font.setFamily("Arial")
            font.setPointSize(10)
            self.chk_box_direction.setFont(font)
            self.chk_box_direction.setText(chk_box_name)

            self.verticalLayout_2.addWidget(self.chk_box_direction)

            self.checkboxnames = check_box_names
            self.checkboxes = checkboxes
            print(self.checkboxnames)

    def growth_rate_check(self, state):
        if state == Qt.Checked:
            self.growthrates = True
            print(f"Growth Rates: {self.growthrates}")
        else:
            self.growthrates = False
            print(f"Growth Rates: {self.growthrates}")

    def pca_checked(self, state):
        if state == Qt.Checked:
            self.pca = True
            print(f"PCA: {self.pca}")
        else:
            self.pca = False
            print(f"PCA: {self.pca}")

    def sa_vol_checked(self, state):
        if state == Qt.Checked:
            self.sa_vol = True
            print(f"SA:V {self.sa_vol}")
        else:
            self.sa_vol = False
            print(f"SA:V {self.sa_vol}")

    def cda_checked(self, state):
        if state == Qt.Checked:
            self.cda = True
            print(f"CDA: {self.cda}")

            self.long_facet.setEnabled(True)
            self.medium_facet.setEnabled(True)
            # self.aspect_range_checkBox.setEnabled(True)
            # self.count_checkBox.setEnabled(True)
            self.ratio_label1.setEnabled(True)

            if len(self.checked_directions) >= 3:
                self.short_facet.setEnabled(True)
                self.ratio_label2.setEnabled(True)
        else:
            self.cda = False
            print("CDA is not checked")
            print(f"CDA: {self.cda}")

            self.long_facet.setEnabled(False)
            self.medium_facet.setEnabled(False)
            self.aspect_range_checkBox.setEnabled(False)
            self.count_checkBox.setEnabled(False)
            self.ratio_label1.setEnabled(False)
            self.short_facet.setEnabled(False)
            self.ratio_label2.setEnabled(False)

    def plot_check(self, state):
        if state == Qt.Checked:
            self.plot = True
            print(f"Plot: {self.plot}")
        else:
            self.plot = False
            print(f"Plot: {self.plot}")

    def replot_AR_read(self):
        self.PlottingOptions.clear()
        input_path = self.ar_lineEdit.text()

        if input_path != "":
            input_path = Path(input_path)

            if input_path.exists() and input_path.suffix == ".csv":
                self.AR_csv = input_path
                self.GeneratePlots.setEnabled(True)

        else:
            input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Select Aspect Ratio .csv"
            )
            input_path = Path(input_path)
            if input_path.exists() and input_path.suffix == ".csv":
                self.AR_csv = input_path
                self.GeneratePlots.setEnabled(True)

        self.ar_lineEdit.setText(str(input_path))

        self.reread_info(input_path)
        print(input_path)

    def replot_summary_read(self):

        find = Find()

        input_path = self.summaryfile_lineEdit.text()

        if input_path != "":
            input_path = Path(input_path)

            if input_path.exists() and input_path.suffix == ".csv":
                self.summary_csv = input_path

        else:
            input_path, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Select Growth Rate .csv"
            )
            input_path = Path(input_path)
            if input_path.exists() and input_path.suffix == ".csv":
                self.summary_csv = input_path

        self.summaryfile_lineEdit.setText(str(input_path))

        find.summary_compare(
            summary_csv=input_path,
            savefolder=self.replot_folder,
            aspect_csv=self.AR_csv,
        )

        self.AR_csv = f"{self.replot_folder}/aspectratio_energy.csv"

        self.replot_info._replace(Energies=True)

    def reread_info(self, csv):
        print('reading info')
        print(self.AR_csv)

        find = Find()
        replot = Replotting()
        replot_info = namedtuple(
            "PresentData", "Directions, PCA, CDA, Equations, Energies, SAVol, Temperature, CDA_Extended, Supersaturation, GrowthRates"
        )
        self.folder_path = csv.parent

        '''self.replot_folder = find.create_aspects_folder(self.folder_path)'''
        df = pd.read_csv(csv)
        self.ShowData(df)

        directions = []
        energies = False
        pca = False
        cda = False
        equations = False
        savar = False
        temperature = False
        cda_extended = False
        supersaturation = False
        gr_rate = False

        for col in df.columns:
            if col.startswith(" ") or col.startswith("-"):
                directions.append(col)
            if col.startswith("interaction") or col.startswith("tile"):
                energies = True
            if col.startswith("S:M"):
                pca = True
            if col.startswith("S/M"):
                cda = True
            if col.startswith("CDA_Equation"):
                equations = True
            if col.startswith("SA"):
                savar = True
            if col.startswith("temperature"):
                temperature = True
            if col.startswith("AspectRatio"):
                cda_extended = True
            if col.startswith("supersaturation"):
                supersaturation = True
            if col.startswith("Growth"):
                gr_rate = True

        self.input_directions(directions=directions)

        if energies is False:
            self.summary_cs_label.setEnabled(True)
            self.summaryfile_lineEdit.setEnabled(True)
            self.summaryfile_browse_button.setEnabled(True)

        self.replot_info = replot_info(
            Directions=directions,
            PCA=pca,
            CDA=cda,
            Equations=equations,
            Energies=energies,
            SAVol=savar,
            Temperature=temperature,
            CDA_Extended=cda_extended,
            Supersaturation=supersaturation,
            GrowthRates=gr_rate
        )
        print(self.replot_info)
        self.plot_list, self.equation_list = replot.calculate_plots(csv=csv, info=self.replot_info)
        self.SelectPlots.setEnabled(True)
        selected = self.plot_selection(self.replot_info)

    def ShowData(self, df):
        ''' Displaying the dataframe as a QTable '''
        print('Entering Display CSV')
        print(df)
        df = df.iloc[:, 0:]
        self.table = self.DisplayDataFrame
        self.table.setRowCount(df.shape[0])
        self.table.setColumnCount(df.shape[1])
        self.table.setHorizontalHeaderLabels(df.columns)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        for row in df.iterrows():
            values = row[1]
            for col_index, value in enumerate(values):
                if isinstance(value, (float, int)):
                    value = QTableWidgetItem('{:,.2f}'.format(value))
                tableItem = QTableWidgetItem(str(value))
                self.table.setItem(row[0], col_index, tableItem)
        #self.table.setItem(QTableWidgetItem(df))


    def plot_selection(self, plotting_info):
        print('plot selection entered')
        print(plotting_info)

        selected = []

        if plotting_info.PCA == True:
            self.PlottingOptions.addItem("PCA Morphology Map")
            selected.append("PCA Morphology Map")

        if plotting_info.PCA and plotting_info.Equations == True:
            self.PlottingOptions.addItem("Morphology Map by CDA Equation")
            selected.append("Morphology Map by CDA Equation")

        if plotting_info.PCA and plotting_info.Energies and plotting_info.Equations == True:
            self.PlottingOptions.addItem("Morphology Map by CDA Equation vs Energy")
            selected.append("Morphology Map by CDA Equation vs Energy")

        if plotting_info.CDA == True:
            print('CDA True')
            self.PlottingOptions.addItem("CDA Aspect Ratio")
            selected.append("CDA Aspect Ratio")

        if plotting_info.PCA and plotting_info.Energies == True:
            self.PlottingOptions.addItem("Morphology Map vs Energy")
            selected.append("Morphology Map vs Energy")

        if plotting_info.GrowthRates == True:
            self.PlottingOptions.addItem("Growth Rates")
            selected.append("Growth Rates")

        if plotting_info.CDA_Extended == True:
            self.PlottingOptions.addItem("Extended CDA Aspect Ratio")
            selected.append("Extended CDA Aspect Ratio")

        if plotting_info.SAVol == True:
            self.PlottingOptions.addItem("Surface Area vs Volume")
            selected.append("Surface Area vs Volume")
        if plotting_info.SAVol and plotting_info.Energies == True:
            self.PlottingOptions.addItem("Surface Area vs Volume vs Energy")
            selected.append("Surface Area vs Volume vs Energy")
        print(selected)

        return selected

    def plotting_choices(self, whole_plot_list):
        self.SelectPlots.clear()
        self.SelectPlots.update()
        print("plotting choices entered")
        filtered_plot_list = []
        if self.PlottingOptions.currentText() == "CDA Aspect Ratio":
            for item in whole_plot_list:
                if item.startswith("CDA Aspect Ratio"):
                    filtered_plot_list.append(item)
            print("CDA Aspect Ratio")
        if self.PlottingOptions.currentText() == "Extended CDA Aspect Ratio":
            for item in whole_plot_list:
                if item.startswith("Extended CDA"):
                    filtered_plot_list.append(item)
            print("Extended CDA")
        if self.PlottingOptions.currentText() == "Morphology Map by CDA Equation vs Energy":
            for item in whole_plot_list:
                if item.startswith("Morphology Map filter energy "):
                    filtered_plot_list.append(item)
            print("Morphology Map filter energy ")
        if self.PlottingOptions.currentText() == "PCA Morphology Map":
            for item in whole_plot_list:
                if item.startswith("Morphology Map"):
                    filtered_plot_list.append(item)
            print("Morphology Mapping")
        if self.PlottingOptions.currentText() == "Morphology Map vs Energy":
            for item in whole_plot_list:
                if item.startswith("Morphology Map vs "):
                    filtered_plot_list.append(item)
            print("Morphology Map vs Energy")
        if self.PlottingOptions.currentText() == "Surface Area vs Volume":
            for item in whole_plot_list:
                if item.startswith("Surface Area vs Volume"):
                    filtered_plot_list.append(item)
            print("Surface Area vs Volume")
            if self.PlottingOptions.currentText() == "Surface Area vs Volume vs Energy":
                for item in whole_plot_list:
                    if item.startswith("Surface Area vs Volume vs Energy "):
                        filtered_plot_list.append(item)
                print("Surface Area vs Volume vs Energy")
        if self.PlottingOptions.currentText() == "Morphology Map vs Temperature":
            for item in whole_plot_list:
                if item.startswith("Morphology Map vs Temperature"):
                    filtered_plot_list.append(item)
            print("Morphology Map vs Temperature")
        if self.PlottingOptions.currentText() == "Growth Rates":
            for item in whole_plot_list:
                if item.startswith("Growth Rates"):
                    filtered_plot_list.append(item)
            print("Growth Rates")
        if self.PlottingOptions.currentText() == "Morphology Map by CDA Equation":
            for item in whole_plot_list:
                if item.startswith("Morphology Map filtered by "):
                    filtered_plot_list.append(item)
            print("Morphology Map by CDA Equation")
        self.SelectPlots.addItems(filtered_plot_list)
        print(filtered_plot_list)
        self.SelectPlots.update()

    def call_replot(self):
        print('Entering call replot')
        replot = Replotting()
        self.current_plot = self.SelectPlots.currentText()
        print(self.current_plot)
        replot.plotting_called(csv=self.AR_csv,
                               selected=self.current_plot,
                               plot_frame=self.Plotting_Frame,
                               equations_list=self.equation_list)

    def subplotting(self):
        print('entered subplotting')

    def threeD_plotting(self):
        print('entered 3D plotting')
        self.current_plot = self.SelectPlots.currentText()
        if self.AR_csv.suffix == '.csv':
            plot_window = PlotWindow(self)
            plot_window.plotting_info(csv=self.AR_csv,
                                      selected=self.current_plot,
                                      equation_list=self.equation_list)
            plot_window.exec_()
        else:
            pass

    def run_calc(self):
        print(self.checked_directions)
        if self.aspectratio:
            print(self.checked_directions)

            if self.cda:

                long = self.long_facet.currentText()
                medium = self.medium_facet.currentText()
                short = self.short_facet.currentText()

                self.selected_directions = [short, medium, long]
                print('clicked run calc')
                print(self.selected_directions)

        find = Find()
        AspectXYZ = AspectRatioCalc()
        aspect_ratio = AspectRatio()
        plotting = Plotting()
        table = TableDialog()
        save_folder = find.create_aspects_folder(self.folder_path)

        '''if self.sa_vol and self.pca is False:
            aspect_ratio = AspectRatio()
            savar_df = aspect_ratio.savar_calc(
                subfolder=self.folder_path, savefolder=save_folder
            )
            savar_df_final = find.summary_compare(
                summary_csv=self.summary_file,
                aspect_df=savar_df,
                savefolder=save_folder,
            )
            if self.plot:
                plotting.SAVAR_plot(df=savar_df_final, folderpath=save_folder)
        if self.pca and self.sa_vol:
            aspect_ratio = AspectRatio()
            pca_df = aspect_ratio.shape_all(
                subfolder=self.folder_path, savefolder=save_folder
            )
            plot_df = find.summary_compare(
                summary_csv=self.summary_file, aspect_df=pca_df, savefolder=save_folder
            )
            final_df = plot_df
            #self.signals.message.emit("PCA & SA:Vol Calculations complete!")

            if self.plot:
                plotting.SAVAR_plot(df=plot_df, folderpath=save_folder)
                plotting.build_PCAZingg(df=plot_df, folderpath=save_folder)
                #self.signals.message.emit("Plotting PCA & SA:Vol Results!")

        if self.aspectratio:
            aspect_ratio = AspectRatio()
            print(self.checked_directions)

            if self.cda:

                cda_df = aspect_ratio.build_AR_CDA(
                    folderpath=self.folder_path,
                    folders=self.folders,
                    directions=self.checked_directions,
                    selected=self.selected_directions,
                    savefolder=save_folder,
                )

                zn_df = aspect_ratio.defining_equation(
                    directions=self.selected_directions,
                    ar_df=cda_df,
                    filepath=save_folder,
                )
                zn_df_final = find.summary_compare(
                    summary_csv=self.summary_file,
                    aspect_df=zn_df,
                    savefolder=save_folder,
                )
                final_df = zn_df_final
                #self.signals.message.emit("CDA Calculations complete!")

                if self.plot:
                    plotting.CDA_Plot(df=zn_df_final, folderpath=save_folder)
                    plotting.build_zingg_seperated_i(
                        df=zn_df_final, folderpath=save_folder
                    )
                    plotting.Aspect_Extended_Plot(
                        df=zn_df_final,
                        selected=self.selected_directions,
                        folderpath=save_folder,
                    )
                    #self.signals.message.emit("Plotting CDA Results!")
        if self.pca and self.sa_vol:
            aspect_ratio.PCA_shape_percentage(pca_df=pca_df, folderpath=save_folder)

        if self.pca and self.sa_vol is False:
            pca_df = aspect_ratio.build_AR_PCA(
                subfolder=self.folder_path, savefolder=save_folder
            )
            final_df = pca_df
            #self.signals.message.emit("PCA Calculations complete!")

            aspect_ratio.PCA_shape_percentage(pca_df=pca_df, folderpath=save_folder)
            if self.plot:
                #self.signals.message.emit("Plotting PCA Results!")
                plotting.build_PCAZingg(df=pca_df, folderpath=save_folder)

        if self.pca and self.cda:
            pca_cda_df = aspect_ratio.Zingg_CDA_shape_percentage(
                pca_df=pca_df, cda_df=zn_df, folderpath=save_folder
            )
            #self.signals.message.emit("PCA & CDA Calculations complete!")
            if self.plot:
                #self.signals.message.emit("Plotting PCA & CDA Results!")
                plotting.PCA_CDA_Plot(df=pca_cda_df, folderpath=save_folder)
                plotting.build_PCAZingg(df=pca_df, folderpath=save_folder)'''

        if self.aspectratio:
            if self.pca:
                xyz_df = AspectXYZ.collect_all(folder=self.folder_path)
                print(xyz_df)
                xyz_df_final = find.summary_compare(
                    summary_csv=self.summary_file,
                    aspect_df=xyz_df
                )
                xyz_df_final_csv = f"{save_folder}/AspectRatio.csv"
                xyz_df_final.to_csv(xyz_df_final_csv, index=None)
                AspectXYZ.shape_number_percentage(
                    df=xyz_df_final,
                    savefolder=save_folder
                )

                if self.cda is False:
                    self.ShowData(xyz_df_final)
            if self.cda:
                cda_df = aspect_ratio.build_AR_CDA(
                    folderpath=self.folder_path,
                    folders=self.folders,
                    directions=self.checked_directions,
                    selected=self.selected_directions,
                    savefolder=save_folder,
                )
                zn_df = aspect_ratio.defining_equation(
                    directions=self.selected_directions,
                    ar_df=cda_df,
                    filepath=save_folder,
                )
                zn_df_final = find.summary_compare(
                    summary_csv=self.summary_file,
                    aspect_df=zn_df
                )
                zn_df_final_csv = f"{save_folder}/CDA.csv"
                zn_df_final.to_csv(zn_df_final_csv, index=None)
                if self.pca is False:
                    table.DisplayData(zn_df_final)

            if self.cda and self.pca:
                combined_df = find.combine_XYZ_CDA(
                    CDA_df=zn_df,
                    XYZ_df=xyz_df
                )
                final_cda_xyz = find.summary_compare(
                    summary_csv=self.summary_file,
                    aspect_df=combined_df
                )
                final_cda_xyz_csv = f"{save_folder}/CrystalAspects.csv"
                final_cda_xyz.to_csv(final_cda_xyz_csv, index=None)
                self.ShowData(final_cda_xyz)
                aspect_ratio.CDA_Shape_Percentage(
                    df=final_cda_xyz,
                    savefolder=save_folder
                )


    def run_xyz_movie(self, filepath):
        worker_xyz_movie = Worker_Movies(filepath)
        worker_xyz_movie.signals.result.connect(self.get_xyz_movie)
        worker_xyz_movie.signals.progress.connect(self.update_progress)
        worker_xyz_movie.signals.message.connect(self.update_statusbar)
        worker_xyz_movie.signals.finished.connect(
            lambda: Visualiser.init_crystal(self, result=self.xyz_result)
        )
        self.threadpool.start(worker_xyz_movie)

    def get_xyz_movie(self, result):
        self.xyz_result = result

    def update_movie(self, frame):
        Visualiser.update_frame(self, frame)
        self.current_frame_comboBox.setCurrentIndex(frame)
        self.current_frame_spinBox.setValue(frame)
        self.frame_slider.setValue(frame)

    def play_movie(self, frames):
        for frame in range(frames):
            Visualiser.update_frame(self, frame)
            self.current_frame_comboBox.setCurrentIndex(frame)
            self.current_frame_spinBox.setValue(frame)
            self.frame_slider.setValue(frame)

    def update_XYZ_info(self, xyz):

        worker_xyz = Worker_XYZ(xyz)
        worker_xyz.signals.result.connect(self.insert_info)
        worker_xyz.signals.progress.connect(self.update_progress)
        worker_xyz.signals.message.connect(self.update_statusbar)
        self.threadpool.start(worker_xyz)

    def slider_change(self, var, slider_list, dspinbox_list, summ_df, crystals):
        slider = self.sender()
        i = 0
        for name in slider_list:
            if name == slider:
                slider_value = name.value()
                print(slider_value)
                dspinbox_list[i].setValue(slider_value / 100)
            i += 1
        value_list = []
        filter_df = summ_df
        for i in range(var):
            value = slider_list[i].value() / 100
            print(f"locking for: {value}")
            filter_df = filter_df[(summ_df.iloc[:, i] == value)]
            value_list.append(value)
        print("Combination: ", value_list)
        print(filter_df)
        for row in filter_df.index:
            XYZ_file = crystals[row]
            self.output_textBox_3.append(f"Row Number: {row}")
            self.update_progress(0)
            Visualiser.update_XYZ(self, XYZ_file)

    def dspinbox_change(self, var, dspinbox_list, slider_list):
        dspinbox = self.sender()
        i = 0
        for name in dspinbox_list:
            if name == dspinbox:
                dspinbox_value = name.value()
                print(dspinbox_value)
                slider_list[i].setValue(int(dspinbox_value * 100))
            i += 1
        value_list = []
        for i in range(var):
            value = dspinbox_list[i].value()
            value_list.append(value)
        print(value_list)

    def update_vis_sliders(self, value):
        print(value)
        self.fname_comboBox.setCurrentIndex(value)
        self.mainCrystal_slider.setValue(value)
        self.vis_simnum_spinBox.setValue(value)
        self.frame_slider.setValue(value)

    def insert_info(self, result):

        print("Inserting data to GUI!")
        aspect1 = result.aspect1
        aspect2 = result.aspect2
        shape_class = "Unassigned"

        if aspect1 >= 2 / 3:
            if aspect2 >= 2 / 3:
                shape_class = "Block"
            else:
                shape_class = "Needle"
        if aspect1 <= 2 / 3:
            if aspect2 <= 2 / 3:
                shape_class = "Lath"
            else:
                shape_class = "Plate"

        self.sm_label.setText("Small/Medium: {:.2f}".format(aspect1))
        self.ml_label.setText("Medium/Long: {:.2f}".format(aspect2))
        self.shape_label.setText(f"General Shape: {shape_class}")
        self.crystal_sa_label.setText(
            "Crystal Surface Area (nm^2): {:2g}".format(result.surface_area)
        )
        self.crystal_vol_label.setText(
            "Crystal Volume (nm^3): {:2g}".format(result.volume)
        )
        self.crystal_savol_label.setText(
            "Surface Area/Volume: {:2g}".format(result.sa_vol)
        )

    def update_progress(self, progress):
        self.progressBar.setValue(progress)

    def update_statusbar(self, status):
        self.statusBar().showMessage(status)

    def thread_finished(self):
        print("THREAD COMPLETED!")
        '''DataFrame = self.folder_path / 'CrystalAspects' / 'aspectratio_energy.csv'
        print(self.AR_csv)
        print("Printed CSV")
        self.AR_csv = DataFrame
        self.reread_info(csv=self.AR_csv)'''

    def tabChanged(self):
        self.mode = self.tabWidget.currentIndex() + 1
        if self.mode == 1:
            print("Normal Mode selected")
            self.simFolder_Button.setText("Open Simulations Folder")
            self.progressBar.show()
        if self.mode == 2:
            print("3D Data mode selected")
            self.simFolder_Button.setText("XYZ/Simulations Folder")
            self.output_textBox_3.setText(
                "Please open the folder containing the XYZ file(s) to start using the Visualiser/Sliders"
            )

    def output_folder_button(self):
        try:
            dir_path = os.path.realpath(self.folder_path / "CrystalAspects")
            if sys.platform == "win32":
                os.startfile(dir_path)
            else:
                opener = "open" if sys.platform == "darwin" else "xdg-open"
                subprocess.call([opener, dir_path])
            self.statusBar().showMessage("Taking you to the CrystalAspects folder.")
        except NameError:
            try:
                dir_path = os.path.realpath(self.folder_path / "CrystalAspects")
                if sys.platform == "win32":
                    os.startfile(dir_path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, dir_path])
                self.statusBar().showMessage("Taking you to the CrystalAspects folder.")
            except NameError:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Warning)
                msg.setText("Please select CrystalGrower output folder first!")
                msg.setInformativeText(
                    "An output folder is created only once you have selected a CrystalGrower output folder."
                )
                msg.setWindowTitle("Error: Folder not found!")
                msg.exec_()


# Override sys excepthook to prevent app abortion upon any error
# (Reverts to old PyQt4 behaviour of
# simply printing the traceback to stdout/stderr)


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == "__main__":

    # Override sys excepthook to prevent app abortion upon any error
    sys.excepthook = except_hook

    # Setting taskbar icon permissions - windows
    try:
        import ctypes

        appid = "CNM.CrystalGrower.DataProcessor.v1.0"  # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    except:
        pass

    # ############# Runs the application ############## #
    QApplication.setAttribute(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icon.png")))
    mainwindow = MainWindow()
    mainwindow.show()
    sys.exit(app.exec_())
