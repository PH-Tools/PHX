from math import radians
from honeybee.face import Face
from PHX.from_HBJSON.cleanup_merge_faces import are_touching


def test_are_touching_true():
    # Define two touching faces
    face1 = Face.from_vertices("face_1", [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])
    face2 = Face.from_vertices("face_2", [(0, 0, 0), (0, 1, 0), (0, 1, 1), (0, 0, 1)])

    # Check that the faces are touching
    assert are_touching(face1, face2, 0.01) == True


def test_are_touching_false():
    # Define two non-touching faces
    face1 = Face.from_vertices("f1", [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)])
    face2 = Face.from_vertices("f2", [(0, 0, 1), (0, 1, 1), (1, 1, 1), (1, 0, 1)])

    # Check that the faces are not touching
    assert are_touching(face1, face2, 0.01) == False
