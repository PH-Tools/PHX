# to_PHPP
These modules are used to output a PHX model and all relevant building data to a Passive House Planning Package (PHPP) excel document.

# Usage:
1. Ensure that a valid PHPP Excel document is opened before using these export tools.
2. The modules here will find the 'active' excel document and write to it. To avoid conflicts and errors, it is recommended to close all other excel documents except the PHPP which you would like to write the data to. 
3. These modules will overwrite any existing data in the target PHPP file.
4. You must already own a copy of the PHPP for this export tool to write to. The PHPP file is not included along with the modules here. These modules only write to the PHPP. If you do not already have a copy of the PHPP, you can find more information here: [link](https://passivehouse.com/04_phpp/04_phpp.htm)

# Compatibility:

1. Currently, the PHPP exporter only supports Windows OS. Mac OS support is in development.
2. The current exporter is compatible with PHPP v9.6a. New formats will be supported once they are released.