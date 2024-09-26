from anarci import number

from .cdr import CDR, Residue


class AnarciError(Exception):
    pass


def compute_cdrs(sequence: str, ids: list[int], chain: str) -> list[CDR]:
    """Computes the CDRs of a given sequence of residues."""

    # Use ANARCI to number the input sequence with Chothia scheme
    numbering, _ = number(sequence, scheme="chothia")

    if numbering is False or len(numbering) == 0:
        raise AnarciError("ANARCI failed to number the sequence.")

    # Store the CDR sequences with two extra residues on each side
    # CDR1: from 26 to 32
    # CDR2: from 52 to 56
    # CDR3: from 95 to 102
    extended_cdr1_range = range(26 - 2, 32 + 2)
    extended_cdr2_range = range(52 - 2, 56 + 2)
    extended_cdr3_range = range(95 - 2, 102 + 2)
    extended_cdrs = [CDR(), CDR(), CDR()]

    for i, ((position, _), res_name) in enumerate(numbering):
        res = Residue(res_name, ids[i], chain, 0.0)

        if position in extended_cdr1_range:
            extended_cdrs[0].residues.append(res)
        if position in extended_cdr2_range:
            extended_cdrs[1].residues.append(res)
        if position in extended_cdr3_range:
            extended_cdrs[2].residues.append(res)

    return extended_cdrs
