"""Read-only validation for identities and references consumed by exporters."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

from PHX.model.components import PhxComponentAperture, PhxComponentOpaque
from PHX.model.geometry import PhxPolygon, PhxVertix
from PHX.model.hvac import PhxDeviceVentilation
from PHX.model.hvac.piping import PhxPipeElement
from PHX.model.identity import IdentityNamespace, IdentityNamespaces
from PHX.model.project import PhxProject, PhxVariant


class IdentityValidationTarget(str, Enum):
    """Export contracts with identity-bearing project references."""

    WUFI = "wufi"
    METR = "metr"
    PHPP = "phpp"


class IdentityIssueKind(str, Enum):
    """Stable categories emitted by identity validation."""

    DUPLICATE = "duplicate"
    DANGLING_REFERENCE = "dangling-reference"


@dataclass(frozen=True)
class IdentityIssue:
    """One duplicate identity or dangling reference in the project graph."""

    path: str
    namespace: IdentityNamespace
    value: int
    kind: IdentityIssueKind
    detail: str

    @property
    def sort_key(self) -> tuple[str, str, int, str, str]:
        return (str(self.namespace), self.kind, self.value, self.path, self.detail)

    def __str__(self) -> str:
        return f"{self.kind.value}: {self.path} -> {self.namespace!r} ID {self.value} ({self.detail})"


class IdentityValidationError(ValueError):
    """Aggregate error raised before an exporter consumes an invalid graph."""

    def __init__(self, target: IdentityValidationTarget, issues: list[IdentityIssue]):
        self.target = target
        self.issues = tuple(sorted(issues, key=lambda issue: issue.sort_key))
        message = f"{target.value} identity validation failed with {len(self.issues)} issue(s):\n- " + "\n- ".join(
            str(issue) for issue in self.issues
        )
        super().__init__(message)


@dataclass(frozen=True)
class _VariantGraph:
    """One reusable snapshot of the allocating/sorting variant accessors."""

    components: tuple[PhxComponentOpaque | PhxComponentAperture, ...]
    polygons: tuple[PhxPolygon, ...]
    vertices: tuple[PhxVertix, ...]


class _GraphValidator:
    def __init__(self, target: IdentityValidationTarget):
        self.target = target
        self.issues: list[IdentityIssue] = []
        self.members: dict[IdentityNamespace, dict[int, str]] = {}

    def add(self, namespace: IdentityNamespace, value: int, path: str) -> None:
        members = self.members.setdefault(namespace, {})
        if previous := members.get(value):
            self.issues.append(
                IdentityIssue(path, namespace, value, IdentityIssueKind.DUPLICATE, f"also used by {previous}")
            )
        else:
            members[value] = path

    def reference(
        self, namespace: IdentityNamespace, value: int | None, path: str, sentinels: tuple[int, ...] = ()
    ) -> None:
        if value is None or value in sentinels:
            return
        if value not in self.members.get(namespace, {}):
            self.issues.append(
                IdentityIssue(path, namespace, value, IdentityIssueKind.DANGLING_REFERENCE, "no matching object")
            )

    def validate(self, project: PhxProject) -> None:
        self._project_members(project)
        for variant_index, variant in enumerate(project.variants):
            owner = f"variants[{variant_index}]"
            self.add(IdentityNamespaces.VARIANTS, variant.id_num, owner)
            graph = self._variant_graph(variant)
            self._variant_members(variant, owner, graph)
            self._variant_references(variant, owner, graph)

    def _project_members(self, project: PhxProject) -> None:
        collections = [
            (IdentityNamespaces.ASSEMBLIES, "assembly_types", project.assembly_types.values()),
            (IdentityNamespaces.WINDOWS, "window_types", project.window_types.values()),
            (IdentityNamespaces.SHADES, "shade_types", project.shade_types.values()),
        ]
        if self.target is not IdentityValidationTarget.PHPP:
            collections.extend(
                (
                    (
                        IdentityNamespaces.VENTILATION_PATTERNS,
                        "utilization_patterns_ventilation",
                        project.utilization_patterns_ventilation.values(),
                    ),
                    (
                        IdentityNamespaces.OCCUPANCY_PATTERNS,
                        "utilization_patterns_occupancy",
                        project.utilization_patterns_occupancy.values(),
                    ),
                    (
                        IdentityNamespaces.LIGHTING_PATTERNS,
                        "utilization_patterns_lighting",
                        project.utilization_patterns_lighting.values(),
                    ),
                )
            )
        for namespace, label, values in collections:
            for index, value in enumerate(values):
                self.add(namespace, value.id_num, f"project.{label}[{index}]")

        if self.target in (IdentityValidationTarget.WUFI, IdentityValidationTarget.METR):
            for assembly_index, assembly in enumerate(project.assembly_types.values()):
                material_namespace = (IdentityNamespaces.MATERIALS, assembly.id_num)
                materials = [layer.material for layer in assembly.layers]
                materials.extend(assembly.exchange_materials)
                seen_objects: set[int] = set()
                for material_index, material in enumerate(materials):
                    if id(material) in seen_objects:
                        continue
                    seen_objects.add(id(material))
                    self.add(
                        material_namespace,
                        material.id_num,
                        f"project.assembly_types[{assembly_index}].materials[{material_index}]",
                    )

    def _variant_graph(self, variant: PhxVariant) -> _VariantGraph:
        components = tuple(variant.building.all_components)
        polygons: list[PhxPolygon] = []
        seen: set[int] = set()
        for component in components:
            for polygon in component.polygons:
                if id(polygon) not in seen:
                    seen.add(id(polygon))
                    polygons.append(polygon)
        vertices = () if self.target is IdentityValidationTarget.PHPP else tuple(variant.graphics3D.vertices)
        return _VariantGraph(components, tuple(polygons), vertices)

    def _variant_members(self, variant: PhxVariant, owner: str, graph: _VariantGraph) -> None:
        if self.target is not IdentityValidationTarget.PHPP:
            for zone_index, zone in enumerate(variant.zones):
                self.add((owner, IdentityNamespaces.ZONES), zone.id_num, f"{owner}.zones[{zone_index}]")
                for space_index, space in enumerate(zone.spaces):
                    self.add(
                        (owner, IdentityNamespaces.SPACES),
                        space.id_num,
                        f"{owner}.zones[{zone_index}].spaces[{space_index}]",
                    )

        for component_index, component in enumerate(graph.components):
            self.add(
                (owner, IdentityNamespaces.COMPONENTS),
                component.id_num,
                f"{owner}.components[{component_index}]",
            )

        for polygon_index, polygon in enumerate(graph.polygons):
            polygon_path = f"{owner}.polygons[{polygon_index}]"
            self.add((owner, IdentityNamespaces.POLYGONS), polygon.id_num, polygon_path)
        for vertex_index, vertex in enumerate(graph.vertices):
            self.add((owner, IdentityNamespaces.VERTICES), vertex.id_num, f"{owner}.vertices[{vertex_index}]")

        for collection_index, collection in enumerate(variant.mech_collections):
            collection_path = f"{owner}.mechanical_systems[{collection_index}]"
            if self.target is not IdentityValidationTarget.PHPP:
                self.add((owner, IdentityNamespaces.MECHANICAL_SYSTEMS), collection.id_num, collection_path)
            for device_index, device in enumerate(collection.devices):
                if self.target is IdentityValidationTarget.PHPP and not isinstance(device, PhxDeviceVentilation):
                    continue
                namespace = (owner, IdentityNamespaces.mechanical_devices(device.__class__))
                self.add(namespace, device.id_num, f"{collection_path}.devices[{device_index}]")
            if self.target is IdentityValidationTarget.PHPP:
                continue
            for duct_index, duct in enumerate(collection.vent_ducting):
                self.add((owner, IdentityNamespaces.DUCTS), duct.id_num, f"{collection_path}.ducts[{duct_index}]")
            for trunk_index, trunk in enumerate(collection.dhw_distribution_trunks):
                trunk_path = f"{collection_path}.pipe_trunks[{trunk_index}]"
                self.add((owner, IdentityNamespaces.PIPE_TRUNKS), trunk.id_num, trunk_path)
                self._pipe_element(owner, trunk.pipe_element, f"{trunk_path}.pipe_element")
                for branch_index, branch in enumerate(trunk.branches):
                    branch_path = f"{trunk_path}.branches[{branch_index}]"
                    self.add((owner, IdentityNamespaces.PIPE_BRANCHES), branch.id_num, branch_path)
                    self._pipe_element(owner, branch.pipe_element, f"{branch_path}.pipe_element")
                    for fixture_index, fixture in enumerate(branch.fixtures):
                        self._pipe_element(owner, fixture, f"{branch_path}.fixtures[{fixture_index}]")
            for pipe_index, pipe in enumerate(collection.dhw_recirc_piping):
                self._pipe_element(owner, pipe, f"{collection_path}.recirc_piping[{pipe_index}]")

    def _pipe_element(self, owner: str, pipe: PhxPipeElement, path: str) -> None:
        self.add((owner, IdentityNamespaces.PIPE_ELEMENTS), pipe.id_num, path)

    def _variant_references(self, variant: PhxVariant, owner: str, graph: _VariantGraph) -> None:
        for component_index, component in enumerate(graph.components):
            component_path = f"{owner}.components[{component_index}]"
            if isinstance(component, PhxComponentOpaque):
                self.reference(
                    IdentityNamespaces.ASSEMBLIES,
                    component.assembly_type_id_num,
                    f"{component_path}.assembly_type_id_num",
                    (-1,),
                )
            if isinstance(component, PhxComponentAperture):
                self.reference(
                    IdentityNamespaces.WINDOWS,
                    component.window_type_id_num,
                    f"{component_path}.window_type_id_num",
                    (-1,),
                )
                self.reference(
                    IdentityNamespaces.SHADES,
                    component.shade_type_id_num,
                    f"{component_path}.shade_type_id_num",
                    (-1,),
                )

        polygon_namespace = (owner, IdentityNamespaces.POLYGONS)
        vertex_namespace = (owner, IdentityNamespaces.VERTICES)
        for polygon in graph.polygons:
            polygon_path = f"{owner}.polygon[{polygon.id_num}]"
            for child_id in polygon.child_polygon_ids:
                self.reference(polygon_namespace, child_id, f"{polygon_path}.child_polygon_ids")
            if self.target is not IdentityValidationTarget.PHPP:
                for vertex_id in polygon.vertices_id_numbers:
                    self.reference(vertex_namespace, vertex_id, f"{polygon_path}.vertices")

        if self.target is not IdentityValidationTarget.PHPP:
            zone_namespace = (owner, IdentityNamespaces.ZONES)
            zone_ids = self.members.get(zone_namespace, {})
            for zone_index, zone in enumerate(variant.zones):
                for space_index, space in enumerate(zone.spaces):
                    space_path = f"{owner}.zones[{zone_index}].spaces[{space_index}]"
                    if space.has_ventilation_airflow:
                        self.reference(
                            IdentityNamespaces.VENTILATION_PATTERNS,
                            space.ventilation.schedule.id_num,
                            f"{space_path}.ventilation.schedule.id_num",
                            (0,),
                        )
                    self.reference(
                        IdentityNamespaces.OCCUPANCY_PATTERNS,
                        space.occupancy.schedule.id_num,
                        f"{space_path}.occupancy.schedule.id_num",
                        (0,),
                    )

            for collection_index, collection in enumerate(variant.mech_collections):
                if zone_ids:
                    self.reference(
                        zone_namespace,
                        collection.zone_coverage.zone_num,
                        f"{owner}.mechanical_systems[{collection_index}].zone_coverage.zone_num",
                    )

        for message in variant.ventilation_assignment_issues():
            if "references missing ventilation device ID" not in message:
                continue
            match = re.search(r"ID (\d+)", message)
            if match:
                self.issues.append(
                    IdentityIssue(
                        owner,
                        IdentityNamespaces.VENTILATION_REFERENCES,
                        int(match.group(1)),
                        IdentityIssueKind.DANGLING_REFERENCE,
                        message,
                    )
                )


def validate_project_identities(project: PhxProject, target: IdentityValidationTarget | str) -> None:
    """Raise one deterministic aggregate error when an export graph is invalid."""
    resolved_target = IdentityValidationTarget(target)
    validator = _GraphValidator(resolved_target)
    validator.validate(project)
    if validator.issues:
        raise IdentityValidationError(resolved_target, validator.issues)
