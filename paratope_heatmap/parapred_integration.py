import os

import torch
from parapred.model import Parapred, clean_output
from parapred.cnn import generate_mask
from parapred.preprocessing import encode_batch

from .cdr import CDR


def score_cdrs(cdrs: list[CDR]):
    """Computes the probability for each CDR atom to be part of the paratope."""

    sequences = [cdr.get_sequence() for cdr in cdrs]

    # PyTorch's pack padded sequence function requires length sorting from longest to shortest
    sorted_cdr_strings = [
        cdr for cdr in sorted(sequences, key=lambda z: len(z), reverse=True)
    ]
    lookup_cdr = dict([(v, i) for i, v in enumerate(sorted_cdr_strings)])

    # Encoded is a tensor of (batch_size x features x max_length). so is mask.
    encoded, lengths = encode_batch(sorted_cdr_strings, max_length=40)
    mask = generate_mask(encoded, lengths)

    # Initialise the model and load pretrained weights
    model = Parapred()
    model.load_state_dict(
        torch.load(
            os.path.join(os.path.dirname(__file__), "../weights", "parapred_pytorch.h5")
        )
    )

    # Trigger evaluation mode and don't allow gradients to move around
    _ = model.eval()
    with torch.no_grad():
        probs = model(encoded, mask, lengths)

    # This cleans up probabilities that would have been predicted for the
    # padded positions, which we should ignore.
    probs = [clean_output(pr, lengths[i]).tolist() for i, pr in enumerate(probs)]

    # Map back to CDR sequence; remember that we submitted length-sorted strings
    mapped = [list(zip(sorted_cdr_strings[i], pr)) for i, pr in enumerate(probs)]

    # We need to re-order `mapped` back to the original (unsorted) ordering
    mapped = [mapped[lookup_cdr[s]] for s in sequences]

    # Convert to CDR objects
    for i, cdr in enumerate(cdrs):
        for j, res in enumerate(cdr.residues):
            res.prob = mapped[i][j][1]

    return cdrs
