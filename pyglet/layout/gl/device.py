#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from ctypes import *

from pyglet.GL.VERSION_1_1 import *
import pyglet.text
from pyglet.layout.base import *
from pyglet.layout.frame import *
from pyglet.layout.locator import *
from pyglet.image import *

class GLFont(object):
    def __init__(self, font):
        self.font = font

    def create_text_frame(self, box, parent, containing_block,
                          text, width):
        glyphs = self.font.get_glyphs_for_width(text, width)

        frame = GLTextFrame(box, parent, containing_block, 
            self.font, text[:len(glyphs)], glyphs)
        
        if len(text) > len(glyphs) and text[len(glyphs)] == '\n':
            frame.hard_break = True

        return frame

class GLRenderDevice(RenderDevice):
    _stock_font_names = {
        'serif':        'Bitstream Vera Serif',
        'sans-serif':   'Bitstream Vera Sans',
        'monospace':    'Bitstream Vera Sans Mono',
        'fantasy':      'Bistream Vera Serif',
        'cursive':      'Bistream Vera Serif',
    }

    def __init__(self, locator=LocalFileLocator):
        self.locator = locator
        self.texture_cache = {}

    def get_font(self, names, size, style, weight):
        names = names[:]

        for i, name in enumerate(names):
            if isinstance(name, Ident) and name in self._stock_font_names:
                names[i] = self._stock_font_names[name]

        italic = style == 'italic'
        bold = weight >= 700
        assert type(size) == Dimension and size.unit == 'pt'

        return GLFont(pyglet.text.Font(names, size, italic=italic, bold=bold))

    def create_text_frame(self, style, element, text):
        return GLTextFrame(style, element, text)

    def draw_solid_border(self, x1, y1, x2, y2, x3, y3, x4, y4, 
                          color, style):
        '''Draw one side of a border, which is not 'dotted' or 'dashed'.
        '''
        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex2f(x1, y1)
        glVertex2f(x2, y2)
        glVertex2f(x3, y3)
        glVertex2f(x4, y4)
        glEnd()


    def draw_vertical_border(self, x1, y1, x2, y2, x3, y3, x4, y4,
                             color, style):
        '''Draw one vertical edge of a border.
        
        Order of vertices is inner-top, inner-bottom, outer-bottom, outer-top
        '''
        if style in ('dotted', 'dashed'):
            width = max(abs(x1 - x4), 1)
            height = y1 - y2
            if style == 'dotted':
                period = width
            else:
                period = width * 3
            cycles = int(height / period)
            padding = (height - cycles * period) / 2
            vertices = [
                # Top cap
                x1, y1, x1, y1 - padding, x4, y1 - padding, x4, y4,
                # Bottom cap
                x2, y2, x2, y2 + padding, x3, y2 + padding, x3, y3]
            y = y1 - padding
            phase = cycles % 2
            if phase == 0:
                y -= period / 2
            for i in range(cycles):
                if i % 2 == phase:
                    vertices += [x1, y, x1, y - period, x3, y - period, x3, y]
                y -= period
            self.vertices = (c_float * len(vertices))(*vertices)
            glColor4f(*color)
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, self.vertices)
            glDrawArrays(GL_QUADS, 0, len(self.vertices)/2)
            glPopClientAttrib()
        else:
            self.draw_solid_border(x1, y1, x2, y2, x3, y3, x4, y4, color, style)

    def draw_horizontal_border(self, x1, y1, x2, y2, x3, y3, x4, y4,
                               color, style):
        '''Draw one horizontal edge of a border.
        
        Order of vertices is inner-left, inner-right, outer-right, outer-left.
        '''
        if style in ('dotted', 'dashed'):
            height = max(abs(y1 - y4), 1)
            width = x2 - x1
            if style == 'dotted':
                period = height 
            else:
                period = height * 3
            cycles = int(width / period)
            padding = (width - cycles * period) / 2
            vertices = [
                # Left cap
                x1, y1, x1 + padding, y1, x1 + padding, y4, x4, y4,
                # Right cap
                x2, y2, x2 - padding, y2, x2 - padding, y3, x3, y3]
            x = x1 + padding
            phase = cycles % 2
            if phase == 0:
                x += period / 2
            for i in range(cycles):
                if i % 2 == phase:
                    vertices += [x, y1, x + period, y1, x + period, y3, x, y3]
                x += period
            self.vertices = (c_float * len(vertices))(*vertices)
            glColor4f(*color)
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(2, GL_FLOAT, 0, self.vertices)
            glDrawArrays(GL_QUADS, 0, len(self.vertices)/2)
            glPopClientAttrib()
        else:
            self.draw_solid_border(x1, y1, x2, y2, x3, y3, x4, y4, color, style)

    def draw_background(self, x1, y1, x2, y2, frame):
        compute = frame.get_computed_property
        background_color = compute('background-color')
        if background_color != 'transparent':
            glPushAttrib(GL_CURRENT_BIT)
            glColor4f(*box.background_color)
            glBegin(GL_QUADS)
            glVertex2f(x1, y1)
            glVertex2f(x1, y2)
            glVertex2f(x2, y2)
            glVertex2f(x2, y1)
            glEnd()
            glPopAttrib()

        background_image = compute('background-image')
        if background_image != 'none':
            repeat = compute('background-repeat')
            if background_image not in self.texture_cache:
                self.texture_cache[background_image] = None
                stream = self.locator.get_stream(background_image)
                if stream:
                    texture = Image.load(file=stream).texture()
                    if repeat != 'no-repeat':
                        texture.stretch()
                    self.texture_cache[background_image] = texture
            texture = self.texture_cache[background_image]
            if texture:
                u1, v1 = 0,0
                u2, v2 = texture.uv
                width, height = texture.width, texture.height
                if repeat in ('no-repeat', 'repeat-y'):
                    x2 = x1 + width
                else:
                    u2 = (x2 - x1) / width

                if repeat in ('no-repeat', 'repeat-x'):
                    y2 = y1 - height
                else:
                    v2 = (y1 - y2) / height
                    # Compensate to keep tiling beginning at top, not bottom
                    v1 = -(v2 - int(v2))
                    v2 += v1

                      # uv          # xyz
                ar = [u1, v1,       x1, y2, 0,
                      u1, v2,       x1, y1, 0,
                      u2, v2,       x2, y1, 0,
                      u2, v1,       x2, y2, 0]
                ar = (c_float * len(ar))(*ar)
            
                glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
                glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
                glColor3f(1, 1, 1)
                glEnable(GL_TEXTURE_2D)
                glEnable(GL_BLEND)
                glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                glBindTexture(GL_TEXTURE_2D, texture.id)
                glInterleavedArrays(GL_T2F_V3F, 0, ar)
                glDrawArrays(GL_QUADS, 0, 4)
                glPopAttrib()
                glPopClientAttrib()
                    
   
