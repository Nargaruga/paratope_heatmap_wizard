import os
import subprocess
import re

from .cdr import CDR, Residue


class AnarciError(Exception):
    pass


def parse_line(line: str):
    """Parses a numbering line from ANARCI's stdout."""

    pattern = re.compile(r"([A-Z])\s([0-9]+)\s*([A-Z])?\s([A-Z])$")
    match = pattern.match(line)

    if match is None:
        return None

    return int(match.group(2)), str(match.group(4))


def compute_cdrs(sequence: str, ids: list[int], chain: str) -> list[CDR]:
    """Computes the CDRs of a given sequence of residues."""

    # Use ANARCI to number the input sequence with Chothia scheme
    if os.name == "nt":
        # Use Docker version
        res = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "anarci",
                "--scheme",
                "imgt",
                "-i",
                sequence,
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        numbering = [
            parse_line(line)
            for line in res.stdout.strip().splitlines()
            if line[0] != "#" and line != r"\\"
        ]

        numbering = [x for x in numbering if x is not None]
    else:
        from anarci import number

        numbering, _ = number(sequence, scheme="imgt")

    if numbering is False or len(numbering) == 0:
        raise AnarciError("ANARCI failed to number the sequence.")

    # Store the CDR sequences with two extra residues on each side
    if chain == "H":
        # CDR H1: from 27 to 37
        # CDR H2: from 57 to 64
        # CDR H3: from 107 to 117
        extended_cdr1_range = range(27 - 2, 37 + 3)
        extended_cdr2_range = range(57 - 2, 64 + 3)
        extended_cdr3_range = range(107 - 2, 117 + 3)
    elif chain == "L":
        # CDR L1: from 24 to 40
        # CDR L2: from 56 to 69
        # CDR L3: from 105 to 117
        extended_cdr1_range = range(24 - 2, 40 + 3)
        extended_cdr2_range = range(56 - 2, 69 + 3)
        extended_cdr3_range = range(105 - 2, 117 + 3)
    else:
        raise AnarciError(f"Unrecognized chain {chain}.")

    extended_cdrs = [CDR(), CDR(), CDR()]

    filtered = [
        (res_pos, res_name) for ((res_pos, _), res_name) in numbering if res_name != "-"
    ]

    for i, (res_pos, res_name) in enumerate(filtered):
        res = Residue(res_name, ids[i], chain, 0.0)

        if res_pos in extended_cdr1_range:
            extended_cdrs[0].residues.append(res)
        if res_pos in extended_cdr2_range:
            extended_cdrs[1].residues.append(res)
        if res_pos in extended_cdr3_range:
            extended_cdrs[2].residues.append(res)

    return extended_cdrs
