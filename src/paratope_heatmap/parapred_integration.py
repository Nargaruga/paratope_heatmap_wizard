import os
import subprocess
import tempfile
import json
from .cdr import CDR


class ParapredError(Exception):
    """Custom exception for Parapred errors."""

    pass


def read_parapred_output(output_file) -> list[tuple[str, float]]:
    """Parses the output of Parapred."""

    try:
        data = json.load(output_file)
    except json.JSONDecodeError as e:
        raise ParapredError(f"error decoding Parapred output: {e.msg}")

    return list(data.values())[0]


def score_cdr(cdr: CDR) -> CDR:
    """Computes the probability for each CDR atom to be part of the paratope."""

    parapred_output = tempfile.NamedTemporaryFile(suffix=".json", delete=False)

    subprocess.run(
        f"conda run --no-capture-output --name parapred parapred predict {cdr.get_sequence()} -o {parapred_output.name}",
        shell=True,
    )

    annotated_sequence = read_parapred_output(parapred_output)
    for i, residue in enumerate(cdr.residues):
        residue.prob = float(annotated_sequence[i][1])

    parapred_output.close()
    os.remove(parapred_output.name)

    return cdr
