# CoastalMappingTools

Tools conducting topological and topographical analysis of coasts. Developed for the (Dynamic Coast Project)[www.dynamiccoast.com]. 

## Installation

### Install Python

To run the toolbox you first need to install the required Python packages in an environment. If you don't already have it, **Anaconda** can be downloaded freely [here](https://www.anaconda.com/download/).

Once you have Anaconda installed on your PC, we will work from a command line:
- Windows: open the Anaconda Prompt (not Powershell)
- Mac and Linux: open a terminal window

### Download the code
You can download the tools either by clicking the <span style="color:white;background-color:#2EA043;">Code</span> button at the top and downloading + extracting the zipped folder, or by navigating to where you want to download it on your local machine and running at a terminal command line (or Anaconda Prompt on Windows):

```
git clone https://github.com/mdhurst1/CoastalMappingTools.git
```

### Create a conda enviroment

Navigate to the folder with the repository files. If you downloaded the code zip file manually, it's recommended you extract the files to a new local folder rather than keeping it in your Downloads!
```
cd CoastalMappingTools
```
Create a new `conda` environment named `coastlearn` with all the required packages by entering this command (make sure you're in the repo folder!):

```
conda env create -f ./conda_env/environment.yml
```
Please note that solving and building the environment can take some time (minutes to hours depending on the the nature of your base environment). Once this step is complete, all the required packages will have been installed in an environment called `CMT`. Always make sure that the environment is activated with:

```
conda activate CMT
```

## Some Basic Applications

### Generate shore-normal transects

### Genereate topographic cross sections

### Analyse barrier morphology

### Conduct shoreline change analysis

The repository contains a worked example demonstrating the Coastal Mapping Tools workflow using data from **Montrose Bay, Scotland**. The example takes historical shoreline observations, analyses historical shoreline change, and generates future shoreline predictions under sea-level rise scenarios using a calibrated Bruun-rule approach.

### Prerequisites

Before running the example, ensure you have:

* Cloned the repository.
* Created and activated the required Python environment.

### Running the example

From the repository root, run:

```bash
python examples/Montrose_Example_Driver.py
```

### What the example does

The driver demonstrates a complete future coastal change analysis workflow, including:

1. Loading the Montrose example datasets.
2. Building coastal transects and MHWS shoreline time series.
3. Calculating historical shoreline change rates using the available regression methods (including Time-Weighted Regression by default).
4. Predicting future shoreline positions using a modified Bruun rule approach and future sea-level rise scenarios from UKCP18.
5. Writing example outputs for visualisation and further analysis.

### Outputs

Example outputs are written to the `results/` directory (ignored by Git) and may include:

* Predicted shoreline positions.
* Shoreline change rates.
* GIS layers (e.g. Shapefiles/GeoPackages).
* Raster outputs (where applicable).
* Diagnostic plots and figures.

### Notes

This example is intended as a reference workflow for developing and testing new functionality. As the `Future-Updating` branch is under active development, file formats and outputs may change as the prediction framework evolves.


Description goes here.
