from pymol import cmd

from .anarci_integration import compute_cdrs, ChainType
from .parapred_integration import score_cdr


def get_residues(selection: str) -> list[tuple[str, int]]:
    """Returns the sequence of the selection along with the residue IDs."""

    residues = []
    cmd.iterate(
        f"{selection} and name CA", "residues.append((oneletter, resi))", space=locals()
    )

    return residues


class Heatmap:
    """Handles heatmap creation and visualization."""

    default_prob_threshold = 0.3

    def __init__(self, molecule_name, antibody_selection, antigen_selection, selection_name, threshold):
        self.prob_threshold = threshold  # threshold for label visualization
        self.molecule_name = molecule_name  # the molecule to create the heatmap on
        self.antibody_selection = antibody_selection
        self.antigen_selection = antigen_selection
        self.selection_name = selection_name  # the selection name for the paratope
        self.annotated_cdrs = []  # CDRs annotated with probabilities

    def compute_scores(self, h_chain_ids, l_chain_ids):
        """Compute the probability for each CDR atom to belong to the paratope."""

        if not self.molecule_name:
            print("Error: molecule name not provided.")
            return

        if not h_chain_ids and not l_chain_ids:
            print("Error: no chains provided.")
            return

        # Identify the CDRs and feed them to Parapred
        print("Computing scores...")
        h_cdrs = []
        for id in h_chain_ids:
            chain_residues = get_residues(f"{self.molecule_name} and chain {id}")
            h_cdrs += compute_cdrs(chain_residues, id, ChainType.HEAVY)

        l_cdrs = []
        for id in l_chain_ids:
            chain_residues = get_residues(f"{self.molecule_name} and chain {id}")
            l_cdrs += compute_cdrs(chain_residues, id, ChainType.LIGHT)

        self.annotated_cdrs = []
        for cdr in h_cdrs + l_cdrs:
            self.annotated_cdrs.append(score_cdr(cdr))

    def create_heatmap(self):
        """Displays the heatmap on the protein structure."""

        print("Creating heatmap...")

        cmd.alter("all", "b = 0")
        cmd.color("grey", f"{self.molecule_name} and {self.antibody_selection}")
        cmd.color("tv_blue", f"{self.molecule_name} and {self.antigen_selection}")
        for cdr in self.annotated_cdrs:
            for residue in cdr.residues:
                cmd.alter(
                    f"%{self.molecule_name} and chain {residue.chain} and resi {residue.id}",
                    f"b = {residue.prob}",
                )

                if residue.prob > 0.5:
                    cmd.select(
                        "to_color",
                        f"%{self.molecule_name} and chain {residue.chain} and resi {residue.id}",
                        merge=1,
                    )

        # TODO check that the selection is not empty
        cmd.spectrum("b", "red_green", "to_color", 0.5, 1.0)
        cmd.delete("to_color")

    def create_labels(self):
        """Associate to each residue a label with the probability of being part of the paratope."""

        print("Creating labels...")

        cmd.label(self.molecule_name, "''")
        cmd.set("label_connector", True)

        for cdr in self.annotated_cdrs:
            for residue in cdr.residues:
                # Ignore residues with low probability
                if float(residue.prob) <= self.prob_threshold:
                    continue

                cmd.label(
                    f"%{self.molecule_name} and chain {residue.chain} and resi {residue.id} and name CA",
                    f'"({residue.name}, {residue.id}, {residue.prob:.2f})"',
                )

    def select_paratope(self):
        for cdr in self.annotated_cdrs:
            for residue in cdr.residues:
                # Ignore residues with low probability
                if float(residue.prob) <= self.prob_threshold:
                    continue

                cmd.select(
                    self.selection_name,
                    f"%{self.molecule_name} and chain {residue.chain} and resi {residue.id}",
                    merge=1,
                )

    def update_threshold(self, threshold):
        """Update the probability threshold and redraw the labels."""
        self.prob_threshold = threshold
        self.create_labels()
        cmd.delete(self.selection_name)
        self.select_paratope()

    def show_labels(self):
        """Show the labels on the protein structure."""

    def hide_labels(self):
        """Hide the labels on the protein structure."""
        cmd.hide("labels")

    def reset(self):
        cmd.label("all", "''")
        self.molecule_name = ""
        self.selection_name = ""
        self.annotated_cdrs = []
        self.prob_threshold = Heatmap.default_prob_threshold
