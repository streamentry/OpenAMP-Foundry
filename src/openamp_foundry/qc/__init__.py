"""Pre-synthesis QC layer for OpenAMP Foundry.

Flags risky peptides (DKP, pyroglutamate, oxidation, aggregation,
length, proline-rich) and generates vendor-ready synthesis orders.
"""

from openamp_foundry.qc.order_generator import (
    generate_synthesis_order,
    write_order_csv,
    write_synthesis_checklist,
)
from openamp_foundry.qc.presynth_check import (
    SynthQC,
    check_panel,
    check_sequence,
)

__all__ = [
    "SynthQC",
    "check_panel",
    "check_sequence",
    "generate_synthesis_order",
    "write_order_csv",
    "write_synthesis_checklist",
]
