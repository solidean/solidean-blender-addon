# #
#
#  Copyright (c) 2023-2026 Shaped Code GmbH.
#  Solidean is proprietary software. Use of this SDK is permitted only under an
#  applicable Solidean license (Community or Commercial). See LICENSE.txt.
#
#  You may redistribute these SDK headers and accompanying helper/source files
#  as permitted by the license; redistribution of Solidean core binary components
#  is not permitted without a Commercial License.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL
#  SHAPED CODE GMBH BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY.
#


# Solidean Python API
# This file is auto-generated. Do not modify manually.

import ctypes
import os
import sys
from enum import IntEnum, IntFlag
from functools import cached_property
from typing import Optional, Union, List, ForwardRef
from pathlib import Path

import numpy as np
from numpy.typing import NDArray


# =================================
#        Forward References
# =================================

Context = ForwardRef('Context')
ExactArithmetic = ForwardRef('ExactArithmetic')
MeshBuilder = ForwardRef('MeshBuilder')
Mesh = ForwardRef('Mesh')
Operation = ForwardRef('Operation')
SurfaceBuilder = ForwardRef('SurfaceBuilder')
Surface = ForwardRef('Surface')
TypedBlob = ForwardRef('TypedBlob')

# =================================
#            Type Aliases
# =================================
# Newtype wrappers around primitives

MeshOperand = ctypes.c_uint64

# =================================
#            DLL Loading
# =================================

def _load_dll():
    if sys.platform.startswith("win"):
        lib_name = "solidean.dll"
    elif sys.platform.startswith("darwin"):
        lib_name = "libsolidean.dylib"
    else:
        lib_name = "libsolidean.so"

    here = Path(__file__).resolve().parent
    lib_path = here / lib_name

    if not lib_path.is_file():
        raise RuntimeError(
            f"Could not find {lib_name} next to {Path(__file__).name}.\n"
            f"Expected: {lib_path}"
        )

    # Windows: allow loading dependent DLLs from the same directory.
    if sys.platform.startswith("win"):
        os.add_dll_directory(str(here))

    return ctypes.CDLL(str(lib_path))

_dll = _load_dll()


# =================================
#           Exception Class
# =================================

class SolideanException(Exception):
    """Exception raised when a Solidean API call returns an error code."""

    def __init__(self, result: 'Result'):
        self.result = result
        super().__init__(f"Solidean error: {result.name}")


# =================================
#        NumPy Array Helpers
# =================================

class _SolideanArray(np.ndarray):
    """NumPy array subclass that can hold a reference to keep native objects alive."""
    __array_priority__ = 1000  # ensure ufuncs prefer our subclass

    def __array_finalize__(self, parent):
        if parent is None:
            return
        # propagate owner to views/slices
        self._owner = getattr(parent, "_owner", None)


def _as_owned_array_from_ptr(ptr: ctypes.c_void_p, n_bytes: int, owner) -> np.ndarray:
    """Create a numpy array from a pointer with proper memory ownership tracking.

    Args:
        ptr: ctypes pointer to the data
        n_bytes: size of the data in bytes
        owner: Python object to keep alive while the array exists

    Returns:
        Read-only NumPy array viewing the data, with owner reference attached
    """
    # Build a ctypes array object that exposes the buffer (exporter lives in Python)
    buf_type = ctypes.c_uint8 * n_bytes
    buf = buf_type.from_address(ptr.value)
    # Create ndarray that views the buffer
    arr = np.ctypeslib.as_array(buf)  # shape=(n_bytes,)
    # Upgrade to subclass so we can attach attributes
    arr = arr.view(_SolideanArray)
    arr._owner = owner  # keep owner alive
    arr.setflags(write=False)  # make readonly - data is owned by native code
    return arr



# =================================
#              Enums
# =================================

class DataSlot(IntEnum):
    """
        Identifies the payload slots a TypedBlob can provide
    
        Enum identifying the various payloads that a TypedBlob can carry.
        See TypedBlob::GetData.
    """

    PositionsF32 = 10000
    """
        Array of float32 vertex positions (x,y,z)
    
        A contiguous list of 3D positions.
        Each consecutive 3 floats defines a position (x, y, z).
    
        This slot is for example used in Operation::ExportToIndexedTrianglesF32 or Operation::ExportDefectNetwork or Operation::Export.
    """

    PositionsF64 = 10001
    """
        Array of float64 vertex positions (x,y,z)
    
        A contiguous list of 3D positions.
        Each consecutive 3 doubles defines a position (x, y, z).
    
        This slot is for example used in Operation::Export.
    """

    PositionsXYZ192_W192 = 10111
    """
        Array of exact homogeneous integer positions (x,y,z,w) with 192-bit components
    
        A contiguous list of homogeneous 3D integer positions.
        Each position is stored as (x, y, z, w) where each coordinate is stored in 192 bit two's complement (aka 3x u64, interpreted as i192).
    
        This slot is for example used in Operation::Export.
    """

    PositionsPlanesABC64_D128 = 10211
    """
        Array of exact positions stored as intersections of three integer planes
    
        A contiguous list of 3D positions stored as the intersection of 3 homogeneous integer planes.
        Each position is stored as planes (p, q, r).
        A plane is stored as (a, b, c, d) where abc is the integer normal stored in i64 per component and d is the plane equation constant as i128 (stored as 2x u64).
    
        This slot is for example used in Operation::Export.
    """

    VertexToHalfedge = 11000
    """
        Array mapping each vertex to one of its incident halfedges
    
        A contiguous list of halfedge indices, one per position.
        The halfedge is some arbitrary halfedge that points to this vertex/position.
    
        This slot is for example used in Operation::Export.
    """

    TrianglesF32 = 20000
    """
        Array of unindexed triangles stored as float32 coordinates
    
        A contiguous list of individual triangles.
        Each consecutive 9 floats defines a triangle (3 x pos3).
    
        This slot is for example used in Operation::ExportToTrianglesF32 or Operation::Export.
    """

    TrianglesF64 = 20001
    """
        Array of unindexed triangles stored as float64 coordinates
    
        A contiguous list of individual triangles.
        Each consecutive 9 doubles defines a triangle (3 x pos3).
    
        This slot is for example used in Operation::Export.
    """

    TrianglesXYZ192_W192 = 20111
    """
        Array of unindexed triangles with exact 192-bit homogeneous integer coordinates
    
        A contiguous list of individual triangles.
        Each consecutive 3 homogeneous 3D integer positions define a triangle.
        Each position is stored as (x, y, z, w) where each coordinate is stored in 192 bit two's complement (aka 3x u64, interpreted as i192).
    
        This slot is for example used in Operation::Export.
    """

    TrianglesPlanesABC64_D128 = 20211
    """
        Array of unindexed triangles with vertices defined by plane intersections
    
        A contiguous list of individual triangles consisting of 3 positions each.
        Each position is stored as 3 homogeneous integer planes (p, q, r).
        A plane is stored as (a, b, c, d) where abc is the integer normal stored in i64 per component and d is the plane equation constant as i128 (stored as 2x u64).
    
        This slot is for example used in Operation::Export.
    """

    TrianglesIndexed = 29000
    """
        Array of indexed triangles referencing a position slot
    
        A contiguous list of indexed triangles.
        Each consecutive 3 int32_t define a triangle.
        The indices usually point into a position data slot like PositionsF32.
    
        This slot is for example used in Operation::ExportToIndexedTrianglesF32 or Operation::Export.
    """

    SegmentsIndexed = 39000
    """
        Array of indexed line segments referencing a position slot
    
        A contiguous list of indexed segments.
        Each consecutive 2 int32_t define a segment.
        The indices usually point into a position data slot like PositionsF32.
    
        This slot is for example used in Operation::ExportDefectNetwork or Operation::Export.
    """

    PrimitiveSize = 40001
    """
        Array of polygon sizes specifying number of vertices/edges per polygon
    
        A contiguous list of int32_t polygon sizes, i.e. the number of vertices/edges/halfedges per polygon.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToVertex = 50001
    """
        Array mapping halfedges to their target vertices
    
        A contiguous list of int32_t vertex indices, one per halfedge.
        This array maps halfedge indices to vertex indices (with the intended semantic that the halfedge "points to" the given vertex).
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToEdge = 50002
    """
        Array mapping halfedges to edge indices
    
        A contiguous list of int32_t edge indices, one per halfedge.
        This array maps halfedge indices to edge indices.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToFace = 50003
    """
        Array mapping halfedges to face indices
    
        A contiguous list of int32_t face indices, one per halfedge.
        This array maps halfedge indices to face indices.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToNextHalfedge = 50004
    """
        Array mapping each halfedge to its next halfedge in the relation
    
        A contiguous list of int32_t halfedge indices, one per halfedge.
        This array maps halfedge indices to halfedge indices that are the "next" in the halfedge relation.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToPrevHalfedge = 50005
    """
        Array mapping each halfedge to its previous halfedge in the relation
    
        A contiguous list of int32_t halfedge indices, one per halfedge.
        This array maps halfedge indices to halfedge indices that are the "prev" in the halfedge relation.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgeToOppositeHalfedge = 50006
    """
        Array mapping each halfedge to its opposite halfedge
    
        A contiguous list of int32_t halfedge indices, one per halfedge.
        This array maps halfedge indices to halfedge indices that are the "opposite" in the halfedge relation.
    
        This slot is for example used in Operation::Export.
    """

    HalfedgePlaneABC64_D128 = 50111
    """
        Stores exact integer edge planes for halfedges
    
        A contiguous list of exact outward integer edge planes, one per halfedge.
        A plane is stored as (a, b, c, d) where abc is the integer normal stored in i64 per component and d is the plane equation constant as i128 (stored as 2x u64).
    
        This slot is for example used in Operation::Export.
    """

    Defects = 80001
    """
        Integer defect values per primitive, used in defect networks
    
        A contiguous list of integer defect numbers.
        Each u32 signifies an integer defect.
        These IDs correspond 1-to-1 to stored primitives, like SegmentsIndexed.
    
        This slot is for example used in Operation::ExportDefectNetwork or Operation::Export.
    """

    PrimitiveIDs = 90000
    """
        64-bit tracking IDs assigned to primitives
    
        A contiguous list of primitive IDs.
        Each u64 defines a primitive ID as specified in SurfaceBuilder::TrackID.
        These IDs correspond 1-to-1 to stored primitives, like TrianglesF32 or TrianglesIndexed.
    
        This slot is for example used in Operation::ExportToTrianglesF32WithID or Operation::ExportToIndexedTrianglesF32WithID or Operation::Export.
    """

    PrimitiveToHalfedge = 90050
    """
        Array mapping primitives to one of their incident halfedges
    
        A contiguous list of halfedge indices.
        These halfedges correspond 1-to-1 to stored primitives and point to some arbitrary halfedge that belongs to the primitive.
    
        This slot is for example used in Operation::Export.
    """

    PrimitiveSupportingPlaneABC64_D128 = 90111
    """
        Exact integer planes supporting each primitive
    
        A contiguous list of primitive supporting planes, stored as exact integer coordinates.
        These planes correspond 1-to-1 to stored primitives, like TrianglesF32 or TrianglesIndexed.
        A plane is stored as (a, b, c, d) where abc is the integer normal stored in i64 per component and d is the plane equation constant as i128 (stored as 2x u64).
    
        This slot is for example used in Operation::Export.
    """

    QueryResultBool = 110001
    """
        Boolean results returned by query operations
    
        A single bool or array of bools, stored as 1 byte per bool.
        Usually found in BlobType::QueryResult, which results from Operation::QueryXYZ calls.
    
        This slot is for example used in Operation::QueryIsSupersolid or Operation::QueryIsSolid.
    """

    QueryResultF64 = 110003
    """
        Double precision results returned by query operations
    
        A single 64 bit double or array of doubles.
        Usually found in BlobType::QueryResult, which results from Operation::QueryXYZ calls.
    """

class ArithmeticKernel(IntEnum):
    """
        Selects the precision kernel used for exact arithmetic computations
    
        The ArithmeticKernel enum specifies which fixed-width arithmetic variant Solidean uses internally.
        Each kernel defines bit-depths for positions, planes, and intermediates, balancing performance with accuracy.
        The default choice is Fixed256Pos26, which uses 256-bit intermediates with 26-bit positional inputs - a practical trade-off between robustness and runtime efficiency.
        Other kernels may be added to support use cases requiring either higher precision or faster evaluation.
    """

    Fixed256Pos26 = 256026
    """
        256-bit arithmetic kernel with 26-bit input positions for exact mesh operations
    
        Using 256 bit intermediate precision and 26 bit for input positions.
    
        Exact vertices have the XYZ192_W192 format.
        Exact planes have the ABC64_D128 format.
    """

class ExecuteMode(IntEnum):
    """
        Selects how Solidean executes Boolean operations, balancing performance, threading, and validation
    
        The ExecuteMode enum controls the strategy used when running Boolean operations.
        It determines whether Solidean executes single-threaded, uses multithreading across all available CPU cores, or enables a debug mode with additional validation.
        By choosing an appropriate mode, users can trade off between maximum performance, deterministic execution, and strong input verification.
    """

    Singlethreaded = 100
    """
        Executes in a single thread, blocking until the operation completes
    
        Singlethreaded execution. Context::Execute will block the current thread and only use the current thread for execution.
    """

    Multithreaded = 200
    """
        Executes using all available CPU cores (default)
    
        Multithreaded execution mode distributes the Boolean workload across all available hardware threads.
        This is the default mode and generally provides the best throughput for large and complex meshes.
        Future releases may expose configuration options for limiting or pinning the number of threads, making it possible to tune performance in multi-tenant environments.
    """

    Debug = 300
    """
        Executes with additional verification of input constraints, at a significant performance cost
    
        In debug mode, execution will attempt to verify and detect all required input constraints.
    
        Most noteworthy, it will attempt to verify all input constraints.
        If a mesh was declared self-intersection-free but actually has self-intersection, the execution will fail with an appropriate ExecuteResult.
    
        This mode has a non-trivial performance penalty as the whole reason for declaring the input mesh type is that the whole Boolean operation is often faster than the required checks.
    
        NOTE: not all checks are fully implemented here, which can lead to spurious NotImplemented results.
    """

