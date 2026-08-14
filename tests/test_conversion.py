import json
from pathlib import Path

import pytest
from honeybee.model import Model
from honeybee.room import Room

from PHX import conversion
from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.model.project import PhxProject
from PHX.to_METr_JSON import metr_builder
from tests.conftest import _reset_phx_class_counters

REFERENCE_MODEL = Path(
    "tests",
    "reference_files",
    "from_grasshopper_tests",
    "hbjson",
    "Default_Model_Single_Zone.hbjson",
)


def _load_reference_model() -> Model:
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(REFERENCE_MODEL)
    return read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)


def _snapshot(project: PhxProject) -> str:
    return json.dumps(metr_builder.generate_metr_json_dict(project), sort_keys=True)


@pytest.mark.parametrize(
    "options",
    [
        {},
        {
            "group_components": False,
            "merge_faces": True,
            "merge_spaces_by_erv": True,
            "merge_exhaust_vent_devices": True,
        },
    ],
)
def test_from_honeybee_matches_legacy_converter(options) -> None:
    legacy_options = {f"_{key}": value for key, value in options.items()}

    _reset_phx_class_counters()
    legacy_project = create_project.convert_hb_model_to_PhxProject(_load_reference_model(), **legacy_options)
    legacy_snapshot = _snapshot(legacy_project)

    _reset_phx_class_counters()
    facade_project = conversion.from_honeybee(_load_reference_model(), **options)
    facade_snapshot = _snapshot(facade_project)

    assert facade_snapshot == legacy_snapshot


def test_from_honeybee_delegates_all_public_options(monkeypatch) -> None:
    hb_model = Model("delegation_test")
    expected_project = PhxProject()
    received = {}

    def fake_converter(model, **kwargs):
        received["model"] = model
        received["kwargs"] = kwargs
        return expected_project

    monkeypatch.setattr(conversion.create_project, "convert_hb_model_to_PhxProject", fake_converter)

    actual_project = conversion.from_honeybee(
        hb_model,
        group_components=False,
        merge_faces=0.01,
        merge_spaces_by_erv=True,
        merge_exhaust_vent_devices=True,
    )

    assert actual_project is expected_project
    assert received == {
        "model": hb_model,
        "kwargs": {
            "_group_components": False,
            "_merge_faces": 0.01,
            "_merge_spaces_by_erv": True,
            "_merge_exhaust_vent_devices": True,
        },
    }


def test_from_honeybee_rejects_wrong_input_type() -> None:
    with pytest.raises(TypeError, match=r"hb_model must be honeybee\.model\.Model; got builtins\.object"):
        conversion.from_honeybee(object())  # type: ignore[arg-type]


def test_from_honeybee_reports_missing_model_ph_properties(monkeypatch) -> None:
    hb_model = Model("missing_model_ph")
    monkeypatch.setattr(type(hb_model.properties), "ph", property(lambda _: None))

    with pytest.raises(
        conversion.MissingHoneybeePhPropertiesError,
        match=r"Model 'missing_model_ph'.*model\.properties\.ph",
    ):
        conversion.from_honeybee(hb_model)


def test_from_honeybee_reports_missing_room_ph_properties(monkeypatch) -> None:
    hb_room = Room.from_box("missing_room_ph", 5.0, 5.0, 3.0)
    hb_model = Model("room_extension_test", [hb_room])
    monkeypatch.setattr(type(hb_room.properties), "ph", property(lambda _: None))

    with pytest.raises(
        conversion.MissingHoneybeePhPropertiesError,
        match=r"Room 'missing_room_ph'.*rooms\['missing_room_ph'\]\.properties\.ph",
    ):
        conversion.from_honeybee(hb_model)
