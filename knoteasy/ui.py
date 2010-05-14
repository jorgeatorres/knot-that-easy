# encoding: utf-8
import math

import pygtk
pygtk.require('2.0')
import gtk, pango

from knoteasy.core import Point, Line, Crossing, KnotModel


class KnotDrawingArea(gtk.DrawingArea):

    MODE_DRAWING = 0
    MODE_DONE = 1
    
    BG_COLOR = gtk.gdk.color_parse('white')
    FG_COLOR = gtk.gdk.color_parse('black')
    GHOST_LINE_COLOR = gtk.gdk.color_parse('#aaa')
    INITIAL_VERTEX_COLOR = gtk.gdk.color_parse('red')
    
    MINIMUM_VERTEX_DISTANCE = 10
    LINE_WIDTH = 1.5
    VERTEX_RADIUS = 3.0
    
    ARROW_LENGTH = 10
    
    def __init__(self):
        super(KnotDrawingArea, self).__init__()
        self.add_events(gtk.gdk.POINTER_MOTION_MASK |
                        gtk.gdk.BUTTON_PRESS_MASK)
        self.set_flags(gtk.CAN_FOCUS)
        self.connect('configure-event', self._configure_cb)
        self.connect('expose-event', self._expose_cb)
        self.connect('button-press-event', self._button_press_cb)
        self.connect('motion-notify-event', self._motion_notify_cb)
        self.set_size_request(500, 400)
        self.width = 0
        self.height = 0
        self._mode = self.MODE_DRAWING
        self.cursor = None
        
        self.set_model(KnotModel())
        
    def clear(self):
        self.knot_model.set_vertices([])

    def _model_changed_cb(self, model):
        if model.is_done():
            self._mode = self.MODE_DONE
        else:
            self._mode = self.MODE_DRAWING
        self.queue_draw()
        
    def _append_vertex(self, v, over=True):
        if not self.knot_model.vertices:
            self.knot_model.append_vertex(v, over)
        else:
            if self.knot_model.vertices[0].distance(v) <= self.VERTEX_RADIUS:
                v = self.knot_model.vertices[0]

            if self.knot_model.vertices[-1] != v:
                self.knot_model.append_vertex(v, over)

    def _configure_cb(self, widget, event):
        self.width = event.width
        self.height = event.height
        return False
    
    def _button_press_cb(self, widget, event):
        if self._mode == self.MODE_DRAWING and event.button == 1:
            self._append_vertex(Point(event.x, event.y))
        elif self._mode == self.MODE_DRAWING and event.button == 3:
            self._append_vertex(Point(event.x, event.y), False)
        else:
            pass
        return False
    
    def set_model(self, model):
        self.knot_model = model
        model.connect('model-changed', self._model_changed_cb)
        self.queue_draw()        

    def get_model(self):
        return self.knot_model
    
    def _expose_cb(self, widget, event):
        cc = self.window.cairo_create()
        cc.set_line_width(self.LINE_WIDTH)
        
        cc.save()
        cc.set_source_color(self.BG_COLOR)
        cc.rectangle(0, 0, self.width, self.height)
        cc.fill()
        cc.restore()
        
        # Draw initial vertex
        if self.knot_model.vertices:
            first_vertex = self.knot_model.vertices[0]
            
            cc.save()
            cc.set_source_color(self.INITIAL_VERTEX_COLOR)
            cc.arc(first_vertex.x, first_vertex.y, self.VERTEX_RADIUS, 0.0, 2.0 * math.pi)
            cc.fill()

            cc.restore()
        
        # Draw line segments
        cc.set_source_color(self.FG_COLOR)
        cc.save()
        for s in self.knot_model.segments:
            cc.move_to(s.orig.x, s.orig.y)
            cc.line_to(s.dest.x, s.dest.y)
            cc.stroke()
            
            s2 = 1.0 / math.sqrt(2)
            unit_vector = s.get_direction_vector()

            cc.move_to(s.dest.x + (unit_vector.x - unit_vector.y) * s2 * self.ARROW_LENGTH,
                       s.dest.y + (unit_vector.x + unit_vector.y) * s2 * self.ARROW_LENGTH)
            cc.line_to(s.dest.x + (unit_vector.x + unit_vector.y) * s2 * self.ARROW_LENGTH,
                       s.dest.y + (-unit_vector.x + unit_vector.y) * s2* self.ARROW_LENGTH)
            cc.line_to(s.dest.x, s.dest.y)
            cc.fill()
            
        cc.restore()
        
        # Draw dashed line to cursor from last point
        if self._mode == self.MODE_DRAWING:
            if self.cursor is not None and self.knot_model.vertices:
                last_vertex = self.knot_model.vertices[-1]

                cc.save()
                cc.set_source_color(self.GHOST_LINE_COLOR)
                cc.set_dash([5.0])
                cc.move_to(last_vertex.x, last_vertex.y)
                cc.line_to(self.cursor.x, self.cursor.y)
                cc.stroke()
                cc.restore()
                
        # Draw crossings
        cc.save()
        for c in self.knot_model.crossings:
            cc.set_source_color(self.BG_COLOR)
            cc.arc(c.crosspoint.x, c.crosspoint.y,
                   self.VERTEX_RADIUS * 2.0,
                   0.0, 2.0 * math.pi)
            cc.fill()
            
            # This is a hack but works for now
            cc.set_source_color(self.FG_COLOR)
            over = c.over.get_direction_vector()
            
            x0 = c.crosspoint.x - (self.VERTEX_RADIUS * 2.5) * over.x + 0.5
            y0 = c.crosspoint.y - (self.VERTEX_RADIUS * 2.5) * over.y + 0.5
            x1 = c.crosspoint.x + (self.VERTEX_RADIUS * 2.5) * over.x + 0.5
            y1 = c.crosspoint.y + (self.VERTEX_RADIUS * 2.5) * over.y + 0.5
            
            cc.move_to(x0, y0)
            cc.line_to(x1, y1)
            cc.stroke()
            
        cc.restore()

        return False
    
    def _motion_notify_cb(self, widget, event):
        self.cursor = Point(event.x, event.y)
        self.queue_draw()
        return False
    
    def undo(self):
        self.knot_model.remove_last_vertex()


