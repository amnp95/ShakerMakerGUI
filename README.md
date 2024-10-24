# ShakerMaker

ShakerMaker is an application designed for earthquake engineers and seismologists. It utilizes the frequency-wavenumber (FK) method to produce ground-motion datasets for analysis with the Domain Reduction Method (DRM). The core FK method is implemented in Fortran with f2py wrappers, allowing for efficient computation and integration into a Python-based GUI.

## Features

- Load and manage fault database metadata.
- Download and organize fault information and related files.
- Interactive GUI for selecting input parameters and visualizing results.
- Support for various fault models and simulation parameters.
- Easy integration with external files and sources.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ShakerMaker.git
   ```

2. Navigate to the project directory:
   ```bash
   cd ShakerMaker
   ```

3. **Install required dependencies**:
   You can install the required dependencies using either `pip` or `conda`.

   - **Using pip**:
     ```bash
     pip install -r requirements.txt
     ```

   - **Using conda**:
     Create a new conda environment and install the dependencies:
     ```bash
     conda env create -f environment.yml
     ```

## Usage

1. Launch the application:
   ```bash
   python ShakerMakerGUI.py
   ```
<!--
2. Set the working directory in the GUI.

3. Select the desired parameters for the fault model (country, fault type, magnitude, etc.).

4. Click the "Load Database" button to retrieve fault information.

5. Use the application to analyze ground-motion datasets based on the loaded parameters.

## Code Overview

- `load_database`: Loads the fault database and manages file downloads.
- `update_database`: Updates the metadata for available countries and faults.
- `find_button_location_and_browse`: Opens a file dialog to select files.
- `remove_table_row`: Removes a row from the file table in the GUI.
- `choose_file`: Allows users to select files for metadata and time functions.

## Contributing

Contributions are welcome! If you would like to contribute to ShakerMaker, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your message here"
   ```
4. Push to your branch:
   ```bash
   git push origin feature/YourFeatureName
   ```
5. Create a pull request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Requests](https://docs.python-requests.org/en/master/) for handling HTTP requests.
- [PyQt5](https://riverbankcomputing.com/software/pyqt/intro) for creating the GUI.
- [Fortran](https://fortran-lang.org/) for implementing the FK method.

## Contact

For any questions or suggestions, please reach out to [your email@example.com].

- pyvista
- pyvistaqt
- pyproj
- geopandas
- plotly
- geopy
