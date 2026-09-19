"""Turn an evolved genome back into fold instructions a human could follow."""

from __future__ import annotations

from .genome import USABLE_AREA_M2, Genome


def describe(genome: Genome) -> str:
    span_cm = genome.wingspan_m * 100
    chord_cm = genome.wing_chord_m * 100
    fuselage_len_cm = genome.fuselage_length_m * 100
    fuselage_wid_cm = genome.fuselage_width_m * 100
    tail_cm = genome.tail_fin_height_m * 100

    if genome.wingspan_m > 0.24:
        wing_note = "wide glider wings"
    elif genome.wingspan_m < 0.14:
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
    cg_note = (
        f"concentrate {genome.nose_weight * 100:.0f}% of the fold near the nose "
        "(fold the nose section over on itself rather than the tail)"
    )

    paper_used_pct = 100 * genome.paper_area_m2() / USABLE_AREA_M2

    lines = [
        f"- Wings: {wing_note}, span {span_cm:.1f} cm, chord {chord_cm:.1f} cm, "
        f"swept back {genome.wing_sweep_deg:.0f} deg",
        f"- Fuselage: spine {fuselage_len_cm:.1f} cm long, {fuselage_wid_cm:.1f} cm wide",
        f"- Nose: {nose_note} ({genome.nose_angle_deg:.0f} deg taper), "
        f"folded over {layers} time{'s' if layers != 1 else ''}",
        f"- Weight balance: {cg_note}",
        f"- Dihedral: fold both wingtips up {genome.dihedral_deg:.0f} deg "
        "from the centerline for roll stability",
        f"- Tail fin: fold a vertical fin {tail_cm:.1f} cm tall at the back "
        "for yaw stability"
        if genome.tail_fin_height_m > 0.002
        else "- Tail fin: none",
        f"- Trim: bend the trailing edge flaps {abs(genome.trim_deg):.1f} deg "
        f"{'up' if genome.trim_deg >= 0 else 'down'} to set the glide angle",
        f"- Uses {paper_used_pct:.0f}% of one A4 sheet "
        f"(mass ~{genome.mass_kg() * 1000:.1f} g) -- fits on a single sheet, no tape needed",
    ]
    return "\n".join(lines)
