from __future__ import annotations

from .constants import SW_BODY_TYPE_SOLID


def get_solid_bodies(model):
    bodies = model.GetBodies2(SW_BODY_TYPE_SOLID, True)
    return list(bodies or [])


def get_all_faces(model):
    result = []
    for body_index, body in enumerate(get_solid_bodies(model)):
        for face_index, face in enumerate(body.GetFaces() or []):
            surface = face.GetSurface()
            result.append(
                {
                    "body_index": body_index,
                    "face_index": face_index,
                    "face": face,
                    "area_m2": face.GetArea(),
                    "edge_count": face.GetEdgeCount(),
                    "is_plane": bool(surface.IsPlane()),
                    "is_cylinder": bool(surface.IsCylinder()),
                    "is_cone": bool(surface.IsCone()),
                    "is_sphere": bool(surface.IsSphere()),
                }
            )
    return result


def summarize_faces(model):
    return [
        {k: v for k, v in face.items() if k != "face"}
        for face in get_all_faces(model)
    ]