class GLTextFrame(TextFrame):
    glyph_string = None
    from_index = 0
    to_index = 0
    is_continuation = False

    content_ascent = 0

    def __init__(self, style, element, text):
        super(GLTextFrame, self).__init__(style, element, text)

    def flow_inline(self, containing_block, remaining_width):
        # Clear previous flow continuation if any
        self.continuation = None

        # Get GL glyph sequence if not already cached
        font = self.get_computed_property('--font').font
        if not self.glyph_string:
            self.glyph_string = pyglet.text.GlyphString(self.text, font.get_glyphs(self.text))

        computed = self.get_computed_property
        def used(property):
            value = computed(property)
            if type(value) == Percentage:
                value = value * containing_block.width
            return value
        
        # Calculate computed and used values of box properties when
        # relative to containing block width.
        # margin top/bottom remain at class default 0
        content_right = computed('border-right-width') + used('padding-right')
        content_bottom = computed('border-bottom-width') + used('padding-bottom')
        self.content_top = computed('border-top-width') + used('padding-top')
        self.margin_right = used('margin-right')
        if not self.is_continuation:
            self.margin_left = used('margin-left')
            self.content_left = computed('border-left-width') + used('padding-left')

        # Calculate text metrics (actually not dependent on flow, could
        # optimise out).
        self.content_ascent = font.ascent + self.content_top
        self.content_descent = font.descent - content_bottom
        line_height = self.get_computed_property('line-height') 
        if line_height != 'normal':
            half_leading = (line_height - \
                (self.content_ascent - self.content_descent)) / 2
        else:
            half_leading = 0
        self.line_ascent = self.content_ascent + half_leading
        self.line_descent = self.content_descent + half_leading
        self.border_edge_height = self.content_ascent - self.content_descent

        # How much text will fit?
        remaining_width -= self.margin_left + self.content_left + \
            content_right + self.margin_right

        # Create continuation if necessary
        self.to_index = self.glyph_string.get_break_index(self.from_index,
            remaining_width)
        if self.to_index < len(self.text) - 1:
            self.continuation = GLTextFrame(
                self.style, self.element, self.text)
            self.continuation.is_continuation = True
            self.continuation.from_index = self.to_index + 1
            self.continuation.glyph_string = self.glyph_string

            self.margin_right = 0
            content_right = 0
        self.fit_flow = self.from_index != self.to_index

        # Calculate edge size
        self.border_edge_width = self.content_left + \
            self.glyph_string.get_subwidth(self.from_index, self.to_index) + \
            content_right
        

    def draw_text(self, x, y, render_context):
        glPushAttrib(GL_CURRENT_BIT | GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)
        glColor4f(*self.get_computed_property('color'))
        glPushMatrix()
        glTranslatef(x, y, 0)
        self.glyph_string.draw(self.from_index, self.to_index)
        glPopMatrix()
        glPopAttrib()
 