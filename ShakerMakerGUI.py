import sys
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QTextEdit,
    QLabel,
    QSplitter,
    QGroupBox,
    QFileDialog,QGridLayout,QPushButton,QMenu,QTabWidget,QToolBar,QTabBar,QDialog,QAction,
    QTableWidget,QTableWidgetItem,QHeaderView,QComboBox,QColorDialog,QSizePolicy,QLayout
)


from PyQt5.QtCore import Qt,QDir,QUrl
from PyQt5.QtGui import QDoubleValidator, QIntValidator # Correct import
from PyQt5.QtGui import QIcon,QBrush,QColor,QFont
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineSettings

import pyvista as pv
import pyvistaqt as pvqt
import requests
import json
import os
import numpy as np

from pyproj import Transformer
import geopandas as gpd
import pandas as pd
import plotly.express as px
from shapely.geometry import Point
from geopy.distance import geodesic
import shutil



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_global_variables()
        self.setup_toolbar_and_menu()
        self.setup_window_layout()

        self.show()

    def setup_global_variables(self):
        """Set up global variables for the main window."""
        self.tmp_lat = ""
        self.tmp_long = ""
        self.MeshObjects = {}

    def setup_toolbar_and_menu(self):
        """Create the toolbar and menu for the main window."""
        toolbar = self.addToolBar("Main Toolbar")

        # File menu with import/export actions
        file_menu = QtWidgets.QMenu("File", self)
        import_action = file_menu.addAction("Import")
        export_action = file_menu.addAction("Export")
        
        # Connect import action to open file dialog
        import_action.triggered.connect(lambda: QFileDialog.getOpenFileName(self, "Open File"))
        
        # Add file menu action to toolbar
        file_menu_action = toolbar.addAction("File")
        file_menu_action.triggered.connect(lambda: file_menu.exec_(toolbar.mapToGlobal(QtCore.QPoint(0, toolbar.height()))))

        # Exit action
        exit_action = toolbar.addAction("Exit")
        exit_action.triggered.connect(self.close)

    def setup_window_layout(self):
        """Set up the main window layout and split views."""
        self.setWindowTitle("ShakerMaker")
        self.setWindowIcon(QIcon("Icons/ShakerMaker.png"))
        
        # Main window splitter
        splitter = QSplitter(self)
        self.setCentralWidget(splitter)

        # Left and right layouts
        left_widget = QWidget()
        right_widget = QWidget()

        self.left_layout = QVBoxLayout(left_widget)
        self.right_layout = QVBoxLayout(right_widget)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)

        splitter.setStretchFactor(0, 0)  # Left widget minimal size
        splitter.setStretchFactor(1, 1)  # Right widget stretches

        # Set up right layout (top/bottom split)
        self.setup_right_layout(right_widget)

        # Set up left layout (tabs)
        self.setup_left_layout()

    def setup_right_layout(self, right_widget):
        """Set up the right layout (PyVista plotter and terminal)."""
        right_splitter = QSplitter(Qt.Vertical, right_widget)
        self.right_layout.addWidget(right_splitter)

        # Top and bottom widgets
        top_widget = QWidget()
        bottom_widget = QWidget()

        self.top_layout = QVBoxLayout(top_widget)
        self.bottom_layout = QVBoxLayout(bottom_widget)

        right_splitter.addWidget(top_widget)
        right_splitter.addWidget(bottom_widget)

        # Layout options
        right_splitter.setStretchFactor(0, 2)
        right_splitter.setStretchFactor(1, 0)

        top_widget.setMinimumHeight(100)
        bottom_widget.setMinimumHeight(10)

        # Add PyVista plotter and terminal
        self.add_pyvista_plot()
        self.add_terminal()

    def setup_left_layout(self):
        """Set up the left layout (tabs for Fault, Crust, Stations, Analysis)."""
        self.left_layout.setAlignment(Qt.AlignTop)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.left_layout.addWidget(self.tab_widget)

        # Add tabs
        self.tab_widget.addTab(self.add_Source_information(), QIcon("Icons/Fault.png"), "Fault")
        self.tab_widget.addTab(self.add_Crust_information(), QIcon("Icons/Crust.png"), "Crust")
        self.tab_widget.addTab(self.add_Stations_information(), QIcon("Icons/Stations.png"), "Stations")
        self.tab_widget.addTab(self.add_Analysis_information(), QIcon("Icons/Analysis.png"), "Analysis")

        self.tab_widget.setIconSize(QtCore.QSize(64, 64))
        self.tab_widget.setStyleSheet(self.tab_style)

  

    def add_Stations_information(self):
        """
        Create and return a group box for the "Stations Information" tab.
        This includes a dropdown menu for selecting between "Single Station" and "DRM Stations",
        and a stacked widget that shows the corresponding content.
        """

        # Create the stations group box and set alignment
        stations_group = QGroupBox("Stations Information")
        stations_group.setAlignment(Qt.AlignTop)

        # Create a layout for the group box
        form_layout = QGridLayout(stations_group)

        # Create the stations dropdown (for selecting between different station types)
        self.stations_dropdown = QComboBox()
        self.stations_dropdown.addItems(["Single Stations", "DRM Stations"])
        self.stations_dropdown.setStyleSheet(self.drop_down_style)  # Set the dropdown style

        # Create a stacked widget for displaying station information
        self.stations_widget = QtWidgets.QStackedWidget()
        self.stations_widget.addWidget(self.add_single_station())  # Add "Single Station" widget
        self.stations_widget.addWidget(self.add_drm_stations())    # Add "DRM Stations" widget

        # Connect dropdown selection change to update the displayed widget in the stacked widget
        self.stations_dropdown.currentTextChanged.connect(
            lambda: self.stations_widget.setCurrentIndex(self.stations_dropdown.currentIndex())
        )

        # Add dropdown menu and stacked widget to the form layout
        form_layout.addWidget(self.stations_dropdown, 0, 0)
        form_layout.addWidget(self.stations_widget, 1, 0)

        # Set the default active tab to the first option ("Single Station")
        self.stations_widget.setCurrentIndex(0)

        # Set group box style
        stations_group.setStyleSheet(self.group_style)

        return stations_group

    




    def add_Visualization_information(self):
        """
        This method creates a group box for the visualization tab.
        """

        # Create a group box for the visualization information
        self.visualization_group = QGroupBox("Visualization Information")
        self.visualization_group.setAlignment(Qt.AlignTop)  # Align title at the top

        # Create a layout for the group box
        form_layout = QGridLayout(self.visualization_group)

        # Fault mesh checkbox
        self.fault_mesh_checkbox = QtWidgets.QCheckBox("Fault Mesh")
        self.fault_mesh_checkbox.setChecked(True)
        form_layout.addWidget(self.fault_mesh_checkbox, 0, 0)

        # Crust mesh checkbox
        self.crust_mesh_checkbox = QtWidgets.QCheckBox("Crust Mesh")
        self.crust_mesh_checkbox.setChecked(True)
        form_layout.addWidget(self.crust_mesh_checkbox, 0, 1)

        # Active Scalars ComboBox
        active_scalars = QComboBox()
        active_scalars.addItems(["Strike", "Dip", "Rake", "T0", "Slip", "None"])
        form_layout.addWidget(QLabel("Active Scalars"), 0, 2)
        form_layout.addWidget(active_scalars, 0, 3)

        # Plot button
        plot_button = QPushButton("Plot")
        plot_button.setStyleSheet(self.button_style)
        plot_button.clicked.connect(
            lambda: self.plot(active_scalars.currentText(), 
                            self.fault_mesh_checkbox.isChecked(), 
                            self.crust_mesh_checkbox.isChecked()))
        form_layout.addWidget(plot_button, 0, 6, 1, 2)

        # Plot Map button
        plot_map_button = QPushButton("Plot Map")
        plot_map_button.setStyleSheet(self.button_style)
        plot_map_button.clicked.connect(self.plot_map)
        form_layout.addWidget(plot_map_button, 0, 8, 1, 2)

        # Set layout and styles for the group box
        self.visualization_group.setStyleSheet(self.group_style)

        return self.visualization_group


    def add_single_station(self):
        """
        Creates and returns a group box for single station widget.
        """

        # Create a group box for single station information
        single_station_group = QGroupBox("Single Station Information")
        
        # Create a layout for the group box
        form_layout = QGridLayout(single_station_group)

        # Create a table widget
        self.single_stations_table = QTableWidget()
        self.single_stations_table.setRowCount(1)
        self.single_stations_table.setColumnCount(3)
        self.single_stations_table.setHorizontalHeaderLabels(["Latitude", "Longitude", "Depth (km)"])
        self.single_stations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.single_stations_table.horizontalHeader().setStyleSheet(self.table_style)
        self.single_stations_table.setStyleSheet(self.table_style)

        # Add the table widget to the form layout
        form_layout.addWidget(self.single_stations_table, 0, 0, 1, 2)

        # Add Station button
        add_button = QPushButton("Add Station")
        add_button.setStyleSheet(self.button_style)
        add_button.clicked.connect(lambda: self.single_stations_table.insertRow(0))
        form_layout.addWidget(add_button, 1, 0)

        # Remove Station button
        remove_button = QPushButton("Remove Station")
        remove_button.setStyleSheet(self.button_style)
        remove_button.clicked.connect(lambda: self.single_stations_table.removeRow(0) if self.single_stations_table.rowCount() > 1 else None)
        form_layout.addWidget(remove_button, 1, 1)

        # Load File button
        load_button = QPushButton("Load File")
        load_button.setStyleSheet(self.button_style)
        load_button.clicked.connect(self.load_Stations)
        form_layout.addWidget(load_button, 2, 0)

        # Google Maps button
        google_button = QPushButton("Map")
        google_button.setStyleSheet(self.button_style)
        google_button.clicked.connect(self.open_google_maps)
        form_layout.addWidget(google_button, 2, 1)

        # Enable custom context menu for the table
        self.single_stations_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.single_stations_table.customContextMenuRequested.connect(self.show_table_context_menu)

        return single_station_group



    def add_drm_stations(self):
        """
        Creates and returns a group box for DRM stations information.
        """
        # Create a group box for the DRM stations information
        self.drm_stations_group = QGroupBox("DRM Stations Information")
        
        # adjust alignment to the top
        self.drm_stations_group.setAlignment(Qt.AlignTop)

        # Create a layout for the group box
        form_layout = QGridLayout(self.drm_stations_group)

        # Add layout and widget initialization here for the DRM stations
        # latitude
        self.drm_lat = QLineEdit()
        self.drm_lat.setPlaceholderText("Latitude")
        self.drm_lat.setValidator(QDoubleValidator())
        form_layout.addWidget(QLabel("Latitude"), 0, 0)
        form_layout.addWidget(self.drm_lat, 0, 1)
        form_layout.addWidget(QLabel("Latitude of the center of the DRM station"), 0, 2)

        # longitude
        self.drm_long = QLineEdit()
        self.drm_long.setPlaceholderText("Longitude")
        self.drm_long.setValidator(QDoubleValidator())
        form_layout.addWidget(QLabel("Longitude"), 1, 0)
        form_layout.addWidget(self.drm_long, 1, 1)
        form_layout.addWidget(QLabel("Longitude of the center of the DRM station"), 1, 2)

        # width x
        self.drm_width_x = QLineEdit()
        self.drm_width_x.setPlaceholderText("Width X (m)")
        self.drm_width_x.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Width X (m)"), 2, 0)
        form_layout.addWidget(self.drm_width_x, 2, 1)
        form_layout.addWidget(QLabel("Width of the DRM station in the X direction (North-South)"), 2, 2)

        # Mesh size x
        self.drm_mesh_size_x = QLineEdit()
        self.drm_mesh_size_x.setPlaceholderText("Mesh Size X (m)")
        self.drm_mesh_size_x.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Mesh Size X (m)"), 5, 0)
        form_layout.addWidget(self.drm_mesh_size_x, 5, 1)
        form_layout.addWidget(QLabel("Mesh size in the X direction (North-South)"), 5, 2)

        # width y
        self.drm_width_y = QLineEdit()
        self.drm_width_y.setPlaceholderText("Width Y (m)")
        self.drm_width_y.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Width Y (m)"), 3, 0)
        form_layout.addWidget(self.drm_width_y, 3, 1)
        form_layout.addWidget(QLabel("Width of the DRM station in the Y direction (East-West)"), 3, 2)

        # Mesh size y
        self.drm_mesh_size_y = QLineEdit()
        self.drm_mesh_size_y.setPlaceholderText("Mesh Size Y (m)")
        self.drm_mesh_size_y.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Mesh Size Y (m)"), 6, 0)
        form_layout.addWidget(self.drm_mesh_size_y, 6, 1)
        form_layout.addWidget(QLabel("Mesh size in the Y direction (East-West)"), 6, 2)

        # depth
        self.drm_depth = QLineEdit()
        self.drm_depth.setPlaceholderText("Depth (m)")
        self.drm_depth.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Depth (m)"), 4, 0)
        form_layout.addWidget(self.drm_depth, 4, 1)
        form_layout.addWidget(QLabel("Depth of the DRM station"), 4, 2)

        # Mesh size z
        self.drm_mesh_size_z = QLineEdit()
        self.drm_mesh_size_z.setPlaceholderText("Mesh Size Z (m)")
        self.drm_mesh_size_z.setValidator(QIntValidator())
        form_layout.addWidget(QLabel("Mesh Size Z (m)"), 7, 0)
        form_layout.addWidget(self.drm_mesh_size_z, 7, 1)
        form_layout.addWidget(QLabel("Mesh size in the Z direction (Up-Down)"), 7, 2)


        self.drm_stations_group.setStyleSheet(self.group_style)
        min_size = self.drm_stations_group.sizeHint() 
        self.drm_stations_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.drm_stations_group.setFixedHeight(min_size.height()) 
        
        # set tht style
        # form_layout.setS     

        # Adjust the size to shrink it
        self.drm_stations_group.adjustSize()

        
        return self.drm_stations_group




    def load_Stations(self):
        """
        Loads station information from a JSON file and populates the appropriate table.
        """

        # Call the file dialog to choose a file
        file = self.choose_file("Stations File")
        
        # Check if a file is selected
        if file == "":
            self.terminal_output.append("<font color='red'>Error: Stations file is not set</font>")
            return
        
        if file is None:
            return

        # Check if the file exists
        if not os.path.exists(file):
            self.terminal_output.append("<font color='red'>Error: Stations file does not exist</font>")
            return

        # Check if the file format is supported (only JSON is supported for now)
        file_format = file.split(".")[-1]
        if file_format != "json":
            self.terminal_output.append("<font color='red'>Error: Stations file format not supported</font>")
            return

        # Read the JSON file
        with open(file, "r") as f:
            data = json.load(f)

        # Validate the content of the JSON file
        if "station_type" not in data:
            self.terminal_output.append("<font color='red'>Error: Stations file does not have the station_type key</font>")
            self.terminal_output.append(f"  format: {json.dumps({'station_type': 'your station type (Single, DRM, ...)'}, indent=4)}")
            return

        # Check if the file contains the necessary information based on station type
        station_type = data["station_type"].lower()
        
        if station_type == "single":
            if "station_info" not in data:
                self.terminal_output.append("<font color='red'>Error: Stations file does not have the station_info key</font>")
                self.terminal_output.append(f"  format: {json.dumps({'station_type': 'Single', 'station_info': [{'Latitude': '', 'Longitude': '', 'Depth': ''}]}, indent=4)}")
                return
        elif station_type == "drm":
            if "station_info" not in data:
                self.terminal_output.append("<font color='red'>Error: Stations file does not have the station_info key</font>")
                self.terminal_output.append(f"  format: {json.dumps({'station_type': 'DRM', 'station_info': [{'Latitude': '', 'Longitude': '', 'Width X': '', 'Width Y': '', 'Depth': '', 'Mesh Size X': '', 'Mesh Size Y': '', 'Mesh Size Z': ''}]}, indent=4)}")
                return
        else:
            self.terminal_output.append("<font color='red'>Error: Station type not supported</font>")
            return

        # Process the data and populate the table for 'Single' station type
        if station_type == "single":
            # Clear existing rows except the last one
            for i in range(self.single_stations_table.rowCount() - 1):
                self.single_stations_table.removeRow(0)
            
            # Populate the table with station data
            for i, station in enumerate(data["station_info"][::-1]):
                if "Latitude" not in station or "Longitude" not in station or "Depth" not in station:
                    self.terminal_output.append("<font color='red'>Error: Stations file does not have all the keys in the station</font>")
                    self.terminal_output.append(f"  format: {json.dumps({'Latitude': '', 'Longitude': '', 'Depth': ''}, indent=4)}")
                    return
                
                # Insert a new row if needed
                if i != 0:
                    self.single_stations_table.insertRow(0)
                
                # Set the station data in the table
                self.single_stations_table.setItem(0, 0, QTableWidgetItem(str(station["Latitude"])))
                self.single_stations_table.setItem(0, 1, QTableWidgetItem(str(station["Longitude"])))
                self.single_stations_table.setItem(0, 2, QTableWidgetItem(str(station["Depth"])))

        
    def show_table_context_menu(self, position):
        """
        Show context menu on right-click at the table and allow pasting of latitude and longitude.
        """
        # Get the row at the position of the mouse
        row_at_click = self.single_stations_table.rowAt(position.y())

        # If no row is found under the click, return
        if row_at_click == -1:
            return

        # Create the context menu
        menu = QMenu()

        # Create and add the action for pasting latitude and longitude
        paste_action = QAction("Paste Latitude and Longitude", self)
        paste_action.triggered.connect(lambda: self.paste_lat_long_to_row(row_at_click))
        menu.addAction(paste_action)

        # Show the context menu at the clicked position
        menu.exec_(self.single_stations_table.viewport().mapToGlobal(position))


    def paste_lat_long_to_row(self, row):
        """
        Paste latitude and longitude into the specified row.
        """
        # Check if latitude and longitude are set
        if self.tmp_lat == "" or self.tmp_long == "":
            self.terminal_output.append("Latitude and Longitude not found in the clipboard")
            return

        # Set latitude and longitude in the table's row
        self.single_stations_table.setItem(row, 0, QTableWidgetItem(self.tmp_lat))  # Latitude
        self.single_stations_table.setItem(row, 1, QTableWidgetItem(self.tmp_long))  # Longitude


    def open_google_maps(self):
        """
        Open a new window with Google Maps and allow copying latitude and longitude.
        """
        # Create a new QDialog for the Google Maps window
        map_dialog = QDialog(self)
        map_dialog.setWindowTitle("Google Maps")
        map_dialog.resize(1000, 800)

        # Create a layout for the dialog
        layout = QVBoxLayout(map_dialog)

        # Create a QWebEngineView and load Google Maps
        self.map_view = QWebEngineView()
        map_url = QUrl("https://www.google.com/maps")
        self.map_view.setUrl(map_url)
        layout.addWidget(self.map_view)

        # Create a button to copy latitude and longitude to the clipboard
        copy_button = QPushButton("Copy Latitude and Longitude to Clipboard")
        copy_button.clicked.connect(self.copy_lat_long_to_clipboard)
        layout.addWidget(copy_button)

        # Set the layout and show the dialog
        map_dialog.setLayout(layout)
        map_dialog.show()


    def copy_lat_long_to_clipboard(self):
        """
        Extract latitude and longitude from the Google Maps URL and copy them to the clipboard.
        """
        # Get the current URL of the map
        url = self.map_view.url().toString()

        # Find the position of the first 'data='
        at_index = url.find('data=')

        if at_index != -1:
            # Extract latitude and longitude data
            lat_lng_part = url[at_index + 1:]
            lat_lng_split = lat_lng_part.split('!3d')[-1].split('!4d')

            if len(lat_lng_split) >= 2:
                # Set latitude and longitude
                lat = lat_lng_split[0]
                lng = lat_lng_split[1].split('!')[0].split('?')[0]
                self.tmp_lat = lat
                self.tmp_long = lng
                lat_lng_str = f"Latitude: {lat}, Longitude: {lng}"
                self.terminal_output.append(lat_lng_str)

                # Copy to clipboard
                clipboard = QApplication.clipboard()
                clipboard.setText(lat_lng_str)
                self.terminal_output.append("Latitude and Longitude copied to clipboard")
            else:
                self.terminal_output.append("Latitude and Longitude not found in the URL")
        else:
            self.terminal_output.append("Please open Google Maps and click on a location")

         

    
    def add_Crust_information(self):
        """
        Creates a group box for the crust information and sets up the table, buttons, and interactions.
        """
        # Create a group box for the crust information
        crust_group = QGroupBox("Crust Information")

        # Move the title "Crust Information" to the top of the group box
        crust_group.setAlignment(Qt.AlignTop)

        # Create a layout for the group box
        form_layout = QGridLayout(crust_group)

        # Add a table widget to the form layout
        self.crust_table = QTableWidget()

        # Set the number of rows and columns in the table
        self.crust_table.setRowCount(1)
        self.crust_table.setColumnCount(7)

        # Set the headers for the table with HTML for mathematical symbols
        self.crust_table.setHorizontalHeaderLabels([
            "Layer Name", 
            "Thickness (km)", 
            "Vp (km/s)", 
            "Vs (km/s)", 
            "Density (g/cm³)",  # Unicode superscript for ³
            "Qp", 
            "Qs"
        ])

        # Set the first row of the table
        self.crust_table.setItem(0, 0, QTableWidgetItem("Half Space"))
        self.crust_table.setItem(0, 1, QTableWidgetItem("∞"))
        # make the "Half Space" name and thickness bold and bigger font size for thicknees
        # self.crust_table.item(0, 0).setFont(QFont("Arial", 10, QFont.Bold))
        self.crust_table.item(0, 1).setFont(QFont("Arial", 20))

        # Make the "Half Space" name and thickness uneditable
        self.crust_table.item(0, 0).setFlags(Qt.ItemIsEnabled)
        self.crust_table.item(0, 1).setFlags(Qt.ItemIsEnabled)

        # Resize columns to fit contents while stretching the first column
        header = self.crust_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)  # Stretch "Layer Name" column
        for i in range(0, self.crust_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)  # Minimize other columns

        # Add the table to the form layout
        form_layout.addWidget(self.crust_table, 0, 0, 1, 7)

        # Add "Add Layer" button
        add_button = QPushButton("Add Layer")
        add_button.setStyleSheet(self.button_style)
        add_button.clicked.connect(lambda: self.crust_table.insertRow(0))
        form_layout.addWidget(add_button, 1, 0, 1, 3)

        # Add "Remove Layer" button
        remove_button = QPushButton("Remove Layer")
        remove_button.setStyleSheet(self.button_style)
        remove_button.clicked.connect(lambda: self.crust_table.removeRow(0) if self.crust_table.rowCount() > 1 else None)
        form_layout.addWidget(remove_button, 1, 4, 1, 3)

        # Add "Load from File" button
        load_button = QPushButton("Load from File")
        load_button.setStyleSheet(self.button_style)
        load_button.clicked.connect(lambda: load_crust())
        form_layout.addWidget(load_button, 2, 0, 1, 3)

        # Add "Plot Crust" button
        plot_button = QPushButton("Plot Crust")
        plot_button.setStyleSheet(self.button_style)
        plot_button.clicked.connect(self.create_crust_mesh)
        form_layout.addWidget(plot_button, 2, 4, 1, 3)

        def load_crust():
            """
            Load crust data from a selected file and populate the table with layer details.
            """
            # Open file dialog to select crust file
            file = self.choose_file("Crust File")
            
            if not file:
                self.terminal_output.append("<font color='red'>Error: Crust file is not set</font>")
                return

            if not os.path.exists(file):
                self.terminal_output.append("<font color='red'>Error: Crust file does not exist</font>")
                return

            # Check file format
            format = file.split(".")[-1]
            if format != "json":
                self.terminal_output.append("<font color='red'>Error: Crust file format not supported</font>")
                return

            # Read the JSON file
            with open(file, "r") as f:
                data = json.load(f)

            # Validate file contents
            if "layers" not in data and "crust" not in data:
                self.terminal_output.append("<font color='red'>Error: Crust file does not have the layers or crust key</font>")
                self.terminal_output.append(f"  format: {json.dumps({'layers': [{'Layer Name': '', 'Thickness': '', 'Vp': '', 'Vs': '', 'Density': '', 'Qp': '', 'Qs': ''}], 'crust': [{'Layer Name': '', 'Thickness': '', 'Vp': '', 'Vs': '', 'Density': '', 'Qp': '', 'Qs': ''}]}, indent=4)}")
                return

            # Get the layers and populate the table
            layers = data.get("layers", data.get("crust"))
            for i in range(self.crust_table.rowCount() - 1):
                self.crust_table.removeRow(0)

            for i, layer in enumerate(layers[::-1]):
                if not all(key in layer for key in ["Layer Name", "Thickness", "Vp", "Vs", "Density", "Qp", "Qs"]):
                    self.terminal_output.append("<font color='red'>Error: Crust file does not have all the keys in the layer</font>")
                    return

                if i != 0:
                    self.crust_table.insertRow(0)

                self.crust_table.setItem(0, 0, QTableWidgetItem(layer["Layer Name"]))
                self.crust_table.setItem(0, 1, QTableWidgetItem(str(layer["Thickness"])))
                self.crust_table.setItem(0, 2, QTableWidgetItem(str(layer["Vp"])))
                self.crust_table.setItem(0, 3, QTableWidgetItem(str(layer["Vs"])))
                self.crust_table.setItem(0, 4, QTableWidgetItem(str(layer["Density"])))
                self.crust_table.setItem(0, 5, QTableWidgetItem(str(layer["Qp"])))
                self.crust_table.setItem(0, 6, QTableWidgetItem(str(layer["Qs"])))

        # Apply table and group styles
        self.crust_table.horizontalHeader().setStyleSheet(self.table_style)
        self.crust_table.setStyleSheet(self.table_style)
        crust_group.setStyleSheet(self.group_style)

        return crust_group




    def create_crust_mesh(self, clear=True):
        """Creates the crust mesh based on the thicknesses specified in the crust table."""
        # First clean the plotter
        if clear:
            self.Plotter.clear()

        thicknesses = []
        # Read all the thicknesses in the table
        for i in range(self.crust_table.rowCount()):
            thickness = self.crust_table.item(i, 1).text()
            # Check for the last row
            if thickness == "∞":
                thicknesses.append(0)
            else:
                thicknesses.append(float(thickness))

        # Create the mesh
        # Check if the fault mesh exists
        if "Fault" in self.Renderer.actors.keys():
            xmin, xmax, ymin, ymax, zmin, zmax = self.MeshObjects["Fault"].bounds
            # Multiply by 1.2
            factor = 1.2
            xmin *= factor
            xmax *= factor
            ymin *= factor
            ymax *= factor
        else:
            # Print a warning message in the terminal that the fault mesh does not exist
            self.terminal_output.append("<font color='orange'>Warning: Fault mesh does not exist</font>")
            self.terminal_output.append("The crust mesh is just for visualization and does not necessarily incorporate the fault mesh")
            # Create the crust mesh
            xmin, xmax, ymin, ymax = -1.0, 1.0, -1.0, 1.0

        Crust = pv.MultiBlock()

        if len(thicknesses) == 1:
            # Create a single layer crust
            thick = zmax + 5 if "Fault" in self.Renderer.actors.keys() else 1
            Crust.append(pv.Cube(bounds=[xmin, xmax, ymin, ymax, 0, thick]), name="Half Space")
        else:
            depth = 0
            for i in range(len(thicknesses)):
                if i == len(thicknesses) - 1:
                    # Find maximum thickness
                    thick = max(thicknesses)
                    thick = max(thick, 5)
                    if "Fault" in self.Renderer.actors.keys() and depth + thick < zmax:
                        thick = zmax - depth + thick
                else:
                    thick = thicknesses[i]

                if self.crust_table.item(i, 0) is None:
                    self.terminal_output.append(f"<font color='red'>Error: Layer name for layer {i + 1} is not set</font>")
                    return

                Crust.append(pv.Cube(bounds=[xmin, xmax, ymin, ymax, depth, depth + thick]), name=self.crust_table.item(i, 0).text())
                depth += thicknesses[i]

        # Add the crust mesh to the plotter
        self.Plotter.add_mesh(Crust, opacity=0.25, multi_colors=True, label="Crust", name="Crust")
        self.view_ShakerMaker()
        self.MeshObjects["Crust"] = Crust

    def create_fault_mesh(self, active_scalar, clear=True):
        """Creates the fault mesh based on the metadata and fault files."""
        # First clean the plotter
        if clear:
            self.Plotter.clear()

        # Check if the fault meta data file is set
        if self.source_meta_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: Fault meta data file is not set</font>")
            return

        meshlist = []

        # Check if there are any fault files
        if self.source_filestable.rowCount() == 0:
            self.terminal_output.append("<font color='red'>Error: No fault files are set</font>")
            return

        numFaults = self.source_filestable.rowCount()

        # Read the fault meta data file
        faultinfo = json.load(open(self.source_meta_input.text(), "r"))
        xfault = faultinfo['xmean']
        yfault = faultinfo['ymean']

        # Load the fault files
        for i in range(numFaults):
            # Get the file path
            if self.source_filestable.item(i, 0) is None:
                self.terminal_output.append(f"<font color='red'>Error: File path for fault {i + 1} is not set</font>")
                return

            file_path = self.source_filestable.item(i, 0).text()

            if file_path == "":
                self.terminal_output.append(f"<font color='red'>Error: File path for fault {i + 1} is not set</font>")
                return

            # Check if the file exists
            if not os.path.exists(file_path):
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} does not exist</font>")
                return
            
            # Check if the file is a valid JSON
            if file_path.split(".")[-1] != "json":
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} is not a json file</font>")
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} is not supported</font>")
                return

            # Read the file
            with open(file_path, "r") as f:
                sources = json.load(f)

            x = np.zeros(len(sources))
            y = np.zeros(len(sources))
            z = np.zeros(len(sources))
            c1 = np.zeros(len(sources))
            c2 = np.zeros(len(sources))
            c3 = np.zeros(len(sources))
            c4 = np.zeros(len(sources))
            c5 = np.zeros(len(sources))

            for j, source in enumerate(sources):
                x[j] = source['x']
                y[j] = source['y']
                z[j] = source['z']
                c1[j] = source['strike']
                c2[j] = source['dip']
                c3[j] = source['rake']
                c4[j] = source['t0']
                c5[j] = source['slip']

            # Filter the sources based on the minimum slip
            #check that minum slip can be converted to float
            try:
                minslip = float(self.source_min_slip_input.text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: Minimum slip must be a number</font>")
                return 
            minslip = float(self.source_min_slip_input.text())
            indicies = np.where(c5 > minslip)[0]
            x, y, z, c1, c2, c3, c4, c5 = x[indicies], y[indicies], z[indicies], c1[indicies], c2[indicies], c3[indicies], c4[indicies], c5[indicies]

            # Create the mesh
            mesh = pv.PolyData(np.c_[x, y, z])
            mesh['Strike'] = c1
            mesh['Dip'] = c2
            mesh['Rake'] = c3
            mesh['T0'] = c4
            mesh['Slip'] = c5
            meshlist.append(mesh)

        # Merge the meshes
        Mesh = meshlist[0]
        for i in range(1, numFaults):
            Mesh = Mesh.merge(meshlist[i])

        # Shift the mesh to the center of the fault
        Mesh.points -= np.array([xfault, yfault, 0])

        # Add the mesh to the plotter
        if active_scalar == "None":
            ac = self.Plotter.add_mesh(Mesh, label="Fault", name="Fault", show_scalar_bar=False)
            ac.mapper.scalar_visibility = False
        else:
            self.Plotter.add_mesh(Mesh, scalars=active_scalar, cmap='coolwarm', show_scalar_bar=True, label="Fault", name="Fault")
        
        self.MeshObjects["Fault"] = Mesh

        # Print fault Mesh information in the terminal
        self.terminal_output.append(f"<font color='green'>Fault mesh created successfully</font>")
        self.terminal_output.append(f"Number of faults: {numFaults}")
        self.terminal_output.append(f"Fault meta data file: {self.source_meta_input.text()}")
        for i in range(numFaults):
            npoints = len(meshlist[i].points)
            self.terminal_output.append(f"Fault {i + 1}: {npoints} points")

    def view_ShakerMaker(self, do_iso=True):
        """Defines the ShakerMaker style view."""
        if do_iso:
            self.Plotter.view_isometric()
        self.Plotter.camera.up = (0, 0, -1)
        self.Plotter.camera.elevation = 60
        self.Plotter.camera.azimuth = -90

    def plot(self, active_scalar, plot_fault=True, plot_crust=True):
        """Plots the fault and crust mesh."""
        # Clean the plotter
        Plotter.disable()
        self.Plotter.clear()
        Plotter.view_isometric()

        # First create the fault mesh
        if plot_fault:
            self.create_fault_mesh(active_scalar, clear=False)
        if plot_crust:
            self.create_crust_mesh(clear=False)
        self.view_ShakerMaker(do_iso=False)
        Plotter.enable()

    def plot_map(self):
        '''
        This function plots the fault points on the map
        '''
        
        # Check if the fault mesh exists
        if self.source_meta_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: Fault meta data file is not set</font>")
            return

        meshlist = []

        # Check for fault files
        if self.source_filestable.rowCount() == 0:
            self.terminal_output.append("<font color='red'>Error: No fault files are set</font>")
            return

        numFaults = self.source_filestable.rowCount()  

        # Read the fault meta data file
        faultinfo = json.load(open(self.source_meta_input.text(), "r"))
        xfault = faultinfo['xmean']
        yfault = faultinfo['ymean']

        # Load the fault files
        for i in range(self.source_filestable.rowCount()):
            # Get the file path
            if self.source_filestable.item(i, 0) is None:
                self.terminal_output.append(f"<font color='red'>Error: File path for fault {i + 1} is not set</font>")
                return
            
            file_path = self.source_filestable.item(i, 0).text()

            if file_path == "":
                self.terminal_output.append(f"<font color='red'>Error: File path for fault {i + 1} is not set</font>")
                return

            # Check if the file exists
            if not os.path.exists(file_path):
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} does not exist</font>")
                return

            # Get the format of the file
            format = file_path.split(".")[-1]
            if format != "json":
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} is not a json file</font>")
                self.terminal_output.append(f"<font color='red'>Error: File {file_path} is not supported</font>")
                return
            
            # Read the file
            with open(file_path, "r") as f:
                sources = json.load(f)
            x = np.zeros(len(sources))
            y = np.zeros(len(sources))
            z = np.zeros(len(sources))

            for j, source in enumerate(sources):
                sourcetype = source['stf']['type']  # noqa: F841
                x[j] = source['x']
                y[j] = source['y']
                z[j] = source['z']

            mesh = pv.PolyData(np.c_[x, y, z])
            meshlist.append(mesh)

        Mesh = meshlist[0]  
        for i in range(1, numFaults):
            Mesh = Mesh.merge(meshlist[i]) 

        xy = Mesh.points[:, :2]
        transformer = Transformer.from_crs(faultinfo['epsg'], 'epsg:4326')
        xy = xy * 1000

        # Add (xfault, yfault) to the first row of xy
        xy = np.vstack((xy, [xfault, yfault]))
        x2, y2 = transformer.transform(xy[:, 1], xy[:, 0])
        geometry1 = [Point(xy) for xy in zip(x2, y2)]
        gdf1 = gpd.GeoDataFrame(geometry=geometry1)
        gdf1['type'] = 'Fault'
        gdf1.loc[gdf1.index[-1], 'type'] = 'Fault Center'

        # if info['plottingStation'].lower() in ['yes', 'true']:
        #     stationCoordinates = info['stationCoordinates']  # noqa: N806
        #     coords = []
        #     xy2 = []
        #     for coord in stationCoordinates:
        #         north, east = calculate_distances_with_direction(
        #             faultinfo['latitude'], faultinfo['longitude'], coord[0], coord[1]
        #         )
        #         coords.append([north, east, coord[2]])
        #         xy2.append([north + xfault, east + yfault])

        #     stations = pv.PolyData(np.array(coords))

        #     xmin0, xmax0, ymin0, ymax0, zmin0, zmax0 = stations.bounds
        #     # Update extreme values
        #     xmin = min(xmin, xmin0)
        #     xmax = max(xmax, xmax0)
        #     ymin = min(ymin, ymin0)
        #     ymax = max(ymax, ymax0)
        #     zmin = min(zmin, zmin0)
        #     zmax = max(zmax, zmax0)

        # if info['plottingStation'].lower() in ['yes', 'true']:
        #     xy2 = np.array(xy2) * 1000
        #     x2, y2 = transformer.transform(xy2[:, 1], xy2[:, 0])
        #     geometry2 = [Point(xy) for xy in zip(x2, y2)]
        #     gdf2 = gpd.GeoDataFrame(geometry=geometry2)
        #     gdf2['type'] = 'Station'
        #     # Make the first row of the type column of gdf2 to be "Fault Center"

        #     gdf = gpd.GeoDataFrame(pd.concat([gdf1, gdf2], ignore_index=True))
        # else:
        gdf = gdf1

        # Move the row with 'Fault Center' type to the last row
        faultlat = faultinfo['latitude']
        faultlon = faultinfo['longitude']

        # Find the closest station to the fault center
        fault_center = Point(faultlat, faultlon)
        # Find the closest point and change the type to "Fault Center"
        gdf['distance'] = gdf['geometry'].apply(lambda x: x.distance(fault_center))
        gdf = gdf.sort_values('distance', ascending=False)
        gdf.loc[gdf.index[-1], 'type'] = 'Fault Center'

        # Use different colors for fault and stations
        color_map = {'Fault': 'blue', 'Station': 'red', 'Fault Center': 'green'}
        gdf['size'] = gdf['type'].apply(lambda x: 50 if x != 'Fault' else 0.25)
        gdf['marker'] = gdf['type'].apply(lambda x: 'x' if x == 'Fault Center' else 'o')

        # Plot with custom colors
        fig = px.scatter_mapbox(
            gdf,
            lat=gdf.geometry.x,
            lon=gdf.geometry.y,
            color=gdf['type'],
            size=gdf['size'],
            color_discrete_map=color_map,  # Apply the custom color map
        )
        
        min_lat, max_lat = gdf.geometry.x.min(), gdf.geometry.x.max()  # noqa: F841
        min_lon, max_lon = gdf.geometry.y.min(), gdf.geometry.y.max()  # noqa: F841

        # Update layout and display map
        fig.update_layout(
            mapbox_style='open-street-map',
            mapbox_zoom=10,  # Initial zoom level (adjustable)
            # mapbox_center={"lat": (min_lat + max_lat) / 2, "lon": (min_lon + max_lon) / 2},  # Center the map
            # mapbox_bounds={"west": min_lon, "east": max_lon, "south": min_lat, "north": max_lat}  # Set bounds
        )
        
        # Save the figure as an HTML file
        basepath = self.dir_input.text().replace("\\", "/")
        file = f'{basepath}/faults_map.html'
        file = file.replace('\\', '/')
        fig.write_html(file)

        # Open new window and view with the webengine view
        new_window = QDialog(self)
        new_window.setWindowTitle("Faults Map")
        new_window.resize(1000, 800)

        # Create a layout for the dialog
        layout = QVBoxLayout(new_window)

        # Create a QWebEngineView and load the HTML file
        map_view = QWebEngineView()
        map_url = QUrl(f'{basepath}/faults_map.html')

        # Check if the file exists
        if not os.path.exists(f'{basepath}/faults_map.html'):
            self.terminal_output.append(f"<font color='red'>Error: File {basepath}/faults_map.html does not exist</font>")
            return

        map_view.setUrl(map_url)

        # Allow local content to access remote content (if necessary)
        settings = map_view.settings()
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, True)

        # Add the map view to the layout
        layout.addWidget(map_view)

        # Set the dialog layout and show the dialog
        new_window.setLayout(layout)
        new_window.exec_()  # Show the dialog modally


    def add_Source_information(self):
        # Create a group box for the fault information
        self.source_group = QGroupBox("Fault Information")
        self.source_group.setAlignment(Qt.AlignTop)  # Move title to the top
        
        # Create a layout for the group box
        form_layout = QGridLayout()
        
        # Validators
        double_validator = QDoubleValidator()
        int_validator = QIntValidator()

        # Fault Latitude Input
        self.source_lat_input = QLineEdit()
        self.source_lat_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Latitude"), 0, 0)
        form_layout.addWidget(self.source_lat_input, 0, 1)
        form_layout.addWidget(QLabel("Latitude of the Epicenter"), 0, 2)

        # Fault Longitude Input
        self.source_lon_input = QLineEdit()
        self.source_lon_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("Longitude"), 1, 0)
        form_layout.addWidget(self.source_lon_input, 1, 1)
        form_layout.addWidget(QLabel("Longitude of the Epicenter"), 1, 2)

        # Meta Data File Input
        self.source_meta_input = QLineEdit()
        form_layout.addWidget(QLabel("Meta Data File"), 2, 0)
        form_layout.addWidget(self.source_meta_input, 2, 1)

        meta_button = QPushButton("Choose")
        meta_button.setStyleSheet(self.button_style)  # Make button color 3D and default blue
        meta_button.clicked.connect(self.choose_file)
        form_layout.addWidget(meta_button, 2, 2)

        # Time Function File Input
        self.source_time_input = QLineEdit()
        form_layout.addWidget(QLabel("Time Function File"), 3, 0)
        form_layout.addWidget(self.source_time_input, 3, 1)

        time_button = QPushButton("Choose")
        time_button.setStyleSheet(self.button_style)
        time_button.clicked.connect(self.choose_file)
        form_layout.addWidget(time_button, 3, 2)

        # Minimum Slip Input
        self.source_min_slip_input = QLineEdit()
        self.source_min_slip_input.setValidator(double_validator)
        self.source_min_slip_input.setText("0.0")  # Default value
        form_layout.addWidget(QLabel("Minimum Slip"), 4, 0)
        form_layout.addWidget(self.source_min_slip_input, 4, 1)
        form_layout.addWidget(QLabel("Minimum Slip for Filtering"), 4, 2)

        # File Table
        self.source_filestable = QTableWidget()
        self.source_filestable.setRowCount(1)
        self.source_filestable.setColumnCount(3)
        self.source_filestable.setHorizontalHeaderLabels(["File Path", "Browse", "Remove"])
        self.source_filestable.horizontalHeader().setStyleSheet(self.table_style)
        self.source_filestable.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Expand first column

        # Browse Button in Table
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(self.button_style)
        self.source_filestable.setCellWidget(0, 1, browse_button)
        browse_button.clicked.connect(lambda: self.find_button_location_and_browse(browse_button))

        # Remove Button in Table
        remove_button = QPushButton("Remove")
        remove_button.setStyleSheet(self.button_style)
        self.source_filestable.setCellWidget(0, 2, remove_button)
        remove_button.clicked.connect(lambda: self.remove_table_row(remove_button))

        form_layout.addWidget(self.source_filestable, 5, 0, 1, 3)

        # Add Row Button
        add_button = QPushButton("Add Row")
        add_button.setStyleSheet(self.button_style)
        add_button.clicked.connect(self.source_filestable_add_row)
        form_layout.addWidget(add_button, 6, 0, 1, 3)

        # Add Database Section
        form_layout.addWidget(self.add_databse(), 7, 0, 1, 3)

        # Set the layout for the group box
        self.source_group.setLayout(form_layout)
        self.source_group.setStyleSheet(self.group_style)  # Thick border for the group box

        return self.source_group



    def add_databse(self):
        # Create a group box for the database information
        database_group = QGroupBox("Database Information")

        # Create a layout for the group box
        form_layout = QGridLayout(database_group)

        # drop down menu for contries
        self.country_input = QComboBox()

        #load data from DatabaseMetadata.json
        
        # read the countries from the json file
        countries = self.data['Countries']
        # add the countries to the drop down menu
        self.country_input.addItems(countries)
        form_layout.addWidget(QLabel("Country"), 0,0)
        form_layout.addWidget(self.country_input, 0,1)

        # drop down menu for faults
        self.fault_input = QComboBox()
        # read the faults for the selected country
        country = self.country_input.currentText()
        faults = self.data[country]["Faults"]
        self.fault_input.addItems(faults)
        form_layout.addWidget(QLabel("Fault"), 1,0)
        form_layout.addWidget(self.fault_input, 1,1)

        # drop down menu for Magnitude
        self.magnitude_input = QComboBox()
        fault = self.fault_input.currentText()
        magnitudes = self.data[country][fault]["Magnitudes"]
        self.magnitude_input.addItems(magnitudes)
        form_layout.addWidget(QLabel("Magnitude"), 2,0)
        form_layout.addWidget(self.magnitude_input, 2,1)

        # drop down menu for Types
        self.types_input = QComboBox()
        magnitude = self.magnitude_input.currentText()
        types = self.data[country][fault][magnitude]["Types"]
        self.types_input.addItems(types)
        form_layout.addWidget(QLabel("Type"), 3,0)
        form_layout.addWidget(self.types_input,3,1)



        # drop down menu for Realizations
        self.realizations_input = QComboBox()
        type = self.types_input.currentText()
        realizations = self.data[country][fault][magnitude][type]["Realizations"]
        self.realizations_input.addItems(realizations)
        form_layout.addWidget(QLabel("Realization"), 4,0)
        form_layout.addWidget(self.realizations_input, 4,1)



        # load database button
        loadDatabase_button = QPushButton("Load Database")
        loadDatabase_button.setStyleSheet(self.button_style)
        form_layout.addWidget(loadDatabase_button, 5,0)
        loadDatabase_button.clicked.connect(self.load_database)


        # update database button
        updateDatabase_button = QPushButton("Update Database")
        updateDatabase_button.setStyleSheet(self.button_style)
        form_layout.addWidget(updateDatabase_button, 5,1)
        updateDatabase_button.clicked.connect(self.update_database)



        def update_faults():
            # read the faults for the selected country
            country = self.country_input.currentText()
            faults = self.data[country]["Faults"]
            self.fault_input.blockSignals(True)
            self.fault_input.clear()
            self.fault_input.addItems(faults)
            update_magnitudes()
            self.fault_input.blockSignals(False)


            
        
        def update_magnitudes():
            fault = self.fault_input.currentText()
            magnitudes = self.data[self.country_input.currentText()][fault]["Magnitudes"]
            self.magnitude_input.blockSignals(True)
            self.magnitude_input.clear()
            self.magnitude_input.addItems(magnitudes)
            update_types()
            self.magnitude_input.blockSignals(False)


        
        def update_types():
            magnitude = self.magnitude_input.currentText()
            types = self.data[self.country_input.currentText()][self.fault_input.currentText()][magnitude]["Types"]
            self.types_input.blockSignals(True)
            self.types_input.clear()
            self.types_input.addItems(types)
            update_realizations()
            self.types_input.blockSignals(False)
        

        def update_realizations():
            type = self.types_input.currentText()
            realizations = self.data[self.country_input.currentText()][self.fault_input.currentText()][self.magnitude_input.currentText()][type]["Realizations"]
            self.realizations_input.blockSignals(True)
            self.realizations_input.clear()
            self.realizations_input.addItems(realizations)
            self.realizations_input.blockSignals(False)



        # connect the country drop down menu that when the country is changed the fault drop down menu should be updated
        # self.country_input.currentTextChanged.connect(update_faults)
        self.country_input.currentTextChanged.connect(update_faults)
        self.fault_input.currentTextChanged.connect(update_magnitudes)
        self.magnitude_input.currentTextChanged.connect(update_types)
        self.types_input.currentTextChanged.connect(update_realizations)

        return database_group
    

    
    def load_database(self):
        # Check that the input directory is set
        if self.dir_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: Working directory is not set</font>")
            self.terminal_output.append("Please set the working directory")
            return
        elif not os.path.exists(self.dir_input.text()):
            self.terminal_output.append("<font color='red'>Error: Working directory does not exist</font>")
            self.terminal_output.append("Please set the working directory")
            return
        
        # Clear the directory before loading new files
        for file in os.listdir(self.dir_input.text()):
            os.remove(os.path.join(self.dir_input.text(), file))

        # Read selected options
        country = self.country_input.currentText()
        fault = self.fault_input.currentText()
        magnitude = self.magnitude_input.currentText()
        type = self.types_input.currentText()
        realization = self.realizations_input.currentText()

        # Download fault info JSON file
        url = f"https://raw.githubusercontent.com/amnp95/ShakerMakerFaultDatabase/Pythoninterface/{country}/{fault}/M_{magnitude}_type_{type}_number_{realization}/faultInfo.json"
        res = requests.get(url)

        if res.status_code != 200:
            self.terminal_output.append(f"<font color='red'>Error: Database failed to load </font>")
            self.terminal_output.append(f"  message: {res.text}")
            return

        faultInfo = res.json()
        
        # Set latitude and longitude in the input fields
        lat = faultInfo["latitude"]
        lon = faultInfo["longitude"]
        self.source_lat_input.setText(str(lat))
        self.source_lon_input.setText(str(lon))

        # Clear the table and prepare to add new files
        self.source_filestable.setRowCount(0)
        basePath = self.dir_input.text() + "/"
        faultfiles = faultInfo["Faultfilenames"]

        # Download fault files
        for file in faultfiles:
            url = f"https://raw.githubusercontent.com/amnp95/ShakerMakerFaultDatabase/Pythoninterface/{country}/{fault}/M_{magnitude}_type_{type}_number_{realization}/{file}"
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    filePath = basePath + file
                    with open(filePath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # Only write non-empty chunks
                                f.write(chunk)
                    
                    row_count = self.source_filestable.rowCount()
                    self.source_filestable.setRowCount(row_count + 1)
                    self.source_filestable.setItem(row_count, 0, QTableWidgetItem(basePath + file))

                    # Create Browse button
                    browse_button = QPushButton("Browse")
                    browse_button.setStyleSheet(self.button_style)
                    self.source_filestable.setCellWidget(row_count, 1, browse_button)
                    browse_button.clicked.connect(lambda: self.find_button_location_and_browse(browse_button))

                    # Create Remove button
                    remove_button = QPushButton("Remove")
                    remove_button.setStyleSheet(self.button_style)
                    self.source_filestable.setCellWidget(row_count, 2, remove_button)
                    remove_button.clicked.connect(lambda: self.remove_table_row(remove_button))
                else:
                    self.terminal_output.append(f"<font color='red'>Error: {file} failed to download </font>")
                    return
            except requests.exceptions.RequestException as e:
                print(f"Download failed due to: {e}")

        # Download additional required files
        additional_files = [
            faultInfo["SourceTimeFunction"]["filename"],
            "faultInfo.json"
        ]
        for file in additional_files:
            url = f"https://raw.githubusercontent.com/amnp95/ShakerMakerFaultDatabase/Pythoninterface/{country}/{fault}/M_{magnitude}_type_{type}_number_{realization}/{file}"
            try:
                response = requests.get(url, stream=True)
                if response.status_code == 200:
                    filePath = basePath + file
                    with open(filePath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:  # Only write non-empty chunks
                                f.write(chunk)
                else:
                    self.terminal_output.append(f"<font color='red'>Error: {file} failed to download </font>")
                    return
            except requests.exceptions.RequestException as e:
                print(f"Download failed due to: {e}")

        # Set paths for meta and time function files
        self.source_meta_input.setText(basePath + "faultInfo.json")
        self.source_time_input.setText(basePath + faultInfo["SourceTimeFunction"]["filename"])

        # Print success message and fault details in the terminal
        self.terminal_output.append("<font color='green'>Success: Database loaded successfully</font>")
        self.terminal_output.append(f"\tFault name: {faultInfo['name']}")
        self.terminal_output.append(f"\tLatitude: {lat}")
        self.terminal_output.append(f"\tLongitude: {lon}")
        self.terminal_output.append(f"\tEPSG: {faultInfo['epsg']}")
        self.terminal_output.append(f"\tFiles downloaded to: {self.dir_input.text()}")




    def update_database(self):
        """Update the database metadata and populate the country input."""
        res = requests.get("https://raw.githubusercontent.com/amnp95/ShakerMakerFaultDatabase/Pythoninterface/DatabaseMetadata.json")
        
        if res.status_code != 200:
            self.terminal_output.append("<font color='red'>Error: Database Metadata failed to load </font>")
            self.terminal_output.append(f"  message: {res.text}")
            return
        
        # Update global variable and populate country input
        self.data = res.json()
        countries = self.data['Countries']
        
        self.country_input.blockSignals(True)
        self.country_input.clear()
        self.country_input.addItems(countries)
        self.country_input.blockSignals(False)
        
        self.terminal_output.append("<font color='green'>Success: Database Metadata loaded successfully</font>")
        
        # Emit a fake signal to indicate that countries have changed
        self.country_input.currentTextChanged.emit(self.country_input.currentText())


    def find_button_location_and_browse(self, button):
        """Find the button's position in the table and open the file dialog."""
        index = self.source_filestable.indexAt(button.pos())
        row = index.row()
        column = index.column()
        
        self.source_filestable_browse(row, column)


    def remove_table_row(self, button):
        """Remove the corresponding row from the table."""
        index = self.source_filestable.indexAt(button.pos())
        row = index.row()
        
        if row >= 0:  # Ensure the button is in a valid row
            self.source_filestable.removeRow(row)


    def source_filestable_browse(self, row, column):
        """Open a file dialog to select a file and set the path in the table."""
        file, _ = QFileDialog.getOpenFileName(self, "Select File")
        if file:
            self.source_filestable.setItem(row, 0, QTableWidgetItem(file))


    def source_filestable_add_row(self):
        """Add a new row to the file table with browse and remove buttons."""
        row_count = self.source_filestable.rowCount()
        self.source_filestable.setRowCount(row_count + 1)

        # Create and configure the Browse button
        browse_button = QPushButton("Browse")
        browse_button.setStyleSheet(self.button_style)
        self.source_filestable.setCellWidget(row_count, 1, browse_button)
        browse_button.clicked.connect(lambda: self.find_button_location_and_browse(browse_button))

        # Create and configure the Remove button
        remove_button = QPushButton("Remove")
        remove_button.setStyleSheet(self.button_style)
        self.source_filestable.setCellWidget(row_count, 2, remove_button)
        remove_button.clicked.connect(lambda: self.remove_table_row(remove_button))


    def choose_file(self, input_field):
        """Open a file dialog to select a file and set it in the appropriate input field."""
        file, _ = QFileDialog.getOpenFileName(self, "Select File")
        
        if file:
            if input_field == "Meta Data File":
                self.source_meta_input.setText(file) 
            elif input_field == "Time Function File":
                self.source_time_input.setText(file)
            elif input_field in ["Crust File", "Stations File"]:
                return file



    def add_pyvista_plot(self):
        # Create a sphere using pyvista
        global Plotter   # Global plotter to allow access in exec statements
        global Renderer  # Global renderer to allow access in exec statements

        # Create the BackgroundPlotter for pyvista
        Plotter = pvqt.QtInteractor(self)
        # Display the PyVista plotter
        Renderer = Plotter.renderer

        self.Plotter = Plotter
        self.Renderer = Renderer


        # sphere = pv.Sphere()
        # Plotter.add_mesh(sphere)
        # Plotter.add_mesh(pv.Cube(), color="r")


        plotter_toolbar = QtWidgets.QToolBar("Plotter Toolbar", self)
        plotter_toolbar.setStyleSheet("""
            QToolBar {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                            stop:0 #e0e0e0, stop:1 #b0b0b0);
                border: 1px solid #888888;
                border-radius: 5px;
            }
            QToolButton {
                background: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 3px;
                margin: 2px;
                padding: 5px;
            }
            QToolButton:hover {
                background: #d0d0d0;
            }
            QToolButton:pressed {
                background: #c0c0c0;
                border: 1px solid #aaaaaa;
            }
        """)
        # Add screenshot button
        screenshot_action = plotter_toolbar.addAction("Screenshot")
        # screenshot_action.triggered.connect(lambda: self.Plotter.take_screenshot("screenshot.png"))

        # Add a button to the toolbar for Layers
        layer_action = plotter_toolbar.addAction("Layers")
        layer_action.triggered.connect(self.Plotter_Layers)

        # Create the view menu
        view_menu = QtWidgets.QMenu("View", self)

        # Add the "Isometric View" action
        isometric_action = view_menu.addAction("Isometric View")
        isometric_action.triggered.connect(lambda: Plotter.view_isometric())

        
        actionxy = view_menu.addAction("View xy")
        actionxy.triggered.connect(lambda: Plotter.view_xy())

        actionxz = view_menu.addAction("View xz")
        actionxz.triggered.connect(lambda: Plotter.view_xz())

        actionyx = view_menu.addAction("View yx")
        actionyx.triggered.connect(lambda: Plotter.view_yx())

        actionyz = view_menu.addAction("View yz")
        actionyz.triggered.connect(lambda: Plotter.view_yz())

        actionzx = view_menu.addAction("View zx")
        actionzx.triggered.connect(lambda: Plotter.view_zx())

        actionzy = view_menu.addAction("View zy")
        actionzy.triggered.connect(lambda: Plotter.view_zy())

        actionViewShakerMaker = view_menu.addAction("View ShakerMaker view")
        actionViewShakerMaker.triggered.connect(lambda: self.view_ShakerMaker())




        # Create a tool button for the View menu (to avoid showing a down arrow)
        view_button = QtWidgets.QToolButton()
        view_button.setText("View")
        view_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        view_button.setMenu(view_menu)

        # Add the View button to the toolbar
        plotter_toolbar.addWidget(view_button)

        view_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

        # Optionally, connect the button to open the menu if clicked
        view_button.clicked.connect(lambda: view_menu.exec_(plotter_toolbar.mapToGlobal(QtCore.QPoint(0, plotter_toolbar.height()))))


    
        # add options to the toolbar
        Options_menu = QtWidgets.QMenu("Options", self)

        show_axes = Options_menu.addAction("Axes")
        # check mark beside the axes
        show_axes.setCheckable(True)
        # if the axes is checked then show the axes with plotter show_axes and if not checked then hide the axes with plotter.hide_axes
        show_axes.triggered.connect(lambda: Plotter.show_axes() if show_axes.isChecked() else Plotter.hide_axes())


        # add legend
        show_grid = Options_menu.addAction("Grid")
        # show_grid.setCheckable(True)
        show_grid.triggered.connect(lambda: self.Plotter.show_grid(xtitle='X (North)', ytitle='Y (East)', ztitle='Z (Depth)'))

        


        options_button = QtWidgets.QToolButton()
        options_button.setText("Options")
        options_button.setPopupMode(QtWidgets.QToolButton.InstantPopup)
        options_button.setMenu(Options_menu)

        plotter_toolbar.addWidget(options_button)

        options_button.setStyleSheet("QToolButton::menu-indicator { image: none; }")

        options_button.clicked.connect(lambda: Options_menu.exec_(plotter_toolbar.mapToGlobal(QtCore.QPoint(0, plotter_toolbar.height()))))

        

    

        

        self.top_layout.addWidget(plotter_toolbar)
        self.top_layout.addWidget(Plotter.interactor)
        self.top_layout.addWidget(self.add_Visualization_information())





    def Plotter_Layers(self):
        # get he names mesh dict
        info = Renderer.actors.copy()

        # delte the keys that sart with a Addr
        for key in list(info.keys()):
            if key.startswith("Addr") or key.startswith("Actor"): 
                del info[key]

        # Open a dialog that has table the first column is the name of the mesh and the second column is visibility, third column is color
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Layers")
        dialog.setWindowModality(QtCore.Qt.ApplicationModal)
        # dialog.resize(400, 300)

        # Create a layout for the dialog
        layout = QtWidgets.QVBoxLayout(dialog)

        # Create a table widget
        table = QtWidgets.QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["Name", "Visibility", "Color", "Opacity","Style","Show Edges","Metallic","Interpolation"])
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)



        # Set the first column (Name) to resize based on the contents of the cells
        table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)

        # Set the second and third columns (Visibility, Color) to be as small as possible but still show the header text
        table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)

        # Optional: Make the color column a fixed width if ResizeToContents doesn't work perfectly for it
        table.setColumnWidth(2, 60)  # Adjust this value as needed
        # Add the table to the layout
        layout.addWidget(table)





        # Add the meshes to the table
        for i, (name, mesh) in enumerate(info.items()):
            # if name not in self.MeshObjects.keys():
            #     continue
            table.insertRow(i)
            table.setItem(i, 0, QtWidgets.QTableWidgetItem(name))

            # Create a checkbox for visibility
            visibility = QtWidgets.QCheckBox()
            visibility.setChecked(mesh.visibility)
            table.setCellWidget(i, 1, visibility)

            # make the background of the color column to the color of the mesh
            color = mesh.prop.color  # Assuming `mesh.prop.color` gives a tuple like (r, g, b)
            # color_item = QtWidgets.QTableWidgetItem()
            color_item = QtWidgets.QTableWidgetItem("")

            # # Extract the hex value and convert it to QColor
            color_qt = QColor(color.hex_rgb)  # QColor can directly use the hex format
            
            # # Set the background color using the QColor object
            color_item.setBackground(QBrush(color_qt))
            
            # # Set the color item in the table
            table.setItem(i, 2, color_item)

            # self.terminal_output.append(f"Color: {mesh.prop.opacity}")
            # Create a spin box for opacity
            opacity = QtWidgets.QSpinBox()
            opacity.setRange(0, 100)
            opacity.setValue(int(mesh.prop.opacity * 100))
            table.setCellWidget(i, 3, opacity)


            # add the scopy of tyle to the table
            style = QtWidgets.QComboBox()
            style.addItems(["Wireframe", "Surface", "Points"])
            style.setCurrentText(mesh.prop.style)
            table.setCellWidget(i, 4, style)

            # add the show edges checkbox
            show_edges = QtWidgets.QCheckBox()
            show_edges.setChecked(mesh.prop.show_edges)
            table.setCellWidget(i, 5, show_edges)


            # add the metallic spin box
            metallic = QtWidgets.QSpinBox()
            metallic.setRange(0, 100)
            metallic.setValue(int(mesh.prop.metallic * 100))
            table.setCellWidget(i, 6, metallic)

            # add the interpolation combo box
            interpolation = QtWidgets.QComboBox()
            interpolation.addItems(["Flat", "Gouraud", "Phong","pbr"])
            if mesh.prop.interpolation == pv.plotting.opts.InterpolationType.FLAT:
                interpolation.setCurrentText("Flat")
            elif mesh.prop.interpolation == pv.plotting.opts.InterpolationType.GOURAUD:
                interpolation.setCurrentText("Gouraud")
            elif mesh.prop.interpolation == pv.plotting.opts.InterpolationType.PHONG:
                interpolation.setCurrentText("Phong")
            else:
                interpolation.setCurrentText("pbr")
            
            table.setCellWidget(i, 7, interpolation)







            # connect the opacity spin box to the function that changes the opacity of the mesh
            opacity.valueChanged.connect(lambda value, mesh=mesh: setattr(mesh.prop, 'opacity', value / 100))


            # # Connect the checkbox to a function that toggles the visibility of the mesh
            visibility.stateChanged.connect(lambda state, mesh=mesh: setattr(mesh, 'visibility', state == Qt.Checked))

            # connect the style combo box to the function that changes the style of the mesh
            style.currentTextChanged.connect(lambda text, mesh=mesh: setattr(mesh.prop, 'style', text))

            # connect the show edges checkbox to the function that toggles the visibility of the edges
            show_edges.stateChanged.connect(lambda state, mesh=mesh: setattr(mesh.prop, 'show_edges', state == Qt.Checked))

            # connect the metallic spin box to the function that changes the metallic of the mesh
            metallic.valueChanged.connect(lambda value, mesh=mesh: setattr(mesh.prop, 'metallic', value / 100))

            # # connect the interpolation combo box to the function that changes the interpolation of the mesh
            interpolation.currentTextChanged.connect(lambda text, mesh=mesh: setattr(mesh.prop, 'interpolation', text))

        # Function to handle double-click on color item
        def on_color_item_double_clicked(item):
            row = item.row()  # Get the row of the clicked item
            column = item.column()  # Ge
            if column == 2:  # Assuming column 2 is the color column
                # Open a color dialog
                current_color = table.item(row, column).background().color()
                new_color = QColorDialog.getColor(current_color, dialog, "Select Color")

                if new_color.isValid():
                    # Update the color of the mesh and the table item
                    mesh = info[table.item(row, 0).text()]  # Get the corresponding mesh
                    mesh.prop.color = QColor(new_color).name()  # Update the mesh's color property
                    
                    # Set the new color in the table
                    color_item = QtWidgets.QTableWidgetItem()
                    color_item.setBackground(QBrush(new_color))
                    # make the string of the color to be empty
                    color_item.setText("")
                    # make the color item uneditable
                    color_item.setFlags(color_item.flags() & ~QtCore.Qt.ItemIsEditable)
                    table.setItem(row, column, color_item)

        # Connect the double-click signal to the function
        table.itemDoubleClicked.connect(on_color_item_double_clicked)


        

            

        table.resizeColumnsToContents()
        # Calculate the total width of the table (including borders)
        table_width = table.horizontalHeader().length() + 56

        # Resize the dialog to match the table's width and set a fixed height
        dialog.resize(table_width, 400)
        # Resize the dialog to be large enough
        # Show the dialog
        dialog.show()


    


    def add_terminal(self):
        # Create a label for the terminal
        self.terminal_label = QLabel("Output:")
        self.bottom_layout.addWidget(self.terminal_label)

        # Create a QTextEdit for the terminal to display output
        self.terminal_output = QTextEdit(self)
        self.terminal_output.setReadOnly(True)  # Output area is read-only
        self.bottom_layout.addWidget(self.terminal_output)

        # make the terminal output at least 200 pixels high
        # self.terminal_output.setMinimumHeight(100)

        # Create a QLineEdit for user input
        self.bottom_layout.addWidget(QLabel("Terminal:"))
        self.terminal_input = QLineEdit(self)
        self.terminal_input.returnPressed.connect(self.process_terminal_input)
        self.bottom_layout.addWidget(self.terminal_input)





  
    def add_Analysis_information(self):
        # Create a group box for the analysis information
        self.analysis_group = QGroupBox("Analysis Information")

        # Create a layout for the group box
        form_layout = QGridLayout()
        # Validators
        double_validator = QDoubleValidator()
        int_validator = QIntValidator()

        # dt
        self.dt_input = QLineEdit()
        self.dt_input.setValidator(double_validator) 
        form_layout.addWidget(QLabel("dt"), 0,0)
        form_layout.addWidget(self.dt_input, 0,1)
        form_layout.addWidget(QLabel("Timestep for output dataset"), 0,2)

        # nfft
        self.nfft_input = QLineEdit()
        self.nfft_input.setValidator(int_validator)
        form_layout.addWidget(QLabel("nfft"), 1,0)
        form_layout.addWidget(self.nfft_input, 1,1)
        form_layout.addWidget(QLabel("Number of samples (need power of 2)"), 1,2)

        # dk
        self.dk_input = QLineEdit()
        self.dk_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("dk"), 2,0)
        form_layout.addWidget(self.dk_input, 2,1)
        form_layout.addWidget(QLabel("Wavelength discretization"), 2,2)

        # tmin
        self.tmin_input = QLineEdit()
        self.tmin_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("tmin"), 3,0)
        form_layout.addWidget(self.tmin_input, 3,1)
        form_layout.addWidget(QLabel("Start time for simulation"), 3,2)

        # tmax
        self.tmax_input = QLineEdit()
        self.tmax_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("tmax"), 4,0)
        form_layout.addWidget(self.tmax_input, 4,1)
        form_layout.addWidget(QLabel("End time for simulation (must be contained in nfft window)"), 4,2)

        # dh (m)
        self.dh_input = QLineEdit()
        self.dh_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("dh (m)"), 5,0)
        form_layout.addWidget(self.dh_input, 5,1)
        form_layout.addWidget(QLabel("Horizontal distance criteria for database creation"), 5,2)

        # dv_rec (m)
        self.dv_rec_input = QLineEdit()
        self.dv_rec_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("dv_rec (m)"), 6,0)
        form_layout.addWidget(self.dv_rec_input, 6,1)
        form_layout.addWidget(QLabel("Vertical distance criteria for receiver points in database"), 6,2)

        # dv_src (m)
        self.dv_src_input = QLineEdit()
        self.dv_src_input.setValidator(double_validator)
        form_layout.addWidget(QLabel("dv_src (m)"), 7,0)
        form_layout.addWidget(self.dv_src_input, 7,1)
        form_layout.addWidget(QLabel("Vertical distance criteria for source points in database"), 7,2)

        # the working directory
        ShakerMakerPath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        if not os.path.exists(f"{ShakerMakerPath}/WorkDir"):
            os.makedirs(f"{ShakerMakerPath}/WorkDir")

        self.dir_input = QLineEdit()
        # form_layout.addWidget(QLabel("Working Directory"), 8,0)
        # form_layout.addWidget(self.dir_input, 8,1)
        dir_button = QPushButton("Choose")
        dir_button.clicked.connect(self.choose_directory)
        dir_button.setStyleSheet(self.button_style)
        #  put default directory in the input field
        self.dir_input.setText(f"{ShakerMakerPath}"   + "/WorkDir")

        # form_layout.addWidget(dir_button, 8,2)



        # Add push button to create the model
        self.model_dir = QLineEdit()
        self.model_dir.setText(f"{ShakerMakerPath}"   + "/Model")
        form_layout.addWidget(QLabel("Model Directory"), 8,0)
        form_layout.addWidget(self.model_dir, 8,1)
        form_layout.addWidget(QLabel("Directory to save the model"), 8,2)


        
        create_button = QPushButton("Create Model")
        create_button.setStyleSheet(self.button_style)
        create_button.clicked.connect(self.create_model)
        form_layout.addWidget(create_button, 9,0,1,3)


        # Set the layout for the group box
        self.analysis_group.setLayout(form_layout)

        # self.analysis_group.setStyleSheet("QGroupBox { border: 2px solid black; }")
        self.analysis_group.setStyleSheet(self.group_style)
        minsize = self.analysis_group.sizeHint()
        self.analysis_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.analysis_group.setFixedHeight(minsize.height()) 


        # create deafulat values for the input fields
        self.dt_input.setText("0.0025")
        self.nfft_input.setText("16384")
        self.dk_input.setText("0.2")
        self.tmin_input.setText("0.0")
        self.tmax_input.setText("100.0")
        self.dh_input.setText("40.0")
        self.dv_rec_input.setText("5.0")
        self.dv_src_input.setText("200")

        return self.analysis_group
    
    

    def create_model(self):
        """
        This method gather all the infomation and create the model in the working directory
        """
        # Create Model folder in the working directory
        if not os.path.exists(self.model_dir.text()):
            os.makedirs(self.model_dir.text())
            if not os.path.exists(f"{self.model_dir.text()}"):
                os.makedirs(f"{self.model_dir.text()}")
        else:
            if not os.path.exists(f"{self.model_dir.text()}"):
                os.makedirs(f"{self.model_dir.text()}")

        
        # Create the model
        # Check  that fault metadata file is set
        if self.source_meta_input == None or self.source_meta_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: Fault metadata file is not set</font>")
            self.terminal_output.append("Please set the fault metadata file")
            return
        
        if self.source_time_input == None or self.source_time_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: Source time function file is not set</font>")
            self.terminal_output.append("Please set the source time function file")
            return
        
        # check if the files exist
        if not os.path.exists(self.source_meta_input.text()):
            self.terminal_output.append("<font color='red'>Error: Fault metadata file does not exist</font>")
            self.terminal_output.append("Please set the fault metadata file")
            return
    
        if not os.path.exists(self.source_time_input.text()):
            self.terminal_output.append("<font color='red'>Error: Source time function file does not exist</font>")
            self.terminal_output.append("Please set the source time function file")
            return

        # read minimum slip
        # check if the minimum slip can be converted to a float
        try:
            minslip = float(self.source_min_slip_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: Minimum slip must be a float number</font>")
            return 
        minslip = float(self.source_min_slip_input.text())
    
        # read the files in table 
        # fault files in the table
        fault_files = []
        numpoints = 0
        for row in range(self.source_filestable.rowCount()):
            # check if the row is empty
            if self.source_filestable.item(row, 0) == None :
                self.terminal_output.append("<font color='red'>Error: Fault file is not set</font>")
                self.terminal_output.append("Please set the fault files in the table")
                return
            if self.source_filestable.item(row, 0).text() == "":
                self.terminal_output.append("<font color='red'>Error: Fault file is not set</font>")
                self.terminal_output.append("Please set the fault files in the table")
                return
            # check if the file exists
            if not os.path.exists(self.source_filestable.item(row, 0).text()):
                self.terminal_output.append("<font color='red'>Error: Fault file does not exist</font>")
                self.terminal_output.append("Please set the fault files in the table")
                return
            # just 
            filename = self.source_filestable.item(row, 0).text()

            # open the file and read the json file
            with open(filename, 'r') as file:
                fault = json.load(file)


            if fault == None:
                self.terminal_output.append("<font color='red'>Error: Fault file is empty</font>")
                return
            
            # iterate through the file points and filter based on the minimum slip
            # fault is list of dictionaries
            if minslip < 1e-13:
                minslip = 0
            if minslip > 0:
                # print waiting warning message
                self.terminal_output.append("<font color='orange'>Warning: Filtering fault file based on minimum slip</font>")
                
                indicies = []
                for i, point in enumerate(fault):
                    if point["slip"] > minslip:
                        indicies.append(i)
                
                # filter the fault file based on the indicies
                fault = [fault[i] for i in indicies]

            # write the filtered fault file to the model directory
            with open(f"{self.model_dir.text()}/{os.path.basename(filename)}", 'w') as file:
                json.dump(fault, file, indent=4)

            numpoints += len(fault)

            # drop the path and get the file name
            fault_files.append(os.path.basename(filename))


        # print the number of points in the fault files
        self.terminal_output.append(f"Number of points in the fault files: {numpoints}")


        # copy the source time function file to the model directory
        shutil.copy(self.source_time_input.text(), self.model_dir.text())
        

        # load the fault metadata file
        with open(self.source_meta_input.text(), 'r') as file:
            fault_info = json.load(file)

        # edit the fault info
        # fault_info["min_slip"] = minslip

        fault_info["Faultfilenames"] = fault_files
        fault_info["SourceTimeFunction"]["filename"] = os.path.basename(self.source_time_input.text())

        # lat and lon
        # check if the source lat and lon can be converted to a float
        try:
            lat = float(self.source_lat_input.text())
            lon = float(self.source_lon_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: Source latitude and longitude must be float numbers</font>")
            return
        lat = float(self.source_lat_input.text())
        lon = float(self.source_lon_input.text())


        fault_info["latitude"] = lat
        fault_info["longitude"] = lon

        # write the fault info to the model directory
        with open(f"{self.model_dir.text()}/faultInfo.json", 'w') as file:
            json.dump(fault_info, file, indent=4)

        # copy the Scripts\ShakerMakermodel.py to the model directory
        ShakerMakerPath = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
        shutil.copy(f"{ShakerMakerPath}/Scripts/ShakerMakermodel.py", self.model_dir.text())


        metadata = {}
        metadata["analysisdata"] = {}
        # check if the dt is not None
        if self.dt_input == None or self.dt_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: dt is not set</font>")
            self.terminal_output.append("Please set the dt")
            return
        try:
            dt = float(self.dt_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: dt must be a float number</font>")
            return
        metadata["analysisdata"]["dt"] = dt

        # check if the nfft is not None
        if self.nfft_input == None or self.nfft_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: nfft is not set</font>")
            self.terminal_output.append("Please set the nfft")
            return
        try:
            nfft = int(self.nfft_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: nfft must be an integer number</font>")
            return
        
        metadata["analysisdata"]["nfft"] = nfft

        # check if the dk is not None
        if self.dk_input == None or self.dk_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: dk is not set</font>")
            self.terminal_output.append("Please set the dk")
            return
        try:
            dk = float(self.dk_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: dk must be a float number</font>")
            return
        
        metadata["analysisdata"]["dk"] = dk

        # check if the tmin is not None
        if self.tmin_input == None or self.tmin_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: tmin is not set</font>")
            self.terminal_output.append("Please set the tmin")
            return
        try:
            tmin = float(self.tmin_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: tmin must be a float number</font>")
            return
        
        metadata["analysisdata"]["tmin"] = tmin

        # check if the tmax is not None
        if self.tmax_input == None or self.tmax_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: tmax is not set</font>")
            self.terminal_output.append("Please set the tmax")
            return
        try:
            tmax = float(self.tmax_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: tmax must be a float number</font>")
            return
        
        metadata["analysisdata"]["tmax"] = tmax

        # check if the dh is not None
        if self.dh_input == None or self.dh_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: dh is not set</font>")
            self.terminal_output.append("Please set the dh")
            return
        try:
            dh = float(self.dh_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: dh must be a float number</font>")
            return
        
        metadata["analysisdata"]["dh"] = dh

        # check if the dv_rec is not None
        if self.dv_rec_input == None or self.dv_rec_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: dv_rec is not set</font>")
            self.terminal_output.append("Please set the dv_rec")
            return
        try:
            dv_rec = float(self.dv_rec_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: dv_rec must be a float number</font>")
            return
        
        metadata["analysisdata"]["delta_v_rec"] = dv_rec

        # check if the dv_src is not None
        if self.dv_src_input == None or self.dv_src_input.text() == "":
            self.terminal_output.append("<font color='red'>Error: dv_src is not set</font>")
            self.terminal_output.append("Please set the dv_src")
            return
        try:
            dv_src = float(self.dv_src_input.text())
        except ValueError:
            self.terminal_output.append("<font color='red'>Error: dv_src must be a float number</font>")
            return
        
        metadata["analysisdata"]["delta_v_src"] = dv_src



        metadata["crustdata"] =  []

        # loop over crust files in the table
        rowindex = 0
        for row in range(self.crust_table.rowCount()):
            layerinfo = {}
            # check if the row is empty
            if self.crust_table.item(row, 0) == None :
                self.terminal_output.append("<font color='red'>Error: layer name is not set</font>")
                self.terminal_output.append("Please set the layer name in the table")
                return
            if self.crust_table.item(row, 0).text() == "":
                self.terminal_output.append("<font color='red'>Error: layer name is not set</font>")
                self.terminal_output.append("Please set the layer name in the table")
                return
            
            layerinfo["name"] = self.crust_table.item(row, 0).text()

            # check if the thickness is not None
            if self.crust_table.item(row, 1) == None :
                self.terminal_output.append("<font color='red'>Error: thickness is not set</font>")
                self.terminal_output.append("Please set the thickness in the table")
                return
            if self.crust_table.item(row, 1).text() == "":
                self.terminal_output.append("<font color='red'>Error: thickness is not set</font>")
                self.terminal_output.append("Please set the thickness in the table")
                return
            if rowindex == (self.crust_table.rowCount()-1):
                layerinfo["thick"] = 0
            else:
                try:
                    layerinfo["thick"] = float(self.crust_table.item(row, 1).text())
                except ValueError:
                    self.terminal_output.append("<font color='red'>Error: thickness must be a float number</font>")
                    return
            
            # check if the vp is not None
            if self.crust_table.item(row, 2) == None :
                self.terminal_output.append("<font color='red'>Error: vp is not set</font>")
                self.terminal_output.append("Please set the vp in the table")
                return
            if self.crust_table.item(row, 2).text() == "":
                self.terminal_output.append("<font color='red'>Error: vp is not set</font>")
                self.terminal_output.append("Please set the vp in the table")
                return
            try:
                layerinfo["vp"] = float(self.crust_table.item(row, 2).text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: vp must be a float number</font>")
                return
            
            # check if the vs is not None
            if self.crust_table.item(row, 3) == None :
                self.terminal_output.append("<font color='red'>Error: vs is not set</font>")
                self.terminal_output.append("Please set the vs in the table")
                return
            if self.crust_table.item(row, 3).text() == "":
                self.terminal_output.append("<font color='red'>Error: vs is not set</font>")
                self.terminal_output.append("Please set the vs in the table")
                return
            try:
                layerinfo["vs"] = float(self.crust_table.item(row, 3).text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: vs must be a float number</font>")
                return
            
            # check if the rho is not None
            if self.crust_table.item(row, 4) == None :
                self.terminal_output.append("<font color='red'>Error: rho is not set</font>")
                self.terminal_output.append("Please set the rho in the table")
                return
            if self.crust_table.item(row, 4).text() == "":
                self.terminal_output.append("<font color='red'>Error: rho is not set</font>")
                self.terminal_output.append("Please set the rho in the table")
                return
            try:
                layerinfo["rho"] = float(self.crust_table.item(row, 4).text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: rho must be a float number</font>")
                return
            
            # check if the Qp is not None
            if self.crust_table.item(row, 5) == None :
                self.terminal_output.append("<font color='red'>Error: Qp is not set</font>")
                self.terminal_output.append("Please set the Qp in the table")
                return
            if self.crust_table.item(row, 5).text() == "":
                self.terminal_output.append("<font color='red'>Error: Qp is not set</font>")
                self.terminal_output.append("Please set the Qp in the table")
                return
            try:
                layerinfo["Qa"] = float(self.crust_table.item(row, 5).text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: Qp must be a float number</font>")
                return
            
            # check if the Qs is not None
            if self.crust_table.item(row, 6) == None :
                self.terminal_output.append("<font color='red'>Error: Qs is not set</font>")
                self.terminal_output.append("Please set the Qs in the table")
                return
            if self.crust_table.item(row, 6).text() == "":
                self.terminal_output.append("<font color='red'>Error: Qs is not set</font>")
                self.terminal_output.append("Please set the Qs in the table")
                return
            try:
                layerinfo["Qb"] = float(self.crust_table.item(row, 6).text())
            except ValueError:
                self.terminal_output.append("<font color='red'>Error: Qs must be a float number</font>")
                return
            
            # add the layer info to metadata
            metadata["crustdata"].append(layerinfo)

            rowindex += 1



        metadata["stationdata"] = {}

        # check if the station type is not None
        if self.stations_dropdown.currentText() == "Single Stations":
            metadata["stationdata"]["stationType"] = "single"
            metadata["stationdata"]["name"] = "Station provided by user"
            metadata["stationdata"]["Singlestations"] = []

            # loop over the station files in the table
            if self.single_stations_table.rowCount() == 0:
                self.terminal_output.append("<font color='red'>Error: No station file is set</font>")
                self.terminal_output.append("Please set the station files in the table")
                return

            for row in range(self.single_stations_table.rowCount()):
                stationInfo = {}
                # check if lat 
                if self.single_stations_table.item(row, 0) == None :
                    self.terminal_output.append("<font color='red'>Error: Station latitude is not set</font>")
                    self.terminal_output.append("Please set the station latitude in the table")
                    return
                if self.single_stations_table.item(row, 0).text() == "":
                    self.terminal_output.append("<font color='red'>Error: Station latitude is not set</font>")
                    self.terminal_output.append("Please set the station latitude in the table")
                    return
                try:
                    lat = float(self.single_stations_table.item(row, 0).text())
                except ValueError:
                    self.terminal_output.append("<font color='red'>Error: Station latitude must be a float number</font>")
                    return
                
                stationInfo["latitude"] = lat

                # check if lon
                if self.single_stations_table.item(row, 1) == None :
                    self.terminal_output.append("<font color='red'>Error: Station longitude is not set</font>")
                    self.terminal_output.append("Please set the station longitude in the table")
                    return
                if self.single_stations_table.item(row, 1).text() == "":
                    self.terminal_output.append("<font color='red'>Error: Station longitude is not set</font>")
                    self.terminal_output.append("Please set the station longitude in the table")
                    return
                try:
                    lon = float(self.single_stations_table.item(row, 1).text())
                except ValueError:
                    self.terminal_output.append("<font color='red'>Error: Station longitude must be a float number</font>")
                    return
                
                stationInfo["longitude"] = lon

                # check if the elevation is not None
                if self.single_stations_table.item(row, 2) == None :
                    self.terminal_output.append("<font color='red'>Error: Station depth is not set</font>")
                    self.terminal_output.append("Please set the station depth in the table")
                    return
                if self.single_stations_table.item(row, 2).text() == "":
                    self.terminal_output.append("<font color='red'>Error: Station depth is not set</font>")
                    self.terminal_output.append("Please set the station depth in the table")
                    return
                try:
                    depth = float(self.single_stations_table.item(row, 2).text())
                except ValueError:
                    self.terminal_output.append("<font color='red'>Error: Station depth must be a float number</font>")
                    return
                
                stationInfo["depth"] = depth
                stationInfo["metadata"] = {"filter_parameters": {"fmax": 10},"filter_results": False, "name": "Station 1"}
                
                # add the station info to metadata
                metadata["stationdata"]["Singlestations"].append(stationInfo)



        if self.stations_dropdown.currentText() == "DRM Stations":
            # print not implemented error
            self.terminal_output.append("<font color='red'>Error: DRM Stations is not implemented</font>")
            return
        
















        # write the metadata to the model directory
        with open(f"{self.model_dir.text()}/metadata.json", 'w') as file:
            json.dump(metadata, file, indent=4)


        # print success message and the model directory and how to run the model
        self.terminal_output.append("<font color='green'>Success: Model created successfully</font>")
        self.terminal_output.append(f"\t Model directory: {self.model_dir.text()}")
        self.terminal_output.append("\t To run the model, open the model directory and run the command:")
        self.terminal_output.append("\t mpirun/mpiexec -n <number of processors> python ShakerMakermodel.py")



        





    def choose_directory(self):
        # Open a file dialog to select a directory
        directory = QFileDialog.getExistingDirectory(self, "Select Directory")
        if directory:
            self.dir_input.setText(directory)



    def process_terminal_input(self):
        # Get the text from the input
        command = self.terminal_input.text()

        # Clear the input field
        self.terminal_input.clear()

        # Check if the command is "clear"
        if command.strip().lower() == "clear":
            # Clear the terminal output
            self.terminal_output.clear()
            return


        # Execute the command and update the output
        self.terminal_output.append(f"> {command}")

        try:
            # Try to evaluate the command as an expression
            result = eval(command, self.global_context, self.local_context)
            if result is not None:
                self.terminal_output.append(str(result))
        except:
            try:
                # If eval fails, execute the command as a statement (e.g., assignments)
                exec(command, self.global_context, self.local_context)
            except Exception as e:
                # If there's an error, display it in the terminal output
                self.terminal_output.append(f"Error: {e}")




    # ===================================================================================
    # Data Base
    # ===================================================================================
    data = {
        "Countries":[
            "United States",
            "Chile"
        ],

        "Chile": {
            "Faults":["Sanramon"],
            "Sanramon": {
                "Magnitudes": ["6.7"],
                "6.7":{
                    "Types": ["bl"],
                    "bl":{"Realizations": ["1","2","3","4","5","6","7","8","9","10"]}
                }
            }
        },

        "United States": {
            "Faults":["San Andreas","Hayward"],
            "San Andreas": {
                "Magnitudes": ["7.8","8.0"],
                "7.8":{
                    "Types": ["tr"],
                    "tr":{"Realizations": ["1","2","3","4"]}
                },
                "8.0":{
                    "Types": ["bl","hf"],
                    "hf":{"Realizations": ["1","2","3","4","5","6","7","8","9","10"]},
                    "bl":{"Realizations": ["1","2","3","4","5"]}
                }
            },
            "Hayward": {
                "Magnitudes": ["7.0"],
                "7.0":{
                    "Types": ["tr"],
                    "tr":{"Realizations": ["1","2","3","4","5","6","7","8","9","10"]}
                }
            }
        }

    }


    # ===================================================================================
    # Styles
    # ===================================================================================

    button_style = """
            QPushButton {
                background-color: #2196F3;  /* Blue background */
                color: white;  /* White text */
                border: 2px solid #0b7dda;  /* Darker blue border */
                border-radius: 6px;  /* Rounded corners */
                padding: 6px;  /* Padding for a raised effect */
                font-weight: bold;
                /* Add a gradient to simulate light */
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4fc3f7, stop: 1 #2196F3
                );
            }
            QPushButton:pressed {
                background-color: #1976D2;  /* Darker blue when pressed */
                border: 2px solid #0b7dda;  /* Same border but a different shade */
                /* Inset effect when pressed */
                padding-top: 8px;
                padding-left: 8px;
            }
            QPushButton:hover {
                background-color: #64b5f6;  /* Lighter blue on hover */
            }
        """

    table_style = """
            QTableWidget {
                border: 3px solid #2196F3;  /* Outline border color */
                border-radius: 10px;  /* Rounded corners for the outline */
                padding: 5px;  /* Optional padding */
            }
            QTableWidget::item {
                padding: 10px;  /* Cell padding */
            }
            QHeaderView::section {
                color: black;
                background-color: lightgray;
                padding: 4px;
                border: 1px solid #6c6c6c;
                border-radius: 4px;
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #dcdcdc
                );
                font-weight: bold;
                min-height: 30px;  /* Adjust this for header height */
            }
            QTableWidget::item:selected {
                background-color: #64b5f6;  /* Highlighted item background */
            }
            QTableWidget::item:hover {
                background-color: #e3f2fd;  /* Highlighted item on hover */
            }
                                                        """
    group_style = "QGroupBox { border: 2px solid gray; border-color: #FF17365D; margin-top: 20px; font-size: 18px; border-radius: 15px; padding: 20px 0px;}"
        
    tab_style = """
        QTabBar::tab {
            height: 60px; 
            background-color: #e0e0e0; 
            border: 2px solid #aaa; 
            border-bottom: none; 
            border-top-left-radius: 15px;  /* Increase radius for rounder look */
            border-top-right-radius: 15px; /* Increase radius for rounder look */
            padding: 10px;
            font-weight: bold;
            color: #333;
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #d3d3d3, stop: 1 #e7e7e7);
        }
        QTabBar::tab:hover {
            background-color: #d0d0d0;
            border-top-left-radius: 15px;  /* Maintain rounded corners on hover */
            border-top-right-radius: 15px; /* Maintain rounded corners on hover */
        }
        QTabBar::tab:selected {
            background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #b0b0b0, stop: 1 #d5d5d5); 
            color: #000;
            border: 4px solid #888; 
            border-bottom: none;
            border-top-left-radius: 10px;  /* Maintain rounded corners when selected */
            border-top-right-radius: 10px; /* Maintain rounded corners when selected */
        }
        QTabBar::tab:!selected {
            margin-top: 2px;
        }
    """

    drop_down_style = """
        QComboBox {
            padding: 10px 20px;  /* Increased padding for larger size */
            font-size: 20px;      /* Increased font size */
        }
      /* Style for the drop-down list */
    QComboBox QAbstractItemView {
        border: 2px solid #888;  /* Border for the list */
        border-radius: 10px;     /* Rounded corners for the list */
        background-color: #f7f7f7;  /* Background of the drop-down list */
        color: #333;  /* Text color */
        padding: 15px;  /* Increased padding for items */
        selection-background-color: #d5d5d5;  /* Background color when item is selected */
        selection-color: #000;  /* Text color for selected item */
        outline: none;  /* Remove the focus outline */
        font-size: 20px;
    }
    QComboBox QAbstractItemView::item {
        font-size: 20px;  /* Increased font size for drop-down list items */
        padding: 10px 20px;  /* Additional padding for items */
    }
    """

    grid_style = """           

            QLabel {
                font-weight: bold;  /* Bold labels */
                color: #333;  /* Dark gray text color */
                padding: 5px;  /* Padding around labels */
            }
            QLineEdit {
                border: 1px solid #ccc;  /* Light gray border */
                border-radius: 5px;  /* Rounded corners */
                background-color: #fff;  /* White background */
            }
        """



if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Arial",8)  # Replace "YourFontFamily" with the desired font family
    app.setFont(font)

    # Create and display the main window
    window = MainWindow()
    window.showMaximized()


    sys.exit(app.exec_())

