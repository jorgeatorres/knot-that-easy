# encoding: utf-8
import math

def ccw(A,B,C):
    return (C.y-A.y)*(B.x-A.x) > (B.y-A.y)*(C.x-A.x)

# TODO - si los arcos, puntos, etc. se hicieran no mutables e
# implementaran __hash__() seguramente se podria mejorar el desempeño
# o utilizar diccionarios mas a menudo para hacer todo mas 'evidente'

# TODO - optimizar esta funcion: no todas las posibles coloraciones son
# validas (y esto lo sabemos aun antes de verificar)
# i.e. coloraciones que usan menos de 3 colores
def _possible_colorings(data):
    
    data = list(data)
    colorings = []
    
    if len(data) == 1:
        for i in (0, 1, 2):
            colorings.append([i])
    else:
        data.remove(data[0])
        
        _colorings = _possible_colorings(data)
        
        for i in (0, 1, 2):
            for x in _colorings:
                new_coloring = [i]
                new_coloring.extend(x)
                colorings.append(new_coloring)

    return colorings


class Point(object):
    
    def __init__(self, x = 0.0, y = 0.0):
        self.x = x
        self.y = y
        
    def distance(self, p2):
        return math.sqrt(math.pow((self.x - p2.x), 2) +
                         math.pow((self.y - p2.y), 2))
        
    def length(self):
        return self.distance(Point(0.0, 0.0))
        
    def __repr__(self):
        return '(%0.2f,%0.2f)' % (self.x, self.y)
    
    def __eq__(self, obj):
        if isinstance(obj, Point):
            return self.x == obj.x and self.y == obj.y
        return False
    
    def __ne__(self, obj):
        return not (self == obj)


class Line(object):
    
    def __init__(self, orig, dest):
        self.orig = orig
        self.dest = dest


    def get_direction_vector(self):
        dir = Point(self.orig.x - self.dest.x,
                    self.orig.y - self.dest.y)
        len = dir.length()
        return Point(dir.x / len, dir.y / len)

    def intersects(self, l2):        
        return ccw(self.orig, l2.orig, l2.dest) != ccw(self.dest, l2.orig, l2.dest) and \
               ccw(self.orig, self.dest, l2.orig) != ccw(self.orig, self.dest, l2.dest)
               
    def intersection(self, l2):
        if not self.intersects(l2):
            return None
        
        a = -(self.orig.y - self.dest.y)
        b = self.orig.x - self.dest.x
        c = -(l2.orig.y - l2.dest.y)
        d = l2.orig.x - l2.dest.x
        
        e = a * self.orig.x + b * self.orig.y
        f = c * l2.orig.x + d * l2.orig.y
        
        det = a * d - b * c
        
        return Point((d * e - b * f) / det,
                     (a * f - c * e) / det)
        
    def reversed(self):
        return Line(self.dest, self.orig)
        
    def __eq__(self, obj):
        if isinstance(obj, Line):
            return self.orig == obj.orig and self.dest == obj.dest
        return False
    
    def __ne__(self, obj):
        return not (self == obj)    

    def __repr__(self):
        return '[%s - %s]' % (self.orig, self.dest)


class Arc(object):
    
    def __init__(self, s0):
        self.segments = []
        self.add(s0)
        
    def add(self, segment):
        if not self.segments:
            self.segments.append(segment)
        
        if segment not in self.segments:
            last_segment = self.segments[-1]

            if last_segment.orig == segment.dest:
                self.segments.insert(0, segment)
            elif last_segment.dest == segment.orig:
                self.segments.append(segment)
                
    def join(self, arc):
        new_arc = Arc(self.segments[0])
        
        for s in self.segments[1:]:
            new_arc.add(s)
                
        if new_arc.segments[0].orig == arc.segments[-1].dest:
            for s in reversed(arc.segments):
                new_arc.add(s)
        elif new_arc.segments[-1].dest == arc.segments[0].orig:
            for s in arc.segments:
                new_arc.add(s)
                
        return new_arc
    
    # two arcs are considered the same if they are constructed from the same
    # segments
    def __eq__(self, obj):
        if isinstance(obj, Arc):
            if len(self.segments) != len(obj.segments):
                return False
            
            for i in xrange(0, len(self.segments)):
                if self.segments[i] != obj.segments[i]:
                    return False
            
            return True
        
        return False
    
    def __ne__(self, obj):
        return not (self == obj)    

    def __repr__(self):
        return '[%d segments from %s to %s]' % (len(self.segments),
                                                self.segments[0].orig, self.segments[-1].dest)
       


