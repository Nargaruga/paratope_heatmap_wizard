from pymol import cmd

from . import anarci_integration
from . import parapred_integration


def get_sequence_and_ids(selection: str) -> tuple[str, list[int]]:
    """Returns the sequence of the selection along with the residue IDs."""

    fasta_str = cmd.get_fastastr(selection)
    # Remove the header line and join the rows
    sequence = "".join(fasta_str.split("\n")[1:])
    # Get the list of residues and their IDs from the selection
    res_ids = []
    cmd.iterate(selection, "res_ids.append((resi))", space=locals())
    # Remove duplicates residue ids (as "iterate" iterates over all atoms, not residues)
    res_ids = list(dict.fromkeys(res_ids))

    return sequence, res_ids


class Heatmap:
    """Handles heatmap creation and visualization."""

    default_prob_threshold = 0.3

    def __init__(self, molecule_name, threshold):
        self.prob_threshold = threshold  # threshold for label visualization
        self.molecule_name = molecule_name  # the molecule to create the heatmap on
        self.annotated_cdrs = []  # CDRs annotated with probabilities

    def compute_scores(self):
        """Compute the probability for each CDR atom to belong to the paratope."""

        if not self.molecule_name:
            print("Error: molecule name not provided.")
            return

        print("Computing scores...")

        # Identify the CDRs and feed them to Parapred
        h_chain_seq, h_chain_ids = get_sequence_and_ids(
            f"{self.molecule_name} and chain H"
        )
        l_chain_seq, l_chain_ids = get_sequence_and_ids(
            f"{self.molecule_name} and chain L"
        )
        try:
            h_cdrs = anarci_integration.compute_cdrs(h_chain_seq, h_chain_ids, "H")
            l_cdrs = anarci_integration.compute_cdrs(l_chain_seq, l_chain_ids, "L")
            self.annotated_cdrs = parapred_integration.score_cdrs(h_cdrs + l_cdrs)
        except (anarci_integration.AnarciError, FileNotFoundError):
            print("Error: could not compute CDRs or scores.")
            raise

    def create_heatmap(self):
        """Displays the heatmap on the protein structure."""

        print("Creating heatmap...")

        cmd.alter("all", "b = 0")
        for cdr in self.annotated_cdrs:
            for residue in cdr.residues:
                score_int = int(residue.prob * 100)
                cmd.alter(
                    f"%{self.molecule_name} and chain {residue.chain} and resi {residue.id}",
                    f"b = {score_int}",
                )

        cmd.spectrum("b", "red_green", self.molecule_name, 0, 100)

    def create_labels(self):
        """Associate to each residue a label with the probability of being part of the paratope."""

        print("Creating labels...")

        cmd.label("all", "''")
        cmd.set("float_labels", True)
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

    def update_threshold(self, threshold):
        """Update the probability threshold and redraw the labels."""
        self.prob_threshold = threshold
        self.create_labels()

    def show_labels(self):
        """Show the labels on the protein structure."""

    def hide_labels(self):
        """Hide the labels on the protein structure."""
        cmd.hide("labels")

    def reset(self):
        cmd.label("all", "''")
        self.molecule_name = ""
        self.annotated_cdrs = []
        self.prob_threshold = Heatmap.default_prob_threshold