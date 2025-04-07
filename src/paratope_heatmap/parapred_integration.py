import os
import subprocess
import tempfile
import json
from .cdr import CDR


def read_parapred_output(output_file) -> list[str, float]:
    """Parses the output of Parapred."""

    try:
        data = json.load(output_file)
    except json.JSONDecodeError:
        print(f"Error decoding JSON Parapred output: {output_file}")
        raise

    return list(data.values())[0]


def score_cdr(cdr: CDR, parapred_dir: str) -> CDR:
    """Computes the probability for each CDR atom to be part of the paratope."""

    parapred_output = tempfile.NamedTemporaryFile(suffix=".json", delete=False)

    if os.name == "nt":
        prefix = ["powershell.exe"]
    else:
        prefix = ""

    subprocess.run(
        prefix
        + [
            "conda",
            "run",
            "--no-capture-output",
            "--name",
            "parapred",
            "python",
            "cli.py",
            "predict",
            cdr.get_sequence(),
            "-o",
            parapred_output.name,
        ],
        cwd=parapred_dir,
    )

    annotated_sequence = read_parapred_output(parapred_output)
    for i, residue in enumerate(cdr.residues):
        residue.prob = annotated_sequence[i][1]

    parapred_output.close()
    os.remove(parapred_output.name)

    return cdr
