from pymol.wizard import Wizard
from pymol import cmd

from . import paratope_heatmap


class Paratope(Wizard):
    """Wizard for displaying the paratope heatmap on a protein structure."""

    def __init__(self, _self=cmd):
        Wizard.__init__(self, _self)
        self.heatmap = None
        self.molecule = None  # the molecule to be used for the heatmap
        self.show_labels = (
            True  # whether to show the probability labels on the protein structure
        )
        self.prob_threshold = (
            0.8  # residues with probability below this threshold will not be labeled
        )

        self.populate_molecule_choices()
        self.populate_threshold_choices()

    def populate_molecule_choices(self):
        """Populate the menu with the available molecules in the session."""

        molecules = cmd.get_names("objects")
        self.menu["molecule"] = [[2, "Molecule", ""]]
        for m in molecules:
            self.menu["molecule"].append([
                1,
                m,
                'cmd.get_wizard().set_molecule("' + m + '")',
            ])

    def populate_threshold_choices(self):
        """Populate the menu with the available threshold choices."""

        self.menu["threshold"] = [[2, "Threshold", ""]]
        thresholds = [0.7, 0.8, 0.9]
        for threshold in thresholds:
            self.menu["threshold"].append([
                1,
                str(threshold),
                "cmd.get_wizard().set_threshold(" + str(threshold) + ")",
            ])

    def set_molecule(self, molecule):
        """Set the molecule to be used for the heatmap."""

        self.molecule = molecule
        cmd.refresh_wizard()

    def toggle_labels(self):
        """Toggle the visibility of the labels on the protein structure."""

        self.show_labels = not self.show_labels
        if self.show_labels:
            cmd.show("labels")
        else:
            cmd.hide("labels")
        cmd.refresh_wizard()

    def set_threshold(self, threshold):
        """Set the minimum threshold for showing probability labels."""

        self.prob_threshold = threshold
        if self.heatmap is not None:
            self.heatmap.update_threshold(threshold)
        cmd.refresh_wizard()

    def run(self):
        if self.molecule is None:
            print("Please select a molecule.")
            return

        self.heatmap = paratope_heatmap.Heatmap(self.molecule, self.prob_threshold)

        """Compute and visualize the paratope heatmap on the selected molecule."""
        try:
            self.heatmap.compute_scores()
        except (
            paratope_heatmap.anarci_integration.AnarciError,
            FileNotFoundError,
        ) as e:
            print(f"Error: {e}")
            return

        cmd.show_as("licorice", self.molecule)
        # TODO: avoid doing 3 separate loops
        self.heatmap.create_heatmap()
        self.heatmap.create_labels()
        self.heatmap.select_paratope()

        cmd.refresh_wizard()

    def get_panel(self):
        """Return the menu panel for the wizard."""

        if self.molecule is None:
            molecule_label = "Choose molecule"
        else:
            molecule_label = self.molecule

        threshold_label = "Threshold: " + str(self.prob_threshold)
        show_labels_label = f"Show Labels: {self.show_labels}"

        return [
            [1, "Paratope Heatmap", ""],
            [3, molecule_label, "molecule"],
            [3, threshold_label, "threshold"],
            [2, show_labels_label, "cmd.get_wizard().toggle_labels()"],
            [2, "Run", "cmd.get_wizard().run()"],
            [2, "Dismiss", "cmd.set_wizard()"],
        ]