class ExecuteResult(IntEnum):
    """
        Reports non-critical errors detected during operation execution
    
        Enum for reporting non-critical errors during Operation execution.
    
        NOTE: 0 is always Success, non-0 is always Failure
    
        For ExecuteResult, Failure means that the input data is likely wrong (e.g. a mesh was defined without self-intersections, but actually has them).
        If Operation::Execute returns Result::Ok but a failing ExecuteResult, then the mesh is still produced in a best-effort manner.
        It will be flagged as being potentially wrong though.
    """

    Ok = 0
    """
        Execution succeeded without errors
    
        No error occurred.
    """

    HardError = 6000
    """
        Fatal error, results are invalid and cannot be trusted
    
        A hard error occurred and the resulting data cannot be trusted at all.
        This always means that the returned Result is not Result::Ok.
    """

    InputIsNotSupersolid = 7001
    """
        Input mesh declared supersolid but evidence of non-supersolid geometry was found
    
        During execution, evidence that the provided input mesh is not supersolid was encountered.
        This usually means that the input has holes.
    
        See MeshBuilder::AllowNonSupersolid and Operation::Heal for how to handle non-supersolid meshes.
    
        NOTE: ExecuteResult::InputIsNonSupersolid means that the Mesh is declared supersolid but we found evidence that it is not.
              Result::OperandMustBeSupersolid means that the Mesh is declared non-supersolid but passed to an operation that requires supersolid meshes.
              The former is usually bad data while the latter indicates a programming error (wrong use of API).
    """

    InputIsNonFinite = 7002
    """
        Input contained non-finite values such as NaN or infinity
    
        Some input vertices are not finite (aka infinite or NaN).
    
        NOTE: this is only reliably checked with ExecutionMode::Debug. It can cause undefined behavior in other modes.
    """

    InputIsNotWellDefined = 7003
    """
        Input mesh was malformed, e.g. out-of-bounds indices
    
        Some input mesh is not well-defined (e.g. index-out-of-bounds).
    
        NOTE: this is only reliably checked with ExecutionMode::Debug. It can cause undefined behavior in other modes.
    """

    InputIsOutOfBounds = 7004
    """
        Input coordinates exceeded the range supported by the selected ExactArithmetic
    
        The ExactArithmetic has a maximum supported coordinate, i.e. a bounding box that all meshes must be inside of.
        This error indicates that some floating point inputs are out of this bounding box.
    """

    InputIsNotSolid = 7005
    """
        Input mesh declared solid but failed solidness checks (holes, overlaps, wrong normals)
    
        Without any flags, an input mesh must be a solid mesh: Its faces must enclose a solid volume, without any holes, and without overlapping each other.
        All triangles must also consistently point into the volume, or away from it.
        Sometimes, input that violates these assumptions can be detected, in which case this error is returned.
    
        Should a more complex mesh setup be necessary, see MeshBuilder::AllowSurfaceIntersections, MeshBuilder::AllowNestedComponents, and SurfaceBuilder::AllowSelfIntersections.
        This can ease the requirement to allow for supersolid meshes as well.
    
        This error is common in three cases:
        * the input has complex internal structure such as self-intersections (solution: allow the appropriate mesh configurations)
        * the input has holes (the mesh is not supersolid and error-tolerant booleans or preprocessing is necessary)
        * the input has inwards-oriented normals (flip the winding order of all faces)
    """

    InputHasNestedComponents = 7006
    """
        Input mesh contained nested components without the required configuration
    
        An input mesh without MeshBuilder::AllowNestedComponents or MeshType::Supersolid was found to actually have nested components.
        This usually indicates that the mesh was not imported properly.
    
        NOTE: this is only reliably checked with ExecutionMode::Debug. It can yield unexpected results in other modes.
    """

    InputHasSelfIntersections = 7007
    """
        Input surface contained self-intersections without being marked as allowed
    
        An input mesh without SurfaceBuilder::AllowSelfIntersections or MeshType::Supersolid was found to actually have a surface where primitives intersect each other (or overlap).
        This usually indicates that the mesh was not imported properly.
    
        NOTE: this is only reliably checked with ExecutionMode::Debug. It can yield unexpected results in other modes.
    """

    InputHasSurfaceIntersections = 7008
    """
        Input mesh contained intersecting surfaces without being marked as allowed
    
        An input mesh without MeshBuilder::AllowSurfaceIntersections or MeshType::Supersolid was found to actually have two different surfaces that intersect each other.
        This usually indicates that the mesh was not imported properly.
    
        NOTE: this is only reliably checked with ExecutionMode::Debug. It can yield unexpected results in other modes.
    """

class ExportFormat(IntEnum):
    """
        Specifies the structural format used when exporting a mesh
    
        This enum specifies the desired export format of Operation::Export.
        Determines if the result is indexed or unrolled, if they are triangles or polys, if we create a half-edge topology, etc.
    
        NOTE: by default, no vertex positions or tracking IDs are exported.
        ExportOption is used to specify exactly how positions and any other attributes are exported (in addition to other post-processing options like guaranteed manifoldness).
    """

    Triangles = 1000
    """
        Unrolled triangle soup; populates DataSlot::TrianglesF32 or similar depending on options
    
        Export a mesh as unrolled triangles.
        Triangulates polygons before export.
    
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::TrianglesF32.
    
        NOTE: all desired extra attributes, _including_ positions must be configured using ExportOption.
    """

    Polygons = 1001
    """
        Unrolled polygon soup with explicit sizes; populates DataSlot::PrimitiveSize and attributes
    
        Export a mesh as unrolled polygons.
        Unrolled polygons are effectively flat lists of half-edge attributes.
    
        Populates DataSlot::PrimitiveSize to define how many contiguous attributes belong to the same polygon.
        For example, with ExportOption::VertexPositionF32, this format also populates DataSlot::PositionsF32.
        The polygon sizes then dictate which PositionsF32 belong to which polygon (in order).
    
        NOTE: depending on the export options, these polygons might not be convex. They will never have holes, though.
    """

    IndexedTriangles = 2000
    """
        Triangle mesh with vertex indices; populates DataSlot::TrianglesIndexed and attributes
    
        Export a mesh as triangles with vertex indices.
        Triangulates polygons before export.
    
        Populates DataSlot::TrianglesIndexed to index into other attributes.
    
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
    """

    IndexedPolygons = 2001
    """
        Polygon mesh with vertex indices; populates DataSlot::PrimitiveSize, DataSlot::HalfedgeToVertex, and attributes
    
        Export a mesh as polygons with vertex indices.
    
        Populates DataSlot::PrimitiveSize to define how many contiguous indices belong to the same polygon.
        The vertex indices themselves are stored in DataSlot::HalfedgeToVertex.
        These can then used to access vertex attributes.
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
    """

    HalfedgeExplicit = 3000
    """
        Half-edge structure with explicit next and opposite relations; fully indexed topology
    
        Export a mesh as a half-edge data structure with explicit halfedge relations.
        Populates DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToNextHalfedge, and DataSlot::HalfedgeToOppositeHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
    """

    HalfedgeImplicitOpposite = 3001
    """
        Half-edge structure with implicit opposite relation encoded by storage order
    
        Export a mesh as a half-edge data structure with implicit-opposite halfedge relations.
        Populates DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToNextHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        "Implicit-opposite" means that halfedges are stored next to their opposite.
        This effectively means that we're storing edges as (halfedge, opposite halfedge) pairs.
        "opposite(h)" is a trivial "h ^ 1" (bitwise xor). "edge(h)" is "h >> 1". "halfedges(e)" is "(e * 2 + 0, e * 2 + 1)".
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
    """

    HalfedgeImplicitNext = 3002
    """
        Half-edge structure with implicit next relation encoded by polygon ordering
    
        Export a mesh as a half-edge data structure with implicit-next halfedge relations.
        Populates DataSlot::PrimitiveSize, DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToOppositeHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        "Implicit-next" means that halfedges belonging to the same polygon are stored contiguously in-order.
        Given the polygon size "s" and the relative index "i" of the halfedge inside the polygon, the next halfedge is simply "(i + 1) % s" in local terms.
        For efficient random access, a prefix sum of the polygon sizes is advisable.
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
    """

    DefectNetwork = 9001
    """
        Defect graph export with indexed segments, defect values, and optional vertex attributes
    
        Exports a graph that represents the defect network of a mesh.
    
        The vertex type must be specified using an ExportOption, e.g. with ExportOption::VertexPositionF32, this format populates DataSlot::PositionsF32.
        The graph itself is represented as indexed segments, i.e. DataSlot::SegmentsIndexed.
        The defect value is stored per-segment in DataSlot::Defects.
    """

