import yaml
from dataclasses import dataclass


@dataclass
class AntibodyChains:
    light_chains: list[str]
    heavy_chains: list[str]

    def serialize(self, outfile: str):
        """Serializes the antibody chains to a YAML file."""
        with open(outfile, "w") as f:
            yaml.dump(
                {
                    "light_chains": self.light_chains,
                    "heavy_chains": self.heavy_chains,
                },
                f,
                default_flow_style=False,
            )

    def deserialize(self, infile: str):
        """Deserializes the antibody chains from a YAML file."""
        with open(infile, "r") as f:
            data = yaml.safe_load(f)
            self.light_chains = data["light_chains"]
            self.heavy_chains = data["heavy_chains"]
