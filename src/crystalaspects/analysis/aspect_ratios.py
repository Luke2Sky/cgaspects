import logging
from collections import namedtuple
from pathlib import Path

from PySide6.QtCore import QThreadPool, Signal
from PySide6.QtWidgets import QDialog, QWidget

import crystalaspects.analysis.ar_dataframes as ar
import crystalaspects.fileio.find_data as fd
from crystalaspects.analysis.gui_threads import WorkerAspectRatios
from crystalaspects.gui.dialogs.aspectratio_dialog import AnalysisOptionsDialog
from crystalaspects.visualisation.plot_data import Plotting
from crystalaspects.gui.dialogs.plot_dialog import PlottingDialog

logger = logging.getLogger("CA:A-Ratios")


class AspectRatio(QWidget):
    def __init__(self, signals):
        self.input_folder = None
        self.output_folder = None
        self.directions = None
        self.information = None
        self.directions = None
        self.selected_direction = None
        self.options: namedtuple | None = None
        self.threadpool = None
        self.threadpool = QThreadPool()
        self.result_tuple = namedtuple("Result", ["csv", "selected", "folder"])

        self.signals = signals
        self.plotting_csv = None

    def update_progress(self, value):
        self.signals.progress.emit(value)

    def set_folder(self, folder):
        self.input_folder = Path(folder)
        logger.info("Folder set for aspect ratio calculations")

    def set_information(self, information):
        self.information = information
        logger.info("Information set for aspect ratio calculations")

    def calculate_aspect_ratio(self):
        logger.debug("Called aspect ratio method at directory: %s", self.input_folder)
        # Check if the user selected a folder
        if self.input_folder:
            if self.information is None:
                logger.warning(
                    "Method called without information, looking for information now."
                )
                # Read the information from the selected folder
                self.information = fd.find_info(self.input_folder)
            logger.info("Attempting to calculate Aspect Ratios...")

            """Future Note: The follwing renders the 
            dataprocessor unable to process just XYZ files
            in the envent no *simulation_parameters.txt files are not present"""

        if not self.input_folder and self.information:
            logger.warning("Input folder and Information not set properly")
            return

        # Get the directions from the information
        self.directions = self.information.directions
        logger.debug("All Directions: %s", self.directions)

        # Create the analysis options dialog
        dialog = AnalysisOptionsDialog(directions=self.directions)

        if dialog.exec() != QDialog.Accepted:
            logger.warning("Selecting aspect ratio options cancelled")
            return

        # if dialog.exec() == QDialog.Accepted:
        # Retrieve the selected options
        self.options = dialog.get_options()
        logger.info(
            "Options:: AR: %s  CDA: %s  Checked: %s   Selected: %s   Auto Plot: %s",
            self.options.selected_ar,
            self.options.selected_cda,
            self.options.checked_directions,
            self.options.selected_directions,
            self.options.plotting,
        )

        # self.circular_progress = CircularProgress(calc_type="Aspect Ratio")
        # self.circular_progress.show()
        # self.circular_progress.raise_()
        # # Display the information in a QMessageBox
        # self.circular_progress.update_options(self.options)

        if self.threadpool:
            worker = WorkerAspectRatios(
                information=self.information,
                options=self.options,
                input_folder=self.input_folder,
                output_folder=self.output_folder,
            )
            worker.signals.progress.connect(self.update_progress)
            worker.signals.result.connect(self.set_plotting)
            worker.signals.location.connect(self.get_location)
            self.signals.started.emit()
            self.threadpool.start(worker)

        else:
            logger.warning("Running Calculation on the same (GUI) thread!")
            self.run_on_same_thread()
            self.set_plotting(plotting_csv=self.plotting_csv)

    def set_plotting(self, plotting_csv):
        result = self.result_tuple(csv=plotting_csv, selected=None, folder=None)
        self.signals.finished.emit()
        self.signals.result.emit(result)
        logger.debug("Sending plotting information to GUI: %s", result)
        self.plot(plotting_csv=plotting_csv)

    def plot(self, plotting_csv):
        # self.circular_progress.hide()
        if self.options.plotting:
            self.perform_plotting(
                csv_file=plotting_csv,
                folderpath=self.output_folder,
                selected_directions=self.options.selected_directions,
            )

        PlottingDialogs = PlottingDialog(csv=plotting_csv)
        PlottingDialogs.show()

    def perform_plotting(self, csv_file, folderpath, selected_directions=None):
        plotting = Plotting()
        # Handle XYZ plotting
        if self.options.selected_ar:
            plotting.plot_pca(csv=csv_file, folderpath=folderpath)
            plotting.plot_oba(csv=csv_file, folderpath=folderpath)
            plotting.plot_sa_vol(csv=csv_file, folderpath=folderpath)

        # Handle CDA plotting
        if self.options.selected_cda:
            plotting.plot_cda_extended(
                csv=csv_file, folderpath=folderpath, selected=selected_directions
            )
            plotting.plot_cda(csv=csv_file, folderpath=folderpath)

        # Handle combined CDA and XYZ plotting
        if self.options.selected_ar and self.options.selected_cda:
            plotting.plot_cda_pca(csv=csv_file, folderpath=folderpath)
            plotting.plot_cda_oba(csv=csv_file, folderpath=folderpath)

    def get_location(self, location):
        self.output_folder = location
        self.signals.location.emit(location)

    def run_on_same_thread(self):
        self.output_folder = fd.create_aspects_folder(self.input_folder)

        summary_file = self.information.summary_file
        folders = self.information.folders

        if self.options.selected_ar:
            xyz_df = ar.collect_all(folder=self.input_folder)
            xyz_combine = xyz_df
            if summary_file:
                xyz_df = fd.summary_compare(summary_csv=summary_file, aspect_df=xyz_df)
            xyz_df_final_csv = self.output_folder / "aspectratio.csv"
            xyz_df.to_csv(xyz_df_final_csv, index=None)
            ar.get_xyz_shape_percentage(df=xyz_df, savefolder=self.output_folder)
            self.plotting_csv = xyz_df_final_csv

        if self.options.selected_cda:
            cda_df = ar.build_cda(
                folderpath=self.input_folder,
                folders=folders,
                directions=self.options.checked_directions,
                selected=self.options.selected_directions,
                savefolder=self.output_folder,
            )
            zn_df = ar.build_ratio_equations(
                directions=self.options.selected_directions,
                ar_df=cda_df,
                filepath=self.output_folder,
            )
            if summary_file:
                zn_df = fd.summary_compare(summary_csv=summary_file, aspect_df=zn_df)
            zn_df_final_csv = self.output_folder / "cda.csv"
            zn_df.to_csv(zn_df_final_csv, index=None)
            self.plotting_csv = zn_df_final_csv

            if self.options.selected_ar and self.options.selected_cda:
                combined_df = fd.combine_xyz_cda(CDA_df=zn_df, XYZ_df=xyz_combine)
                final_cda_xyz_csv = self.output_folder / "crystalaspects.csv"
                combined_df.to_csv(final_cda_xyz_csv, index=None)
                ar.get_cda_shape_percentage(
                    df=combined_df, savefolder=self.output_folder
                )
                self.plotting_csv = final_cda_xyz_csv
