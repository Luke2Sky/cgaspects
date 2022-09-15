import numpy as np
import pandas as pd
import os
from natsort import natsorted
import re
from pathlib import Path
from DataProcessor.tools.shape_analysis import CrystalShape as cs
from DataProcessor.data.calc_data import Calculate as calc

from PyQt5 import QtWidgets, QtGui, QtCore, QtOpenGL 

from PyQt5.QtWidgets import QApplication, QComboBox, QMainWindow, QMessageBox, QShortcut, QFileDialog
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QKeySequence


# Project module imports
from load_GUI import Ui_MainWindow
from DataProcessor.data.find_data import Find


class GUICommands(QMainWindow, Ui_MainWindow):

    def __init__(self, *args, **kwargs):
        super(GUICommands, self).__init__(*args, **kwargs)
        self.setupUi(self)
        


        self.find = Find()
       
        self.mode = 1

