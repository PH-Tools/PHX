# -*- Python Version: 3.10 -*-

"""Export-time transforms applied to a PhxProject before serialization.

WUFI-Passive XML and METr JSON carry psi-install only on the WindowType — the
aperture Component has no per-instance psi field. Apertures whose elements resolve
to per-edge psi-install values different from their window-type's therefore need a
*variant* window type at export time. This module synthesizes the minimal set of
deterministic, content-keyed variants and re-points the aperture components.

PHPP is NOT routed through this transform: it supports per-window-row psi-install
natively, so the PHPP writer reads the elements' resolved values directly.
"""

import hashlib
from copy import deepcopy

from PHX.model.components import PhxApertureElementPsiInstall, PhxComponentAperture
from PHX.model.constructions import PhxConstructionWindow
from PHX.model.project import PhxProject

# -- ISO 10077-2:2006 Annex F standard window size, used for the stored
# -- standard-window U-w (matches honeybee_ph_utils.iso_10077_1.build_standard_window).
_STANDARD_WINDOW_WIDTH_M = 1.23
_STANDARD_WINDOW_HEIGHT_M = 1.48


def _component_resolved_psi_install(
    _component: PhxComponentAperture,
) -> PhxApertureElementPsiInstall | None:
    """Return the single resolved psi-install shared by all the component's elements.

    Returns None if the component has no elements. Raises ValueError if the elements
    resolve to different values - such a component cannot reference one WindowType and
    should have been kept separate by 'unique_key' during merging.
    """
    if not _component.elements:
        return None

    resolved = {e.resolved_psi_install.unique_key: e.resolved_psi_install for e in _component.elements}
    if len(resolved) > 1:
        raise ValueError(
            f"Aperture component '{_component.display_name}' has elements with different "
            f"resolved psi-install values ({sorted(resolved.keys())}). Components must be "
            "psi-homogeneous - check 'PhxComponentAperture.unique_key' merging."
        )
    return next(iter(resolved.values()))


def _window_type_psi_values(_window_type: PhxConstructionWindow) -> tuple[float, float, float, float]:
    """The window-type's own per-edge psi-install values in (top, right, bottom, left) order."""
    return (
        _window_type.frame_top.psi_install,
        _window_type.frame_right.psi_install,
        _window_type.frame_bottom.psi_install,
        _window_type.frame_left.psi_install,
    )


def _adjusted_standard_window_u_value(_base: PhxConstructionWindow, _psi: PhxApertureElementPsiInstall) -> float:
    """The base type's U-w adjusted for the variant's psi-install deltas.

    The stored 'u_value_window' is a standard-window (1.23m x 1.48m) U-w that includes
    install heat loss. Rather than recomputing from scratch (the base value may come
    from a WUFI file, not from the ISO calc), adjust it by the exact delta:
    sum((psi_new - psi_base) * edge_length) / standard_window_area.
    """
    base_psi = _window_type_psi_values(_base)
    edge_lengths = (
        _STANDARD_WINDOW_WIDTH_M,  # top
        _STANDARD_WINDOW_HEIGHT_M,  # right
        _STANDARD_WINDOW_WIDTH_M,  # bottom
        _STANDARD_WINDOW_HEIGHT_M,  # left
    )
    delta = sum((new - old) * length for new, old, length in zip(_psi.values, base_psi, edge_lengths))
    return _base.u_value_window + delta / (_STANDARD_WINDOW_WIDTH_M * _STANDARD_WINDOW_HEIGHT_M)


def _build_window_type_psi_variant(
    _base: PhxConstructionWindow, _psi: PhxApertureElementPsiInstall
) -> PhxConstructionWindow:
    """A clone of the base window type with its per-edge psi-install values replaced.

    The identifier is content-keyed (base identifier + hash of the psi tuple) so
    repeated exports of the same model produce byte-identical identifiers. The
    display-name carries the values in readable t/r/b/l form for QA in the target UI.
    """
    variant = deepcopy(_base)
    psi_hash = hashlib.sha256(_psi.unique_key.encode("utf-8")).hexdigest()[:8]
    variant.identifier = f"{_base.identifier}__psi-{psi_hash}"
    variant.display_name = "{} [Psi-i {:.3f}/{:.3f}/{:.3f}/{:.3f}]".format(_base.display_name, *_psi.values)
    variant.frame_top.psi_install = _psi.top
    variant.frame_right.psi_install = _psi.right
    variant.frame_bottom.psi_install = _psi.bottom
    variant.frame_left.psi_install = _psi.left
    variant.u_value_window = _adjusted_standard_window_u_value(_base, _psi)
    return variant


def synthesize_window_type_psi_variants(_phx_project: PhxProject) -> None:
    """Give apertures with non-default resolved psi-install their own window-type variant.

    For each aperture component whose elements' resolved psi-install differs from its
    window-type's own values, get-or-create a content-keyed variant type and re-point
    the component. Apertures sharing a (base-type, psi-tuple) pair share one variant:
    M base types + K distinct non-default tuples => exactly M + K window types.

    Mutates the project in place. Idempotent: components already pointing at a variant
    whose values match their elements' are left alone. Models with no per-instance
    psi-install overrides are untouched (the no-op invariant).
    """
    variants_by_key: dict[tuple[int, str], PhxConstructionWindow] = {}

    for phx_variant in _phx_project.variants:
        for phx_component in phx_variant.building.opaque_components:
            for phx_aperture in phx_component.apertures:
                psi = _component_resolved_psi_install(phx_aperture)
                if psi is None:
                    continue
                base_type = phx_aperture.window_type
                if psi.values == _window_type_psi_values(base_type):
                    continue

                cache_key = (base_type.id_num, psi.unique_key)
                variant_type = variants_by_key.get(cache_key)
                if variant_type is None:
                    variant_type = _build_window_type_psi_variant(base_type, psi)
                    _phx_project.add_new_window_type(variant_type, _key=variant_type.identifier)
                    variants_by_key[cache_key] = variant_type

                phx_aperture.set_window_type(variant_type)
