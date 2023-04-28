# PHX (Passive House Exchange):
The Passive House Exchange (PHX) model standard and libraries enable users to move their building model data in and out of energy modeling software platforms such as the Passive House Planning Package (PHPP) and WUFI-Passive.

This library can be used as part of a [Honeybee-PH plugin](https://github.com/PH-Tools/honeybee_ph) workflow, or on its own using the command-line or other user-created GUI tools. Certain workflows have been created for use within the [Rhino-3D](https://www.rhino3d.com/) software which are the most typical workflow.

## Packages:
- **from_HBJSON:** Modules used to create a new PHX model from an existing HBJSON file which has been created using the [Honeybee-PH plugin](https://github.com/PH-Tools/honeybee_ph).

- **from_WUFI_XML:** Modules used to create a new PHX model from an existing WUFI-Passive XML file.

- **from_PHPP:** Modules used to create a new PHX model from an existing PHPP file.'

- **model:** The PHX model classes and structures. These objects are designed to be built by one of the 'from_*' libraries above.

- **to_PHPP:** Libraries to allow for the export of PHX data to a PHPP Microsoft Excel spreasheet.

- **to_WUFI_XML:** Libraries to allow for the export of a WUFI-Passive XML file with all of the PHX model data. This XML file can then be opened from within the WUFI-Passive application.

## Setting up a development environment with Docker
* Make sure you have [Docker installed](https://docs.docker.com/get-docker/) on your machine.
* Clone the repository to your local machine using Git. For example, you can run the following command in your terminal: 
`git clone https://github.com/PH-Tools/PHX.git `
* Navigate to the project directory:
`cd PHX`
* Create a Docker container:
` docker run -it --name phx-dev -v /opt/phx -v /$(pwd):/opt python:3.7 bash `
* Navigate to the project directory in the Docker contianer:
`cd opt`
* Install the required dependencies:
` pip install -r dev-requirements.txt && pip install -e . `
* Run the unit tests to make sure everything is working properly:
`pytest`
* Starts a Docker container 
`docker container start -i phx-dev `

# More Information:
For more information on the use of these tools, check out the the Passive House Tools website:
http://www.PassiveHouseTools.com

![Tests](https://github.com/PH-Tools/PHX/actions/workflows/ci.yaml/badge.svg )
![versions](https://img.shields.io/pypi/pyversions/pybadges.svg)
