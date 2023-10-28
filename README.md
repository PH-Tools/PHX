# PHX (Passive House Exchange):

### The Passive House Exchange (PHX) package enables users to move building model data into and out of the Passive House energy modeling software platforms (PHPP or WUFI-Passive).

PHX is a converter which accepts [HBJSON](https://github.com/ladybug-tools/honeybee-schema/wiki) files, converts all the data into 'PH-Style', and then manages the data-input to the proprietary PH-Calculators like PHPP and WUFI-Passive. PHX 'models' are not written directly, but instead created based on a 'source' file like a HBJSON.

PHX itself does not have serialization / deserialization, and is not intended to be stored or written directly: it is an in-memory-only model which is created as a middle-step when moving the building data from the source (usually a HBJSON file) to the destination (PHPP, WUFI-Passive).

This library is designed to be used as part of the [Honeybee-PH plugin](https://github.com/PH-Tools/honeybee_ph) workflow, or other similar tools which require interfacing with the Passive House modeling platforms.

<img width="1692" alt="Screen Shot 2023-10-28 at 11 53 01 AM" src="https://github.com/PH-Tools/PHX/assets/69652712/03ff5cfa-4a81-4077-b475-e35b39190640">

## Packages:

- **from_HBJSON:** Modules used to create a new PHX model from an existing HBJSON file which has been created using the [Honeybee-PH plugin](https://github.com/PH-Tools/honeybee_ph).

- **from_WUFI_XML:** Modules used to create a new PHX model from an existing WUFI-Passive XML file.

- **from_PHPP:** Modules used to create a new PHX model from an existing PHPP file.'

- **model:** The PHX model classes and structures. These objects are designed to be built by one of the 'from\_\*' libraries above.

- **to_PHPP:** Libraries to allow for the export of PHX data to a PHPP Microsoft Excel spreadsheet.

- **to_WUFI_XML:** Libraries to allow for the export of a WUFI-Passive XML file with all of the PHX model data. This XML file can then be opened from within the WUFI-Passive application.

# More Information:

For more information on the use of these tools, check out the the Passive House Tools website:
http://www.PassiveHouseTools.com

![Tests](https://github.com/PH-Tools/PHX/actions/workflows/ci.yaml/badge.svg)
![versions](https://img.shields.io/pypi/pyversions/pybadges.svg)
