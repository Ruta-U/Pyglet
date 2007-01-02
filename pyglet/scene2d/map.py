#!/usr/bin/env python

'''
Model code for managing rectangular and hexagonal maps
======================================================

This module provides classes for managing rectangular and hexagonal maps.

---------------
Getting Started
---------------

You may create a map interactively and query it:

    >>> from pyglet.scene2d import *
    >>> m = Map(32, 32, meta=[['a', 'd'], ['b', 'e'], ['c', 'f']])
    >>> m.get((0,0))
    <Tile object at 0x-4828d82c (0, 0) meta='a' image=None>
    >>> _.get_neighbor(_.RIGHT)
    <Tile object at 0x-483c80bc (1, 0) meta='b' image=None>
    >>> _.get_neighbor(_.UP)
    <Tile object at 0x-4828d82c (1, 1) meta='e' image=None>
    >>> print _.get_neighbor(_.UP)
    None

Similarly:

    >>> m = HexMap(32, meta=[['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'height']])
    >>> m.get((0,0))
    <HexTile object at 0x-482f682c (0, 0) meta='a' image=None>
    >>> _.get_neighbor(_.UP)
    <HexTile object at 0x-484310bc (0, 1) meta='b' image=None>
    >>> _.get_neighbor(_.DOWN_RIGHT)
    <HexTile object at 0x-484310bc (2, 0) meta='e' image=None>
    >>> print _.get_neighbor(_.DOWN)
    None

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import math

class MapBase(object):
    '''Base class for Maps.

    Both rect and hex maps have the following attributes:

        (width, height)     -- size of map in tiles
        (pxw, pxh) -- size of map in pixels
        (tw, th)   -- size of each tile in pixels
        (x, y, z)  -- offset of map top left from origin in pixels
        meta       -- array [x][y] of meta-data (arbitrary data allowed)
        images     -- array [x][y] of objects with .draw() and
                      optionally .animate(dt)
    '''

    def get(self, pos=None, px=None):
        ''' Return Tile at tile pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        raise NotImplemented()

