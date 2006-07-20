## vim:ts=4:et:nowrap
##
##---------------------------------------------------------------------------##
##
## PySol -- a Python Solitaire game
##
## Copyright (C) 2003 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2002 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2001 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 2000 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1999 Markus Franz Xaver Johannes Oberhumer
## Copyright (C) 1998 Markus Franz Xaver Johannes Oberhumer
## All Rights Reserved.
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; see the file COPYING.
## If not, write to the Free Software Foundation, Inc.,
## 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
## Markus F.X.J. Oberhumer
## <markus@oberhumer.com>
## http://www.oberhumer.com/pysol
##
##---------------------------------------------------------------------------##

__all__ = ['MfxCanvasGroup',
           'MfxCanvasImage',
           'MfxCanvasText',
           'MfxCanvasLine',
           'MfxCanvasRectangle',
           'MfxCanvas']

# imports
import os, sys, types
import Tkinter, Canvas
try:
    # PIL (Python Image Library)
    import Image
except ImportError:
    Image = None
else:
    import ImageTk
    # for py2exe
    import GifImagePlugin, PngImagePlugin, JpegImagePlugin, BmpImagePlugin, PpmImagePlugin
    Image._initialized=2

# Toolkit imports
from tkutil import bind, unbind_destroy, loadImage


# /***********************************************************************
# // canvas items
# ************************************************************************/

class MfxCanvasGroup(Canvas.Group):
    def __init__(self, canvas, tag=None):
        Canvas.Group.__init__(self, canvas=canvas, tag=tag)
        # register ourself so that we can unbind from the canvas
        assert not self.canvas.items.has_key(self.id)
        self.canvas.items[self.id] = self
    def addtag(self, tag, option="withtag"):
        self.canvas.addtag(tag, option, self.id)
    def delete(self):
        del self.canvas.items[self.id]
        Canvas.Group.delete(self)
    def gettags(self):
        return self.canvas.tk.splitlist(self._do("gettags"))

class MfxCanvasImage(Canvas.ImageItem):
    def moveTo(self, x, y):
        c = self.coords()
        self.move(x - int(c[0]), y - int(c[1]))

MfxCanvasLine = Canvas.Line

MfxCanvasRectangle = Canvas.Rectangle

class MfxCanvasText(Canvas.CanvasText):
    def __init__(self, canvas, x, y, preview=-1, **kw):
        if preview < 0:
            preview = canvas.preview
        if preview > 1:
            return
        if not kw.has_key("fill"):
            kw["fill"] = canvas._text_color
        apply(Canvas.CanvasText.__init__, (self, canvas, x, y), kw)
        self.text_format = None
        canvas._text_items.append(self)


# /***********************************************************************
# // canvas
# ************************************************************************/

class MfxCanvas(Tkinter.Canvas):
    def __init__(self, *args, **kw):
        apply(Tkinter.Canvas.__init__, (self,) + args, kw)
        self.preview = 0
        # this is also used by lib-tk/Canvas.py
        self.items = {}
        # private
        self.__tileimage = None
        self.__tiles = []           # id of canvas items
        self.__topimage = None
        self.__tops = []            # id of canvas items
        # friend MfxCanvasText
        self._text_color = "#000000"
        self._stretch_bg_image = 0
        self._text_items = []
        # resize bg image
        self.bind('<Configure>', lambda e: self.set_bg_image())

    def set_bg_image(self):
        ##print 'set_bg_image', self._bg_img
        if not hasattr(self, '_bg_img'):
            return
        if not self._bg_img: # solid color
            return
        stretch = self._stretch_bg_image
        if Image:
            if stretch:
                w = max(self.winfo_width(), int(self.cget('width')))
                h = max(self.winfo_height(), int(self.cget('height')))
                im = self._bg_img.resize((w, h))
                image = ImageTk.PhotoImage(im)
            else:
                image = ImageTk.PhotoImage(self._bg_img)
        else: # not Image
            stretch = 0
            image = self._bg_img
        for id in self.__tiles:
            self.delete(id)
        self.__tiles = []
        # must keep a reference to the image, otherwise Python will
        # garbage collect it...
        self.__tileimage = image
        if stretch:
            #
            id = self._x_create("image", 0, 0, image=image, anchor="nw")
            self.tag_lower(id)          # also see tag_lower above
            self.__tiles.append(id)
        else:
            iw, ih = image.width(), image.height()
            #sw = max(self.winfo_screenwidth(), 1024)
            #sh = max(self.winfo_screenheight(), 768)
            sw = max(self.winfo_width(), int(self.cget('width')))
            sh = max(self.winfo_height(), int(self.cget('height')))
            for x in range(0, sw - 1, iw):
                for y in range(0, sh - 1, ih):
                    id = self._x_create("image", x, y, image=image, anchor="nw")
                    self.tag_lower(id)          # also see tag_lower above
                    self.__tiles.append(id)
        return 1


    #
    # top-image support
    #

    def _x_create(self, itemType, *args, **kw):
        return Tkinter.Canvas._create(self, itemType, args, kw)

    def _create(self, itemType, args, kw):
        ##print "_create:", itemType, args, kw
        id = Tkinter.Canvas._create(self, itemType, args, kw)
        if self.__tops:
            self.tk.call(self._w, "lower", id, self.__tops[0])
        return id

    def tag_raise(self, id, aboveThis=None):
        ##print "tag_raise:", id, aboveThis
        if aboveThis is None and self.__tops:
            self.tk.call(self._w, "lower", id, self.__tops[0])
        else:
            self.tk.call(self._w, "raise", id, aboveThis)

    def tag_lower(self, id, belowThis=None):
        ##print "tag_lower:", id, belowThis
        if belowThis is None and self.__tiles:
            self.tk.call(self._w, "raise", id, self.__tiles[-1])
        else:
            self.tk.call(self._w, "lower", id, belowThis)


    #
    #
    #

    def setInitialSize(self, width, height):
        ##print 'setInitialSize:', width, height
        self.config(width=width, height=height)
        self.config(scrollregion=(0, 0, width, height))


    #
    #
    #

    # delete all CanvasItems, but keep the background and top tiles
    def deleteAllItems(self):
        self._text_items = []
        for id in self.items.keys():
            assert not id in self.__tiles   # because the tile is created by id
            unbind_destroy(self.items[id])
            self.items[id].delete()
        assert self.items == {}

    def findCard(self, stack, event):
        if isinstance(stack.cards[0].item, Canvas.Group):
            current = self.gettags("current")           # get tags
            for i in range(len(stack.cards)):
                if stack.cards[i].item.tag in current:
                    return i
        else:
