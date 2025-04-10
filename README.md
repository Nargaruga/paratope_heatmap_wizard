# Paratope Heatmap Wizard
PyMOL wizard for paratope recognition. It leverages ANARCI and Parapred to detect the paratope of a given antibody and displays a labeled heatmap on the surface of the molecule in PyMOL, showing the probability of each residue being part of the paratope.

Tested on Ubuntu 22.04 and OpenSUSE Tumbleweed 20240910. VR interaction tested on Meta Quest 3.

## Installation
The wizard can be installed with the [Wizard Installer](https://github.com/Nargaruga/pymol_wizard_installer) tool.

## Usage
Use the wizard's interface to select a molecule, specify the light and heavy chain(s) and click the `Run` button. The wizard will display a gradient on the surface of the molecule, with green indicating a high probability of being part of the paratope and red indicating a low probability. Labels in the form `(residue name, residue id, probability)` will be displayed on any residue whose probability is above the specified threshold.
