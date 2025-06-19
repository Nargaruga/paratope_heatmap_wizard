import os
import pathlib
from enum import IntEnum, auto

from pymol.wizard import Wizard
from pymol import cmd
import threading

from paratope_heatmap import (
    anarci_integration,
    antibody_chains,
    parapred_integration,
    heatmap,
)


class ParatopeIdentificationError(Exception):
    pass


class WizardInputState(IntEnum):
    READY = auto()
    MOLECULE_SELECTED = auto()
    CHAINS_SELECTED = auto()


class WizardTaskState(IntEnum):
    IDLE = auto()
    IDENTIFYING_PARATOPE = auto()


class Paratope(Wizard):
    """Wizard for displaying the paratope heatmap on a protein structure."""

    def __init__(self, _self=cmd):
        Wizard.__init__(self, _self)
        self.input_state = WizardInputState.READY
        self.task_state = WizardTaskState.IDLE
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
        self.highlight = True

        self.init_cache()

        self.populate_molecule_choices()
        self.populate_threshold_choices()

    def get_prompt(self):  # type: ignore
        """Return the prompt for the current state of the wizard."""

        prompt = []
        if self.input_state == WizardInputState.READY:
            prompt.append("Select a molecule to continue.")
        elif self.input_state == WizardInputState.MOLECULE_SELECTED:
            prompt.append("Select the heavy and light chains to continue.")
        elif self.input_state == WizardInputState.CHAINS_SELECTED:
            prompt.append(
                f"Run to identify the paratope for {self.molecule} on chains {self.heavy_chains} and {self.light_chains}."
            )

        if self.task_state == WizardTaskState.IDENTIFYING_PARATOPE:
            prompt.append("Locating paratope, please wait...")

        return prompt

    def get_panel(self):  # type: ignore
        """Return the menu panel for the wizard."""

        # Title
        options = [[1, "Paratope Heatmap", ""]]

        # Molecule list
        if self.input_state >= WizardInputState.READY:
            if self.molecule is None:
                molecule_label = "Choose molecule"
            else:
                molecule_label = self.molecule

            options.append([3, molecule_label, "molecule"])

        # Chain lists
        if self.input_state >= WizardInputState.MOLECULE_SELECTED:
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

            options.append([3, heavy_chain_label, "heavy_chain"])
            options.append([3, light_chain_label, "light_chain"])

        # Settings
        threshold_label = f"Threshold: {str(self.prob_threshold)}"
        show_labels_label = f"Show Labels: {self.show_labels}"
        distance_labels_label = f"Distance Labels: {self.distance_labels}"
        options.extend(
            [
                [3, threshold_label, "threshold"],
                [2, show_labels_label, "cmd.get_wizard().toggle_labels()"],
                [2, distance_labels_label, "cmd.get_wizard().toggle_label_pos()"],
            ]
        )

        # Run button
        if self.input_state >= WizardInputState.CHAINS_SELECTED:
            options.append([2, "Run", "cmd.get_wizard().run()"])

        # Close button
        options.append(
            [2, "Dismiss", "cmd.set_wizard()"],
        )

        return options

    def update_input_state(self):
        """Update the state of the wizard based on the current inputs."""

        if self.molecule:
            self.input_state = WizardInputState.MOLECULE_SELECTED
        else:
            self.input_state = WizardInputState.READY
            return

        if self.heavy_chains or self.light_chains:
            self.input_state = WizardInputState.CHAINS_SELECTED

        cmd.refresh_wizard()

    def init_cache(self):
        """Create the cache directory if necessary."""

        self.cache_dir = os.path.join(
            pathlib.Path(__file__).parent.resolve(), ".paratope_wiz_cache"
        )
        os.makedirs(self.cache_dir, exist_ok=True)

    def fetch_cached_chains(self) -> antibody_chains.AntibodyChains:
        """Return the cached antibody chains for the current molecule."""

        chains = antibody_chains.AntibodyChains([], [])
        try:
            chains.deserialize(
                os.path.join(self.cache_dir, f"{self.molecule}_chains.yaml")
            )

        except FileNotFoundError:
            pass

        return chains

    def autocomplete(self):
        """Load the antibody heavy and light chains with from cache."""

        chains = self.fetch_cached_chains()
        self.heavy_chains = chains.heavy_chains
        self.light_chains = chains.light_chains
        self.update_input_state()

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
                    'cmd.get_wizard().toggle_heavy_chain("' + c + '")',
                ]
            )

        self.menu["light_chain"] = [[2, "Light Chain", ""]]
        for c in chains:
            self.menu["light_chain"].append(
                [
                    1,
                    c,
                    'cmd.get_wizard().toggle_light_chain("' + c + '")',
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

    def toggle_labels(self):
        """Toggle the visibility of the labels on the protein structure."""

        self.show_labels = not self.show_labels
        if self.show_labels:
            self.heatmap.show_labels()
        else:
            self.heatmap.hide_labels()
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
        self.autocomplete()
        self.update_input_state()

    def is_heavy_chain_selected(self, chain):
        """Check if the specified heavy chain was already selected."""

        return chain in self.heavy_chains

    def is_light_chain_selected(self, chain):
        """Check if the specified light chain was already selected."""

        return chain in self.light_chains

    def toggle_heavy_chain(self, chain):
        """Set the heavy chain to be used for the heatmap."""

        if self.is_heavy_chain_selected(chain):
            print(f"Removing heavy chain {chain}")
            self.heavy_chains.remove(chain)
        else:
            print(f"Adding heavy chain {chain}")
            self.heavy_chains.append(chain)

        self.update_input_state()

    def toggle_light_chain(self, chain):
        """Set the light chain to be used for the heatmap."""

        if self.is_light_chain_selected(chain):
            print(f"Removing light chain {chain}")
            self.light_chains.remove(chain)
        else:
            print(f"Adding light chain {chain}")
            self.light_chains.append(chain)

        self.update_input_state()

    def set_highlight(self, highlight):
        """Set whether to highlight the paratope on the protein structure."""

        self.highlight = highlight

    def set_selection_name(self, selection_name):
        """Set the name of the selection to be used for the heatmap."""

        self.selection_name = selection_name

    def set_threshold(self, threshold):
        """Set the minimum threshold for showing probability labels."""

        self.prob_threshold = threshold
        if self.heatmap is not None:
            self.heatmap.update_threshold(threshold)
        cmd.refresh_wizard()

    def run(self, block=False):
        """Compute and visualize the paratope heatmap on the selected molecule."""

        def aux():
            if self.molecule is None:
                print("Please select a molecule.")
                return

            if not self.heavy_chains and not self.light_chains:
                print("Please specify the antibody chains.")
                return

            chains = antibody_chains.AntibodyChains(
                light_chains=self.light_chains, heavy_chains=self.heavy_chains
            )
            chains.serialize(
                os.path.join((self.cache_dir), f"{self.molecule}_chains.yaml")
            )

            self.task_state = WizardTaskState.IDENTIFYING_PARATOPE
            cmd.refresh_wizard()

            heavy_chains_str = "none"
            for hc in self.heavy_chains:
                if heavy_chains_str == "none":
                    heavy_chains_str = f"chain {hc}"
                else:
                    heavy_chains_str += f" or chain {hc}"

            light_chains_str = "none"
            for lc in self.light_chains:
                if light_chains_str == "none":
                    light_chains_str = f"chain {lc}"
                else:
                    light_chains_str += f" or chain {lc}"

            antibody_selection = (
                f"{self.molecule} and ({heavy_chains_str} or {light_chains_str})"
            )
            antigen_selection = f"{self.molecule} and not ({antibody_selection})"
            self.heatmap = heatmap.Heatmap(
                self.molecule,
                antibody_selection,
                antigen_selection,
                self.selection_name,
                self.prob_threshold,
            )

            try:
                self.heatmap.compute_scores(self.heavy_chains, self.light_chains)
            except (
                anarci_integration.AnarciError,
                parapred_integration.ParapredError,
                FileNotFoundError,
            ) as e:
                print(f"Failed to identify paratope: {e}")
                self.task_state = WizardTaskState.IDLE
                self.update_input_state()
                return

            if self.highlight:
                self.heatmap.create_heatmap()
                self.heatmap.create_labels()
            self.heatmap.select_paratope()

            self.task_state = WizardTaskState.IDLE
            self.update_input_state()

        if block:
            aux()
        else:
            worker_thread = threading.Thread(
                target=aux,
            )
            worker_thread.start()
