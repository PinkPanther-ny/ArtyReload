import math

SECOND_POSITION_OFFSET = -47


def get_angle_from_map(origin, target):
    cx, cy = origin
    px, py = target

    dx = px - cx
    dy = py - cy

    angle = math.degrees(math.atan2(-dy, dx))

    angle = (90 - angle) % 360 + SECOND_POSITION_OFFSET
    if angle < 0:
        angle += 360

    return angle


def get_distance_from_map(origin, target):
    cx, cy = origin
    px, py = target

    dx = px - cx
    dy = py - cy

    # 88 pixels per 200m block
    pixel_distance = math.sqrt(dx ** 2 + dy ** 2)
    distance = pixel_distance * (200 / 88)

    return distance


def shortest_turn_direction(current_dir, target_dir):
    """Determine the shortest turn direction and distance."""
    diff_inside = abs(target_dir - current_dir)
    diff_outside = 360 - max(target_dir, current_dir) + min(target_dir, current_dir)
    if target_dir < current_dir:
        if diff_inside < diff_outside:
            return 'A', diff_inside
        else:
            return 'D', diff_outside
    else:
        if diff_inside < diff_outside:
            return 'D', diff_inside
        else:
            return 'A', diff_outside