class Crossing(object):
    
    def __init__(self, under, over):
        self.under = under
        self.over = over
        self.crosspoint = under.intersection(over)
    
    def get_orientation(self):
        x1 = self.over.orig.x - self.over.dest.x
        y1 = self.over.orig.y - self.over.dest.y
        x2 = self.under.orig.x - self.under.dest.x
        y2 = self.under.orig.y - self.under.dest.y
        
        d = x2 * y1 - x1 * y2
        
        if d > 0:
            return 1
        elif d < 0:
            return -1
        else:
            return 0
        
    def sign(self):
        return self.get_orientation()
        
    def under_to_over(self):
        temp = self.over
        self.over = self.under
        self.under = temp
        
    def involves(self, line):
        return self.under == line or self.over == line
    
    def __eq__(self, obj):
        if isinstance(obj, Crossing):
            return self.under == obj.under and self.over == obj.over
        return False
    
    def __ne__(self, obj):
        return not (self == obj)    
        
    def __repr__(self):
        return '{%s%s}' % ('+' if self.get_orientation() == 1 else '-', self.crosspoint)


def _sort_crossings(x, y):
    dx = x[0]
    dy = y[0]
    
    if dx < dy:
        return -1
    elif dx > dy:
        return 1
    
    return 0

#def gauss_code_to_dowker(gauss_code):
#    dowker = {}
#
#    # FIXME This is extremely inefficient
#    for i, k in enumerate(gauss_code):
#        if k not in dowker and -k not in dowker:
#            delta = 0
#            
#            for m in gauss_code[i:]:
#                if m != -1 * k:
#                    delta = delta + 1
#                else:
#                    if (abs(k) + delta) % 2 == 0 and m < 0:
#                        delta = -delta
#                    break
#            
#            if abs(k) % 2 != 0:
#                k = abs(k)
#
#            if delta > 0:
#                dowker[k] = abs(k) + delta
#            else:
#                dowker[k] = -1 * (abs(k) + abs(delta))
#            
#    res = {}
#    
#    for x, y in dowker.iteritems():
#        if abs(x) % 2 != 0:
#            res[x] = y
#        elif abs(y) % 2 != 0:
#            res[y] = x
#
#    res = res.items()
#    res.sort(lambda x,y: cmp(x[0], y[0]))
#
#    return [e[1] for e in res]



