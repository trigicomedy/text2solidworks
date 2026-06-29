# Assembly Runtime Modules

Date: 2026-06-29

The assembly runtime is intentionally separated from part modeling modules by
using the `assembly_*.py` prefix. Assembly code should focus on document
creation, component insertion, component references, mates, and validation. It
should not create part geometry directly.

## Modules

### `assembly_documents.py`

Responsibilities:

- find an assembly template;
- create a new assembly document;
- open an existing assembly;
- save an assembly;
- activate an open document;
- read a document title across COM property/method variants.

Primary functions:

```python
new_assembly(sw_app, template_path=None)
open_assembly(sw_app, path, silent=True)
save_assembly(assembly, path)
activate_document(sw_app, title)
document_title(model)
```

### `assembly_components.py`

Responsibilities:

- insert part files into an assembly;
- use the already validated AddComponent/AddComponent5 fallback pattern;
- open parts before insertion when required by SW2025;
- list and find components.

Primary functions:

```python
add_component(sw_app, assembly, part_path, name=None, xyz_mm=(0, 0, 0))
list_components(assembly, top_level_only=True)
get_component(assembly, name)
component_name(component)
fix_component(component)
float_component(component)
```

### `assembly_references.py`

Responsibilities:

- represent a planned mate reference as structured data;
- select a named datum/feature inside a component instance;
- hide SolidWorks reference-string details from the skill layer.

Primary data model:

```python
AssemblyRef(component="upper_arm", entity_type="axis", name="AXIS_INPUT")
```

Observed SW2025 reference string:

```text
ref_name@ComponentInstance@AssemblyTitle
```

The wrapper also tries several fallback forms because component instance names
and unsaved assembly titles can vary.

### `assembly_mates.py`

Responsibilities:

- create native SolidWorks mates from selected component references;
- provide typed wrappers for common mate kinds;
- try AddMate5, AddMate3, and AddMate2 in order.

Primary functions:

```python
mate_coincident(assembly, name, ref_a, ref_b)
mate_concentric(assembly, name, ref_a, ref_b)
mate_parallel(assembly, name, ref_a, ref_b)
mate_distance(assembly, name, ref_a, ref_b, distance_mm)
mate_angle(assembly, name, ref_a, ref_b, angle_deg)
```

### `assembly_validation.py`

Responsibilities:

- summarize top-level components;
- best-effort count mates;
- assert required components exist;
- reserve a future entry point for native interference checking.

Primary functions:

```python
summarize_assembly(assembly)
count_mates(assembly)
assert_components_present(assembly, names)
check_interference_placeholder(assembly)
```

## Planned Skill Output Shape

The design/connection skill should prefer semantic references, not raw
SolidWorks selection strings:

```json
{
  "name": "mate_shoulder_to_upper_arm_axis",
  "type": "concentric",
  "a": {"component": "shoulder_housing", "entity_type": "axis", "name": "AXIS_OUTPUT"},
  "b": {"component": "upper_arm", "entity_type": "axis", "name": "AXIS_INPUT"}
}
```

Runtime maps this to:

1. `AssemblyRef(...)`
2. `select_component_reference(...)`
3. `mate_concentric(...)`

## Current Validation Status

Implemented but not yet fully sample-validated as standalone modules:

- `assembly_documents.py`
- `assembly_components.py`
- `assembly_references.py`
- `assembly_mates.py`
- `assembly_validation.py`

The implementation is based on previously successful code in
`examples/create_6dof_robot_arm.py`, especially:

- AddComponent/AddComponent5 fallback insertion;
- component reference selection using `ref@Component@AssemblyTitle`;
- AddMate5/AddMate3/AddMate2 fallback creation.

Next validation target:

1. create two simple block parts with named planes/axes;
2. insert both into a new assembly;
3. create one coincident plane mate and one concentric axis mate;
4. save the resulting SLDASM;
5. record successful API signatures in this document.