class ExportOption(IntFlag):
    """
        Configurable flags controlling attributes, topology, and guarantees during export
    
        These flags extensively configurable the behavior and guarantees of Operation::Export.
    
        Determines if the result is indexed or unrolled, if they are triangles or polys, if we create a half-edge topology, etc.
    
        NOTE: not all combinations of options are valid with each other or all formats. Notable exceptions are
    """

    None_ = 0
    """
        No additional processing; produces bare minimum output for the chosen format
    
        No additional processing.
        Use the bare minimum to produce the chosen ExportFormat and its base guarantees.
    
        NOTE: this means that vertex positions are _not_ exported. Most use cases want to choose one of the VertexPositionXYZ options.
    """

    VertexPositionF32 = 1
    """
        Exports vertex positions as 32-bit floats (DataSlot::PositionsF32 or TrianglesF32)
    
        Export vertex positions as floats (f32).
    
        Populates DataSlot::PositionsF32 or DataSlot::TrianglesF32.
    """

    VertexPositionF64 = 2
    """
        Exports vertex positions as 64-bit doubles (DataSlot::PositionsF64 or TrianglesF64)
    
        Export vertex positions as floats (f64).
    
        Populates DataSlot::PositionsF64 or DataSlot::TrianglesF64.
    """

    VertexPositionExact = 4
    """
        Exports exact vertex positions in the arithmetic's native integer format
    
        Export exact vertex positions.
        The concrete format depends on the created ExactArithmetic (and is documented there).
    
        For example, ArithmeticKernel::Fixed256Pos26 populates DataSlot::PositionsXYZ192_W192 or DataSlot::TrianglesXYZ192_W192.
    """

    VertexPositionPlanes = 8
    """
        Exports exact vertex positions as intersections of three integer planes
    
        Export vertex positions as intersection of 3 exact planes.
        The concrete format depends on the created ExactArithmetic (and is documented there).
    
        For example, ArithmeticKernel::Fixed256Pos26 populates DataSlot::PositionsPlanesABC64_D128 or DataSlot::TrianglesPlanesABC64_D128.
    """

    SupportingPlane = 16
    """
        Exports exact supporting planes for each primitive
    
        Exports exact supporting planes for each exported primitive.
        The concrete format depends on the created ExactArithmetic (and is documented there).
    
        For example, ArithmeticKernel::Fixed256Pos26 populates DataSlot::PrimitiveSupportingPlaneABC64_D128.
    """

    PrimitiveID = 32
    """
        Exports tracking IDs for each primitive (DataSlot::PrimitiveIDs)
    
        Exports tracking IDs for each exported primitive.
        NOTE: any primitives that were not created or imported using the WithID versions will have the special "untracked" ID.
    
        Populates DataSlot::PrimitiveIDs.
    """

    Manifold = 64
    """
        Guarantees manifoldness by duplicating vertices where necessary
    
        Guarantees manifoldness for _any_ type of mesh.
        Will generate topologically open results (aka meshes with boundary) exactly if the input is not supersolid, i.e. has geometrically open boundaries.
        This operation has almost no overhead and introduces no additional primitives.
        Manifoldness is achieved purely by duplicating a few select vertices.
    
        Per default, this will yield the smallest possible surfaces given a solid input.
        This behavior can be overridden by using PreferLargerManifolds.
    """

    PreferLargerManifolds = 128
    """
        Prefers larger manifold surfaces when multiple decompositions are possible (requires Manifold)
    
        Prefers to create topologically larger manifold surfaces instead of the smaller default.
        This only applies to meshes that don't uniquely decompose into manifolds, e.g. those where some edges have 4 or more adjacent faces.
        For solid meshes, this guarantees a decomposition into the topologically largest possible manifolds.
    
        NOTE: this flag requires the Manifold flag.
    """

    Triangulate = 256
    """
        Forces all polygons to be triangulated without changing format
    
        Triangulates all polygons in a naive way, though still guaranteeing that no additional degenerate triangles are introduced.
    
        NOTE: this does NOT change the format. It simply means that all exported faces will have exactly 3 vertices.
    """

    OptimizeTriangulationInteriorAngle = 512
    """
        Improves triangulation by maximizing the minimum interior angle (Delaunay-like)
    
        There is a lot of freedom in placing edges in planar regions during triangulation.
        This flag tries to maximize the minimum interior angle of each triangle, i.e. make triangles Delaunay in planar regions.
    
        NOTE: this flag requires a triangular output format or the ExportOption::Triangulate flag.
    """

    OptimizeTriangulationEdgeRatio = 1024
    """
        Improves triangulation by minimizing edge length ratios (favoring equilateral triangles)
    
        There is a lot of freedom in placing edges in planar regions during triangulation.
        This flag tries to minimize the maximum ratio between smallest and largest edge length of each triangle, thus favoring more equilateral triangles.
    
        NOTE: this flag requires a triangular output format or the ExportOption::Triangulate flag.
    """

    RemoveSpuriousEdges = 2048
    """
        Removes redundant edges between adjacent same-plane, same-ID primitives
    
        For various reasons, we might have adjacent polygons with the same supporting plane and tracking ID.
        The edge between them is, in a way, "spurious".
        This option removes such edges, usually making the polygons non-convex in the process.
    
        NOTE: edges that connect the same polygon on both sides are kept. These "ghost edges" connect the polygon border to any "holes".
    
        NOTE: this is only supported when the output can actually support polygons (i.e. a polygonal ExportFormat and non-triangulating ExportOptions)
    """

    RemoveSpuriousVertices = 4096
    """
        Removes redundant vertices that lie on non-transition edges
    
        For various reasons, we might have manifold vertices that lie on the edge between two "real" adjacent faces (in the same-supporting-plane-and-tracking-id-sense).
        These vertices are, in a way, "spurious".
        This option removes such vertices.
    """

    HalfedgeToVertex = 8192
    """
        Exports halfedge-to-vertex mapping (DataSlot::HalfedgeToVertex)
    
        Populates DataSlot::HalfedgeToVertex with the mapping from halfedge to vertex index (the "to vertex" is the vertex that the halfedge points to).
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgeToEdge = 16384
    """
        Exports halfedge-to-edge mapping (DataSlot::HalfedgeToEdge)
    
        Populates DataSlot::HalfedgeToEdge with the mapping from halfedge to edge index.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgeToFace = 32768
    """
        Exports halfedge-to-face mapping (DataSlot::HalfedgeToFace)
    
        Populates DataSlot::HalfedgeToFace with the mapping from halfedge to face index.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgeToNextHalfedge = 65536
    """
        Exports halfedge-to-next mapping (DataSlot::HalfedgeToNextHalfedge)
    
        Populates DataSlot::HalfedgeToNextHalfedge with the mapping from halfedge to next halfedge index.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgeToPrevHalfedge = 131072
    """
        Exports halfedge-to-previous mapping (DataSlot::HalfedgeToPrevHalfedge)
    
        Populates DataSlot::HalfedgeToPrevHalfedge with the mapping from halfedge to previous halfedge index.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgeToOppositeHalfedge = 262144
    """
        Exports halfedge-to-opposite mapping (DataSlot::HalfedgeToOppositeHalfedge)
    
        Populates DataSlot::HalfedgeToOppositeHalfedge with the mapping from halfedge to opposite halfedge index.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    HalfedgePlane = 524288
    """
        Exports exact integer planes per halfedge (DataSlot::HalfedgePlaneABC64_D128)
    
        Populates a data slot with the mapping from halfedge to exact outward pointing integer plane.
        The concrete format depends on the created ExactArithmetic (and is documented there).
    
        For example, ArithmeticKernel::Fixed256Pos26 populates DataSlot::HalfedgePlaneABC64_D128.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    
        NOTE: non-representable planes introduces by triangulation are stored as (0,0,0,0).
    """

    PrimitiveSize = 1048576
    """
        Exports polygon sizes (DataSlot::PrimitiveSize), including for triangles
    
        Populates DataSlot::PrimitiveSize with the number of vertices per face.
    
        NOTE: this works for consistently any format, even triangles (where it is constant 3).
    """

    PrimitiveToHalfedge = 2097152
    """
        Exports mapping from primitives to one of their halfedges (DataSlot::PrimitiveToHalfedge)
    
        Populates DataSlot::PrimitiveToHalfedge with the mapping from primitive/face/polygon to an arbitrary halfedge belonging to the primitive.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

    VertexToHalfedge = 4194304
    """
        Exports mapping from vertices to one of their halfedges (DataSlot::VertexToHalfedge)
    
        Populates DataSlot::VertexToHalfedge with the mapping from vertex to an arbitrary halfedge pointing to the vertex.
    
        NOTE: this is only valid with a halfedge ExportFormat.
    """

class Lifetime(IntEnum):
    """
        Defines how long user-provided data remains valid in relation to Solidean handles
    
        The Lifetime enum specifies ownership and validity rules for user-provided data.
        It controls whether Solidean copies data immediately, requires it to remain valid until explicitly released, or extends that requirement to both direct and indirect usages.
        Choosing the right lifetime allows balancing memory usage, performance, and safety - with advanced modes enabling zero-copy optimizations but requiring stricter discipline from the user.
    """

    CopyImmediately = 0
    """
        Data is copied on call and can be safely freed or mutated after return
    
        This mode ensures maximum safety by copying all provided data into Solidean's internal storage immediately.
        It is the simplest and safest option, allowing the caller to reuse or release buffers right after the call returns.
        Use CopyImmediately when memory is not a bottleneck and predictable ownership is preferred.
    """

    UntilDirectRelease = 1
    """
        Data must remain valid until all directly created handles using it are released
    
        The provided data is valid until the user calls Handle::Release on all handles that are created with this data.
    
        For example, the user can create a SurfaceBuilder referencing triangle data with UntilDirectRelease.
        With this, two surfaces are created and used in different meshes.
        These are all direct usages that the user explicitly requested.
        Only until after all SurfaceBuilders, Surfaces, MeshBuilders, and Meshes are Released, can the provided data safely be deleted or re-used.
    
        NOTE: if the result is an Operand, e.g. Operation::ImportFromTrianglesF32, then this applies to the Operation handle.
    """

    UntilIndirectRelease = 2
    """
        Data must remain valid until all direct and indirect handles using it are released
    
        The provided data is valid until the user calls Handle::Release on all directly or INDIRECTLY created handles.
    
        A directly created handle is everything that the user explicitly created with this data, e.g. SurfaceBuilders, Surfaces, MeshBuilders, Meshes.
        An example is given in UntilDirectRelease.
    
        Indirectly created handles are all handles that are created during an Operation that this data takes part of.
        For example, an Operation::Union might be able to reuse the data of an input surface for its result.
        If it was created with UntilIndirectRelease, then it does not have to copy the data.
    
        This mode enables zero-copy optimization but requires careful ownership management.
        Incorrect use can easily lead to invalid memory access.
    
        CAUTION: this is an advanced feature and easy to use wrongly.
    """

class MeshType(IntEnum):
    """
        Communicates the geometric guarantees a mesh provides to Solidean
    
        This enum provides some commonly used presets for setting up SurfaceBuilder/MeshBuilder.
        It is strictly used as convenience.
        The appropriate builders still provide the most flexibility and nuance.
    """

    Solid = 0
    """
        Mesh guaranteed to be a valid solid without self-intersections or overlaps
    
        A solid mesh as defined in the manual.
        No self-intersections are allowed, no overlaps, no inner nested components (though holes are fine).
        Each surface primitive is actually on the surface of the represented object.
    
        This is the most restricted but also fastest type of mesh.
    """

    Supersolid = 1
    """
        Mesh guaranteed to allow self-intersections, coplanar faces, and nested components
    
        A supersolid mesh as defined in the manual.
        Self-intersections and nested components are allowed. Coplanar triangles are allowed. Zero-volume constructs are allowed.
        Basically every mesh that can be seen as the superposition of (potentially intersecting) solid meshes.
        In particular, any topologically 2-manifold mesh is supersolid, regardless of its vertex positions.
    
        This is the most permissive but also slowest type of mesh that has well-defined booleans.
    """

    NonSupersolid = 2
    """
        Mesh with no validity guarantees; may be non-manifold, partial, or inconsistent
    
        Any potentially non-supersolid mesh must use this type.
        It allows for holes, partial surfaces, any non-manifold configuration.
        Apart from the coordinate limit chosen by ExactArithmetic, there is literally no restriction on the input geometry.
    
        CAUTION: most operations do not accept this type of mesh. The main way to make it usable is via Operation::Heal.
    """

class Result(IntEnum):
    """
        Common error codes for reporting invalid API usage, licensing errors, or execution failures
    
        Common enum for reporting the error state of an operation (i.e. an error code).
    
        NOTE: 0 is always Success, non-0 is always Failure
    
        Failure results are always considered exceptional and use Exceptions in languages that allow them.
        Most of the failure cases indicate a programming error (aka invalid API usage).
        The exceptions are license errors or out-of-memory situations, which are not programming errors but also considered exceptional.
    
        In particular, passing meshes that are not supersolid as input to an Operation, will result in Result::Ok but ExecuteResult::InputIsNotSupersolid (if detected).
    """

    Ok = 0
    """
        Completed successfully without errors
    
        No error occurred.
    """

    UnknownError = 1000
    """
        Internal error without further diagnostic; contact support
    
        Something went internally wrong without further diagnostic.
        Please contact support.
        Ideally provide a dump or reproduction.
    """

    InvalidArgument = 1001
    """
        Argument validation failed due to invalid input values
    
        Argument validation failed for syntactic or surface-level reasons.
    """

    InvalidNullArgument = 1002
    """
        Null argument was passed where not allowed
    
        A null argument was provided in a place where this is not allowed.
    
        NOTE: unless explicitly allowed, arguments cannot be null
    """

    InvalidCombination = 1003
    """
        Incompatible combination of features or options
    
        An invalid combination of features.
        Commonly used in builders to indicate incompatible features.
    """

    InvalidInvocation = 1004
    """
        Method was invoked in an invalid state or multiple times when only once allowed
    
        This method should not have been called.
        Commonly used in builders, where trying to call set-once methods multiple times.
    """

    InvalidSize = 1005
    """
        Provided array size does not meet required constraints
    
        For various array parameters, the size must meet certain constraints.
        For example, in SurfaceBuilder::TrackPrimitiveIDs, the number of IDs must match the number of primitives for the surface.
        Should this not be the case, this error is returned.
    """

    InvalidContext = 1006
    """
        Context is invalid, e.g. used after being destroyed
    
        The provided context is not valid.
        After Context::Destroy, using the context handle is not allowed anymore.
    """

    InvalidHandle = 1007
    """
        Handle is invalid, e.g. used after being released
    
        The provided handle is not valid.
        After calling Handle::Release, using the handle is not allowed anymore.
    """

    UninitializedHandle = 1008
    """
        Handle was created but not yet initialized with data
    
        The provided handle was created but its data is not yet initialized.
        Handles point to immutable, but async, data.
        For example, querying information from an Operation::Output MeshHandle before the Operation has finished, yields this error.
    """

    ImplementationLimitsReached = 1998
    """
        Hard implementation limits exceeded, e.g. too many triangles or surfaces
    
        There are currently some hard upper limits on certain inputs like the number of triangles or the number of surfaces.
        Those are quite hard and unlikely to be reached in normal operations.
        This error indicates that such a limit was in fact reached.
        Please refer to the error log, the manual, or support for more information.
    """

    NotImplemented = 1999
    """
        Encountered an unimplemented feature in the current version
    
        Indicates that the execution hit a path that is not implemented in the current version but will be in the future.
        We try to document all cases where this can happen, though especially non-stable versions can contain undocumented ones.
        Please contact support if you don't know why you're getting this result.
    """

    LicenseInvalid = 2001
    """
        Current license is invalid
    
        The current license is invalid.
    """

    LicenseNoNetwork = 2002
    """
        License verification failed due to network error
    
        Network error while trying to verify license.
    """

    LicenseMustActivateMachine = 2003
    """
        License requires machine activation
    
        The current machine must be activated.
    """

    LicenseOutOfMachines = 2004
    """
        License exceeded allowed number of machines
    
        Too many machines.
    """

    LicenseOutOfCores = 2005
    """
        License exceeded allowed number of cores
    
        Too many cores.
    """

    LicenseOutOfProcesses = 2006
    """
        License exceeded allowed number of processes
    
        Too many processes.
    """

    LicenseSuspended = 2007
    """
        License is suspended
    
        License is suspended.
    """

    LicenseExpired = 2008
    """
        License has expired
    
        License is expired.
    """

    LicenseOverdue = 2009
    """
        License is overdue
    
        License is overdue.
    """

    LicenseBanned = 2010
    """
        License has been banned
    
        License is banned.
    """

    OutOfScratchMemory = 3001
    """
        Internal scratch memory exhausted during operation
    
        The operation failed because the internal scratch memory was too small.
    """

    OutOfUserMemory = 3002
    """
        Provided user buffer too small, e.g. in TypedBlob::CreateWithFixedBuffer
    
        The operation failed because user-provided output buffers (e.g. a TypedBlob::CreateWithFixedBuffer) were too small.
    """

    HandleAlreadyInitialized = 3003
    """
        Immutable handle would be overwritten; already initialized
    
        The operation failed because an already initialized (immutable) handle would have been overwritten.
        This can for example happen if the same TypedBlob is used in multiple Operation::ExportXYZ statements.
    """

    IncompatibleArithmetics = 3004
    """
        Mixed ExactArithmetic types detected in a single operation
    
        All mesh inputs in an operation require the same ExactArithmetic.
        This error indicates that different arithmetics were mixed in the same operation.
        This also applies when trying to build a mesh with surfaces that are defined using different arithmetics.
    """

    OperationAlreadyExecuted = 3005
    """
        Attempted to modify or reuse an operation after execution
    
        An operation must be executed at most once.
        Adding work to an operation after execution is an error.
        Only when explicitly noted, are methods of an Operation allowed after execute.
    
        A common mistake is trying to output or export from an already executed Operation.
        Any call to Operation::Output or Operation::ExportXYZ is work-relevant and thus only allowed before execute.
    """

    OperationNotYetExecuted = 3006
    """
        Attempted to access objects before the operation completed
    
        Some objects can be created by an operation, e.g. using Operation::Output.
        Others are filled by operations, e.g. a TypedBlob using Operation::ExportToTrianglesF32.
        In both cases, the object itself only becomes valid after the operation completed.
        This error indicates, that the content of such an object was requested before the operation was complete.
    
        A common mistake is to set up the operation, forget to call Context::Execute, and then try to query the resulting data, e.g. via TypedBlob::GetData.
    """

    OperandFromWrongOperation = 3007
    """
        Operand used in an operation different from the one that created it
    
        Operands (such as MeshOperand) must only be used in the operation that created them.
        This error indicates that an operand was used in a different operation.
        Use Operation::Output followed by Operation::Input if you want to use an exact result across operations.
    
        A common mistake is trying to do iterated/consecutive CSG by using a MeshOperand in a follow-up operation instead of using Output/Input.
    """

    DefiningOperationFailed = 3008
    """
        Attempted to access results of an operation that failed
    
        When the Operation that defined a Mesh or TypedBlob failed, said mesh or data is stuck in an error state.
        Accessing the data of objects that should have been the result of a failed operation is itself an error.
    
        A common mistake is ignore the return value of Context::Execute and accessing exported data (e.g. TypedBlob::GetData).
    """

    OperandMustBeSupersolid = 3009
    """
        Non-supersolid mesh passed to an operation requiring supersolid input
    
        Most operations require at least supersolid meshes and many have optimizations for properly solid ones.
        When calling MeshBuilder::AllowNonSupersolid, "bad input" meshes can be defined.
        These will be rejected (using this error) by most operations.
        Typically, these meshes must be routed through Operation::Heal to be of use.
    
        NOTE: ExecuteResult::InputIsNonSupersolid means that the Mesh is declared supersolid but we found evidence that it is not.
              Result::OperandMustBeSupersolid means that the Mesh is declared non-supersolid but passed to an operation that requires supersolid meshes.
              The former is usually bad data while the latter indicates a programming error (wrong use of API).
    """

    DataSlotNotFound = 4001
    """
        Requested DataSlot is not present in the TypedBlob
    
        The provided DataSlot is not present in the given object.
        Mainly happens when TypedBlob::GetData is called with a slot that is not stored in the TypedBlob.
    """

    IncompatibleExportOptions = 4002
    """
        Provided ExportOptions are not valid for the chosen ExportFormat
    
        The provided combination of ExportOptions is not compatible with each other or the chosen ExportFormat.
        Mainly happens when Operation::Export is used in an unsupported way.
    """

class SurfaceType(IntEnum):
    """
        Identifies the underlying representation format of a surface
    
        The SurfaceType enum specifies how surface geometry is stored in memory.
        These formats do not determine accuracy or robustness.
        Solidean always operates in exact arithmetic internally, as defined by the chosen ExactArithmetic.
        Floating-point based formats such as TrianglesF32 and IndexedTrianglesF32 are simply storage layouts; their data is immediately interpreted exactly.
        Any missing topology at this level is automatically reconstructed when using the appropriate Operation::ExportXyz methods.
    """

    TrianglesF32 = 1010000
    """
        Surface defined by an unindexed triangle soup in float32
    
        A flat array of float32 triangles used for simple storage and interchange.
        Although vertices are given as floats, they are converted into the exact integer space on import, so robustness is unaffected.
        Topology such as shared vertices is not preserved in this layout, but can be restored when exporting.
    """

    IndexedTrianglesF32 = 1110000
    """
        Surface defined by indexed float32 triangles
    
        A vertex buffer plus index list representation in float32.
        More compact than a raw triangle soup and capable of sharing vertices across triangles.
        Like TrianglesF32, this is treated exactly once imported, and any missing topological information will be reconstructed by Solidean's exporters.
    """

    MeshletH256 = 4000004
    """
        Surface partitioned into meshlets with 256-bit arithmetic
    
        Stores surfaces in small clusters ("meshlets") internally, each using 256-bit arithmetic for robust processing.
        This format is optimized for internal execution of Boolean operations, balancing exactness with performance.
    """

    PlanePolygonsH256 = 5000004
    """
        Surface defined by plane-based polygons with 256-bit arithmetic
    
        Represents surfaces as exact polygons clipped from planes, rather than tessellated triangles.
        This compact representation preserves high-level geometric structure and avoids unnecessary triangulation, while maintaining 256-bit exactness.
    """

class BlobType(IntEnum):
    """
        Identifies the kind of data stored in a TypedBlob
    
        Identifies the type of data stored in a TypedBlob.
    """

    QueryResult = 100001
    """
        Holds results of query operations (area, volume, properties) to be retrieved after execution
    
        Due to the asynchronous nature of Operations, the Operation::QueryXYZ cannot return their result immediately.
        Thus, they are stored in TypedBlobs with BlobType::QueryResult to be retrieved after the Operation was executed.
        Provides DataSlot::QueryResultXYZ slots. Details are found in the appropriate Operation::QueryXYZ functions.
    """

    DefectNetwork = 200001
    """
        Segment graph describing defect edges in a non-supersolid mesh
    
        A segment graph that describes where a non-supersolid mesh actually violates the supersolid property.
        Segments are stored as DataSlot::SegmentsIndexed with indices pointing into DataSlot::PositionsF32.
        This graph has deduplicated vertices, similar to how Operation::ExportToIndexedTrianglesF32 yields an indexed and topologically connected result.
        Each segment has an associated positive integer defect stored in DataSlot::Defects.
    """

    Triangles = 1001000
    """
        Unindexed triangle soup; exact slots depend on export method and options
    
        A triangle soup.
        The exact data slots depend on the export method used.
    
        For example, with Operation::ExportToTrianglesF32 or Operation::ExportMesh with ExportOption::VertexPositionF32, this blob provides DataSlot::TrianglesF32.
        Provides DataSlot::PrimitiveIDs if exported with primitive tracking, i.e. by Operation::ExportToTrianglesF32WithID, or ExportOption::PrimitiveID.
    """

    Polygons = 1001001
    """
        Polygon soup with explicit polygon sizes and attributes
    
        A polygon soup.
        Unrolled polygons are effectively flat lists of half-edge attributes.
    
        Provides DataSlot::PolygonSize to define how many contiguous attributes belong to the same polygon.
        For example, with Operation::ExportMesh and ExportOption::VertexPositionF32, this blob also provides DataSlot::PositionsF32.
        The polygon sizes then dictate which PositionsF32 belong to which polygon (in order).
    
        NOTE: depending on the export options, these polygons might not be convex. They will never have holes, though.
    """

    IndexedTriangles = 1002000
    """
        Indexed triangle mesh with shared vertices and deduplicated topology
    
        A list of triangles with vertex indices.
    
        Provides DataSlot::TrianglesIndexed to index into other attributes.
    
        For example, with Operation::ExportToIndexedTrianglesF32 or Operation::ExportMesh with ExportOption::VertexPositionF32, this blob provides DataSlot::PositionsF32.
    """

    IndexedPolygons = 1002001
    """
        Indexed polygon mesh with polygon sizes and halfedge-to-vertex mapping
    
        A list of polygons with vertex indices.
    
        Provides DataSlot::PolygonSize to define how many contiguous indices belong to the same polygon.
        The vertex indices themselves are stored in DataSlot::HalfedgeToVertex.
        These can then used to access vertex attributes.
        For example, with Operation::ExportMesh and ExportOption::VertexPositionF32, this blob provides DataSlot::PositionsF32.
    """

    HalfedgeExplicit = 1003000
    """
        Half-edge data structure with explicit next and opposite relations
    
        A half-edge data structure with explicit halfedge relations.
        Provides DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToNextHalfedge, and DataSlot::HalfedgeToOppositeHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with Operation::ExportMesh and ExportOption::VertexPositionF32, this blob provides DataSlot::PositionsF32.
    """

    HalfedgeImplicitOpposite = 1003001
    """
        Half-edge data structure with implicit opposite relation encoded by storage order
    
        A half-edge data structure with implicit-opposite halfedge relations.
        Provides DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToNextHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        "Implicit-opposite" means that halfedges are stored next to their opposite.
        This effectively means that we're storing edges as (halfedge, opposite halfedge) pairs.
        "opposite(h)" is a trivial "h ^ 1" (bitwise xor). "edge(h)" is "h >> 1". "halfedges(e)" is "(e * 2 + 0, e * 2 + 1)".
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with Operation::ExportMesh and ExportOption::VertexPositionF32, this blob provides DataSlot::PositionsF32.
    """

    HalfedgeImplicitNext = 1003002
    """
        Half-edge data structure with implicit next relation encoded by polygon ordering
    
        A half-edge data structure with implicit-next halfedge relations.
        Provides DataSlot::PolygonSize, DataSlot::HalfedgeToVertex, DataSlot::HalfedgeToOppositeHalfedge.
        Other half-edge relations can be added via ExportOption.
    
        "Implicit-next" means that halfedges belonging to the same polygon are stored contiguously in-order.
        Given the polygon size "s" and the relative index "i" of the halfedge inside the polygon, the next halfedge is simply "(i + 1) % s" in local terms.
        For efficient random access, a prefix sum of the polygon sizes is advisable.
    
        NOTE: as always, vertex attributes are opt-in.
        For example, with Operation::ExportMesh and ExportOption::VertexPositionF32, this blob provides DataSlot::PositionsF32.
    """


# =================================
#         DLL Function Setup
# =================================

_dll_Solidean_Context_Create = _dll.Solidean_Context_Create
_dll_Solidean_Context_Create.argtypes = [ctypes.POINTER(ctypes.c_uint64)]
_dll_Solidean_Context_Create.restype = ctypes.c_uint32

_dll_Solidean_Context_Destroy = _dll.Solidean_Context_Destroy
_dll_Solidean_Context_Destroy.argtypes = [ctypes.c_uint64]
_dll_Solidean_Context_Destroy.restype = ctypes.c_uint32

_dll_Solidean_Context_Execute = _dll.Solidean_Context_Execute
_dll_Solidean_Context_Execute.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint64, ctypes.c_uint32]
_dll_Solidean_Context_Execute.restype = ctypes.c_uint32

_dll_Solidean_ExactArithmetic_Create = _dll.Solidean_ExactArithmetic_Create
_dll_Solidean_ExactArithmetic_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_float, ctypes.c_uint32]
_dll_Solidean_ExactArithmetic_Create.restype = ctypes.c_uint32

_dll_Solidean_ExactArithmetic_CreateFromFactor = _dll.Solidean_ExactArithmetic_CreateFromFactor
_dll_Solidean_ExactArithmetic_CreateFromFactor.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_float, ctypes.c_uint32]
_dll_Solidean_ExactArithmetic_CreateFromFactor.restype = ctypes.c_uint32

_dll_Solidean_ExactArithmetic_Release = _dll.Solidean_ExactArithmetic_Release
_dll_Solidean_ExactArithmetic_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_ExactArithmetic_Release.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_Create = _dll.Solidean_MeshBuilder_Create
_dll_Solidean_MeshBuilder_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
_dll_Solidean_MeshBuilder_Create.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_Release = _dll.Solidean_MeshBuilder_Release
_dll_Solidean_MeshBuilder_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_MeshBuilder_Release.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_CreateFromSurface = _dll.Solidean_MeshBuilder_CreateFromSurface
_dll_Solidean_MeshBuilder_CreateFromSurface.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_MeshBuilder_CreateFromSurface.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_CreateFromSurfaces = _dll.Solidean_MeshBuilder_CreateFromSurfaces
_dll_Solidean_MeshBuilder_CreateFromSurfaces.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_MeshBuilder_CreateFromSurfaces.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_AddSurface = _dll.Solidean_MeshBuilder_AddSurface
_dll_Solidean_MeshBuilder_AddSurface.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_MeshBuilder_AddSurface.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_AllowSurfaceIntersections = _dll.Solidean_MeshBuilder_AllowSurfaceIntersections
_dll_Solidean_MeshBuilder_AllowSurfaceIntersections.argtypes = [ctypes.c_uint64]
_dll_Solidean_MeshBuilder_AllowSurfaceIntersections.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_AllowNestedComponents = _dll.Solidean_MeshBuilder_AllowNestedComponents
_dll_Solidean_MeshBuilder_AllowNestedComponents.argtypes = [ctypes.c_uint64]
_dll_Solidean_MeshBuilder_AllowNestedComponents.restype = ctypes.c_uint32

_dll_Solidean_MeshBuilder_AllowNonSupersolid = _dll.Solidean_MeshBuilder_AllowNonSupersolid
_dll_Solidean_MeshBuilder_AllowNonSupersolid.argtypes = [ctypes.c_uint64]
_dll_Solidean_MeshBuilder_AllowNonSupersolid.restype = ctypes.c_uint32

_dll_Solidean_Mesh_Create = _dll.Solidean_Mesh_Create
_dll_Solidean_Mesh_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Mesh_Create.restype = ctypes.c_uint32

_dll_Solidean_Mesh_CreateFromSurfaceBuilder = _dll.Solidean_Mesh_CreateFromSurfaceBuilder
_dll_Solidean_Mesh_CreateFromSurfaceBuilder.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Mesh_CreateFromSurfaceBuilder.restype = ctypes.c_uint32

_dll_Solidean_Mesh_CreateFromTrianglesF32 = _dll.Solidean_Mesh_CreateFromTrianglesF32
_dll_Solidean_Mesh_CreateFromTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Mesh_CreateFromTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Mesh_CreateFromTrianglesF32WithID = _dll.Solidean_Mesh_CreateFromTrianglesF32WithID
_dll_Solidean_Mesh_CreateFromTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Mesh_CreateFromTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32 = _dll.Solidean_Mesh_CreateFromIndexedTrianglesF32
_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32WithID = _dll.Solidean_Mesh_CreateFromIndexedTrianglesF32WithID
_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Mesh_CreateFromIndexedTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Mesh_Release = _dll.Solidean_Mesh_Release
_dll_Solidean_Mesh_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_Mesh_Release.restype = ctypes.c_uint32

_dll_Solidean_Operation_Create = _dll.Solidean_Operation_Create
_dll_Solidean_Operation_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_Create.restype = ctypes.c_uint32

_dll_Solidean_Operation_Release = _dll.Solidean_Operation_Release
_dll_Solidean_Operation_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_Operation_Release.restype = ctypes.c_uint32

_dll_Solidean_Operation_Input = _dll.Solidean_Operation_Input
_dll_Solidean_Operation_Input.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_Input.restype = ctypes.c_uint32

_dll_Solidean_Operation_Output = _dll.Solidean_Operation_Output
_dll_Solidean_Operation_Output.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_Output.restype = ctypes.c_uint32

_dll_Solidean_Operation_Union = _dll.Solidean_Operation_Union
_dll_Solidean_Operation_Union.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_Operation_Union.restype = ctypes.c_uint32

_dll_Solidean_Operation_SelfUnion = _dll.Solidean_Operation_SelfUnion
_dll_Solidean_Operation_SelfUnion.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_SelfUnion.restype = ctypes.c_uint32

_dll_Solidean_Operation_Difference = _dll.Solidean_Operation_Difference
_dll_Solidean_Operation_Difference.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_Operation_Difference.restype = ctypes.c_uint32

_dll_Solidean_Operation_DifferenceSymmetric = _dll.Solidean_Operation_DifferenceSymmetric
_dll_Solidean_Operation_DifferenceSymmetric.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_Operation_DifferenceSymmetric.restype = ctypes.c_uint32

_dll_Solidean_Operation_Intersection = _dll.Solidean_Operation_Intersection
_dll_Solidean_Operation_Intersection.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_Operation_Intersection.restype = ctypes.c_uint32

_dll_Solidean_Operation_ResolveIntersections = _dll.Solidean_Operation_ResolveIntersections
_dll_Solidean_Operation_ResolveIntersections.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ResolveIntersections.restype = ctypes.c_uint32

_dll_Solidean_Operation_ImportFromTrianglesF32 = _dll.Solidean_Operation_ImportFromTrianglesF32
_dll_Solidean_Operation_ImportFromTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Operation_ImportFromTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Operation_ImportFromTrianglesF32WithID = _dll.Solidean_Operation_ImportFromTrianglesF32WithID
_dll_Solidean_Operation_ImportFromTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Operation_ImportFromTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Operation_ImportFromIndexedTrianglesF32 = _dll.Solidean_Operation_ImportFromIndexedTrianglesF32
_dll_Solidean_Operation_ImportFromIndexedTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Operation_ImportFromIndexedTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Operation_ImportFromIndexedTrianglesF32WithID = _dll.Solidean_Operation_ImportFromIndexedTrianglesF32WithID
_dll_Solidean_Operation_ImportFromIndexedTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Operation_ImportFromIndexedTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportToTrianglesF32 = _dll.Solidean_Operation_ExportToTrianglesF32
_dll_Solidean_Operation_ExportToTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ExportToTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportToTrianglesF32WithID = _dll.Solidean_Operation_ExportToTrianglesF32WithID
_dll_Solidean_Operation_ExportToTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ExportToTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportToIndexedTrianglesF32 = _dll.Solidean_Operation_ExportToIndexedTrianglesF32
_dll_Solidean_Operation_ExportToIndexedTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ExportToIndexedTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportToIndexedTrianglesF32WithID = _dll.Solidean_Operation_ExportToIndexedTrianglesF32WithID
_dll_Solidean_Operation_ExportToIndexedTrianglesF32WithID.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ExportToIndexedTrianglesF32WithID.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportDefectNetwork = _dll.Solidean_Operation_ExportDefectNetwork
_dll_Solidean_Operation_ExportDefectNetwork.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_ExportDefectNetwork.restype = ctypes.c_uint32

_dll_Solidean_Operation_ExportMesh = _dll.Solidean_Operation_ExportMesh
_dll_Solidean_Operation_ExportMesh.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_Operation_ExportMesh.restype = ctypes.c_uint32

_dll_Solidean_Operation_Heal = _dll.Solidean_Operation_Heal
_dll_Solidean_Operation_Heal.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_Heal.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryArea = _dll.Solidean_Operation_QueryArea
_dll_Solidean_Operation_QueryArea.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryArea.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryVolume = _dll.Solidean_Operation_QueryVolume
_dll_Solidean_Operation_QueryVolume.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryVolume.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryIsSupersolid = _dll.Solidean_Operation_QueryIsSupersolid
_dll_Solidean_Operation_QueryIsSupersolid.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryIsSupersolid.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryIsSolid = _dll.Solidean_Operation_QueryIsSolid
_dll_Solidean_Operation_QueryIsSolid.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryIsSolid.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryHasNestedComponents = _dll.Solidean_Operation_QueryHasNestedComponents
_dll_Solidean_Operation_QueryHasNestedComponents.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryHasNestedComponents.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryHasSelfIntersections = _dll.Solidean_Operation_QueryHasSelfIntersections
_dll_Solidean_Operation_QueryHasSelfIntersections.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryHasSelfIntersections.restype = ctypes.c_uint32

_dll_Solidean_Operation_QueryHasSurfaceIntersections = _dll.Solidean_Operation_QueryHasSurfaceIntersections
_dll_Solidean_Operation_QueryHasSurfaceIntersections.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Operation_QueryHasSurfaceIntersections.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_Release = _dll.Solidean_SurfaceBuilder_Release
_dll_Solidean_SurfaceBuilder_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_SurfaceBuilder_Release.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_CreateFromTrianglesF32 = _dll.Solidean_SurfaceBuilder_CreateFromTrianglesF32
_dll_Solidean_SurfaceBuilder_CreateFromTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32]
_dll_Solidean_SurfaceBuilder_CreateFromTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_CreateFromIndexedTrianglesF32 = _dll.Solidean_SurfaceBuilder_CreateFromIndexedTrianglesF32
_dll_Solidean_SurfaceBuilder_CreateFromIndexedTrianglesF32.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_float), ctypes.c_uint64, ctypes.POINTER(ctypes.c_int32), ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint32]
_dll_Solidean_SurfaceBuilder_CreateFromIndexedTrianglesF32.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_AllowSelfIntersections = _dll.Solidean_SurfaceBuilder_AllowSelfIntersections
_dll_Solidean_SurfaceBuilder_AllowSelfIntersections.argtypes = [ctypes.c_uint64]
_dll_Solidean_SurfaceBuilder_AllowSelfIntersections.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_TrackID = _dll.Solidean_SurfaceBuilder_TrackID
_dll_Solidean_SurfaceBuilder_TrackID.argtypes = [ctypes.c_uint64, ctypes.c_uint32, ctypes.c_uint32]
_dll_Solidean_SurfaceBuilder_TrackID.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_TrackIDRaw = _dll.Solidean_SurfaceBuilder_TrackIDRaw
_dll_Solidean_SurfaceBuilder_TrackIDRaw.argtypes = [ctypes.c_uint64, ctypes.c_uint64]
_dll_Solidean_SurfaceBuilder_TrackIDRaw.restype = ctypes.c_uint32

_dll_Solidean_SurfaceBuilder_TrackPrimitiveIDs = _dll.Solidean_SurfaceBuilder_TrackPrimitiveIDs
_dll_Solidean_SurfaceBuilder_TrackPrimitiveIDs.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64, ctypes.c_uint32]
_dll_Solidean_SurfaceBuilder_TrackPrimitiveIDs.restype = ctypes.c_uint32

_dll_Solidean_Surface_Create = _dll.Solidean_Surface_Create
_dll_Solidean_Surface_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint64]
_dll_Solidean_Surface_Create.restype = ctypes.c_uint32

_dll_Solidean_Surface_Release = _dll.Solidean_Surface_Release
_dll_Solidean_Surface_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_Surface_Release.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_Create = _dll.Solidean_TypedBlob_Create
_dll_Solidean_TypedBlob_Create.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64)]
_dll_Solidean_TypedBlob_Create.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_CreateWithFixedBuffer = _dll.Solidean_TypedBlob_CreateWithFixedBuffer
_dll_Solidean_TypedBlob_CreateWithFixedBuffer.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint64), ctypes.POINTER(ctypes.c_uint8), ctypes.c_uint64]
_dll_Solidean_TypedBlob_CreateWithFixedBuffer.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_Release = _dll.Solidean_TypedBlob_Release
_dll_Solidean_TypedBlob_Release.argtypes = [ctypes.c_uint64]
_dll_Solidean_TypedBlob_Release.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_HasData = _dll.Solidean_TypedBlob_HasData
_dll_Solidean_TypedBlob_HasData.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
_dll_Solidean_TypedBlob_HasData.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_GetData = _dll.Solidean_TypedBlob_GetData
_dll_Solidean_TypedBlob_GetData.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint64), ctypes.c_uint32]
_dll_Solidean_TypedBlob_GetData.restype = ctypes.c_uint32

_dll_Solidean_TypedBlob_GetType = _dll.Solidean_TypedBlob_GetType
_dll_Solidean_TypedBlob_GetType.argtypes = [ctypes.c_uint64, ctypes.POINTER(ctypes.c_uint32)]
_dll_Solidean_TypedBlob_GetType.restype = ctypes.c_uint32


# =================================
#             Classes
# =================================

class Context:
    """
        Root object managing all Solidean operations, memory, and scheduling
    
        The context is the root object for all Solidean operations and data types.
        It manages internal memory, schedules operations, and holds the internal threadpool.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == Context.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> Context:
        """Internal: create wrapper from native handle."""
        return Context(Context.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_Context_Destroy(self._native_handle)
            self._native_handle = None

    @classmethod
    def create(cls) -> Context:
        """
            Initializes a new context, performing setup and license checks
        
            Initializes a new Solidean Context.
            This is a relatively expensive function, as it also performs license checking, scratch memory allocation, and starting thread pools if configured.
            Re-using the same context for the whole application lifetime is encouraged.
            NOTE: every created context must be eventually destroyed by calling ::Destroy.
        """
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_Context_Create(ctypes.byref(new_handle))
        if _res != 0:
            raise SolideanException(Result(_res))
        return Context._create_from_native(new_handle.value)

    def execute(self, op: Operation, *, mode: Union[ExecuteMode, int] = ExecuteMode.Multithreaded) -> ExecuteResult:
        """
            Runs a given operation in the context, blocking until completion
        
            Executes a given operation.
            This call blocks until the operation is fully executed.
            The result value indicates if any error occurred during execution.
            In that case, check the operation error log.
        
            NOTE: this does NOT call Operation::Release. You MUST still call that yourself.
        """
        assert self._native_handle is not None, 'Context has been released'
        result = ctypes.c_uint32()
        mode = mode.value if isinstance(mode, ExecuteMode) else mode
        _res = _dll_Solidean_Context_Execute(self._native_handle, ctypes.byref(result), op._native_handle, mode)
        if _res != 0:
            raise SolideanException(Result(_res))
        result = ExecuteResult(result.value)
        return result

    def create_exact_arithmetic(self, max_coord: float, *, kernel: Union[ArithmeticKernel, int] = ArithmeticKernel.Fixed256Pos26) -> ExactArithmetic:
        """Constructs an exact arithmetic context from a bounding box maximum coordinate"""
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        kernel = kernel.value if isinstance(kernel, ArithmeticKernel) else kernel
        _res = _dll_Solidean_ExactArithmetic_Create(self._native_handle, ctypes.byref(new_handle), max_coord, kernel)
        if _res != 0:
            raise SolideanException(Result(_res))
        return ExactArithmetic._create_from_native(new_handle.value)

    def create_exact_arithmetic_from_factor(self, factor: float, *, kernel: Union[ArithmeticKernel, int] = ArithmeticKernel.Fixed256Pos26) -> ExactArithmetic:
        """
            Constructs an exact arithmetic context from a custom float-to-int conversion factor
        
            Creates an exact arithmetic based on a provided conversion factor from float to int.
        
            If factor == 1, then this basically allows to pass integers directly (at least the 24 bit afforded by the float mantissa).
        
            NOTE: inputs must not be larger than 2^26 / factor.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        kernel = kernel.value if isinstance(kernel, ArithmeticKernel) else kernel
        _res = _dll_Solidean_ExactArithmetic_CreateFromFactor(self._native_handle, ctypes.byref(new_handle), factor, kernel)
        if _res != 0:
            raise SolideanException(Result(_res))
        return ExactArithmetic._create_from_native(new_handle.value)

    def create_mesh_builder(self) -> MeshBuilder:
        """
            Creates an empty mesh builder for adding surfaces incrementally
        
            Creates an empty mesh builder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_MeshBuilder_Create(self._native_handle, ctypes.byref(new_handle))
        if _res != 0:
            raise SolideanException(Result(_res))
        return MeshBuilder._create_from_native(new_handle.value)

    def create_mesh_builder_from_surface(self, surface: Surface) -> MeshBuilder:
        """
            Initializes a mesh builder with a single surface
        
            Creates a default mesh builder populated with the given surface.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_MeshBuilder_CreateFromSurface(self._native_handle, ctypes.byref(new_handle), surface._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        return MeshBuilder._create_from_native(new_handle.value)

    def create_mesh_builder_from_surfaces(self, surfaces: List[Surface]) -> MeshBuilder:
        """
            Initializes a mesh builder with multiple surfaces
        
            Creates a default mesh builder populated with the given surfaces.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        surfaces_handles = [obj._native_handle for obj in surfaces]
        surfaces_arr = (ctypes.c_uint64 * len(surfaces_handles))(*surfaces_handles)
        _res = _dll_Solidean_MeshBuilder_CreateFromSurfaces(self._native_handle, ctypes.byref(new_handle), surfaces_arr, len(surfaces_handles))
        if _res != 0:
            raise SolideanException(Result(_res))
        return MeshBuilder._create_from_native(new_handle.value)

    def create_mesh(self, builder: MeshBuilder) -> Mesh:
        """
            Constructs a mesh from a mesh builder definition
        
            Creates a mesh from a given mesh definition.
        
            NOTE: meshes are immutable. They will always reflect their initial definition.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_Mesh_Create(self._native_handle, ctypes.byref(new_handle), builder._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_mesh_from_surface_builder(self, builder: SurfaceBuilder) -> Mesh:
        """
            Constructs a mesh directly from a surface builder using defaults
        
            Creates a mesh from a surface builder using a defaulted MeshBuilder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_Mesh_CreateFromSurfaceBuilder(self._native_handle, ctypes.byref(new_handle), builder._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_mesh_from_triangles_f32(self, triangles: Union[NDArray[np.float32], List[float]], arithmetic: ExactArithmetic, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> Mesh:
        """
            Constructs a mesh from a float32 triangle soup with exact arithmetic
        
            Creates a mesh from a triangle soup.
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        triangles_arr = np.asarray(triangles, dtype=np.float32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 9 == 0, 'Flattened array size must be divisible by 9'
            triangles_arr = triangles_arr.reshape(-1, 9)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 9, 'Second dimension must be exactly 9'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 9)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Mesh_CreateFromTrianglesF32(self._native_handle, ctypes.byref(new_handle), triangles_ptr, triangles_count, arithmetic._native_handle, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_mesh_from_triangles_f32_with_id(self, triangles: Union[NDArray[np.float32], List[float]], arithmetic: ExactArithmetic, surface_id: int, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> Mesh:
        """
            Constructs a mesh from a float32 triangle soup with primitive tracking IDs
        
            Creates a mesh from a triangle soup.
        
            The provided surfaceID is used to set up primitive tracking via SurfaceBuilder::TrackID(surfaceID).
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        triangles_arr = np.asarray(triangles, dtype=np.float32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 9 == 0, 'Flattened array size must be divisible by 9'
            triangles_arr = triangles_arr.reshape(-1, 9)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 9, 'Second dimension must be exactly 9'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 9)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Mesh_CreateFromTrianglesF32WithID(self._native_handle, ctypes.byref(new_handle), triangles_ptr, triangles_count, arithmetic._native_handle, surface_id, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_mesh_from_indexed_triangles_f32(self, positions: Union[NDArray[np.float32], List[float]], triangles: Union[NDArray[np.int32], List[int]], arithmetic: ExactArithmetic, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> Mesh:
        """
            Constructs a mesh from indexed float32 triangles with exact arithmetic
        
            Creates a mesh from a indexed triangle list.
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        positions_arr = np.asarray(positions, dtype=np.float32)
        if positions_arr.ndim == 1:
            assert positions_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            positions_arr = positions_arr.reshape(-1, 3)
        elif positions_arr.ndim == 2:
            assert positions_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        positions_arr = np.ascontiguousarray(positions_arr)
        positions_ptr = positions_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        positions_count = positions_arr.shape[0]
        triangles_arr = np.asarray(triangles, dtype=np.int32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            triangles_arr = triangles_arr.reshape(-1, 3)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Mesh_CreateFromIndexedTrianglesF32(self._native_handle, ctypes.byref(new_handle), positions_ptr, positions_count, triangles_ptr, triangles_count, arithmetic._native_handle, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_mesh_from_indexed_triangles_f32_with_id(self, positions: Union[NDArray[np.float32], List[float]], triangles: Union[NDArray[np.int32], List[int]], arithmetic: ExactArithmetic, surface_id: int, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> Mesh:
        """
            Constructs a mesh from indexed float32 triangles with primitive tracking IDs
        
            Creates a mesh from a indexed triangle list.
        
            The provided surfaceID is used to set up primitive tracking via SurfaceBuilder::TrackID(surfaceID).
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        positions_arr = np.asarray(positions, dtype=np.float32)
        if positions_arr.ndim == 1:
            assert positions_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            positions_arr = positions_arr.reshape(-1, 3)
        elif positions_arr.ndim == 2:
            assert positions_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        positions_arr = np.ascontiguousarray(positions_arr)
        positions_ptr = positions_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        positions_count = positions_arr.shape[0]
        triangles_arr = np.asarray(triangles, dtype=np.int32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            triangles_arr = triangles_arr.reshape(-1, 3)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Mesh_CreateFromIndexedTrianglesF32WithID(self._native_handle, ctypes.byref(new_handle), positions_ptr, positions_count, triangles_ptr, triangles_count, arithmetic._native_handle, surface_id, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Mesh._create_from_native(new_handle.value)

    def create_operation(self, arithmetic: ExactArithmetic) -> Operation:
        """
            Creates a new operation with a chosen arithmetic context
        
            Creates a new, empty operation.
            After adding all desired sub-operations, queries, and commands, call Context::Execute.
        
            The arithmetic describes the underlying math that guarantees exact results.
        
            IMPORTANT: only meshes with the same arithmetic can be used together.
        
            NOTE: You still have to manually call ::Release. Until then, you can still query the log and stats of the operation.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Create(self._native_handle, ctypes.byref(new_handle), arithmetic._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Operation._create_from_native(new_handle.value, self)

    def create_surface_builder_from_triangles_f32(self, triangles: Union[NDArray[np.float32], List[float]], arithmetic: ExactArithmetic, *, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> SurfaceBuilder:
        """
            Defines a surface from a float32 triangle soup with exact arithmetic
        
            Defines a surface using a triangle soup.
        
            See Lifetime for the requirements on the user-provided data.
        
            Note: the provided ExactArithmetic uniquely defines how the floating point data will be transformed into an exact representation. See the manual for a high-level introduction.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        triangles_arr = np.asarray(triangles, dtype=np.float32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 9 == 0, 'Flattened array size must be divisible by 9'
            triangles_arr = triangles_arr.reshape(-1, 9)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 9, 'Second dimension must be exactly 9'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 9)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        triangles_count = triangles_arr.shape[0]
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_SurfaceBuilder_CreateFromTrianglesF32(self._native_handle, ctypes.byref(new_handle), triangles_ptr, triangles_count, arithmetic._native_handle, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return SurfaceBuilder._create_from_native(new_handle.value)

    def create_surface_builder_from_indexed_triangles_f32(self, positions: Union[NDArray[np.float32], List[float]], triangles: Union[NDArray[np.int32], List[int]], arithmetic: ExactArithmetic, *, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> SurfaceBuilder:
        """
            Defines a surface from indexed float32 triangles with exact arithmetic
        
            Defines a surface using an indexed triangle list.
        
            See Lifetime for the requirements on the user-provided data.
        
            Note: the provided ExactArithmetic uniquely defines how the floating point data will be transformed into an exact representation. See the manual for a high-level introduction.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        positions_arr = np.asarray(positions, dtype=np.float32)
        if positions_arr.ndim == 1:
            assert positions_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            positions_arr = positions_arr.reshape(-1, 3)
        elif positions_arr.ndim == 2:
            assert positions_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        positions_arr = np.ascontiguousarray(positions_arr)
        positions_ptr = positions_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        positions_count = positions_arr.shape[0]
        triangles_arr = np.asarray(triangles, dtype=np.int32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            triangles_arr = triangles_arr.reshape(-1, 3)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
        triangles_count = triangles_arr.shape[0]
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_SurfaceBuilder_CreateFromIndexedTrianglesF32(self._native_handle, ctypes.byref(new_handle), positions_ptr, positions_count, triangles_ptr, triangles_count, arithmetic._native_handle, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        return SurfaceBuilder._create_from_native(new_handle.value)

    def create_surface(self, builder: SurfaceBuilder) -> Surface:
        """
            Constructs a surface from a surface builder definition
        
            Creates a surface from a given surface definition.
        
            NOTE: surfaces are immutable. They will always reflect their initial definition.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_Surface_Create(self._native_handle, ctypes.byref(new_handle), builder._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        return Surface._create_from_native(new_handle.value)

    def create_typed_blob(self) -> TypedBlob:
        """
            Creates an uninitialized TypedBlob with auto-managed memory
        
            Creates an uninitialized TypeBlob with internally managed auto-growing memory.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        _res = _dll_Solidean_TypedBlob_Create(self._native_handle, ctypes.byref(new_handle))
        if _res != 0:
            raise SolideanException(Result(_res))
        return TypedBlob._create_from_native(new_handle.value)

    def create_typed_blob_with_fixed_buffer(self, buffer: Union[NDArray[np.uint8], List[int]]) -> TypedBlob:
        """
            Creates a TypedBlob backed by fixed-size user-provided memory
        
            Creates a TypedBlob buffer that is backed by fixed-size user memory.
        
            NOTE: this TypedBlob is still uninitialized and must be populated, e.g. by an Operation::ExportXYZ call.
        
            NOTE: the buffer must stay alive until TypedBlob::Release is called.
        """
        assert self._native_handle is not None, 'Context has been destroyed'
        new_handle = ctypes.c_uint64()
        buffer_arr = np.asarray(buffer, dtype=np.uint8)
        buffer_arr = np.ascontiguousarray(buffer_arr)
        buffer_ptr = buffer_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        buffer_count = buffer_arr.shape[0]
        _res = _dll_Solidean_TypedBlob_CreateWithFixedBuffer(self._native_handle, ctypes.byref(new_handle), buffer_ptr, buffer_count)
        if _res != 0:
            raise SolideanException(Result(_res))
        return TypedBlob._create_from_native(new_handle.value)


class ExactArithmetic:
    """
        Solidean’s exact arithmetic context ensuring robust Boolean operations
    
        Solidean takes great care to provide strong exactness guarantees.
        For that, we are working in special exact arithmetics that are closed under the provided operations.
    
        The core insight is that Boolean operations on floating point meshes can never yield another floating point mesh without becoming inexact.
        An approximate result at the end might be acceptable, but approximate intermediate result jeopardize the accuracy and topology of all subsequent operations.
    
        However, floating points are not the only available computationally viable discretization of the real numbers.
        Traditionally, BigInteger, BigRational, BigFloat types provide various exactness guarantees at the cost of unacceptable slowdowns.
        In contrast, our Surrat Compiler generates highly optimized code for fixed-width surreal rational numbers, which are the type of numbers we need to guarantee exact Booleans, exact ray tracing, and various related operations.
    
        In concrete terms, we internally convert all geometry into a plane-based representation where plane normals have roughly 55 bit per component and the plane distance about 80 bit.
        Three planes define a point (x,y,z,w) in homogeneous coordinates, where x,y,z have about 195 bit each and w has about 170 bit.
        This choice guarantees that all important operations fit into 256 bit integer logic.
        If the planes are not given, they can be reconstructed from (x,y,z) integer position meshes as long as each component is at most 26 bit.
        When constructing the planes directly, a higher positional accuracy can be achieved at the same bit depth.
    
        This 256 bit logic is one particular choice with a decent speed-vs-accuracy tradeoff.
        Other choices will be exposed in the future as well.
    
        IMPORTANT: floating-point meshes are discretized into 26 bit integers on import to construct the exact internal representation.
        Once in the internal representation, all operations are exact.
        There is an important conceptual difference between the number system:
        Floating-point numbers have a relative accuracy and a large dynamic range (10^-38 to 10^38).
        Our coordinate system has an absolute accuracy and a fixed range.
        Thus, the user has to specify a bounding box in which all computation takes place.
        The accuracy is then about 7 decimal places in this bounding box.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == ExactArithmetic.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> ExactArithmetic:
        """Internal: create wrapper from native handle."""
        return ExactArithmetic(ExactArithmetic.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_ExactArithmetic_Release(self._native_handle)
            self._native_handle = None


class MeshBuilder:
    """
        Builder for constructing immutable meshes from one or more surfaces
    
        Meshes are immutable.
        Their setup is completely defined by this builder object, which can be built up incrementally.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == MeshBuilder.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> MeshBuilder:
        """Internal: create wrapper from native handle."""
        return MeshBuilder(MeshBuilder.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_MeshBuilder_Release(self._native_handle)
            self._native_handle = None

    def add_surface(self, surface: Surface) -> None:
        """
            Adds another surface to the current mesh builder
        
            Adds a surface to the builder of the mesh.
        """
        assert self._native_handle is not None, 'MeshBuilder has been released'
        _res = _dll_Solidean_MeshBuilder_AddSurface(self._native_handle, surface._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))

    def allow_surface_intersections(self) -> None:
        """
            Marks that different surfaces of the mesh may intersect each other
        
            By default, surfaces of the mesh are assumed to be pairwise non-intersecting.
            Enabling this means that two different surfaces of the same mesh could have intersecting primitives.
        
            NOTE: enabling this has a non-trivial performance penalty. Only set this if you actually have data like this.
        
            NOTE: if a single surface might have self-intersections, you need to set SurfaceBuilder::AllowSelfIntersections.
        """
        assert self._native_handle is not None, 'MeshBuilder has been released'
        _res = _dll_Solidean_MeshBuilder_AllowSurfaceIntersections(self._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))

    def allow_nested_components(self) -> None:
        """
            Marks that the mesh may contain nested components with winding numbers greater than one
        
            By default, a Mesh models a solid.
            You can be inside or outside the solid, but not "twice inside".
            This means that the winding number of this Mesh is always 0 or 1 and surfaces always transition from 0 to 1.
        
            Enabling this means that the mesh might have components that are "twice inside" or more.
        
            Consider two nested sphere surfaces in the same Mesh.
            If the normals of the outer sphere point outwards and that of the inner inwards, then this is a hollow sphere and NOT a case of nested components.
            However, if both normals point outwards, then the inner sphere is "twice inside" and has a winding number of 2.
            In that case, you need to set this property for correct results.
        
            NOTE: Allowing surface- or self-intersections already implies nested components.
                  However, the nested sphere example has no surface- or self-intersections.
                  AllowNestedComponents without the intersection flags has less performance penalty than with.
        
            NOTE: this is an advanced usage flag of a relatively rare use case.
        """
        assert self._native_handle is not None, 'MeshBuilder has been released'
        _res = _dll_Solidean_MeshBuilder_AllowNestedComponents(self._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))

    def allow_non_supersolid(self) -> None:
        """
            Marks that the mesh may be non-supersolid, e.g. with holes or non-manifold configurations
        
            By default, a Mesh models a solid.
            When allowing (inner- or intra-)surface intersections or nested components, the Mesh models a supersolid.
            If the geometry has open borders or certain non-manifold configurations, it is colloquially known as "bad input".
            Most operations require at least supersolid input.
        
            If your input is not supersolid, e.g. contains holes, then it must be marked as such by calling this function.
            Most operations do not work on non-supersolid and will result in Result::OperandMustBeSupersolid.
            The main way to use such a mesh in a boolean is to call Operation::Heal beforehand.
        
            IMPORTANT: this flag does NOT imply AllowSelfIntersections or AllowSurfaceIntersections for added surfaces.
            The most conservative (and slowest) configuration is AllowNonSupersolid and AllowSurfaceIntersections and marking all surfaces as AllowSelfIntersections.
        """
        assert self._native_handle is not None, 'MeshBuilder has been released'
        _res = _dll_Solidean_MeshBuilder_AllowNonSupersolid(self._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))


class Mesh:
    """
        Immutable collection of surfaces forming a solid or supersolid mesh
    
        A Solidean Mesh represents geometry in a broader sense.
        A Mesh consists of a collection of surfaces and some metadata.
        Usually, a mesh is a *solid mesh*, the enclosing boundary of a solid volume.
        However, meshes can also be configured to allow for self-intersections and nested components, resulting in the more general class of supersolid meshes.
        Any combination of supersolid meshes has well-defined Boolean results.
        Other configurations allow processing of meshes with small and even large holes in a best-effort fashion.
    
        NOTE: Individual surfaces are usually not closed or solid. Only all surfaces together form a closed mesh.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == Mesh.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> Mesh:
        """Internal: create wrapper from native handle."""
        return Mesh(Mesh.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_Mesh_Release(self._native_handle)
            self._native_handle = None


class Operation:
    """
        Command buffer for recording, optimizing, and executing mesh operations
    
        An operation realizes a Command Buffer pattern.
        Many elementary operations, queries, and commands can be recorded in a single Operation.
        Using Context::Execute, Operations can be executed.
        Internally, the Solidean engine computes an optimized schedule to execute the whole Operation.
    
        Defining the individual steps of an Operation has no error checking.
        Inputs are Operands that have been introduced using ::Input or ::Import.
        The return value are Operands that represent the result symbolically.
        This Operand is only valid in the source Operation.
        Any result must be exported using ::Output or ::Export and similar functions.
        Error handling is performed during Context::Execute and can be checked in the Operation's error log.
    
        During Execution, an Operation will optimized all given sub-operations.
        In particular, Operands that are not saved via ::Output will in most cases never be explicitly created.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int, ctx: 'Context'):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == Operation.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle
        self._ctx = ctx

    @staticmethod
    def _create_from_native(native_handle: int, ctx: 'Context') -> Operation:
        """Internal: create wrapper from native handle."""
        return Operation(Operation.__private_init, native_handle, ctx)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_Operation_Release(self._native_handle)
            self._native_handle = None

    def __enter__(self) -> Operation:
        """Context manager entry: returns self for use in 'with' statements."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit: executes operation if no exception occurred."""
        if exc_type is not None:
            return False  # Propagate exception

        result = self._ctx.execute(self)
        if result != ExecuteResult.Ok:
            raise SolideanException(result)
        return False

    def input(self, in_mesh: Mesh) -> MeshOperand:
        """
            Introduces a persistent mesh as an operand into an operation
        
            Creates an Operand for the given persistent Mesh.
            This is a symbolic value that is used in further sub-operations.
        
            NOTE: it is safe to call Mesh::Release after this call.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Input(self._native_handle, ctypes.byref(mesh), in_mesh._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def output(self, local_mesh: MeshOperand) -> Mesh:
        """
            Marks an operand to be materialized as a persistent mesh after execution
        
            Ensures that the given MeshOperand is materialized into a persistent Mesh after the Operation is executed.
            If you want to use a result in a later Operation, making a Mesh Output is the recommended way.
            This mesh represents an exact result and is lossless.
            It usually contains additional surface types that the inputs did not have.
            For example, computing the ::Intersection of two Meshes consisting of indexed float triangle surfaces will result in some meshlet surfaces to represent the parts that are not exact in floating point.
        
            NOTE: while this function immediately returns the handle of the result, it will only become valid after the Operation is executed (see Context::Execute).
        
            NOTE: this creates a new MeshHandle, so you have to call Mesh::Release on it
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Output(self._native_handle, ctypes.byref(mesh), local_mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = Mesh._create_from_native(mesh.value)
        return mesh

    def union(self, mesh_a: MeshOperand, mesh_b: MeshOperand) -> MeshOperand:
        """
            Computes the union of two mesh operands
        
            Returns "meshA union meshB", i.e. a mesh that represents all points of A and all points of B together.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Union(self._native_handle, ctypes.byref(mesh), mesh_a, mesh_b)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def self_union(self, in_mesh: MeshOperand) -> MeshOperand:
        """
            Converts a supersolid mesh into a guaranteed solid mesh by removing internal overlaps
        
            Returns the union of "inMesh" with itself, i.e. a solid mesh that does not contain surfaces inside the object.
        
            NOTE: this operation has no effect on meshes that are already strictly solid.
            Only if internal components or some kind of surface intersections are allowed will this actually compute something different.
        
            NOTE: a self-union is NOT the same thing as an outer hull.
            A hollow sphere is already solid (consisting of two sphere surfaces, the inner one oriented towards the center) and the self-union has no effect.
            The outer hull would remove the inner part.
        
            NOTE: this operation is useful to make supersolid meshes guaranteed solid.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_SelfUnion(self._native_handle, ctypes.byref(mesh), in_mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def difference(self, mesh_a: MeshOperand, mesh_b: MeshOperand) -> MeshOperand:
        """
            Computes the subtraction of one mesh operand from another
        
            Returns "meshA \\ meshB", i.e. a mesh that represents all points of A without any point of B.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Difference(self._native_handle, ctypes.byref(mesh), mesh_a, mesh_b)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def difference_symmetric(self, mesh_a: MeshOperand, mesh_b: MeshOperand) -> MeshOperand:
        """
            Computes the symmetric difference between two mesh operands
        
            Returns "(meshA \\ meshB) union (meshB \\ meshA)", i.e. a mesh that represents all points that are either in A or B but not in both.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_DifferenceSymmetric(self._native_handle, ctypes.byref(mesh), mesh_a, mesh_b)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def intersection(self, mesh_a: MeshOperand, mesh_b: MeshOperand) -> MeshOperand:
        """
            Computes the intersection of two mesh operands
        
            Returns "meshA intersect meshB", i.e. a mesh that represents all points that belong to both A and B, i.e. their overlap.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Intersection(self._native_handle, ctypes.byref(mesh), mesh_a, mesh_b)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def resolve_intersections(self, in_mesh: MeshOperand) -> MeshOperand:
        """
            Produces a mesh where no faces intersect each other
        
            Returns a new mesh representing exactly the same surface but where no face properly intersects another face.
        
            NOTE: requires MeshType::Supersolid, MeshType::NonSupersolid, MeshBuilder::AllowSurfaceIntersections, or SurfaceBuilder::AllowSelfIntersections to be meaningful.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ResolveIntersections(self._native_handle, ctypes.byref(mesh), in_mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def import_from_triangles_f32(self, triangles: Union[NDArray[np.float32], List[float]], *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> MeshOperand:
        """
            Creates a mesh operand from a float32 triangle soup
        
            Creates a mesh operand from a triangle soup.
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, create an explicit MeshHandle and go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        triangles_arr = np.asarray(triangles, dtype=np.float32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 9 == 0, 'Flattened array size must be divisible by 9'
            triangles_arr = triangles_arr.reshape(-1, 9)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 9, 'Second dimension must be exactly 9'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 9)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Operation_ImportFromTrianglesF32(self._native_handle, ctypes.byref(mesh), triangles_ptr, triangles_count, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def import_from_triangles_f32_with_id(self, triangles: Union[NDArray[np.float32], List[float]], surface_id: int, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> MeshOperand:
        """
            Creates a mesh operand from a float32 triangle soup with primitive tracking IDs
        
            Creates a mesh operand from a triangle soup.
        
            The provided surfaceID is used to set up primitive tracking via SurfaceBuilder::TrackID(surfaceID).
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, create an explicit MeshHandle and go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        triangles_arr = np.asarray(triangles, dtype=np.float32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 9 == 0, 'Flattened array size must be divisible by 9'
            triangles_arr = triangles_arr.reshape(-1, 9)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 9, 'Second dimension must be exactly 9'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 9)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Operation_ImportFromTrianglesF32WithID(self._native_handle, ctypes.byref(mesh), triangles_ptr, triangles_count, surface_id, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def import_from_indexed_triangles_f32(self, positions: Union[NDArray[np.float32], List[float]], triangles: Union[NDArray[np.int32], List[int]], *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> MeshOperand:
        """
            Creates a mesh operand from indexed float32 triangles
        
            Creates a mesh operand from an indexed triangle list.
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, create an explicit MeshHandle and go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        positions_arr = np.asarray(positions, dtype=np.float32)
        if positions_arr.ndim == 1:
            assert positions_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            positions_arr = positions_arr.reshape(-1, 3)
        elif positions_arr.ndim == 2:
            assert positions_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        positions_arr = np.ascontiguousarray(positions_arr)
        positions_ptr = positions_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        positions_count = positions_arr.shape[0]
        triangles_arr = np.asarray(triangles, dtype=np.int32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            triangles_arr = triangles_arr.reshape(-1, 3)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Operation_ImportFromIndexedTrianglesF32(self._native_handle, ctypes.byref(mesh), positions_ptr, positions_count, triangles_ptr, triangles_count, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def import_from_indexed_triangles_f32_with_id(self, positions: Union[NDArray[np.float32], List[float]], triangles: Union[NDArray[np.int32], List[int]], surface_id: int, *, mesh_type: Union[MeshType, int] = MeshType.Solid, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> MeshOperand:
        """
            Creates a mesh operand from indexed float32 triangles with primitive tracking IDs
        
            Creates a mesh operand from an indexed triangle list.
        
            The provided surfaceID is used to set up primitive tracking via SurfaceBuilder::TrackID(surfaceID).
        
            NOTE: the optional meshType argument allows choosing between some preset types. For full nuance, create an explicit MeshHandle and go via SurfaceBuilder and MeshBuilder.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        positions_arr = np.asarray(positions, dtype=np.float32)
        if positions_arr.ndim == 1:
            assert positions_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            positions_arr = positions_arr.reshape(-1, 3)
        elif positions_arr.ndim == 2:
            assert positions_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        positions_arr = np.ascontiguousarray(positions_arr)
        positions_ptr = positions_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        positions_count = positions_arr.shape[0]
        triangles_arr = np.asarray(triangles, dtype=np.int32)
        if triangles_arr.ndim == 1:
            assert triangles_arr.size % 3 == 0, 'Flattened array size must be divisible by 3'
            triangles_arr = triangles_arr.reshape(-1, 3)
        elif triangles_arr.ndim == 2:
            assert triangles_arr.shape[1] == 3, 'Second dimension must be exactly 3'
        else:
            raise ValueError('Array must be 1D (flattened) or 2D with shape (n, 3)')
        triangles_arr = np.ascontiguousarray(triangles_arr)
        triangles_ptr = triangles_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_int32))
        triangles_count = triangles_arr.shape[0]
        mesh_type = mesh_type.value if isinstance(mesh_type, MeshType) else mesh_type
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_Operation_ImportFromIndexedTrianglesF32WithID(self._native_handle, ctypes.byref(mesh), positions_ptr, positions_count, triangles_ptr, triangles_count, surface_id, mesh_type, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def export_to_triangles_f32(self, mesh: MeshOperand) -> TypedBlob:
        """
            Exports a mesh operand to a flat float32 triangle blob
        
            Converts all primitives of all surfaces into triangles and stores the result in the returned TypedBlob with BlobType::TrianglesF32.
        
            NOTE: Currently, there is no guarantee that vertices on the same exact location are always represented as exactly the same float.
                  Due to rounding, it might be off by up to 3 ULP.
        
            See BlobType::TrianglesF32 for how the resulting bytes are interpreted.
        
            NOTE: Equivalent to ExportMesh(mesh, ExportFormat::Triangles, ExportOption::VertexPositionF32)
        """
        assert self._native_handle is not None, 'Operation has been released'
        triangles = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ExportToTrianglesF32(self._native_handle, ctypes.byref(triangles), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        triangles = TypedBlob._create_from_native(triangles.value)
        return triangles

    def export_to_triangles_f32_with_id(self, mesh: MeshOperand) -> TypedBlob:
        """
            Exports a mesh operand to float32 triangles with primitive tracking IDs
        
            Variant of Operation::ExportToTrianglesF32 with tracking IDs exported.
            Type of the TypedBlob is still BlobType::TrianglesF32 but DataSlot::PrimitiveIDs is available in TypedBlob::GetData.
        
            Tracking is enabled with SurfaceBuilder::TrackID, SurfaceBuilder::TrackIDRaw, and SurfaceBuilder::TrackPrimitiveIDs.
        
            NOTE: see documentation of SurfaceBuilder::TrackID for descriptions of how the IDs work and how the flags are interpreted.
        
            NOTE: this function is useful to transfer input attributes to the output.
        
            NOTE: Equivalent to ExportMesh(mesh, ExportFormat::Triangles, ExportOption::VertexPositionF32 | ExportOption::PrimitiveID)
        """
        assert self._native_handle is not None, 'Operation has been released'
        triangles_with_id = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ExportToTrianglesF32WithID(self._native_handle, ctypes.byref(triangles_with_id), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        triangles_with_id = TypedBlob._create_from_native(triangles_with_id.value)
        return triangles_with_id

    def export_to_indexed_triangles_f32(self, mesh: MeshOperand) -> TypedBlob:
        """
            Exports a mesh operand to an indexed float32 triangle blob
        
            Converts all primitives of all surfaces into an indexed triangle mesh and stores the result in the returned TypedBlob with BlobType::IndexedTrianglesF32.
        
            This operation will make sure all vertices are de-duplicated and all T-junctions are resolved.
        
            In particular, the result will be guaranteed (topologically and geometrically) supersolid if it's the result of a Boolean operation.
            Geometrically connected components can be found via topological connected components.
        
            See BlobType::IndexedTrianglesF32 for how the resulting bytes are interpreted.
        
            NOTE: Equivalent to ExportMesh(mesh, ExportFormat::IndexedTriangles, ExportOption::VertexPositionF32)
        """
        assert self._native_handle is not None, 'Operation has been released'
        triangles = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ExportToIndexedTrianglesF32(self._native_handle, ctypes.byref(triangles), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        triangles = TypedBlob._create_from_native(triangles.value)
        return triangles

    def export_to_indexed_triangles_f32_with_id(self, mesh: MeshOperand) -> TypedBlob:
        """
            Exports a mesh operand to indexed float32 triangles with primitive tracking IDs
        
            Variant of Operation::ExportToIndexedTrianglesF32 with tracking IDs exported.
            Type of the TypedBlob is still BlobType::IndexedTrianglesF32 but DataSlot::PrimitiveIDs is available in TypedBlob::GetData.
        
            Tracking is enabled with SurfaceBuilder::TrackID, SurfaceBuilder::TrackIDRaw, and SurfaceBuilder::TrackPrimitiveIDs.
        
            NOTE: see documentation of SurfaceBuilder::TrackID for descriptions of how the IDs work and how the flags are interpreted.
        
            NOTE: this function is useful to transfer input attributes to the output.
        
            NOTE: Equivalent to ExportMesh(mesh, ExportFormat::IndexedTriangles, ExportOption::VertexPositionF32 | ExportOption::PrimitiveID)
        """
        assert self._native_handle is not None, 'Operation has been released'
        triangles_with_id = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ExportToIndexedTrianglesF32WithID(self._native_handle, ctypes.byref(triangles_with_id), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        triangles_with_id = TypedBlob._create_from_native(triangles_with_id.value)
        return triangles_with_id

    def export_defect_network(self, mesh: MeshOperand) -> TypedBlob:
        """
            Exports the defect network of a mesh to analyze non-supersolid edges
        
            A mesh is not supersolid if it has (resolved) edges that are not topologically supersolid, i.e. where not every edge segment is matched by another primitive that has this segment in opposite direction.
            An edge segment with a mismatch is called a defect edge.
            The integer defect denotes how often the segment needs to be added in opposite direction to make it supersolid.
        
            This network is internally used as the basis for Operation::Heal.
        
            The result is stored in a TypedBlob with BlobType::DefectNetwork and DataSlot::PositionsF32/SegmentsIndexed/Defects.
        """
        assert self._native_handle is not None, 'Operation has been released'
        defect_network = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_ExportDefectNetwork(self._native_handle, ctypes.byref(defect_network), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        defect_network = TypedBlob._create_from_native(defect_network.value)
        return defect_network

    def export_mesh(self, mesh: MeshOperand, format: Union[ExportFormat, int], options: Union[ExportOption, int]) -> TypedBlob:
        """
            Configurable export of a mesh operand to a chosen format and options
        
            Configurable universal mesh export that subsumes ExportToXyz and provides a plethora of options and guarantees.
            Subsumes most other export functions.
        
            Notably, this function is able to create guaranteed manifold results for any input mesh.
            It is also currently the only way to export an exact representation of the mesh.
        """
        assert self._native_handle is not None, 'Operation has been released'
        result_mesh = ctypes.c_uint64()
        format = format.value if isinstance(format, ExportFormat) else format
        options = options.value if isinstance(options, ExportOption) else options
        _res = _dll_Solidean_Operation_ExportMesh(self._native_handle, ctypes.byref(result_mesh), mesh, format, options)
        if _res != 0:
            raise SolideanException(Result(_res))
        result_mesh = TypedBlob._create_from_native(result_mesh.value)
        return result_mesh

    def heal(self, in_mesh: MeshOperand) -> MeshOperand:
        """
            Repairs a non-supersolid mesh into a supersolid one with strong guarantees
        
            Meshes with MeshBuilder::AllowNonSupersolid or MeshType::NonSupersolid are considered "bad input" and will be rejected by operations that require supersolid meshes.
        
            This operation "heals" the mesh and computes a supersolid mesh that closely resembles the input, trying to reuse as much surface as reasonable.
        
            NOTE: this method is 100% robust in the sense that ANY input geometry will be mapped without failure to a supersolid version with certain strong guarantees.
            However, for particularly bad cases the output might not correspond to the user intuition.
            Please contact us if you think the result is particularly unreasonable.
        
            NOTE: this method will only attempt to heal a mesh if it was marked with MeshBuilder::AllowNonSupersolid or MeshType::NonSupersolid.
        
            NOTE: if a solid mesh is desired, Operation::Heal followed by Operation::SelfUnion is an effective combination.
        
            NOTE: for feedback on what parts of the mesh are non-supersolid, see Operation::ExportDefectNetwork.
        """
        assert self._native_handle is not None, 'Operation has been released'
        mesh = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_Heal(self._native_handle, ctypes.byref(mesh), in_mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        mesh = mesh.value
        return mesh

    def query_area(self, mesh: MeshOperand) -> TypedBlob:
        """
            Computes the total surface area of a mesh
        
            Computes the total surface area of all surfaces of a mesh.
        
            This method will simply accumulate all primitives of all surfaces, regardless if they are on a solid surface or an interior.
            Should only the solid surface be desired, apply Operation::SelfUnion before querying.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultF64.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: all intermediates are accumulated in double precision. This cannot hold the exact result and rounding errors can accumulate at roughly 1 ULP per input primitive and up to 5 ULP per newly generated intermediate primitive. If a precise analysis is important to your use case, please contact support.
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryArea(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_volume(self, mesh: MeshOperand) -> TypedBlob:
        """
            Computes the total enclosed volume of a supersolid mesh
        
            Computes the total enclosed mesh volume.
            In the case of supersolid meshes, this counts each volume according to how often it is enclosed.
            For non-supersolid meshes, the volume is undefined and will yield Result::OperandMustBeSupersolid.
        
            For example, two partially overlapping cubes in a single supersolid mesh will count the overlap region twice and the other cube parts once.
            Negatively oriented sub-meshes count negatively. I.e. two disjoint cubes where one has inverted triangle orders will create a total volume of zero.
            Should every region only be counted once (and positively), apply Operation::SelfUnion before querying.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultF64.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: all intermediates are accumulated in double precision. However, the volume computation currently favors speed over numerical accuracy. It depends on the accumulation and cancellation of signed volumes of sub-tetrahedrons. As such, strict and useful precision guarantees are hard to formulate. If a precise analysis is important to your use case, please contact support.
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryVolume(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_is_supersolid(self, mesh: MeshOperand) -> TypedBlob:
        """
            Checks if a non-supersolid mesh is actually supersolid
        
            Given a mesh that is potentially non-supersolid (i.e. MeshBuilder::AllowNonSupersolid or MeshType::NonSupersolid), compute if the mesh is actually supersolid.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultBool.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: The mesh must be marked as MeshBuilder::AllowNonSupersolid or MeshType::NonSupersolid, otherwise the query is trivially true. (i.e. we detect if a MeshType::NonSupersolid is actually supersolid, not if a MeshType::Supersolid or MeshType::Solid was mistakenly marked as such.)
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryIsSupersolid(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_is_solid(self, mesh: MeshOperand) -> TypedBlob:
        """
            Checks if a non-solid mesh is actually solid
        
            Given a mesh that is potentially non-solid (i.e. any of the MeshBuilder/SurfaceBuilder::AllowXYZ relaxations or MeshType::NonSupersolid or MeshType::Supersolid), compute if the mesh is actually solid.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultBool.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: The mesh must not already be marked as solid. (i.e. we detect if a relaxed declaration can be tightened, not if MeshType::Solid was mistakenly marked as such.)
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryIsSolid(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_has_nested_components(self, mesh: MeshOperand) -> TypedBlob:
        """
            Checks if a supersolid mesh contains nested components
        
            Given a mesh with MeshBuilder::AllowNestedComponents, compute if there are actually such components present.
        
            The mesh must be supersolid and will otherwise yield Result::OperandMustBeSupersolid.
            (The property is volumetric and non-supersolids have no well defined volume.)
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultBool.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: The mesh must have set MeshBuilder::AllowNestedComponents. (i.e. we detect if the flag can be safely turned off, not if it was mistakenly disabled.)
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryHasNestedComponents(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_has_self_intersections(self, mesh: MeshOperand) -> TypedBlob:
        """
            Checks if a mesh has self-intersections within a surface
        
            Given a mesh with a surface that enabled SurfaceBuilder::AllowSelfIntersections, compute if there are actually such intersections present.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultBool.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: At least one surface must have enabled SurfaceBuilder::AllowSelfIntersections. (i.e. we detect if the flag can be safely turned off, not if it was mistakenly disabled.)
        
            NOTE: there is currently no way to query which surface has self-intersections specifically. Should this limit your use case, please contact support.
        
            CAUTION: do not confuse SurfaceBuilder::AllowSelfIntersections and MeshBuilder::AllowSurfaceIntersections.
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryHasSelfIntersections(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result

    def query_has_surface_intersections(self, mesh: MeshOperand) -> TypedBlob:
        """
            Checks if a mesh has intersections between different surfaces
        
            Given a mesh with a surface that enabled MeshBuilder::AllowSurfaceIntersections, compute if there are actually such intersections present.
        
            The result is stored in a TypedBlob with BlobType::QueryResult and DataSlot::QueryResultBool.
        
            NOTE: the query result is only available after the Operation was executed.
        
            NOTE: The mesh must be built with MeshBuilder::AllowSurfaceIntersections and have at least two surfaces. (i.e. we detect if the flag can be safely turned off, not if it was mistakenly disabled.)
        
            NOTE: there is currently no way to query which surfaces intersect. Should this limit your use case, please contact support.
        
            CAUTION: do not confuse SurfaceBuilder::AllowSelfIntersections and MeshBuilder::AllowSurfaceIntersections.
        """
        assert self._native_handle is not None, 'Operation has been released'
        query_result = ctypes.c_uint64()
        _res = _dll_Solidean_Operation_QueryHasSurfaceIntersections(self._native_handle, ctypes.byref(query_result), mesh)
        if _res != 0:
            raise SolideanException(Result(_res))
        query_result = TypedBlob._create_from_native(query_result.value)
        return query_result


class SurfaceBuilder:
    """
        Builder for defining immutable surfaces before use in a mesh
    
        Surfaces are immutable.
        Their setup is completely defined by this builder object, which can be built up incrementally.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == SurfaceBuilder.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> SurfaceBuilder:
        """Internal: create wrapper from native handle."""
        return SurfaceBuilder(SurfaceBuilder.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_SurfaceBuilder_Release(self._native_handle)
            self._native_handle = None

    def allow_self_intersections(self) -> None:
        """
            Marks that this surface may contain self-intersections
        
            By default, surface are assumed to be free of any self-intersection.
            Enabling this means that the geometry of this surface might interpenetrate.
        
            NOTE: enabling this has a non-trivial performance penalty. Only set this if you actually have data like this.
        """
        assert self._native_handle is not None, 'SurfaceBuilder has been released'
        _res = _dll_Solidean_SurfaceBuilder_AllowSelfIntersections(self._native_handle)
        if _res != 0:
            raise SolideanException(Result(_res))

    def track_id(self, surface_id: int, *, primitive_start_id: int = 0) -> None:
        """
            Enables primitive tracking using a structured surface and primitive ID scheme
        
            To track primitives (such as triangles) through various operations, a tracking ID can be provided.
            Internally, each primitive has a 64 bit ID (with some upper bits reserved for flags).
            When enabled on a surface, all operations try to keep track of these IDs (even across variadic and iterated Booleans and multiple Operations).
            Resulting IDs can be obtained by using Operation::ExportToTrianglesF32WithID and Operation::ExportToIndexedTrianglesF32WithID instead of the versions without 'WithID'.
            When this contains primitives from untracked surfaces, then their IDs are binary all-one, i.e. u64(-1).
        
            The ID is structured as follows: [2bit flags][30bit surface ID][32bit primitive ID] represented as an u64.
        
            The flags are [1bit is-inverted][1bit is-subset]:
            * if is-inverted is true, the winding order of the primitive changed. For triangles, this means (v0,v1,v2) is emitted as (v0,v2,v1), i.e. last two vertices are swapped.
            * if is-subset is false, then the emitted primitive is input primitive either unchanged or order-swapped (if is-inverted is true).
            * if is-subset is true, then the emitted primitive is a proper subset of the input, e.g. due to cutting up faces during Booleans.
        
            The primitives of a surface are contiguously numbered by default with a customizable start index.
        
            For example, given two surfaces A and B with 1000 and 2000 faces each, you could track them as:
            A->TrackID(0)
            B->TrackID(1)
            which would result in A's faces being (0,0..999) and B's faces being (1,0..1999).
        
            But you could also track them as:
            A->TrackID(0, 0)
            B->TrackID(0, 1000)
            which would result in A's faces being (0,0..999) and B's faces being (0,1000..2999).
        
            This gives plenty of flexibility on how to track input primitives.
            Should these options not suffice, SurfaceBuilder::TrackIDRaw and SurfaceBuilder::TrackPrimitiveIDs allow additional flexibility.
        
            NOTE: when reconstructing output topology (i.e. Operation::ExportToIndexedTrianglesF32WithID), vertices are currently always converted to integer space and back.
                  this implies that no resulting primitive is guaranteed to be bitwise equal to the input.
                  thus, all outputs are marked as is-subset for now.
                  if this affects your use case, please get in touch.
        """
        assert self._native_handle is not None, 'SurfaceBuilder has been released'
        _res = _dll_Solidean_SurfaceBuilder_TrackID(self._native_handle, surface_id, primitive_start_id)
        if _res != 0:
            raise SolideanException(Result(_res))

    def track_idraw(self, raw_start_id: int) -> None:
        """
            Enables primitive tracking using raw 62-bit IDs for each primitive
        
            Same as TrackID but allows setting the start ID in the whole available 62 bit index space, i.e. [30bit surface ID][32bit primitive ID] becomes [62bit raw ID].
            The primitives of this surface are still numbered contiguously, i.e. rawStartID + 0, rawStartID + 1, rawStartID + 2, ...
        
            NOTE: see documentation of SurfaceBuilder::TrackID for descriptions of how the IDs work and how the flags are interpreted.
        
            NOTE: TrackID(surfID, primID) can be seen as TrackIDRaw((surfID << 32) + primID).
        """
        assert self._native_handle is not None, 'SurfaceBuilder has been released'
        _res = _dll_Solidean_SurfaceBuilder_TrackIDRaw(self._native_handle, raw_start_id)
        if _res != 0:
            raise SolideanException(Result(_res))

    def track_primitive_ids(self, primitive_ids: Union[NDArray[np.uint64], List[int]], *, lifetime: Union[Lifetime, int] = Lifetime.CopyImmediately) -> None:
        """
            Enables primitive tracking by providing explicit IDs for each primitive
        
            In TrackID and TrackIDRaw, primitives are always numbered contiguously.
            For maximum flexibility, this method allows setting the available 62bit raw ID for each primitive individually.
        
            NOTE: size must match exactly the number of primitives.
        
            NOTE: see documentation of SurfaceBuilder::TrackID for descriptions of how the IDs work and how the flags are interpreted.
        """
        assert self._native_handle is not None, 'SurfaceBuilder has been released'
        primitive_ids_arr = np.asarray(primitive_ids, dtype=np.uint64)
        primitive_ids_arr = np.ascontiguousarray(primitive_ids_arr)
        primitive_ids_ptr = primitive_ids_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_uint64))
        primitive_ids_count = primitive_ids_arr.shape[0]
        lifetime = lifetime.value if isinstance(lifetime, Lifetime) else lifetime
        _res = _dll_Solidean_SurfaceBuilder_TrackPrimitiveIDs(self._native_handle, primitive_ids_ptr, primitive_ids_count, lifetime)
        if _res != 0:
            raise SolideanException(Result(_res))


class Surface:
    """
        Immutable surface object; building block of meshes
    
        A surface is a piece of 3D geometry.
        A mesh consists of a set of surfaces.
        Each surface itself can be non-manifold, disconnected, degenerate and self-intersecting.
        Only at the mesh level are further guarantees required, most often that the set of surfaces of a mesh are supersolid.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == Surface.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> Surface:
        """Internal: create wrapper from native handle."""
        return Surface(Surface.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_Surface_Release(self._native_handle)
            self._native_handle = None


class TypedBlob:
    """
        Immutable container for exported or queried binary data tagged with a BlobType
    
        A TypedBlob holds raw binary data and a type tag (see BlobType).
        It is often used to hold the result of an export or query operation.
        For example, Operation::ExportToTriangleSoup cannot directly write the result because the operation is deferred and because the size of the result is unknown.
        Instead, it populates a TypedBlob that holds the triangle data after Context::Execute finishes.
    
        NOTE: a TypeBlob is, like Meshes and Surfaces, immutable. It can only be initialized once.
    """

    __private_init = object()

    def __init__(self, private_init, native_handle: int):
        """Private constructor. Use Context.create_*() instead."""
        assert private_init == TypedBlob.__private_init, "Do not call constructor directly. Use Context.create_*() methods."
        self._native_handle = native_handle

    @staticmethod
    def _create_from_native(native_handle: int) -> TypedBlob:
        """Internal: create wrapper from native handle."""
        return TypedBlob(TypedBlob.__private_init, native_handle)

    def __del__(self):
        """Automatic cleanup when object is garbage collected."""
        if hasattr(self, '_native_handle') and self._native_handle is not None:
            _dll_Solidean_TypedBlob_Release(self._native_handle)
            self._native_handle = None

    def has_data(self, slot: Union[DataSlot, int]) -> bool:
        """
            Checks if the blob contains data for a given slot
        
            Returns true iff this blob has data stored in the provided slot.
        """
        assert self._native_handle is not None, 'TypedBlob has been released'
        has_data = ctypes.c_uint32()
        slot = slot.value if isinstance(slot, DataSlot) else slot
        _res = _dll_Solidean_TypedBlob_HasData(self._native_handle, ctypes.byref(has_data), slot)
        if _res != 0:
            raise SolideanException(Result(_res))
        has_data = has_data.value
        has_data = has_data != 0
        return has_data

    def get_data(self, slot: Union[DataSlot, int]) -> NDArray[np.uint8]:
        """
            Retrieves raw data bytes from a given slot in the blob
        
            Returns the raw data stored in this blob for a particular slot.
            The type of the blob defines what data is stored at a minimum and how to interpret the result.
            However, some slots are optional, like primitive IDs.
        
            NOTE: as an immutable object, the returned data pointer stays valid until ::Release is called.
        """
        assert self._native_handle is not None, 'TypedBlob has been released'
        data_ptr = ctypes.c_void_p()
        data_count = ctypes.c_uint64()
        slot = slot.value if isinstance(slot, DataSlot) else slot
        _res = _dll_Solidean_TypedBlob_GetData(self._native_handle, ctypes.byref(data_ptr), ctypes.byref(data_count), slot)
        if _res != 0:
            raise SolideanException(Result(_res))
        data_bytes = _as_owned_array_from_ptr(data_ptr, data_count.value, owner=self)
        data = data_bytes.view(np.uint8)
        return data

    def type(self) -> BlobType:
        """
            BlobType tag describing the data stored in this blob
        
            Returns the type tag for the data stored in this blob.
        """
        assert self._native_handle is not None, 'TypedBlob has been released'
        type = ctypes.c_uint32()
        _res = _dll_Solidean_TypedBlob_GetType(self._native_handle, ctypes.byref(type))
        if _res != 0:
            raise SolideanException(Result(_res))
        type = BlobType(type.value)
        return type


    @cached_property
    def positions_f32(self) -> NDArray[np.float32]:
        """Same as get_data(DataSlot.PositionsF32) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 3) and dtype np.float32."""
        data = self.get_data(DataSlot.PositionsF32)
        assert len(data) % 12 == 0, f'Data size {len(data)} must be divisible by element size 12'
        arr = data.view(np.float32)
        return arr.reshape(-1, 3)

    @cached_property
    def positions_f64(self) -> NDArray[np.float64]:
        """Same as get_data(DataSlot.PositionsF64) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 3) and dtype np.float64."""
        data = self.get_data(DataSlot.PositionsF64)
        assert len(data) % 24 == 0, f'Data size {len(data)} must be divisible by element size 24'
        arr = data.view(np.float64)
        return arr.reshape(-1, 3)

    @cached_property
    def positions_xyz192_w192(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.PositionsXYZ192_W192) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 12) and dtype np.uint64."""
        data = self.get_data(DataSlot.PositionsXYZ192_W192)
        assert len(data) % 96 == 0, f'Data size {len(data)} must be divisible by element size 96'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 12)

    @cached_property
    def positions_planes_abc64_d128(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.PositionsPlanesABC64_D128) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 15) and dtype np.uint64."""
        data = self.get_data(DataSlot.PositionsPlanesABC64_D128)
        assert len(data) % 120 == 0, f'Data size {len(data)} must be divisible by element size 120'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 15)

    @cached_property
    def vertex_to_halfedge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.VertexToHalfedge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.VertexToHalfedge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def triangles_f32(self) -> NDArray[np.float32]:
        """Same as get_data(DataSlot.TrianglesF32) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 9) and dtype np.float32."""
        data = self.get_data(DataSlot.TrianglesF32)
        assert len(data) % 36 == 0, f'Data size {len(data)} must be divisible by element size 36'
        arr = data.view(np.float32)
        return arr.reshape(-1, 9)

    @cached_property
    def triangles_f64(self) -> NDArray[np.float64]:
        """Same as get_data(DataSlot.TrianglesF64) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 9) and dtype np.float64."""
        data = self.get_data(DataSlot.TrianglesF64)
        assert len(data) % 72 == 0, f'Data size {len(data)} must be divisible by element size 72'
        arr = data.view(np.float64)
        return arr.reshape(-1, 9)

    @cached_property
    def triangles_xyz192_w192(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.TrianglesXYZ192_W192) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 36) and dtype np.uint64."""
        data = self.get_data(DataSlot.TrianglesXYZ192_W192)
        assert len(data) % 288 == 0, f'Data size {len(data)} must be divisible by element size 288'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 36)

    @cached_property
    def triangles_planes_abc64_d128(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.TrianglesPlanesABC64_D128) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 45) and dtype np.uint64."""
        data = self.get_data(DataSlot.TrianglesPlanesABC64_D128)
        assert len(data) % 360 == 0, f'Data size {len(data)} must be divisible by element size 360'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 45)

    @cached_property
    def triangles_indexed(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.TrianglesIndexed) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 3) and dtype np.int32."""
        data = self.get_data(DataSlot.TrianglesIndexed)
        assert len(data) % 12 == 0, f'Data size {len(data)} must be divisible by element size 12'
        arr = data.view(np.int32)
        return arr.reshape(-1, 3)

    @cached_property
    def segments_indexed(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.SegmentsIndexed) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 2) and dtype np.int32."""
        data = self.get_data(DataSlot.SegmentsIndexed)
        assert len(data) % 8 == 0, f'Data size {len(data)} must be divisible by element size 8'
        arr = data.view(np.int32)
        return arr.reshape(-1, 2)

    @cached_property
    def primitive_size(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.PrimitiveSize) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.PrimitiveSize)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_vertex(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToVertex) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToVertex)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_edge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToEdge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToEdge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_face(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToFace) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToFace)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_next_halfedge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToNextHalfedge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToNextHalfedge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_prev_halfedge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToPrevHalfedge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToPrevHalfedge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_to_opposite_halfedge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.HalfedgeToOppositeHalfedge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.HalfedgeToOppositeHalfedge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def halfedge_plane_abc64_d128(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.HalfedgePlaneABC64_D128) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 5) and dtype np.uint64."""
        data = self.get_data(DataSlot.HalfedgePlaneABC64_D128)
        assert len(data) % 40 == 0, f'Data size {len(data)} must be divisible by element size 40'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 5)

    @cached_property
    def defects(self) -> NDArray[np.uint32]:
        """Same as get_data(DataSlot.Defects) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.uint32."""
        data = self.get_data(DataSlot.Defects)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.uint32)
        return arr

    @cached_property
    def primitive_ids(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.PrimitiveIDs) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.uint64."""
        data = self.get_data(DataSlot.PrimitiveIDs)
        assert len(data) % 8 == 0, f'Data size {len(data)} must be divisible by element size 8'
        arr = data.view(np.uint64)
        return arr

    @cached_property
    def primitive_to_halfedge(self) -> NDArray[np.int32]:
        """Same as get_data(DataSlot.PrimitiveToHalfedge) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n,) and dtype np.int32."""
        data = self.get_data(DataSlot.PrimitiveToHalfedge)
        assert len(data) % 4 == 0, f'Data size {len(data)} must be divisible by element size 4'
        arr = data.view(np.int32)
        return arr

    @cached_property
    def primitive_supporting_plane_abc64_d128(self) -> NDArray[np.uint64]:
        """Same as get_data(DataSlot.PrimitiveSupportingPlaneABC64_D128) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, 5) and dtype np.uint64."""
        data = self.get_data(DataSlot.PrimitiveSupportingPlaneABC64_D128)
        assert len(data) % 40 == 0, f'Data size {len(data)} must be divisible by element size 40'
        arr = data.view(np.uint64)
        return arr.reshape(-1, 5)

    @cached_property
    def query_result_bool(self) -> bool:
        """Same as get_data(DataSlot.QueryResultBool) but returns a single scalar value.
        
        Raises:
            SolideanException(Result.InvalidSize): If the blob does not contain exactly one element.
        
        Use query_result_bools if multiple elements can be returned."""
        data = self.get_data(DataSlot.QueryResultBool)
        if len(data) != 1:
            raise SolideanException(Result.InvalidSize)
        arr = data.view(np.uint8)
        return arr[0] != 0

    @cached_property
    def query_result_bools(self) -> NDArray[np.uint8]:
        """Same as get_data(DataSlot.QueryResultBool) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, ) and dtype np.uint8.
        
        Use query_result_bool if exactly one element is expected."""
        data = self.get_data(DataSlot.QueryResultBool)
        arr = data.view(np.uint8)
        return arr

    @cached_property
    def query_result_f64(self) -> float:
        """Same as get_data(DataSlot.QueryResultF64) but returns a single scalar value.
        
        Raises:
            SolideanException(Result.InvalidSize): If the blob does not contain exactly one element.
        
        Use query_result_f64s if multiple elements can be returned."""
        data = self.get_data(DataSlot.QueryResultF64)
        assert len(data) % 8 == 0, f'Data size {len(data)} must be divisible by element size 8'
        if len(data) != 8:
            raise SolideanException(Result.InvalidSize)
        arr = data.view(np.float64)
        return arr[0]

    @cached_property
    def query_result_f64s(self) -> NDArray[np.float64]:
        """Same as get_data(DataSlot.QueryResultF64) but returns a properly shaped and typed numpy array.
        
        Returns:
            np.ndarray: Array with shape (n, ) and dtype np.float64.
        
        Use query_result_f64 if exactly one element is expected."""
        data = self.get_data(DataSlot.QueryResultF64)
        assert len(data) % 8 == 0, f'Data size {len(data)} must be divisible by element size 8'
        arr = data.view(np.float64)
        return arr