##             current = self.find("withtag", "current")   # get item ids
##             for i in range(len(stack.cards)):
##                 if stack.cards[i].item.id in current:
##                     return i
            x, y = event.x, event.y
            items = list(self.find_overlapping(x,y,x,y))
            items.reverse()
            for item in items:
                for i in range(len(stack.cards)):
                    if stack.cards[i].item.id == item:
                        return i
        return -1

    def setTextColor(self, color):
        if color is None:
            c = self.cget("bg")
            if type(c) is not types.StringType or c[0] != "#" or len(c) != 7:
                return
            v = []
            for i in (1, 3, 5):
                v.append(int(c[i:i+2], 16))
            luminance = (0.212671 * v[0] + 0.715160 * v[1] + 0.072169 * v[2]) / 255
            ##print c, ":", v, "luminance", luminance
            color = ("#000000", "#ffffff") [luminance < 0.3]
        if self._text_color != color:
            self._text_color = color
            for item in self._text_items:
                item.config(fill=self._text_color)

    def setTile(self, image, stretch=0):
        ##print 'setTile:', image, stretch
        if image:
            if Image:
                try:
                    self._bg_img = Image.open(image)
                except:
                    return 0
            else:
                try:
                    self._bg_img = loadImage(file=image, dither=1)
                except:
                    return 0
            self._stretch_bg_image = stretch
            self.set_bg_image()
        else:
            for id in self.__tiles:
                self.delete(id)
            self.__tiles = []
            self._bg_img = None
        return 1

    def setTopImage(self, image, cw=0, ch=0):
        try:
            if image and type(image) is types.StringType:
                image = loadImage(file=image)
        except Tkinter.TclError:
            return 0
        if len(self.__tops) == 1 and image is self.__tops[0]:
            return 1
        for id in self.__tops:
            self.delete(id)
        self.__tops = []
        # must keep a reference to the image, otherwise Python will
        # garbage collect it...
        self.__topimage = image
        if image is None:
            return 1
        iw, ih = image.width(), image.height()
        if cw <= 0:
            ##cw = max(int(self.cget("width")), self.winfo_width())
            cw = self.winfo_width()
        if ch <= 0:
            ##ch = max(int(self.cget("height")),  self.winfo_height())
            ch = self.winfo_height()
        ###print iw, ih, cw, ch
        x = (cw - iw) / 2
        y = (ch - ih) / 2
        id = self._x_create("image", x, y, image=image, anchor="nw")
        self.tk.call(self._w, "raise", id)
        self.__tops.append(id)
        return 1

    #
    # Pause support
    #

    def hideAllItems(self):
        for item in self.items.values():
            item.config(state='hidden')

    def showAllItems(self):
        for item in self.items.values():
            item.config(state='normal')


    #
    # restricted but fast _bind and _substitute
    #

    def _bind(self, what, sequence, func, add, needcleanup=1):
        funcid = self._register(func, self._substitute, needcleanup)
        cmd = ('%sif {"[%s %s]" == "break"} break\n' %
                (add and '+' or '', funcid, "%x %y"))
        self.tk.call(what + (sequence, cmd))
        return funcid

    def _substitute(self, *args):
        e = Tkinter.Event()
        e.x = int(args[0])
        e.y = int(args[1])
        return (e,)


    #
    # debug
    #

    def update(self):
        ##import mfxutil; print mfxutil.callername()
        # ??????
        Tkinter.Canvas.update(self)

    def update_idletasks(self):
        ##import mfxutil; print mfxutil.callername()
        Tkinter.Canvas.update_idletasks(self)
