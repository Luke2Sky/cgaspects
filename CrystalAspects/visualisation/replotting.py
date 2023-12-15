import numpy as np
import pandas as pd
from pathlib import Path
import ast

# PyQt imports
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDialog, QApplication, QPushButton, \
    QVBoxLayout, QMessageBox, QInputDialog, \
    QVBoxLayout, QHBoxLayout, QFileDialog, \
    QGridLayout, QSpinBox, QLabel, \
    QCheckBox, QSizePolicy, QComboBox, \
    QWidget

# Matplotlib import
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('QT5Agg')

class PlottingDialogue(QDialog):
    def __init__(self, parent=None):
        super(PlottingDialogue, self).__init__(parent)
        self.setWindowTitle("Plot Window")
        self.setGeometry(100, 100, 800, 600)

        # Set the dialog to be non-modal
        self.setWindowModality(QtCore.Qt.NonModal)

        self.create_widgets()
        self.create_layout()

    def plotting_info(self, csv, plotting):
        self.csv = csv
        df = pd.read_csv(self.csv)
        print(df)
        self.growth_rate = None
        # Identify interaction columns
        interaction_columns = [col for col in df.columns if
                               col.startswith(('interaction',
                                               'tile',
                                               'temperature',
                                               'starting_delmu',
                                               'excess'))]
        print(interaction_columns)

        # List to store the results
        plot_types = []

        # Check each column heading
        for column in df.columns:
            if column.startswith('OBA') and 'OBA' not in plot_types:
                plot_types.append('OBA')
            elif column.startswith('PCA') and 'PCA' not in plot_types:
                plot_types.append('PCA')
            elif column == 'Surface Area: Volume Ratio' and 'Surface Area: Volume Ratio' not in plot_types:
                plot_types.append('Surface Area: Volume Ratio')
            elif column.startswith('M/L') and 'CDA' not in plot_types:
                plot_types.append('CDA')
            elif column.startswith('AspectRatio') and 'CDA Extended' not in plot_types:
                plot_types.append('CDA Extended')

        # Get equations
        for column in df.columns:
            if column.startswith("CDA_Equation"):
                equations = set(df["CDA_Equation"])
                print(equations)
                for equation in equations:
                    plot_types.append(f"OBA vs CDA Equation {equation}")
                    plot_types.append(f"PCA vs CDA Equation {equation}")

        self.plots_list = []
        for plot_type in plot_types:
            # Add the basic plot
            self.plots_list.append(plot_type)

            # Add plots with interaction
            for interaction_col in interaction_columns:
                self.plots_list.append(f"{plot_type} vs {interaction_col}")

        if plotting == 'Growth Rates':
            self.plotting = 'Scatter+Line'
            self.growth_rate = True
            directions = []
            for col in df.columns:
                if col.startswith(" "):
                    directions.append(col)
            self.directions = directions
            print(directions)
            self.plots_list = ['Growth Rates']

    def create_widgets(self):

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.button_plot = QPushButton("Plot")
        self.button_save = QPushButton("Save")
        self.button_plot_list = QPushButton("Generate Plot List")
        self.label_pointsize = QLabel("Point Size:")
        self.spin_point_size = QSpinBox()
        self.checkbox_colorbar = QCheckBox("Colorbar")
        self.button_add_trendline = QPushButton("Add Trendline")
        # Set the properties of the widgets
        self.spin_point_size.setRange(1, 100)

        # Initialize the variables
        self.point_size = self.spin_point_size.value()
        self.colorbar = False
        self.scatter = None

        self.checkbox_colorbar = QCheckBox("Show Colorbar")

        # Connect the signals and slots
        # Initialize checkboxes
        self.checkbox_grid = QCheckBox("Show Grid")
        self.checkbox_trendline = QCheckBox("Add Trendline")
        self.button_plot.clicked.connect(self.plot)
        self.button_save.clicked.connect(self.save)
        self.button_plot_list.clicked.connect(self.add_plot_list)
        self.checkbox_colorbar.stateChanged.connect(self.toggle_colorbar)    # Connect the add trendline button to its handler
        self.button_add_trendline.clicked.connect(self.add_trendline)
        self.spin_point_size.valueChanged.connect(self.set_point_size)
        self.canvas.mpl_connect("motion_notify_event", lambda event: self.on_hover(event))

        # Create the plot type combo box
        self.plot_type_combo_box = QComboBox()
        self.plot_type_combo_box.addItems(['Scatter', 'Line', 'Scatter+Line'])
        self.plot_type_combo_box.currentIndexChanged.connect(self.change_plot_type)
        self.btn_change_plot = QPushButton("Change Plot Type")
        self.btn_change_plot.clicked.connect(self.change_plot_type)
        # Create and add items to plot_list_combo_box here
        self.plot_list_combo_box = QComboBox()
        self.plot_list_combo_box.currentIndexChanged.connect(self.change_plot_from_list)
        self.plot_list_combo_box.setMaxVisibleItems(5)
        self.plot_list_combo_box.show()

        # Initialize the plot type
        self.plot_type = "scatter"

    def create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.label_pointsize)
        hbox1.addWidget(self.spin_point_size)
        hbox1.addWidget(self.checkbox_grid)
        hbox1.addWidget(self.plot_type_combo_box)
        hbox1.addWidget(self.plot_list_combo_box)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.button_plot)
        hbox2.addWidget(self.button_save)
        hbox2.addWidget(self.button_plot_list)
        hbox2.addWidget(self.button_add_trendline)

        layout.addLayout(hbox1)
        layout.addLayout(hbox2)

        # Set window properties
        self.setWindowTitle("Plot Window")
        self.setGeometry(100, 100, 800, 600)
        self.setLayout(layout)

    def set_point_size(self, value):
        self.point_size = self.spin_point_size.value()
        if self.scatter is not None:
            self.scatter.set_sizes([self.point_size] * len(self.scatter.get_offsets()))
        self.canvas.draw()

    def toggle_colorbar(self, state):
        self.colorbar = state == Qt.Checked

    def change_plot_type(self):
        plot_type = self.plot_type

        if plot_type == 'Scatter':
            self.plot_type = 'scatter'
            self.plot()
        if plot_type == 'Scatter+Line':
            self.plot_type = 'scatter_line'
            self.plot()
        if plot_type == 'Line':
            self.plot_type = 'line'
            self.plot()

    def add_plot_list(self):
        self.plot_list_combo_box.addItems(self.plots_list)

    def change_plot_from_list(self):
        self.selected_plot = self.plot_list_combo_box.currentText()

    def plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.clear()  # clear the plot
        self.canvas.draw()  # redraw the canvas
        print("entering plotting called")
        # Reading the dataframe
        df = pd.read_csv(self.csv)
        self.plot_objects = {}
        # Finding interactions in data frame if there are any
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction")
               or col.startswith("tile")
               or col.startswith("starting_delmu")
               or col.startswith("temperature_celcius")
               or col.startswith("excess")
        ]

        equation_plot = False
        for col in df.columns:
            if col.startswith("CDA_Equation"):
                equations = set(df["CDA_Equation"])
                equation_plot = True

        for col in df.columns:
            if col.startswith("interaction") or col.startswith('tile'):
                cbar_legend = r"$\Delta G_{Cryst}$ (kcal/mol)"
            if col.startswith("starting_delmu"):
                cbar_legend = r"$\Delta G_{Cryst}$ (kcal/mol)"
                plot_title = "Aspect Ratio vs Supersaturation"
            if col.startswith("temperature_celcius"):
                cbar_legend = u'Temperature (℃)'
                plot_title = "Aspect Ratio vs Temperature"
            if col.startswith("excess"):
                cbar_legend = r"$\Delta G_{Cryst}$ (kcal/mol)"
                plot_title = "Aspect Ratio vs Excess Supersaturation"

        if self.selected_plot == "OBA":
            x_data = df["OBA S:M"]
            y_data = df["OBA M:L"]
            print(x_data)
            print(y_data)
            # Plot the data
            self.scatter = self.ax.scatter(x_data, y_data, s=12)
            # When creating a scatter plot without colour data
            self.plot_objects[f''] = (None, self.scatter, None, None)
            self.ax.axhline(y=0.66, color='black', linestyle='--')
            self.ax.axvline(x=0.66, color='black', linestyle='--')
            self.ax.set_xlabel('S:M')
            self.ax.set_ylabel('M:L')
            self.ax.set_xlim(0, 1.0)
            self.ax.set_ylim(0, 1.0)
            self.ax.set_title('OBA Zingg Diagram')

        if self.selected_plot == "PCA":
            x_data = df["PCA S:M"]
            y_data = df["PCA M:L"]
            print(x_data)
            print(y_data)
            # Plot the data
            self.scatter = self.ax.scatter(x_data, y_data, s=12)
            # When creating a scatter plot without colour data
            self.plot_objects[f''] = (None, self.scatter, None, None)
            self.ax.axhline(y=0.66, color='black', linestyle='--')
            self.ax.axvline(x=0.66, color='black', linestyle='--')
            self.ax.set_xlabel('S:M')
            self.ax.set_ylabel('M:L')
            self.ax.set_xlim(0, 1.0)
            self.ax.set_ylim(0, 1.0)
            self.ax.set_title('PCA Zingg Diagram')

        if self.selected_plot == "Surface Area: Volume Ratio":
            x_data = df["Surface Area (SA)"]
            y_data = df["Volume (Vol)"]
            print(x_data)
            print(y_data)
            # Plot the data
            self.scatter = self.ax.scatter(x_data, y_data, s=12)
            # When creating a scatter plot without colour data
            self.plot_objects[f''] = (None, self.scatter, None, None)
            self.ax.set_xlabel('Surface Area (nm2)')
            self.ax.set_ylabel('Volume (nm3)')
            self.ax.set_title('Surface Area: Volume')

        if self.selected_plot == "CDA":
            x_data = df["S/M"]
            y_data = df["M/L"]
            print(x_data)
            print(y_data)
            # Plot the data
            self.scatter = self.ax.scatter(x_data, y_data, s=12)
            # When creating a scatter plot without colour data
            self.plot_objects[f''] = (None, self.scatter, None, None)
            self.ax.set_xlabel('CDA S/M')
            self.ax.set_ylabel('CDA M/L')
            self.ax.set_xlim(0, 1.0)
            self.ax.set_ylim(0, 1.0)
            self.ax.set_title('CDA Zingg Diagram')

        if self.selected_plot == "CDA Extended":
            x_data = None
            y_data = None
            x_column_name = None
            y_column_name = None
            # Counter for 'AspectRatio' columns
            aspect_ratio_count = 0
            for column in df.columns:
                if column.startswith('AspectRatio'):
                    aspect_ratio_count += 1
                    if aspect_ratio_count == 1:
                        x_data = df[column]
                        x_column_name = column
                    elif aspect_ratio_count == 2:
                        y_data = df[column]
                        y_column_name = column
                        break
            print(x_data)
            print(y_data)
            # Plot the data
            self.scatter = self.ax.scatter(x_data, y_data, s=12)
            # When creating a scatter plot without colour data
            self.plot_objects[f''] = (None, self.scatter, None, None)
            self.ax.set_xlabel(x_column_name)
            self.ax.set_ylabel(y_column_name)
            self.ax.set_title('Extended CDA')
            self.canvas.draw()

        # Plotting each interaction separately
        for interaction in interactions:
            if self.selected_plot.startswith("OBA vs " + interaction):
                print("interaction:", interaction)
                x_data = df["OBA S:M"]
                y_data = df["OBA M:L"]
                colour_data = df[interaction]
                # Check if colour_data is numerical or needs conversion
                if colour_data.dtype.kind not in 'biufc':  # Check if not a number
                    colour_data = pd.factorize(colour_data)[0]
                # Plot the data
                self.scatter = self.ax.scatter(x_data, y_data, c=colour_data, cmap="plasma", s=12)
                # When creating a scatter plot with colour data
                self.plot_objects[f'Plot {interaction}'] = (None, self.scatter, colour_data, interaction)
                self.ax.axhline(y=0.66, color='black', linestyle='--')
                self.ax.axvline(x=0.66, color='black', linestyle='--')
                self.ax.set_xlabel('S:M')
                self.ax.set_ylabel('M:L')
                self.ax.set_xlim(0.0, 1.0)
                self.ax.set_ylim(0.0, 1.0)
                self.ax.set_title(f'OBA {interaction}')
                # Add colorbar and other customizations as needed
                cbar = self.figure.colorbar(self.scatter)
                cbar.set_label(cbar_legend)
                cbar.ax.set_zorder(-1)
                self.canvas.draw()

            if self.selected_plot.startswith("PCA vs " + interaction):
                print("interaction:", interaction)
                x_data = df["PCA S:M"]
                y_data = df["PCA M:L"]
                colour_data = df[interaction]
                # Check if colour_data is numerical or needs conversion
                if colour_data.dtype.kind not in 'biufc':  # Check if not a number
                    colour_data = pd.factorize(colour_data)[0]
                # Plot the data
                self.scatter = self.ax.scatter(x_data, y_data, c=colour_data, cmap="plasma", s=12)
                # When creating a scatter plot with colour data
                self.plot_objects[f'Plot {interaction}'] = (None, self.scatter, colour_data, interaction)
                self.ax.axhline(y=0.66, color='black', linestyle='--')
                self.ax.axvline(x=0.66, color='black', linestyle='--')
                self.ax.set_xlabel('S:M')
                self.ax.set_ylabel('M:L')
                self.ax.set_xlim(0.0, 1.0)
                self.ax.set_ylim(0.0, 1.0)
                self.ax.set_title(f'PCA {interaction}')
                # Add colorbar and other customizations as needed
                cbar = self.figure.colorbar(self.scatter)
                cbar.set_label(cbar_legend)
                cbar.ax.set_zorder(-1)
                self.canvas.draw()

            if self.selected_plot.startswith("Surface Area: Volume Ratio vs " + interaction):
                x_data = df["Surface Area (SA)"]
                y_data = df["Volume (Vol)"]
                colour_data = df[interaction]
                # Check if colour_data is numerical or needs conversion
                if colour_data.dtype.kind not in 'biufc':  # Check if not a number
                    colour_data = pd.factorize(colour_data)[0]
                # Plot the data
                self.scatter = self.ax.scatter(x_data, y_data, c=colour_data, cmap="plasma", s=12)
                # When creating a scatter plot with colour data
                self.plot_objects[f'Plot {interaction}'] = (None, self.scatter, colour_data, interaction)
                self.ax.set_xlabel('Surface Area (nm2)')
                self.ax.set_ylabel('Volume (nm3)')
                self.ax.set_title(f'Surface Area: Volume {interaction}')
                # Add colorbar and other customizations as needed
                cbar = self.figure.colorbar(self.scatter)
                cbar.set_label(cbar_legend)
                cbar.ax.set_zorder(-1)
                self.canvas.draw()

            if self.selected_plot.startswith("CDA vs " + interaction):
                print("interaction:", interaction)
                x_data = df["S/M"]
                y_data = df["M/L"]
                colour_data = df[interaction]
                # Check if colour_data is numerical or needs conversion
                if colour_data.dtype.kind not in 'biufc':  # Check if not a number
                    colour_data = pd.factorize(colour_data)[0]
                # Plot the data
                self.scatter = self.ax.scatter(x_data, y_data, c=colour_data, cmap="plasma", s=12)
                # When creating a scatter plot with colour data
                self.plot_objects[f'Plot {interaction}'] = (None, self.scatter, colour_data, interaction)
                self.ax.axhline(y=0.66, color='black', linestyle='--')
                self.ax.axvline(x=0.66, color='black', linestyle='--')
                self.ax.set_xlabel('CDA S/M')
                self.ax.set_ylabel('CDA M/L')
                self.ax.set_xlim(0.0, 1.0)
                self.ax.set_ylim(0.0, 1.0)
                self.ax.set_title(f'CDA {interaction}')
                # Add colorbar and other customizations as needed
                cbar = self.figure.colorbar(self.scatter)
                cbar.set_label(cbar_legend)
                cbar.ax.set_zorder(-1)
                self.canvas.draw()

            if self.selected_plot.startswith("CDA Extended vs " + interaction):
                print("interaction:", interaction)
                x_data = None
                y_data = None
                x_column_name = None
                y_column_name = None
                # Counter for 'AspectRatio' columns
                aspect_ratio_count = 0
                for column in df.columns:
                    if column.startswith('AspectRatio'):
                        aspect_ratio_count += 1
                        if aspect_ratio_count == 1:
                            x_data = df[column]
                            x_column_name = column
                        elif aspect_ratio_count == 2:
                            y_data = df[column]
                            y_column_name = column
                            break
                print(x_data)
                print(y_data)
                colour_data = df[interaction]
                # Check if colour_data is numerical or needs conversion
                if colour_data.dtype.kind not in 'biufc':  # Check if not a number
                    colour_data = pd.factorize(colour_data)[0]
                # Plot the data
                self.scatter = self.ax.scatter(x_data, y_data, c=colour_data, cmap="plasma", s=12)
                # When creating a scatter plot with colour data
                self.plot_objects[f'Plot {interaction}'] = (None, self.scatter, colour_data, interaction)
                self.ax.set_xlabel(x_column_name)
                self.ax.set_ylabel(y_column_name)
                self.ax.set_title(f'Extended CDA {interaction}')
                # Add colorbar and other customizations as needed
                cbar = self.figure.colorbar(self.scatter)
                cbar.set_label(cbar_legend)
                cbar.ax.set_zorder(-1)
                self.canvas.draw()

        if equation_plot:
            for equation in equations:
                if self.selected_plot.startswith(f"OBA vs CDA Equation {equation}"):
                    df = df[df["CDA_Equation"] == equation]
                    print("interaction:", equation)
                    x_data = df["OBA S:M"]
                    y_data = df["OBA M:L"]
                    # Plot the data
                    self.scatter = self.ax.scatter(x_data, y_data, s=12)
                    # When creating a scatter plot without colour data
                    self.plot_objects[f''] = (None, self.scatter, None, None)
                    self.ax.axhline(y=0.66, color='black', linestyle='--')
                    self.ax.axvline(x=0.66, color='black', linestyle='--')
                    self.ax.set_xlabel('S:M')
                    self.ax.set_ylabel('M:L')
                    self.ax.set_xlim(0.0, 1.0)
                    self.ax.set_ylim(0.0, 1.0)
                    self.ax.set_title(f'OBA vs CDA Equation {equation}')
                    self.canvas.draw()

                if self.selected_plot.startswith(f"PCA vs CDA Equation {equation}"):
                    df = df[df["CDA_Equation"] == equation]
                    print("interaction:", equation)
                    x_data = df["PCA S:M"]
                    y_data = df["PCA M:L"]
                    # Plot the data
                    self.scatter = self.ax.scatter(x_data, y_data, s=12)
                    # When creating a scatter plot without colour data
                    self.plot_objects[f''] = (None, self.scatter, None, None)
                    self.ax.axhline(y=0.66, color='black', linestyle='--')
                    self.ax.axvline(x=0.66, color='black', linestyle='--')
                    self.ax.set_xlabel('S:M')
                    self.ax.set_ylabel('M:L')
                    self.ax.set_xlim(0.0, 1.0)
                    self.ax.set_ylim(0.0, 1.0)
                    self.ax.set_title(f'PCA vs CDA Equation {equation}')
                    self.canvas.draw()

        if self.growth_rate:
            x_data = df["Supersaturation"]
            self.plot_objects = {}  # Store plot objects for reference (both line and scatter)

            # Define the on_legend_click function here
            def on_legend_click(event):
                legline = event.artist
                origline, origscatter, _, _ = self.plot_objects[legline.get_label()]
                vis = not origline.get_visible()
                origline.set_visible(vis)
                origscatter.set_visible(vis)
                legline.set_alpha(1.0 if vis else 0.2)
                self.canvas.draw()

            for i in self.directions:
                self.scatter = self.ax.scatter(x_data, df[i], s=6)
                line, = self.ax.plot(x_data, df[i], label=f' {i}')
                self.plot_objects[f' {i}'] = (line, self.scatter, None, None)
                self.ax.set_xlabel('Supersaturation (kcal/mol)')
                self.ax.set_ylabel('Growth Rate')
                self.ax.set_title('Growth Rates')

            # Create a legend
            legend = self.ax.legend()

            for legline in legend.get_lines():
                legline.set_picker(5)  # Enable clicking on the legend line
                legline.figure.canvas.mpl_connect('pick_event', on_legend_click)

            self.canvas.draw()

        if self.colorbar:
            cbar = self.figure.colorbar(self.scatter)
            cbar.set_label(r"$\Delta G_{Cryst}$ (kcal/mol)")

        if self.checkbox_grid.isChecked():
            self.ax.grid()
        self.annot = self.ax.annotate("", xy=(-1, -1), xytext=(-20, 20),
                                      textcoords="offset points",
                                      ha='center',
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"),
                                      zorder=20)
        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, scatter, colour_data, column_name, ind):
        pos = scatter.get_offsets()[ind["ind"][0]]
        self.annot.xy = pos
        x, y = pos

        # Check if colour_data is available
        if colour_data is not None:
            color_val = colour_data[ind["ind"][0]]
            text = f"Sim Number: {ind['ind'][0] + 1}\n" \
                   f" x: {x:.2f}'\n" \
                   f" y: {y:.2f}\n" \
                   f" {column_name}: {color_val:.2f}"
        else:
            text = f"Sim Number: {ind['ind'][0] + 1}\n" \
                   f" x: {x:.2f}\n" \
                   f" y: {y:.2f}"

        self.annot.set_text(text)
        self.annot.get_bbox_patch().set_alpha(0.4)

    def on_hover(self, event):
        vis = self.annot.get_visible()
        try:
            if event.inaxes == self.ax:
                for _, plot_data in self.plot_objects.items():
                    # Unpack the plot data
                    line, scatter, colour_data, column_name = plot_data

                    # Check if scatter plot exists and handle hover event
                    if scatter is not None:
                        cont, ind = scatter.contains(event)
                        if cont:
                            self.update_annot(scatter, colour_data, column_name, ind)
                            self.annot.set_visible(True)
                            self.figure.canvas.draw_idle()
                            break

                # Hide annotation if no scatter plot contains the event
                if not cont and vis:
                    self.annot.set_visible(False)
                    self.figure.canvas.draw_idle()
        except NameError:
            pass

    def add_trendline(self):
        if self.scatter is None:
            self.statusBar().showMessage("Error: No scatter plot to add trendline to.")
            return
        x = self.scatter.get_offsets()[:, 0]
        y = self.scatter.get_offsets()[:, 1]

        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        self.ax.plot(x, p(x), "r--")

        # Format the equation text
        equation_text = f"y = {z[0]:.2f}x + {z[1]:.2f}"
        # Add the text to the plot. Adjust the position as needed.
        self.ax.text(0.05, 0.95, equation_text, transform=self.ax.transAxes, fontsize=12, verticalalignment='top')

        self.canvas.draw()

    def save(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix("png")
        file_dialog.setNameFilters(["PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*)"])
        file_dialog.setOption(QFileDialog.DontUseNativeDialog)
        file_dialog.setDirectory(".")
        file_dialog.setWindowTitle("Save Plot")

        if file_dialog.exec_() == QDialog.Accepted:
            file_name = file_dialog.selectedFiles()[0]
            transparent = QMessageBox.question(self, "Transparent Background",
                                               "Do you want a transparent background?",
                                               QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.No) == QMessageBox.Yes

            if file_name:
                size = [6.8, 4.8]
                if transparent:
                    self.figure.savefig(file_name, figsize=size, transparent=True, dpi=600)
                else:
                    self.figure.savefig(file_name, figsize=size, dpi=600)



class Replotting:

    def __init__(self):
        super(Replotting, self).__init__()
        self.equations_list = []

    def calculate_plots(self, csv="", info=""):
        print("Info:  ")
        print(info)
        print("Entered calculate plots")
        if csv != "":
            folderpath = Path(csv).parents[0]
            df = pd.read_csv(csv)
        plot_list = []
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction") or col.startswith("tile")
        ]
        print(interactions)
        number_interactions = len(interactions)
        print(number_interactions)
        equations = []
        if info.Equations == True:
            equations = self.read_equations()
        if info.PCA == True:
            plot_list.append("Morphology Map")
        if info.Energies and info.PCA == True:
            for interaction in interactions:
                plot_list.append("Morphology Map vs " + interaction)
        if info.PCA and info.Equations == True:
            for equation in equations:
                plot_list.append("Morphology Map filtered by " + equation)
        if info.Energies and info.PCA and info.Equations == True:
            for interaction in interactions:
                for equation in equations:
                    plot_list.append("Morphology Map filter energy " + interaction + " " + equation)
        if info.CDA == True:
            plot_list.append("CDA Aspect Ratio")
        if info.CDA and info.Energies == True:
            for interaction in interactions:
                plot_list.append("CDA Aspect Ratio " + interaction)
        if info.SAVol == True:
            plot_list.append("Surface Area vs Volume")
        if info.SAVol and info.Energies == True:
            for interaction in interactions:
                plot_list.append("Surface Area vs Volume vs Energy " + interaction)
        if info.CDA_Extended == True:
            plot_list.append("Extended CDA")
        if info.CDA_Extended and info.Energies == True:
            for interaction in interactions:
                plot_list.append("Extended CDA " + interaction)
        if info.CDA and info.Temperature == True:
            plot_list.append("CDA Aspect Ratio vs Temperature")
        if info.Temperature and info.PCA == True:
            plot_list.append("Morphology Map vs Temperature")
        if info.GrowthRates == True:
            plot_list.append("Growth Rates")
        print("List of plots =====")
        print(plot_list)

        return plot_list, equations

    def read_equations(self):
        print("Entering Read Equations")
        msg = QMessageBox()
        msg.setText("CDA Equations found. Please open CDA_equations.txt")
        msg.setIcon(QMessageBox.Question)
        msg.exec_()
        equations_list = []

        equations_txt, _ = QtWidgets.QFileDialog.getOpenFileName(
                None, "Select CDA_Equations .csv"
            )

        with open(equations_txt, "r", encoding="utf-8") as eq_txt:
            eq_line = eq_txt.read()
            if eq_line.startswith("Equation Number1"):
                eq_msg = QMessageBox()
                eq_msg.setText(eq_line)
                eq_msg.exec_()
                with open(equations_txt, "r", encoding="utf-8") as eq_file:
                    equation_lines = eq_file.readlines()
                    print(equation_lines)
                    for line in equation_lines:
                        tuple_str = line.split(':')[1].strip()
                        tuple_obj = ast.literal_eval(tuple_str)
                        equation_obj = tuple_obj[0] + ' : ' \
                                       + tuple_obj[1] + ' : ' \
                                       + tuple_obj[2]
                        equations_list.append(equation_obj)
            '''else:
                eq_problem = QMessageBox()
                eq_problem.setText("File incorrect.\n"
                                   "Please select file named: CDA_equations.txt")
                eq_problem.setIcon(QMessageBox.Critical)
                eq_problem.setStandardButtons(QMessageBox.Retry)
                eq_problem.exec_()
                if QMessageBox.Retry:
                    # User clicked "Retry"
                    self.read_equations()
                    return'''

        print("equations_list :  ")
        print(equations_list)
        self.equations_list = equations_list
        print("self.equations_list ======")
        print(self.equations_list)

        return equations_list

    def plotting_called(self, csv, selected, plot_frame, equations_list):
        print("entering plotting called")
        # Reading the dataframe
        df = pd.read_csv(csv)
        print(df)
        # Reading self.current_plots() coming from self.SelectPlots.currentText()
        selected = selected
        # Finding interactions in data frame if there are any
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction") or col.startswith("tile")
        ]
        print(interactions)
        print(selected)
        # Finding extended CDA in data frame if there are any
        extended = [col for col in df.columns
                    if col.startswith("AspectRatio")]
        print(extended)
        self.figure = plt.figure()
        '''# Create horizontal layout
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout(plot_frame)
        # Create Canvas
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        # End canvas
        # Add canvas
        self.horizontalLayout_4.addWidget(self.canvas)
        # End of horizontal layout'''

        if selected == 'Surface Area vs Volume':
            print("Entering PCA Morphology Map")
            x_data = df['Volume (Vol)']
            y_data = df['Surface_Area (SA)']
            # Plot the data
            plt.scatter(x_data, y_data, s=1.2)
            plt.xlabel(r"Volume ($nm^3$)")
            plt.ylabel(r"Surface Area ($nm^2$)")
            plt.show()

        if selected == "Morphology Map":
            #self.figure.clear()
            print("Entering PCA Morphology Map")
            x_data = df['S:M']
            y_data = df['M:L']
            # Plot the data
            plt.scatter(x_data, y_data, s=1.2)
            plt.axhline(y=0.66, color='black', linestyle='--')
            plt.axvline(x=0.66, color='black', linestyle='--')
            plt.xlabel('S:M')
            plt.ylabel('M:L')
            plt.xlim(0.0, 1.0)
            plt.ylim(0.0, 1.0)
            plt.show()
            # self.canvas.draw()

            # Refresh canvas
            #self.canvas.draw()

        print("printing selected:   ")
        print(selected)

        for interaction in interactions:
            if selected.startswith("Morphology Map vs " + interaction) \
                    or selected.startswith("CDA Aspect Ratio " + interaction)\
                    or selected.startswith("Extended CDA " + interaction)\
                    or selected.startswith("Surface Area vs Volume vs Energy" + interaction):
                self.figure.clear()
                print(interaction)
                print("Entering Morphology Map vs " + interaction)
                self.axes = self.figure.add_subplot(111)
                c_df = df[interaction]
                colour = list(set(c_df))
                if selected.startswith("Morphology Map vs "):
                    x_data = df['S:M']
                    y_data = df['M:L']
                    self.axes.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.axes.axhline(y=0.66, color='black', linestyle='--')
                    self.axes.axvline(x=0.66, color='black', linestyle='--')
                    self.axes.set_xlabel('S: M')
                    self.axes.set_ylabel('M: L')
                    self.axes.set_xlim(0.0, 1.0)
                    self.axes.set_ylim(0.0, 1.0)
                    #self.axes.show()
                if selected.startswith("CDA Aspect Ratio "):
                    x_data = df['S/M']
                    y_data = df['M/L']
                    self.axes.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.axes.axhline(y=0.66, color='black', linestyle='--')
                    self.axes.axvline(x=0.66, color='black', linestyle='--')
                    self.axes.set_xlabel('S/ M')
                    self.axes.set_ylabel('M/ L')
                    self.axes.set_xlim(0.0, 1.0)
                    self.axes.set_ylim(0.0, 1.0)
                if selected.startswith("Extended CDA "):
                    print("extended CDA")
                    x_data = df[extended[0]]
                    y_data = df[extended[1]]
                    print(x_data)
                    self.axes.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    '''self.axes.axhline(y=0.66, color='black', linestyle='--')
                    self.axes.axvline(x=0.66, color='black', linestyle='--')'''
                    self.axes.set_xlabel(extended[0])
                    self.axes.set_ylabel(extended[1])
                if selected.startswith("Surface Area vs Volume vs Energy" + interaction):
                    print('Entered Surface Area vs Volume Plotting:  ')
                    x_data = df["Volume (Vol)"]
                    y_data = df["Surface_Area (SA)"]
                    self.axes.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.axes.set_xlabel(r"Volume ($nm^3$)")
                    self.axes.set_ylabel(r"Surface Area ($nm^2$)")
                    # Plot the data
                plt.show()
                #self.canvas.draw()

        if selected.startswith("Morphology Map filtered by "):
            print("Morphology Map filtered by:   ")
            equation_integer = ''
            print(equations_list)
            for item in equations_list:
                if selected.endswith(item):
                    equation_integer = equations_list.index(item)
                    print(equation_integer)
            self.axes = self.figure.add_subplot(111)
            equation_df = df[df["CDA_Equation"] == equation_integer+1]
            x_data = equation_df["S:M"]
            y_data = equation_df["M:L"]
            self.axes.scatter(x_data, y_data, s=1.2)
            self.axes.axhline(y=0.66, color='black', linestyle='--')
            self.axes.axvline(x=0.66, color='black', linestyle='--')
            self.axes.set_xlabel('S: M')
            self.axes.set_ylabel('M: L')
            self.axes.set_xlim(0.0, 1.0)
            self.axes.set_ylim(0.0, 1.0)
            plt.show()
            #self.canvas.draw()

    def threeD_ploting_called(self, csv, selected, equation_list):
        print("entering 3D plotting called")
        # Reading the dataframe
        df = pd.read_csv(csv)
        print(df)
        # Reading self.current_plots() coming from self.SelectPlots.currentText()
        selected = selected
        # Finding interactions in data frame if there are any
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction") or col.startswith("tile")
        ]
        print(interactions)
        print(selected)
        # Finding extended CDA in data frame if there are any
        extended = [col for col in df.columns
                    if col.startswith("AspectRatio")]
        print(extended)
        pass

    def PlotPopUp(self):
        print("Entered Plot Pop Up")

    def replot_AR(self, csv, info, selected):
        print('Entered Plotting')
        print(csv, info, selected)
        folderpath = Path(csv)
        df = pd.read_csv(csv)
        #savefolder = self.create_plots_folder(folderpath)
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction") or col.startswith("tile")
        ]

        x_data = df["S:M"]
        y_data = df["M:L"]
        print(x_data)

        # Clear figure
        self.figure.clear()

        # Plot the data
        plt.scatter(x_data, y_data, s=1.2)
        plt.axhline(y=0.66, color='black', linestyle='--')
        plt.axvline(x=0.66, color='black', linestyle='--')
        plt.xlabel('S:M')
        plt.ylabel('M:L')
        plt.xlim(0.0, 1.0)
        plt.ylim(0.0, 1.0)

        # Refresh canvas
        self.canvas.draw()

        for interaction in interactions:
            c_df = df[interaction]
            colour = list(set(c_df))
            textstr = interaction
            props = dict(boxstyle="square", facecolor="white")

            plt.figure()
            print("FIG")
            plt.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
            plt.axhline(y=0.66, color="black", linestyle="--")
            plt.axvline(x=0.66, color="black", linestyle="--")
            plt.title(textstr)
            plt.xlabel("S: M")
            plt.ylabel("M: L")
            plt.xlim(0.0, 1.0)
            plt.ylim(0.0, 1.0)
            cbar = plt.colorbar(ticks=colour)
            cbar.set_label(r"$\Delta G_{Cryst}$ (kcal/mol)")

    def replot_GrowthRate(self, csv, info, selected, savepath):
        plt.close()
        print(csv, info, selected)
        gr_df = pd.read_csv(csv)
        x_data = gr_df["Supersaturation"]
        print(selected)
        for i in selected:
            print(selected)
            plt.scatter(x_data, gr_df[i], s=1.2)
            plt.plot(x_data, gr_df[i], label=i)
            plt.legend()
            plt.xlabel("Supersaturation (kcal/mol)")
            plt.ylabel("Growth Rate")
            plt.tight_layout()
            #pylustrator.start()
            plt.show()

class PlotWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Plot Window")
        self.setGeometry(100, 100, 800, 600)
        self.create_widgets()
        self.create_layout()

    def plotting_info(self, csv, selected, equation_list):
        self.csv = csv
        self.selected = selected
        self.equation_list = equation_list
        if selected == 'Growth Rates':
            self.plot_type = 'Scatter+Line'

    def create_widgets(self):

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.button_plot = QPushButton("Plot")
        self.button_save = QPushButton("Save")
        self.button_edit = QPushButton("Edit")
        self.label_pointsize = QLabel("Point Size:")
        self.spin_point_size = QSpinBox()
        self.checkbox_colorbar = QCheckBox("Colorbar")
        self.button_add_trendline = QPushButton("Add Trendline")
        # Set the properties of the widgets
        self.spin_point_size.setRange(1, 100)

        # Initialize the variables
        self.point_size = self.spin_point_size.value()
        self.colorbar = False
        self.scatter = None

        self.checkbox_colorbar = QCheckBox("Show Colorbar")

        # Connect the signals and slots
        # Initialize checkboxes
        self.checkbox_grid = QCheckBox("Show Grid")
        self.checkbox_trendline = QCheckBox("Add Trendline")
        self.button_plot.clicked.connect(self.plot)
        self.button_save.clicked.connect(self.save)
        self.button_edit.clicked.connect(self.edit)
        self.checkbox_colorbar.stateChanged.connect(self.toggle_colorbar)    # Connect the add trendline button to its handler
        self.button_add_trendline.clicked.connect(self.add_trendline)
        self.spin_point_size.valueChanged.connect(self.set_point_size)
        self.canvas.mpl_connect("motion_notify_event", lambda event: self.on_hover(event))

        # Create the plot type combo box
        self.plot_type_combo_box = QComboBox()
        self.plot_type_combo_box.addItems(['Scatter', 'Line', 'Scatter+Line'])
        self.plot_type_combo_box.currentIndexChanged.connect(self.change_plot_type)
        self.btn_change_plot = QPushButton("Change Plot Type")
        self.btn_change_plot.clicked.connect(self.change_plot_type)

        # Initialize the plot type
        self.plot_type = "scatter"

    def create_layout(self):
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.toolbar)

        hbox1 = QHBoxLayout()
        hbox1.addWidget(self.label_pointsize)
        hbox1.addWidget(self.spin_point_size)
        hbox1.addWidget(self.checkbox_grid)
        hbox1.addWidget(self.checkbox_trendline)
        hbox1.addWidget(self.plot_type_combo_box)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.button_plot)
        hbox2.addWidget(self.button_save)
        hbox2.addWidget(self.button_edit)
        hbox2.addWidget(self.button_add_trendline)

        layout.addLayout(hbox1)
        layout.addLayout(hbox2)

        # Set window properties
        self.setWindowTitle("Plot Window")
        self.setGeometry(100, 100, 800, 600)
        self.setLayout(layout)

    def set_point_size(self, value):
        self.point_size = self.spin_point_size.value()
        if self.scatter is not None:
            self.scatter.set_sizes([self.point_size] * len(self.scatter.get_offsets()))
        self.canvas.draw()

    def toggle_colorbar(self, state):
        self.colorbar = state == Qt.Checked

    def change_plot_type(self):
        plot_type = self.plot_type

        if plot_type == 'Scatter':
            self.plot_type = 'scatter'
            self.plot()
        if plot_type == 'Scatter+Line':
            self.plot_type = 'scatter_line'
            self.plot()
        if plot_type == 'Line':
            self.plot_type = 'line'
            self.plot()


    def plot(self):
        self.figure.clear()
        self.ax = self.figure.add_subplot(111)
        self.ax.clear()  # clear the plot
        self.canvas.draw()  # redraw the canvas
        plot_type = self.plot_type
        print("entering plotting called")
        # Reading the dataframe
        df = pd.read_csv(self.csv)
        print(df)
        # Reading self.current_plots() coming from self.SelectPlots.currentText()
        selected = self.selected
        print(selected)
        # Finding interactions in data frame if there are any
        interactions = [
            col
            for col in df.columns
            if col.startswith("interaction") or col.startswith("tile")
        ]
        print(interactions)
        print(selected)
        # Finding extended CDA in data frame if there are any
        extended = [col for col in df.columns
                    if col.startswith("AspectRatio")]
        print(extended)
        if selected == 'Surface Area vs Volume':
            print("Entering PCA Morphology Map")
            x_data = df['Volume (Vol)']
            y_data = df['Surface_Area (SA)']
            # Plot the data
            self.ax.scatter(x_data, y_data, s=1.2)
            self.ax.set_xlabel(r"Volume ($nm^3$)")
            self.ax.set_ylabel(r"Surface Area ($nm^2$)")
            self.scatter = self.ax.scatter(x_data, y_data, s=1.2)

        if selected == "Morphology Map":
            #self.figure.clear()
            print("Entering PCA Morphology Map")
            x_data = df['S:M']
            y_data = df['M:L']
            # Plot the data
            self.ax.scatter(x_data, y_data, s=1.2)
            self.ax.axhline(y=0.66, color='black', linestyle='--')
            self.ax.axvline(x=0.66, color='black', linestyle='--')
            self.ax.set_xlabel('S:M')
            self.ax.set_ylabel('M:L')
            self.scatter = self.ax.scatter(x_data, y_data, s=1.2)
            # self.canvas.draw()

            # Refresh canvas
            #self.canvas.draw()

        if selected.startswith("CDA Aspect Ratio"):
            print("CDA Aspect Ratio:  ")
            x_data = df["S/M"]
            y_data = df["M/L"]
            self.ax.scatter(x_data, y_data, s=1.2)
            self.ax.axhline(y=0.66, color='black', linestyle='--')
            self.ax.axvline(x=0.66, color='black', linestyle='--')
            self.ax.set_xlabel('S/ M')
            self.ax.set_ylabel('M/ L')
            self.ax.set_xlim(0.0, 1.0)
            self.ax.set_ylim(0.0, 1.0)

        print("printing selected:   ")
        print(selected)

        for interaction in interactions:
            if selected.startswith("Morphology Map vs " + interaction) \
                    or selected.startswith("CDA Aspect Ratio " + interaction)\
                    or selected.startswith("Extended CDA " + interaction)\
                    or selected.startswith("Surface Area vs Volume vs Energy" + interaction):
                self.figure.clear()
                print(interaction)
                print("Entering Morphology Map vs " + interaction)
                self.ax = self.figure.add_subplot(111)
                c_df = df[interaction]
                self.c_df = c_df
                colour = list(set(c_df))
                if selected.startswith("Morphology Map vs "):
                    x_data = df['S:M']
                    y_data = df['M:L']
                    self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.ax.axhline(y=0.66, color='black', linestyle='--')
                    self.ax.axvline(x=0.66, color='black', linestyle='--')
                    self.ax.set_xlabel('S: M')
                    self.ax.set_ylabel('M: L')
                    self.ax.set_xlim(0.0, 1.0)
                    self.ax.set_ylim(0.0, 1.0)
                    self.scatter = self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    #self.axes.show()
                if selected.startswith("CDA Aspect Ratio "):
                    x_data = df['S/M']
                    y_data = df['M/L']
                    self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.ax.axhline(y=0.66, color='black', linestyle='--')
                    self.ax.axvline(x=0.66, color='black', linestyle='--')
                    self.ax.set_xlabel('S/ M')
                    self.ax.set_ylabel('M/ L')
                    self.ax.set_xlim(0.0, 1.0)
                    self.ax.set_ylim(0.0, 1.0)
                    self.scatter = self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                if selected.startswith("Extended CDA "):
                    print("extended CDA")
                    x_data = df[extended[0]]
                    y_data = df[extended[1]]
                    print(x_data)
                    self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    '''self.axes.axhline(y=0.66, color='black', linestyle='--')
                    self.axes.axvline(x=0.66, color='black', linestyle='--')'''
                    self.ax.set_xlabel(extended[0])
                    self.ax.set_ylabel(extended[1])
                    self.scatter = self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                if selected.startswith("Surface Area vs Volume vs Energy" + interaction):
                    print('Entered Surface Area vs Volume Plotting:  ')
                    x_data = df["Volume (Vol)"]
                    y_data = df["Surface_Area (SA)"]
                    self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    self.ax.set_xlabel(r"Volume ($nm^3$)")
                    self.ax.set_ylabel(r"Surface Area ($nm^2$)")
                    self.scatter = self.ax.scatter(x_data, y_data, c=c_df, cmap="plasma", s=1.2)
                    # Plot the data
                if not c_df.empty:
                    self.figure.colorbar(self.scatter)
                    self.figure.set_label(r"$\Delta G_{Cryst}$ (kcal/mol)")


        if selected.startswith("Morphology Map filtered by "):
            print("Morphology Map filtered by:   ")
            equation_integer = ''
            print(equations_list)
            for item in equations_list:
                if selected.endswith(item):
                    equation_integer = equations_list.index(item)
                    print(equation_integer)
            self.ax = self.figure.add_subplot(111)
            equation_df = df[df["CDA_Equation"] == equation_integer+1]
            x_data = equation_df["S:M"]
            y_data = equation_df["M:L"]
            self.ax.scatter(x_data, y_data, s=1.2)
            self.ax.axhline(y=0.66, color='black', linestyle='--')
            self.ax.axvline(x=0.66, color='black', linestyle='--')
            self.ax.set_xlabel('S: M')
            self.ax.set_ylabel('M: L')
            self.ax.set_xlim(0.0, 1.0)
            self.ax.set_ylim(0.0, 1.0)

        if self.colorbar:
            cbar = self.figure.colorbar(self.scatter)
            cbar.set_label(r"$\Delta G_{Cryst}$ (kcal/mol)")

        if self.checkbox_grid.isChecked():
            self.ax.grid()
        self.annot = self.ax.annotate("", xy=(0, 0), xytext=(20, 20),
                                      textcoords="offset points",
                                      bbox=dict(boxstyle="round", fc="w"),
                                      arrowprops=dict(arrowstyle="->"))
        self.annot.set_visible(False)

        self.canvas.draw()

    def update_annot(self, ind):

        pos = self.scatter.get_offsets()[ind["ind"][0]]
        self.annot.xy = pos
        text = "Simulation Number: " + "{}".format(" ".join(list(map(str, ind["ind"]))))
        self.annot.set_text(text)
        #self.annot.get_bbox_patch().set_facecolor(self.c_df(norm(c[ind["ind"][0]])))
        self.annot.get_bbox_patch().set_alpha(0.4)
        print("Text for Annotation:")
        print(text)

    def on_hover(self, event):
        vis = self.annot.get_visible()
        try:
            if event.inaxes == self.ax:
                cont, ind = self.scatter.contains(event)
                if cont:
                    self.update_annot(ind)
                    self.annot.set_visible(True)
                    self.figure.canvas.draw_idle()
                else:
                    if vis:
                        self.annot.set_visible(False)
                        self.figure.canvas.draw_idle()
            else:
                if vis:
                    self.annot.set_visible(False)
                self.figure.canvas.draw_idle()
        except NameError:
            pass

    def add_trendline(self):
        if self.scatter is None:
            self.statusBar().showMessage("Error: No scatter plot to add trendline to.")
            return
        x = self.scatter.get_offsets()[:, 0]
        y = self.scatter.get_offsets()[:, 1]

        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
        self.ax.plot(x, p(x), "r--")

        self.canvas.draw()

    def save(self):
        file_dialog = QFileDialog()
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        file_dialog.setDefaultSuffix("png")
        file_dialog.setNameFilters(["PNG(*.png);;JPEG(*.jpg *.jpeg);;All Files(*.*)"])
        file_dialog.setOption(QFileDialog.DontUseNativeDialog)
        file_dialog.setDirectory(".")
        file_dialog.setWindowTitle("Save Plot")

        if file_dialog.exec_() == QDialog.Accepted:
            file_name = file_dialog.selectedFiles()[0]
            transparent = QMessageBox.question(self, "Transparent Background", "Do you want a transparent background?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No) == QMessageBox.Yes

            if file_name:
                size = [6.8, 4.8]
                if transparent:
                    self.figure.savefig(file_name, figsize=size, transparent=True, dpi=600)
                else:
                    self.figure.savefig(file_name, figsize=size, dpi=600)

    def edit(self):
        pass
