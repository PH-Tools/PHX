# -*- Python Version: 3.10 -*-

"""DEV SANDBOX: convert an HBJSON file over to METr JSON format."""

import pathlib

from rich import print as rich_print

from PHX.from_HBJSON import create_project, read_HBJSON_file
from PHX.to_METr_JSON import metr_builder, metr_json_to_file
from tests.conftest import _reset_phx_class_counters

# -- For PyTest files
SOURCE_DIR = pathlib.Path("tests", "reference_files", "from_grasshopper_tests", "hbjson")
SOURCE_FILE_NAMES = [
    "Default_Model_Single_Zone.hbjson",
    "Multi_Room_Complete.hbjson",
]
SOURCE_FILES = [SOURCE_DIR / file for file in SOURCE_FILE_NAMES]
TARGET_DIR = pathlib.Path("tests", "reference_files", "from_hb_json_tests", "metr_json")


def generate_metr_json_file(_source: pathlib.Path, _target_dir: pathlib.Path):
    # -- Re-set all the PHX modules (counters)
    _reset_phx_class_counters()

    target_file = pathlib.Path(_target_dir, _source.stem + ".json")

    # --- Read in an existing HB_JSON and re-build the HB Objects
    # -------------------------------------------------------------------------
    rich_print("[bold green]- [/bold green]" * 50)
    rich_print(f"[bold green]> Reading in the HBJSON file: ./{_source}[/bold green]")
    hb_json_dict = read_HBJSON_file.read_hb_json_from_file(_source)
    hb_model = read_HBJSON_file.convert_hbjson_dict_to_hb_model(hb_json_dict)

    # --- Generate the PhxProject file.
    # -------------------------------------------------------------------------
    rich_print(f"[bold]> Generating PHX Project from Honeybee Model: [{hb_model}][/bold]")
    phx_project = create_project.convert_hb_model_to_PhxProject(hb_model, _group_components=True, _merge_faces=True)

    # --- Output the METr JSON file
    # -------------------------------------------------------------------------
    rich_print(f"[bold]> Generating METr JSON for the PHX Project: [{phx_project}][/bold]")
    metr_json_text = metr_builder.generate_metr_json_text(phx_project)

    rich_print(f"[bold]> Saving the METr JSON file to: ./{target_file}[/bold]")
    metr_json_to_file.write_metr_json_file(target_file, metr_json_text)
    rich_print(f"[bold green]> Done! ({len(metr_json_text):,} bytes)[/bold green]")


if __name__ == "__main__":
    for source_file in SOURCE_FILES:
        generate_metr_json_file(pathlib.Path(source_file), TARGET_DIR)
