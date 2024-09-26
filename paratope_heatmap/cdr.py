from dataclasses import dataclass, field


@dataclass
class Residue:
    name: str
    id: int
    chain: str
    prob: float


@dataclass
class CDR:
    residues: list[Residue] = field(default_factory=list)

    def get_sequence(self):
        """Returns the sequence associated with the CDR."""
        return "".join([res.name for res in self.residues])