class Map(MapBase):
    '''Rectangular map.

    Tiles are stored in column-major order with y increasing up,
    allowing [x][y] addressing:
    +---+---+---+
    | d | e | f |
    +---+---+---+
    | a | b | c |
    +---+---+---+
    Thus tiles = [['a', 'd'], ['b', 'e'], ['c', 'f']]
    and tiles[0][1] = 'd'
    '''
    __slots__ = 'pxw pxh tw th x y z meta images'.split()
    def __init__(self, tw, th, origin=(0, 0, 0), meta=None, images=None):
        if meta is None and images is None:
            raise ValueError, 'Either meta or images must be supplied'
        self.tw, self.th = tw, th
        self.x, self.y, self.z = origin
        self.meta = meta
        self.images = images
        l = meta or images
        self.pxw = len(l) * tw
        self.pxh = len(l[1]) * th
 
    def get(self, pos=None, px=None):
        ''' Return Tile at tile pos=(x,y) or pixel px=(x,y).
        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            x, y = px
            x /= self.tw
            y /= self.th
        else:
            raise ValueError, 'Either tile or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            meta = self.meta and self.meta[x][y]
            image = self.images and self.images[x][y]
            return Tile(self, x, y, meta, image)
        except IndexError:
            return None

class TileBase(object):
    '''Base class for tiles from rect and hex maps.

    Common attributes:
        map         -- Map instance this Tile came from
        x, y        -- top-left coordinate
        width, height        -- dimensions
        meta        -- meta-data from the Map's meta
        image       -- image from the Map's images
    '''
    def __init__(self, map, x, y, meta, image):
        self.map = map
        self.width, self.height = map.tw, map.th
        self.x, self.y = x, y
        self.meta = meta
        self.image = image

    def __repr__(self):
        return '<%s object at 0x%x (%g, %g) meta=%r image=%r>'%(
            self.__class__.__name__, id(self), self.x, self.y, self.meta,
                self.image)

class Tile(TileBase):
    '''A rectangular tile from a Map.

    Read-only attributes:
        top         -- y extent
        bottom      -- y extent
        left        -- x extent
        right       -- x extent
        center      -- (x, y)
        topleft     -- (x, y) of top-left corner
        topright    -- (x, y) of top-right corner
        bottomleft  -- (x, y) of bottom-left corner
        bottomright -- (x, y) of bottom-right corner
        midtop      -- (x, y) of middle of top side
        midbottom   -- (x, y) of middle of bottom side
        midleft     -- (x, y) of middle of left side
        midright    -- (x, y) of middle of right side
    '''
    __slots__ = 'map x y width height meta image'.split()

    # ro, side in pixels, y extent
    def get_top(self):
        return (self.y + 1) * self.height
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.y * self.height
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        return (self.x * self.width + self.width/2, self.y * self.height + self.height/2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        return (self.x * self.width + self.width/2, self.y * self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        return (self.x * self.width + self.width/2, (self.y + 1) * self.height)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        return self.x * self.width
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        return (self.x + 1) * self.width
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        return (self.x * self.width, self.y * self.height)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        return ((self.x + 1) * self.width, self.y * self.height)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        return (self.x * self.height, (self.y + 1) * self.height)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        return ((self.x + 1) * self.width, (self.y + 1) * self.height)
    bottomright = property(get_bottomright)

    # ro, mid-point in pixels, (x, y)
    def get_midleft(self):
        return (self.x * self.width, self.y * self.height + self.height/2)
    midleft = property(get_midleft)
 
    # ro, mid-point in pixels, (x, y)
    def get_midright(self):
        return ((self.x + 1) * self.width, self.y * self.height + self.height/2)
    midright = property(get_midright)
 
    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    def get_neighbor(self, direction):
        '''Get my neighbor Tile in the given direction (dx, dy) which
        is one of self.UP, self.DOWN, self.LEFT or self.RIGHT.

        Returns None if out of bounds.
        '''
        dx, dy = direction
        return self.map.get((self.x + dx, self.y + dy))

 
class HexMap(MapBase):
    '''Map with flat-top, regular hexagonal cells.

    Additional attributes extending MapBase:

        edge_length -- length of an edge in pixels

    Hexmaps store their tiles in an offset array, column-major with y
    increasing up, such that a map:
          /d\ /height\
        /b\_/f\_/
        \_/c\_/g\
        /a\_/e\_/
        \_/ \_/ 
    has tiles = [['a', 'b'], ['c', 'd'], ['e', 'f'], ['g', 'height']]
    '''
    __slots__ = 'tw th edge_length left right pxw pxh x y z meta images'.split()
    def __init__(self, th, origin=(0, 0, 0), meta=None, images=None):
        if meta is None and images is None:
            raise ValueError, 'Either meta or images must be supplied'
        self.th = th
        self.x, self.y, self.z = origin
        self.meta = meta
        self.images = images

        # figure some convenience values
        self.edge_length = int(th / math.sqrt(3))
        self.tw = self.edge_length * 2
        self.left = (self.tw/2, th/2)
        self.right = (self.edge_length * 2, th/2)

        # now figure map dimensions
        l = meta or images
        width = len(l); height = len(l[0])
        self.pxw = HexTile(self, width-1, 0, None, None).right[0]
        if width > 1:
            self.pxh = HexTile(self, 1, height-1, None, None).top
        else:
            self.pxh = HexTile(self, 0, height-1, None, None).top
 
    def get(self, pos=None, px=None):
        '''Get the Tile at tile pos=(x,y) or pixel px=(x,y).

        Return None if out of bounds.'''
        if pos is not None:
            x, y = pos
        elif px is not None:
            raise NotImplemented('TODO: translate pixel to tile')
        else:
            raise ValueError, 'Either tile or pixel pos must be supplied'
        if x < 0 or y < 0:
            return None
        try:
            meta = image = None
            if self.meta:
                meta = self.meta[x][y]
                if meta is None: return None
            if self.images:
                image = self.images[x][y]
                if image is None: return None
            return HexTile(self, x, y, meta, image)
        except IndexError:
            return None
 
# Note that we always add below (not subtract) so that we can try to
# avoid accumulation errors due to rounding ints. We do this so
# we can each point at the same position as a neighbor's corresponding
# point.
class HexTile(TileBase):
    '''A flat-top, regular hexagon tile from a HexMap.

    Read-only attributes:
        top             -- y extent
        bottom          -- y extent
        left            -- (x, y) of left corner
        right           -- (x, y) of right corner
        center          -- (x, y)
        topleft         -- (x, y) of top-left corner
        topright        -- (x, y) of top-right corner
        bottomleft      -- (x, y) of bottom-left corner
        bottomright     -- (x, y) of bottom-right corner
        midtop          -- (x, y) of middle of top side
        midbottom       -- (x, y) of middle of bottom side
        midtopleft      -- (x, y) of middle of left side
        midtopright     -- (x, y) of middle of right side
        midbottomleft   -- (x, y) of middle of left side
        midbottomright  -- (x, y) of middle of right side
    '''
    __slots__ = 'map x y width height meta image'.split()

    def get_origin(self):
        x = self.x * (self.width / 2 + self.width / 4)
        y = self.y * self.height
        if self.x % 2:
            y += self.height / 2
        return (x, y)

    # ro, side in pixels, y extent
    def get_top(self):
        y = self.get_origin()[1]
        return y + self.height
    top = property(get_top)

    # ro, side in pixels, y extent
    def get_bottom(self):
        return self.get_origin()[1]
    bottom = property(get_bottom)

    # ro, in pixels, (x, y)
    def get_center(self):
        x, y = self.get_origin()
        return (x + self.width / 2, y + self.height / 2)
    center = property(get_center)

    # ro, mid-point in pixels, (x, y)
    def get_midtop(self):
        x, y = self.get_origin()
        return (x + self.width/2, y + self.height)
    midtop = property(get_midtop)

    # ro, mid-point in pixels, (x, y)
    def get_midbottom(self):
        x, y = self.get_origin()
        return (x + self.width/2, y)
    midbottom = property(get_midbottom)

    # ro, side in pixels, x extent
    def get_left(self):
        x, y = self.get_origin()
        return (x, y + self.height/2)
    left = property(get_left)

    # ro, side in pixels, x extent
    def get_right(self):
        x, y = self.get_origin()
        return (x + self.width, y + self.height/2)
    right = property(get_right)

    # ro, corner in pixels, (x, y)
    def get_topleft(self):
        x, y = self.get_origin()
        return (x + self.width / 4, y + self.height)
    topleft = property(get_topleft)

    # ro, corner in pixels, (x, y)
    def get_topright(self):
        x, y = self.get_origin()
        return (x + self.width/2 + self.width / 4, y + self.height)
    topright = property(get_topright)

    # ro, corner in pixels, (x, y)
    def get_bottomleft(self):
        x, y = self.get_origin()
        return (x + self.width / 4, y)
    bottomleft = property(get_bottomleft)

    # ro, corner in pixels, (x, y)
    def get_bottomright(self):
        x, y = self.get_origin()
        return (x + self.width/2 + self.width / 4, y)
    bottomright = property(get_bottomright)

    # ro, middle of side in pixels, (x, y)
    def get_midtopleft(self):
        x, y = self.get_origin()
        return (x + self.width / 8, y + self.height/2 + self.height/4)
    midtopleft = property(get_midtopleft)

    # ro, middle of side in pixels, (x, y)
    def get_midtopright(self):
        x, y = self.get_origin()
        return (x + self.width / 2 + self.width / 4 + self.width / 8,
            y + self.height/2 + self.height/4)
    midtopright = property(get_midtopright)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomleft(self):
        x, y = self.get_origin()
        return (x + self.width / 8, y + self.height/4)
    midbottomleft = property(get_midbottomleft)

    # ro, middle of side in pixels, (x, y)
    def get_midbottomright(self):
        x, y = self.get_origin()
        return (x + self.width / 2 + self.width / 4 + self.width / 8,
            y + self.height/4)
    midbottomright = property(get_midbottomright)

    UP = 'up'
    DOWN = 'down'
    UP_LEFT = 'up left'
    UP_RIGHT = 'up right'
    DOWN_LEFT = 'down left'
    DOWN_RIGHT = 'down right'
    def get_neighbor(self, direction):
        '''Get my neighbor HexTile in the given direction which
        is one of self.UP, self.DOWN, self.UP_LEFT, self.UP_RIGHT,
        self.DOWN_LEFT or self.DOWN_RIGHT.

        Return None if out of bounds.
        '''
        if direction is self.UP:
            return self.map.get((self.x, self.y + 1))
        elif direction is self.DOWN:
            return self.map.get((self.x, self.y - 1))
        elif direction is self.UP_LEFT:
            if self.x % 2:
                return self.map.get((self.x - 1, self.y + 1))
            else:
                return self.map.get((self.x - 1, self.y))
        elif direction is self.UP_RIGHT:
            if self.x % 2:
                return self.map.get((self.x + 1, self.y + 1))
            else:
                return self.map.get((self.x + 1, self.y))
        elif direction is self.DOWN_LEFT:
            if self.x % 2:
                return self.map.get((self.x - 1, self.y))
            else:
                return self.map.get((self.x - 1, self.y - 1))
        elif direction is self.DOWN_RIGHT:
            if self.x % 2:
                return self.map.get((self.x + 1, self.y))
            else:
                return self.map.get((self.x + 1, self.y - 1))
        else:
            raise ValueError, 'Unknown direction %r'%direction
