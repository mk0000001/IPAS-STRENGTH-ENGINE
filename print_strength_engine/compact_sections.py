"""Separately bounded union fallback; packed bytes are not an RSS guarantee.

The ordinary road-piece caps stay in automatic_sections. This policy accounts
for live geometry across declared and commanded-volume collectors, including
merge input/output overlap. GEOS internal allocations need a separate measured
process-memory gate. Coordinates and clipping use grid_size=0 throughout.
"""
from shapely import get_num_coordinates, union_all
from shapely.geometry import Polygon
from shapely.errors import GEOSException
from .deposition_section import UnsupportedGeometry

POLICY_ID='EXACT_UNION_COMPACT_V1'
MAX_PACKED_BYTES=128*1024**2
UNION_CHUNK_PIECES=16384
RESOURCE_GAP='LOCAL_SECTION_COMPACT_RESOURCE_BUDGET_EXCEEDED'


def resource_policy():
    return {'id':POLICY_ID,'max_packed_bytes':MAX_PACKED_BYTES,'per_cut_max_union_vertices':1000000}


def shape_cost(shape):
    polygons=list(shape.geoms) if shape.geom_type=='MultiPolygon' else [shape]
    if any(p.geom_type!='Polygon' for p in polygons):raise UnsupportedGeometry('INVALID_LOCAL_SECTION_UNION')
    rings=sum(1+len(p.interiors) for p in polygons)
    coordinates=int(get_num_coordinates(shape))
    # Standard 2-D WKB: geometry headers, ring counts, ring sizes, double XYs.
    packed=(9 if shape.geom_type=='MultiPolygon' else 0)+9*len(polygons)+4*rings+16*coordinates
    return packed,coordinates,coordinates-rings


class CompactGeometryBudget:
    def __init__(self,*,max_packed_bytes=MAX_PACKED_BYTES):
        if isinstance(max_packed_bytes,bool) or not isinstance(max_packed_bytes,int) or max_packed_bytes<=0:
            raise ValueError('POSITIVE_COMPACT_PACKED_BYTE_BUDGET_REQUIRED')
        self.max_packed_bytes=max_packed_bytes;self.active=False;self.usage={}
        self.peak_packed_bytes=0;self.peak_coordinates=0

    def update(self,owner,packed_bytes,coordinates,*,activate=False):
        self.active=self.active or activate
        self.usage[owner]=(packed_bytes,coordinates)
        packed=sum(value[0] for value in self.usage.values())
        coords=sum(value[1] for value in self.usage.values())
        self.peak_packed_bytes=max(self.peak_packed_bytes,packed)
        self.peak_coordinates=max(self.peak_coordinates,coords)
        if self.active and packed>self.max_packed_bytes:raise UnsupportedGeometry(RESOURCE_GAP)

    def release(self,owner):self.usage.pop(owner,None)


class _Accumulator:
    def __init__(self):self.pending=[];self.levels=[];self.pending_coordinates=0;self.pending_vertices=0

    def cost(self):
        coords=self.pending_coordinates;vertices=self.pending_vertices
        packed=13*len(self.pending)+16*coords
        for node in self.levels:
            if node is not None:
                size,count,number=node[1];packed+=size;coords+=count;vertices+=number
        return packed,coords,vertices


class CompactCutUnion:
    def __init__(self,axis,component_selection,budget,*,max_vertices):
        self.axis=axis;self.component_selection=component_selection;self.budget=budget
        self.max_vertices=max_vertices;self.tools={};self.owner=object();self.failed=False
        self.finished_shapes={};self.final_shape=None

    def _cost(self):
        values=[acc.cost() for acc in self.tools.values()]
        values.extend(shape_cost(shape) for shape in self.finished_shapes.values())
        if self.final_shape is not None:values.append(shape_cost(self.final_shape))
        return tuple(sum(value[i] for value in values) for i in range(3))

    def _observe(self,extra=None):
        packed,coordinates,vertices=self._cost()
        if extra:packed+=extra[0];coordinates+=extra[1]
        self.budget.update(self.owner,packed,coordinates,activate=True)

    def _merge(self,shapes,extra_inputs=()):
        result=union_all(shapes,grid_size=0)
        # Existing input nodes remain charged while the result is live.
        costs=[shape_cost(result),*(shape_cost(shape) for shape in extra_inputs)]
        self._observe(tuple(sum(value[i] for value in costs) for i in range(3)))
        return result

    def _flush(self,acc):
        if not acc.pending:return
        inputs=[Polygon(piece) for piece in acc.pending]
        shape=self._merge(inputs,extra_inputs=inputs)
        del inputs
        acc.pending.clear();acc.pending_coordinates=0;acc.pending_vertices=0;level=0
        while level<len(acc.levels) and acc.levels[level] is not None:
            shape=self._merge([acc.levels[level][0],shape],extra_inputs=[shape])
            acc.levels[level]=None;level+=1
        if level==len(acc.levels):acc.levels.append(None)
        acc.levels[level]=(shape,shape_cost(shape));self._observe()

    def add(self,piece,tools):
        if self.failed:raise UnsupportedGeometry(RESOURCE_GAP)
        if self.finished_shapes:
            for key,shape in self.finished_shapes.items():self.tools[key].levels=[(shape,shape_cost(shape))]
            self.finished_shapes={};self.final_shape=None
        points=piece if self.axis==2 else ((piece[0],piece[2]),(piece[1],piece[2]),
                                          (piece[1],piece[3]),(piece[0],piece[3]))
        keys=tools if self.component_selection else (None,)
        try:
            for tool in keys:
                acc=self.tools.setdefault(tool,_Accumulator());acc.pending.append(points)
                acc.pending_vertices+=len(points);acc.pending_coordinates+=len(points)+1
                self._observe()
                if len(acc.pending)>=UNION_CHUNK_PIECES:self._flush(acc)
        except GEOSException as error:
            self.release();self.failed=True
            raise UnsupportedGeometry('INVALID_LOCAL_SECTION_UNION') from error
        except Exception:
            self.release();self.failed=True;raise

    def finish(self):
        try:
            if self.finished_shapes:
                shape=self.final_shape if self.final_shape is not None else next(iter(self.finished_shapes.values()))
                return shape,self.finished_shapes
            for tool,acc in self.tools.items():
                self._flush(acc)
                self.finished_shapes[tool]=self._merge([node[0] for node in acc.levels if node is not None])
                acc.levels.clear();self._observe()
            output=self.finished_shapes
            shape=next(iter(output.values())) if len(output)==1 else self._merge(list(output.values()))
            # Final union can create new holes/vertices. Enforce the old cut
            # vertex limit on that result as well as live intermediate nodes.
            if shape_cost(shape)[2]>self.max_vertices:raise UnsupportedGeometry(RESOURCE_GAP)
            if len(output)>1:self.final_shape=shape
            self._observe()
            return shape,output
        except GEOSException as error:
            self.release();self.failed=True
            raise UnsupportedGeometry('INVALID_LOCAL_SECTION_UNION') from error
        except Exception:
            self.release();self.failed=True;raise

    def release(self):
        self.tools.clear();self.finished_shapes.clear();self.final_shape=None;self.budget.release(self.owner)