class MainWindow(gtk.Window):
    
    def __init__(self, **kw):
        super(MainWindow, self).__init__(gtk.WINDOW_TOPLEVEL)
        self.set_title('knot (that) easy')
        self.connect('destroy', gtk.main_quit)
        
        self.ui_builder = ui_builder = gtk.Builder()

        import os.path
        ui_builder.add_from_file(os.path.join(os.path.dirname(__file__),
        'knoteasy.ui'))
        
        main_vbox = ui_builder.get_object('knoteasy_main_vbox')    
        main_vbox.show()
        self.add(main_vbox)
        
        self.drawing_area = drawing_area = KnotDrawingArea()
        drawing_area.get_model().connect('model-changed', self._model_changed_cb)        
        drawing_area.show()
        main_vbox.pack_start(drawing_area)
        
        ui_builder.get_object('knot_data_output').set_editable(False)

        self.knot_data_nb = ui_builder.get_object('knot_data_nb')

        # Actions & Menubar
        accelgroup = gtk.AccelGroup()
        self.add_accel_group(accelgroup)
        
        actiongroup = gtk.ActionGroup('knoteasy-actions')
        self.actiongroup = actiongroup
        
        menubar = ui_builder.get_object('knoteasy_menubar')
        menubar.show()
       
        knoteasy_action = gtk.Action('Knot', '_Knot', None, None)
        actiongroup.add_action(knoteasy_action)
        knoteasy_menu_item = knoteasy_action.create_menu_item()
        menubar.append(knoteasy_menu_item)
        
        knoteasy_menu = gtk.Menu()
        knoteasy_menu_item.set_submenu(knoteasy_menu)

        action = gtk.Action('mirror-image', '_Mirror image', None, None)
        action.set_accel_group(accelgroup)
        action.set_sensitive(False)
        action.connect('activate', self._mirror_image_cb)
        actiongroup.add_action_with_accel(action, None)
        knoteasy_menu.append(action.create_menu_item())
        action = gtk.Action('reverse-orientation', '_Reverse orientation', None, None)
        action.set_accel_group(accelgroup)
        action.set_sensitive(False)
        action.connect('activate', self._reverse_orientation_cb)
        actiongroup.add_action_with_accel(action, None)
        knoteasy_menu.append(action.create_menu_item())
        action = gtk.Action('make-alternating', 'Make _alternating', None, None)
        action.set_accel_group(accelgroup)
        action.set_sensitive(False)
        action.connect('activate', self._make_alternating)
        actiongroup.add_action_with_accel(action, None)
        knoteasy_menu.append(action.create_menu_item())        
        
        
        knoteasy_menu.append(gtk.SeparatorMenuItem())
        action = gtk.Action('quit', '_Quit', None, gtk.STOCK_QUIT)
        action.set_accel_group(accelgroup)
        action.connect('activate', gtk.main_quit)
        actiongroup.add_action_with_accel(action, None)
        knoteasy_menu.append(action.create_menu_item())
        
        # Edit menu
        edit_action = gtk.Action('Edit', '_Edit', None, gtk.STOCK_EDIT)
        actiongroup.add_action(edit_action)
        edit_menu_item = edit_action.create_menu_item()
        menubar.append(edit_menu_item)
        
        edit_menu = gtk.Menu()
        edit_menu_item.set_submenu(edit_menu)
        
        action = gtk.Action('Undo', '_Undo', None, gtk.STOCK_UNDO)
        action.connect('activate', self._undo_cb)
        action.set_accel_group(accelgroup)
        actiongroup.add_action_with_accel(action, None)
        action.set_sensitive(False)
        
        edit_menu.append(action.create_menu_item())
        edit_menu.append(gtk.SeparatorMenuItem())
        action = gtk.Action('Clear', '_Clear', None, gtk.STOCK_CLEAR)
        action.connect('activate', self.clear_cb)
        action.set_accel_group(accelgroup)
        actiongroup.add_action_with_accel(action, None)
        edit_menu.append(action.create_menu_item())
        
        # Help menu
        help_action = gtk.Action('Help', '_Help', None, gtk.STOCK_HELP)
        actiongroup.add_action(help_action)
        help_menu_item = help_action.create_menu_item()
        menubar.append(help_menu_item)
        
        help_menu = gtk.Menu()
        help_menu_item.set_submenu(help_menu)
        
        action = gtk.Action('About', '_About', None, gtk.STOCK_ABOUT)
        action.connect('activate', self.about_cb)
        action.set_accel_group(accelgroup)
        actiongroup.add_action_with_accel(action, None)
        help_menu.append(action.create_menu_item())

    def _model_changed_cb(self, model):
        self.actiongroup.get_action('Undo').set_sensitive(len(model.vertices) > 0)
        self.actiongroup.get_action('mirror-image').set_sensitive(model.is_done())
        self.actiongroup.get_action('reverse-orientation').set_sensitive(model.is_done())
        self.actiongroup.get_action('make-alternating').set_sensitive(model.is_done())
                
        if model.is_done():
            text_buffer = gtk.TextBuffer()
            text_buffer.insert_at_cursor('Vertices:\n')
            text_buffer.insert_at_cursor(repr(model.vertices) + '\n\n')
            text_buffer.insert_at_cursor('Trail:\n')
            text_buffer.insert_at_cursor(repr(model.get_trail()) + '\n\n')
            text_buffer.insert_at_cursor('Crossings arc info:\n')
            text_buffer.insert_at_cursor(repr(model.get_crossings_arc_info()) + '\n\n')
            self.ui_builder.get_object('knot_data_output').set_buffer(text_buffer)            
            
            self.ui_builder.get_object('label_crossings_no').set_label('%d' % len(model.crossings))
            self.ui_builder.get_object('label_arcs_no').set_label('%d' % len(model.get_arcs()))
            self.ui_builder.get_object('label_alternating').set_label('Yes' if model.is_alternating() else 'No')
            self.ui_builder.get_object('label_writhe').set_label('%d' % model.get_writhe())
            
            gauss_code = model.extended_gauss_code()
            self.ui_builder.get_object('label_gauss_code').set_label('%s / %s' % (' '.join(map(str, gauss_code[0])),
                                                                  ' '.join(gauss_code[1])))
            self.ui_builder.get_object('label_dowker_code').set_label(' '.join(map(str, model.dowker_notation())))

            # Wirtinger            
            wirtinger = model.wirtinger_presentation()
            generators_str = ''
            
            for i in wirtinger['generators']:
                generators_str = generators_str + 'x<sub>%d</sub> ' % i
            self.ui_builder.get_object('label_wirtinger_generators').set_label(generators_str)
            
            relations_vbox = self.ui_builder.get_object('wirtinger_relations_vbox')
            for w in relations_vbox.get_children():
                relations_vbox.remove(w)
                
            if wirtinger['relations']:
                for r in wirtinger['relations']:
                    label = gtk.Label()
                    label.set_size_request(-1, 30)
                    label.show()
                    label.set_selectable(True)
                    label.set_alignment(0, 0)
                    label.set_ellipsize(pango.ELLIPSIZE_END)
                    
                    relation_str = 'x<sub>%d</sub> = ' % r[0]
                    
                    for k in r[1:]:
                        if k > 0:
                            relation_str = relation_str + 'x<sub>%d</sub>' % k
                        else:
                            relation_str = relation_str + 'x<sub>%d</sub><sup>-1</sup>' % abs(k)
                    
                    label.set_markup(relation_str)
                    
                    relations_vbox.pack_start(label, False, False, 0)
            else:
                label = gtk.Label('--')
                label.show()
                relations_vbox.pack_start(label, True, False)
            
            
            # 3-colorability
            is_tricolorable, coloring = model.is_tricolorable()
            self.ui_builder.get_object('label_tricolorability').set_label('Yes' if is_tricolorable else 'No')
            
            if is_tricolorable:
                self.ui_builder.get_object('label_coloring').set_markup(' '.join(['c<sub>%d</sub>' % (x['color'] + 1) for x in coloring]))
            else:
                self.ui_builder.get_object('label_coloring').set_label('--')
            
            self.knot_data_nb.set_sensitive(True)
        else:
            self.knot_data_nb.set_sensitive(False)
    
    def about_cb(self, action):
        dialog = gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_authors(['Jorge Torres'])
        dialog.run()
        
    def _mirror_image_cb(self, action):
        self.drawing_area.set_model(self.drawing_area.get_model().mirror_image())
        self.drawing_area.get_model().connect('model-changed', self._model_changed_cb)
        self._model_changed_cb(self.drawing_area.get_model())
        
    def _reverse_orientation_cb(self, action):
        self.drawing_area.set_model(self.drawing_area.get_model().orientation_reversed())
        self.drawing_area.get_model().connect('model-changed', self._model_changed_cb)
        self._model_changed_cb(self.drawing_area.get_model())
        
    def _make_alternating(self, action):
        self.drawing_area.get_model().make_alternating()        
        
    def _undo_cb(self, action):
        self.drawing_area.undo()
        
    def clear_cb(self, action):
        self.drawing_area.clear()
