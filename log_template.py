from string import Template

target_tpl = Template(
    "=========================================\n"
    "Target set, ${target}\n"
    "Target distance  : ${target_distance} m\n"
    "Target levitation: ${target_levitation} mil\n"
    "Target direction : ${target_direction}°\n"
    "=========================================\n"
)

aim_tpl = Template(
    "Aiming...\n"
    "Levitation: ${levitation} mil ==>> ${target_levitation} mil\n"
    "Direction : ${direction}° (${direction_calculated}°) ==>> ${target_direction}° (${target_direction_calculated}°)\n"
    "=========================================\n"
)


def get_target_string(arty):
    return target_tpl.substitute(
        target=arty.target,
        target_distance=arty.target_distance,
        target_levitation=arty.target_levitation,
        target_direction=arty.target_direction,
    )
    pass


def get_aim_string(arty):
    direction_calculated = round((arty.direction - 47) % 360, 1)
    target_direction_calculated = round((arty.target_direction - 47) % 360, 1)

    return aim_tpl.substitute(
        levitation=arty.levitation,
        target_levitation=arty.target_levitation,
        direction=arty.direction,
        direction_calculated=direction_calculated,
        target_direction=arty.target_direction,
        target_direction_calculated=target_direction_calculated,
    )