# TODO - Si 'cacheamos' la informacion de los cruces (indice), etc. cada vez que 
# agregan cruces todo seria mas eficiente.
# Tal vez hasta el get_crossings_index() podria cambiarse por algo como
# enuemrate(get_crossings(), 1) si los devuelve ya ordenados
class KnotModel(object):

    def __init__(self, vertices=[]):
        self.vertices = []
        self.segments = []
        self.crossings = []
        self._listeners = {'model-changed': [],
                           'vertex-added': [],
                           'crossings-added': [],
                           'segment-added': []}
        self.set_vertices(vertices)

    def set_vertices(self, vertices):
        self.vertices = []
        self.segments = []
        self.crossings = []

        if not vertices:
            self._emit('model-changed', self)
        
        for v in vertices:
            self.append_vertex(v)
            
    def remove_last_vertex(self):
        if self.vertices:
            self.vertices.pop()
            
            if self.segments:
                involved_crossings = self.get_crossings_involving_line(self.segments.pop())
                
                for c in involved_crossings:
                    self.crossings.remove(c)
            
            self._emit('model-changed', self)
            
    def append_vertex(self, v, over=True):
        if not self.vertices:
            self.vertices.append(v)
            self._emit('vertex-added', v)
        else:
            ghost_line = Line(self.vertices[-1], v)
            
            if not self._line_intersects_segment(ghost_line):
                self.vertices.append(v)
                self._emit('vertex-added', v)
                
                self.segments.append(ghost_line)
                self._emit('segment-added', ghost_line)
            else:
                new_crossings = []
                
                for s in self.segments[:-1]:
                    if ghost_line.intersects(s):
                        c = Crossing(s, ghost_line)
                        
                        if not over:
                            c.under_to_over()
                        
                        # TODO FIXME wtf
                        if c.crosspoint.distance(self.vertices[0]) > 3:
                            new_crossings.append(c)
                        
                self.vertices.append(v)
                self._emit('vertex-added', v)
                
                self.segments.append(ghost_line)
                self._emit('segment-added', ghost_line)
                
                self.crossings.extend(new_crossings)
                self._emit('crossings-added', new_crossings)
        
    def mirror_image(self):
        mirror_model = KnotModel(self.vertices)
        
        for crossing in mirror_model.crossings:
            orig_crossing = self.get_crossing_of(crossing.under, crossing.over)
            
            if orig_crossing is not None and \
               orig_crossing.under == crossing.under:
                crossing.under_to_over()

        return mirror_model
    
    def make_alternating(self):
        if self.crossings and not self.is_alternating():
            n = 0
            
            for s in self.segments:
                crossings = self.get_crossings_involving_line(s)
                
                for c in crossings:
                    if n == 0 and c.over != s:
                        c.under_to_over()
                    elif n == 1 and c.under != s:
                        c.under_to_over()
                        
                    n = (n + 1) % 2

            self._emit('model-changed', self)
    
    def orientation_reversed(self):
        reversed_ = KnotModel()
        
        for v in reversed(self.vertices):
            reversed_.append_vertex(v)
            
        for c in reversed_.crossings:
            orig_crossing = self.get_crossing_of(c.under.reversed(),
                                                 c.over.reversed())
            
            if orig_crossing is not None:
                if c.over != orig_crossing.over.reversed():
                    c.under_to_over()

        return reversed_

    # cruces con numero par por encima son negativos
    def dowker_notation(self):
        crossings_indexes = {}
        
        for index, (c, over) in enumerate(self.get_crossings_trail(), 1):
            if c not in crossings_indexes:
                crossings_indexes[c] = [0,0]
            
            if over and index % 2 == 0:
                crossings_indexes[c][1] = -index
            elif index % 2 == 0:
                crossings_indexes[c][1] = index
            else:
                crossings_indexes[c][0] = index
        
        indexes = crossings_indexes.values()
        indexes.sort(cmp=lambda x,y: abs(x[0]) - abs(y[0]))

        return [i[1] for i in indexes]
    
    def gauss_code(self):
        code = []
        crossings_index = self.get_crossings_index()
        
        for c, over in self.get_crossings_trail():
            if over:
                code.append(crossings_index.index(c))
            else:
                code.append(crossings_index.index(c) * -1)
        
        return code
    
    def extended_gauss_code(self):
        gauss_code = self.gauss_code()
        
        return [gauss_code, ['+' if c.sign() > 0 else '-' for c in self.get_crossings()]]    
    
    def get_trail(self):
        trail = []

        for s in self.segments:
            trail.append((u's', s))
            segment_crossings = self.get_crossings_involving_line(s)
                
            for c in segment_crossings:
                trail.append((u'c', c, c.over == s))
                trail.append((u's', s))
                        
        return trail
    
    def get_crossings_trail(self):
        return [(c[1], c[2]) for c in self.get_trail() if c[0] == 'c']
    
    # Si los arcos no son state-less y el join() cambia *ambos* arcos -o algo asi-
    # toda esta logica seria minima pues los arcos tendrian "memoria"
    def _join_arcs(self, arc_index, data):
        if arc_index < len(data):
            arc = data[arc_index][1]
        
            if len(data) > arc_index + 1:
                if data[arc_index + 1][0] == 'c' and data[arc_index + 1][2] == True:
                    other_arc = data[arc_index + 2][1]
                    new_arc = arc.join(other_arc)
                    
                    for i, x in enumerate(data):
                        if x[0] == 'a' and (x[1] == arc or x[1] == other_arc):
                            data[i] = ('a', new_arc)
                    
                    return self._join_arcs(arc_index + 2, data)
        
        return data

    
    def get_arcs_trail(self):
        data = self.get_subarcs_trail_data()
