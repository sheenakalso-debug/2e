"""Turn an evolved genome back into fold instructions a human could follow."""

from __future__ import annotations

from .genome import Genome


def describe(genome: Genome) -> str:
    span_cm = genome.wingspan_m * 100
    chord_cm = genome.wing_chord_m * 100

    if genome.wingspan_m > 0.20:
        wing_note = "wide glider wings"
    elif genome.wingspan_m < 0.13:
        wing_note = "narrow dart wings"
    else:
        wing_note = "standard wings"

    if genome.nose_angle_deg < 25:
        nose_note = "sharp, pointed nose"
    elif genome.nose_angle_deg > 45:
        nose_note = "blunt, rounded nose"
    else:
        nose_note = "medium taper nose"

    layers = round(genome.fold_layers)
    weight_note = (
        f"add {genome.nose_weight * 100:.0f}% extra nose weight "
        f"(a strip of tape or {layers} extra fold{'s' if layers != 1 else ''})"
    )

    lines = [
        f"- Wings: {wing_note}, span {span_cm:.1f} cm, chord {chord_cm:.1f} cm",
        f"- Nose: {nose_note} ({genome.nose_angle_deg:.0f} deg taper), "
        f"folded over {layers} time{'s' if layers != 1 else ''}",
        f"- Nose weight: {weight_note}",
        f"- Dihedral: fold both wingtips up {genome.dihedral_deg:.0f} deg "
        "from the centerline for roll stability",
        f"- Trim: bend the trailing edge flaps {abs(genome.trim_deg):.1f} deg "
        f"{'up' if genome.trim_deg >= 0 else 'down'} to set the glide angle",
    ]
    return "\n".join(lines)
