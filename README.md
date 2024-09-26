# Paratope Heatmap Wizard

**--- THIS MODULE IS A WORK IN PROGRESS AND IS SUBJECT TO CHANGE ---**

Leverages ANARCI and Parapred to detect the paratope of a given antibody and displays a labeled heatmap on the surface of the molecule in PyMOL, showing the probability of each residue being part of the paratope. The wizard can be interacted with in VR as well.

Tested on Ubuntu 22.04 and OpenSUSE Tumbleweed 20240910. VR interaction tested on Meta Quest 3.

## Installation
Prepare and activate a [conda environment](https://docs.anaconda.com/working-with-conda/environments/) with the following:
- Python 3.9
- [PyMOL](https://github.com/schrodinger/pymol-open-source)
- [ANARCI](https://github.com/oxpig/ANARCI?tab=readme-ov-file)
- [parapred-pytorch](https://github.com/alchemab/parapred-pytorch/tree/v1.0.2?tab=readme-ov-file) v1.0.2

Once all dependencies are installed, go ahead and run the `install.sh` script, which will install the wizard.

You can use the `uninstall.sh` script to remove the wizard.

## Usage
Use the wizard's interface to select a molecule, then click on the `Run` button. The wizard will display a heatmap on the surface of the molecule, with green indicating a high probability of being part of the paratope and red indicating a low probability. Labels in the form `(residue name, residue id, probability)` will be displayed on any residue whose probability is above the specified threshold.