#
#        # Join subarcs passing OVER a crossing
        for i in xrange(0, len(data)):
            if data[i][0] == 'a':
                data = self._join_arcs(i, data)
                
        # Join first and last subarcs
        first_arc = data[0][1]
        last_arc = data[-1][1]
        new_arc = data[-1][1].join(data[0][1])
        
        for i, x in enumerate(data):
            if x[0] == 'a' and (x[1] == first_arc or x[1] == last_arc):
                data[i] = ('a', new_arc)
                
        return data
    
    def get_arcs(self):
        arcs = []
        
        for data in self.get_arcs_trail():
            if data[0] == 'a' and data[1] not in arcs:
                arcs.append(data[1])
        
        return arcs
    
    def get_subarcs_trail_data(self):
        if self.segments:
            trail = self.get_trail()
            
            # Add a virtual crossing
            trail.append(('c', None, False))
            
            arc_trail_data = []            
            trail_accum = []

            for e in trail:
                if e[0] == 'c':
                    trail_accum.append(e)
                    arc_trail_data.append(trail_accum)                    
                    trail_accum = [e]
                else:
                    trail_accum.append(e)
            
            arc_trail_data[-1].pop()
            
            arc_trail = []
            for ad in arc_trail_data:
                # starts and ends with a crossing
                if ad[0][0] == 'c' and ad[-1][0] == 'c':
                    if len(ad) == 3:
                        arc_trail.append(ad[0])
                        arc_trail.append(('a', Arc(Line(ad[0][1].crosspoint,
                                                        ad[-1][1].crosspoint))))
                        arc_trail.append(ad[-1])
                    else:
                        arc = Arc(Line(ad[0][1].crosspoint,
                                       ad[1][1].orig))
                        
                        for t, l in ad[1:-3]:
                            arc.add(l)
                            
                        arc.add(Line(ad[-3][1].orig, ad[-1][1].crosspoint))
                        
                        arc_trail.append(ad[0])
                        arc_trail.append(('a', arc))
                        arc_trail.append(ad[-1])

                # starts with a crossing
                elif ad[0][0] == 'c':
                    if len(ad) == 2:
                        arc_trail.append(ad[0])
                        arc_trail.append(('a', Arc(Line(ad[0][1].crosspoint,
                                                        ad[1][1].dest))))
                    else:
                        arc = Arc(Line(ad[0][1].crosspoint,
                                       ad[1][1].dest))
                        
                        for t, l in ad[1:]:
                            arc.add(l)
                        
                        arc_trail.append(ad[0])
                        arc_trail.append(('a', arc))  

                # ends with a crossing
                elif ad[-1][0] == 'c':
                    if len(ad) == 2:
                        arc_trail.append(('a', Arc(Line(ad[0][1].orig,
                                                        ad[-1][1].crosspoint))))
                        arc_trail.append(ad[-1])
                    else:
                        arc = Arc(ad[0][1])
                        
                        for t, l in ad[1:-3]:
                            arc.add(l)
                            
                        arc.add(Line(ad[-2][1].orig,
                                     ad[-1][1].crosspoint))
                        
                        arc_trail.append(('a', arc))
                        arc_trail.append(ad[-1])
                # only segments (trivial knot)
                else:
                    arc = Arc(ad[0][1])
                        
                    for t, l in ad[1:]:
                        arc.add(l)

                    arc_trail.append(('a', arc))
                    
        arc_trail_res = []
        
        for i, d in enumerate(arc_trail[:-1]):
            if d[0] == 'c' and arc_trail[i + 1][1] == d[1]:
                continue
            else:
                arc_trail_res.append(d)

        arc_trail_res.append(arc_trail[-1])

        return arc_trail_res
    
    def get_crossings_index(self):
        indexes = [None,]
        
        for c, over in self.get_crossings_trail():
            if c not in indexes:
                indexes.append(c)
                
        return indexes
    
    def get_crossings(self):
        return [c for c in self.get_crossings_index() if c is not None]
        
    def get_crossings_arc_info(self):
        info = {}
        arcs_trail = self.get_arcs_trail()
                
        for i, item in enumerate(arcs_trail):
            if item[0] == 'c':
                
                if item[1] not in info:
                    info[item[1]] = {'index': len(info) + 1,
                                     'crossing': item[1],
                                     'overstrand': None,
                                     'understrand-incoming': None,
                                     'understrand-leaving': None}
                
                crossing_info = info[item[1]]
                
                if item[2] == True:
                    crossing_info['overstrand'] = arcs_trail[i - 1][1]
                else:
                    crossing_info['understrand-incoming'] = arcs_trail[i - 1][1]
                    crossing_info['understrand-leaving'] = arcs_trail[i + 1][1]
                
        return info
    
    def wirtinger_presentation(self):
        generators = []
        relations = []
        
        if len(self.crossings) >= 1:
            arcs = self.get_arcs()

            generators.extend(xrange(1, len(arcs) + 1))
            
            for crossing, info in self.get_crossings_arc_info().iteritems():
                overstrand_index = arcs.index(info['overstrand']) + 1
                understrand_incoming_index = arcs.index(info['understrand-incoming']) + 1
                understrand_leaving_index = arcs.index(info['understrand-leaving']) + 1

                if crossing.sign() < 0:
                    relation = [understrand_leaving_index,
                                overstrand_index,
                                understrand_incoming_index,
                                -1 * overstrand_index]
                else:
                    relation = [understrand_leaving_index,
                                -1 * overstrand_index,
                                understrand_incoming_index,
                                overstrand_index] 
                
                relations.append(relation)
        else:
            generators = [1]
            relations = []
            
        return {'generators': generators,
                'relations': relations}
            
                     
    def is_done(self):
        if len(self.vertices) > 2:
            return self.vertices[0] == self.vertices[-1]
        return False
    
    def is_alternating(self):
        gauss_code = self.gauss_code()
        
        if len(self.crossings) >= 2:
            for i in xrange(0, len(gauss_code) - 1):
                if gauss_code[i] * gauss_code[i + 1] > 0:
                    return False
        
        return True
    
    def is_tricolorable(self):
        if self.is_done() and len(self.crossings) >= 1:
            arcs = self.get_arcs()
            
            colorings = _possible_colorings([x for x in xrange(0, len(arcs))])
            
            for coloring in colorings:
                coloring_data = []
                
                for arc in arcs:
                    coloring_data.append({'arc': arc,
                                          'color': coloring[arcs.index(arc)]})                
                
                if self.is_valid_coloring(coloring_data):
                    return (True, coloring_data)

            return (False, None)
            
        
        return (False, None)

    def is_valid_coloring(self, coloring):
       
        if len(set([x['color'] for x in coloring])) == 3:
            for crossing, info in self.get_crossings_arc_info().iteritems():
                strands_color = []

                for x in coloring:
                    color = x['color']
                    
                    if x['arc'] == info['overstrand']:
                        strands_color.append(color)

                    if x['arc'] == info['understrand-incoming']:
                        strands_color.append(color)
                        
                    if x['arc'] == info['understrand-leaving']:
                        strands_color.append(color)
                
                if len(strands_color) != 3:
                    raise Exception('ERROR')
                
                if sum(strands_color) % 3 != 0:
                    return False
                
            return True

        return False
            
        
    def get_crossing_of(self, line1, line2):
        for c in self.crossings:
            if (c.under == line1 and c.over == line2) or \
               (c.under == line2 and c.over == line1):
                return c
        
        return None
    
    def get_crossings_involving_line(self, line):
        crossings = []
        
        for c in self.crossings:
            if (c.involves(line)):
                crossings.append((c.crosspoint.distance(line.orig), c))
                
        crossings.sort(cmp=_sort_crossings) # Sort crossings using distance from line initial point
        
        res = []
        for c in crossings:
            res.append(c[1])
        
        return res
    
    def _line_intersects_segment(self, line):
        if len(self.vertices) < 2:
            return False
        
        for s in self.segments[:-1]:
            if s.intersects(line):
                return True
            
        return False
    
    def get_writhe(self):
        return sum([x.sign() for x in self.crossings])

    def connect(self, event, callback):
        if event in self._listeners:
            self._listeners[event].append(callback)
            
    def _emit(self, event, data):
        if event in self._listeners:
            #log '%s:: %s' % (event, data)
            for callback in self._listeners[event]:
                callback(data)
            
            if event != 'model-changed':
                self._emit('model-changed', self)
