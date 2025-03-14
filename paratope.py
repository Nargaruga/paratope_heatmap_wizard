import os
import pathlib

from pymol.wizard import Wizard
from pymol import cmd

from .paratope_heatmap import anarci_integration, heatmap


class Paratope(Wizard):
    """Wizard for displaying the paratope heatmap on a protein structure."""

    def __init__(self, _self=cmd):
        Wizard.__init__(self, _self)
        self.heatmap = None
        self.molecule = None  # the antibody
        self.heavy_chains: list[str] = []  # antibody heavy chain
        self.light_chains: list[str] = []  # antibody light chain
        self.selection_name = (
            None  # the name of the selection to be used for the heatmap
        )
        self.show_labels = (
            True  # whether to show the probability labels on the protein structure
        )
        self.distance_labels = (
            False  # whether to move the labels to the side of the residues
        )
        self.prob_threshold = (
            0.8  # residues with probability below this threshold will not be labeled
        )
        self.gradient = "red_green"  # the color gradient for the heatmap

        self.populate_molecule_choices()
        self.populate_threshold_choices()
        self.populate_gradient_choices()

    def populate_molecule_choices(self):
        """Populate the menu with the available molecules in the session."""

        molecules = cmd.get_names("objects")
        self.menu["molecule"] = [[2, "Molecule", ""]]
        for m in molecules:
            self.menu["molecule"].append(
                [
                    1,
                    m,
                    'cmd.get_wizard().set_molecule("' + m + '")',
                ]
            )

    def populate_chain_choices(self):
        """Populate the menu with the available chains in the selected molecule."""

        if self.molecule is None:
            print("Please select a molecule.")
            return

        chains = cmd.get_chains(self.molecule)
        self.menu["heavy_chain"] = [[2, "Heavy Chain", ""]]
        for c in chains:
            self.menu["heavy_chain"].append(
                [
                    1,
                    c,
                    'cmd.get_wizard().set_heavy_chain("' + c + '")',
                ]
            )

        self.menu["light_chain"] = [[2, "Light Chain", ""]]
        for c in chains:
            self.menu["light_chain"].append(
                [
                    1,
                    c,
                    'cmd.get_wizard().set_light_chain("' + c + '")',
                ]
            )

    def populate_threshold_choices(self):
        """Populate the menu with the available threshold choices."""

        self.menu["threshold"] = [[2, "Threshold", ""]]
        thresholds = [0.7, 0.8, 0.9]
        for threshold in thresholds:
            self.menu["threshold"].append(
                [
                    1,
                    str(threshold),
                    "cmd.get_wizard().set_threshold(" + str(threshold) + ")",
                ]
            )

    def populate_gradient_choices(self):
        """Populate the menu with the available gradient choices."""

        self.menu["gradient"] = [[2, "Gradient", ""]]
        gradients = ["red_green", "grey_green"]
        for gradient in gradients:
            self.menu["gradient"].append(
                [
                    1,
                    gradient,
                    "cmd.get_wizard().set_gradient('" + gradient + "')",
                ]
            )

    def toggle_labels(self):
        """Toggle the visibility of the labels on the protein structure."""

        self.show_labels = not self.show_labels
        if self.show_labels:
            cmd.show("labels")
        else:
            cmd.hide("labels")
        cmd.refresh_wizard()

    def toggle_label_pos(self):
        """Toggle the position of the labels on the protein structure."""

        self.distance_labels = not self.distance_labels
        if self.distance_labels:
            cmd.set("label_position", [10.0, 0.0, 1.75])
        else:
            cmd.set("label_position", [0.0, 0.0, 1.75])
        cmd.refresh_wizard()

    def set_molecule(self, molecule):
        """Set the molecule to be used for the heatmap."""

        self.molecule = molecule
        self.selection_name = f"{molecule}_paratope"
        self.populate_chain_choices()

        cmd.refresh_wizard()

    def set_heavy_chain(self, chain):
        """Set the heavy chain to be used for the heatmap."""

        if chain in self.heavy_chains:
            self.heavy_chains.remove(chain)
        else:
            self.heavy_chains.append(chain)

        cmd.refresh_wizard()

    def set_light_chain(self, chain):
        """Set the light chain to be used for the heatmap."""

        if chain in self.light_chains:
            self.light_chains.remove(chain)
        else:
            self.light_chains.append(chain)

        cmd.refresh_wizard()

    def set_selection_name(self, selection_name):
        """Set the name of the selection to be used for the heatmap."""

        self.selection_name = selection_name

    def set_threshold(self, threshold):
        """Set the minimum threshold for showing probability labels."""

        self.prob_threshold = threshold
        if self.heatmap is not None:
            self.heatmap.update_threshold(threshold)
        cmd.refresh_wizard()

    def set_gradient(self, gradient):
        """Set the color gradient for the heatmap."""

        self.gradient = gradient
        if self.heatmap is not None:
            self.heatmap.update_gradient(gradient)
        cmd.refresh_wizard()

    def run(self):
        """Compute and visualize the paratope heatmap on the selected molecule."""

        if self.molecule is None:
            print("Please select a molecule.")
            return

        if self.heavy_chains is None or self.light_chains is None:
            print("Please select both the heavy and light chain.")
            return

        self.heatmap = heatmap.Heatmap(
            self.molecule, self.selection_name, self.prob_threshold, self.gradient
        )
        try:
            weights_path = os.path.join(
                pathlib.Path(__file__).parent.resolve(),
                "paratope_extra",
                "parapred_pytorch.h5",
            )
            self.heatmap.compute_scores(
                weights_path, self.heavy_chains, self.light_chains
            )
        except (
            anarci_integration.AnarciError,
            FileNotFoundError,
        ) as e:
            print(f"Failed to identify paratope: {e}")
            raise

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

        heavy_chain_label = "Heavy Chains: "
        if self.heavy_chains:
            heavy_chain_label += ", ".join(self.heavy_chains)
        else:
            heavy_chain_label += "None"

        light_chain_label = "Light Chains: "
        if self.light_chains:
            light_chain_label += ", ".join(self.light_chains)
        else:
            light_chain_label += "None"

        threshold_label = f"Threshold: {str(self.prob_threshold)}"
        gradient_label = f"Gradient: {self.gradient}"
        show_labels_label = f"Show Labels: {self.show_labels}"
        distance_labels_label = f"Distance Labels: {self.distance_labels}"

        return [
            [1, "Paratope Heatmap", ""],
            [3, molecule_label, "molecule"],
            [3, heavy_chain_label, "heavy_chain"],
            [3, light_chain_label, "light_chain"],
            [3, threshold_label, "threshold"],
            [3, gradient_label, "gradient"],
            [2, show_labels_label, "cmd.get_wizard().toggle_labels()"],
            [2, distance_labels_label, "cmd.get_wizard().toggle_label_pos()"],
            [2, "Run", "cmd.get_wizard().run()"],
            [2, "Dismiss", "cmd.set_wizard()"],
        ]
