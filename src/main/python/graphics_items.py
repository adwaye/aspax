# -*- coding: utf-8 -*-
"""
Created on Tue Sep  8 07:32:13 2015

@author classes: phanquochuy
"""

from PyQt5 import QtGui
from PyQt5.QtCore import ( QPointF, QRectF, Qt)
from PyQt5.QtGui import (QColor, QBrush, QFont, QPen, QTransform, QPainterPath)
from PyQt5.QtWidgets import (QGraphicsScene, QGraphicsItem, QGraphicsTextItem)


from data_models import *
from common import *
from utils import _NP, _QP
import math
from PyQt5 import QtCore, QtWidgets

DEFAULT_COLOR = QColor(255, 255, 150, 50)
DEFAULT_HIGH_COLOR = Qt.yellow
DEFAULT_EDGE_COLOR = Qt.black
DEFAULT_HIGH_EDGE_COLOR = Qt.blue
DEFAULT_HANDLE_COLOR = Qt.green
DEFAULT_HANDLE_SIZE = 5
DEFAULT_EDGE_WIDTH = 1
DEFAULT_ANN_EDGE_STYLE = Qt.DashLine
DEFAULT_ANN_EDGE_WIDTH = 1.5
DEFAULT_IDMAN = IDManager()


def dataModel2GraphicsItem(model):
    """"""
    if isinstance(model, str):
        return globals()[model + 'Item']


class InteractiveScene(QGraphicsScene):
    """"""
    def __init__(self, parent=None):
        # self._active_item = None
        self._layer_stack = LayerStack()
        super(InteractiveScene, self).__init__(parent)
        self.reset()

    def addItem(self, item):
        self._layer_stack.addItemToCurrentLayer(item)
        super(InteractiveScene, self).addItem(item)



#    def mousePressEvent(self, event):
#        super(InteractiveScene, self).mousePressEvent(event)
#        item = InteractiveScene()
#        position = QPointF(event.scenePos()) - item.rectF.center()
#        item.setPos(position.x() , position.y())
#        self.addItem(item)


    def mousePressEvent(self, e):
        """
        if the user click on an item, set it to the current_item in the LayerStack.
        :param e:
        :return:
        """
        pos = e.scenePos()
        items = [item for item in self.items(pos) if issubclass(item.__class__, ControllableItem)]

        if len(items) == 0 and self._layer_stack.hasCurrentItem():
            self.sendEvent(self._layer_stack.current_item, e)
            return super(InteractiveScene, self).mousePressEvent(e)

        for item in items:
            if item.idd == self._layer_stack.current_item_id:
                self.sendEvent(item, e)
                return super(InteractiveScene, self).mousePressEvent(e)

        item = self.itemAt(pos.x(), pos.y(), QTransform())
        if item in self._layer_stack:
            self._layer_stack.current_item = item

        return super(InteractiveScene, self).mousePressEvent(e)


    def reset(self):
        self._layer_stack.clear()
        self.clear()
        self.setBackgroundBrush(QBrush(Qt.white, Qt.SolidPattern))
        self.addLine(0, 0, 1000, 0, QPen(Qt.DashLine))
        self.addLine(0, 0, 0, 1000, QPen(Qt.DashLine))


class ControllableItem(QGraphicsItem):
    """ A controllable graphics item has handles

    :param model: must be a subclass of DataModels.Geometry
    :type model: data_model.Geometry
    :param color: fill color
    :type color: QColor
    :param parent: parent object, defaults to None
    :type parent: QWidget
    :param label: a label for this item
    :type label: str
    :param handle_size: size of the handls
    :type handle_size: int
    :param handle_color: color of the handles
    :type handle_color: QColor
    :param edge_color: color of the edges
    :type edge_color: QColor
    :param edge_width: width of the edges
    :type: float
    """
    # deleted = pyqtSignal(int, name='itemDeleted')
    HandlePositionHasChanged = 100

    def __init__(self, model, color=DEFAULT_COLOR, parent=None, label="", handle_size=4,
                 handle_color=DEFAULT_HANDLE_COLOR,
                 edge_color=DEFAULT_EDGE_COLOR, edge_width=DEFAULT_EDGE_WIDTH, draw_flag=bool(0),
                 drag_flag=bool(0)):

        super(ControllableItem, self).__init__(parent)
        # if not issubclass(model.__class__, Geometry):
        #     raise ValueError('Invalid model, need to be a subclass of Geometry')

        self._model = model
        self._model.changed.connect(self.modelChanged)

        self._controls = []
        self._handle_size = handle_size
        self._handle_color = handle_color
        self._color = color
        self._edge_color = edge_color

        # the bounding rectangle
        self._rect = QRectF(0, 0, 100, 100)
        self._idd = DEFAULT_IDMAN.next()
        self._edge_width = edge_width
        self._draw_flag  = draw_flag
        self._drag_flag  = drag_flag


        self.control_points = self.model.control_points

        self._label = QGraphicsTextItem(label, self)
        self._label.setPos(QPointF(self.rect.x(), self.rect.y()))
        self._label.setFont(QFont('', 40))

        self._updateRect()

    def itemChange(self, change, value):
        """tell the inner model to update itself with new control points, also notifies other Items sharing this model

        :param change:
        :param value:
        :return:
        """
        if change == self.HandlePositionHasChanged:
            self.model.control_points = self.control_points
            self.update()

        return super(ControllableItem, self).itemChange(change, value)

    def modelChanged(self, change=0):
        self.control_points = self.model.control_points
        # print('model changed')

    @property
    def drag_flag(self):
        """"""
        return self._drag_flag

    @drag_flag.setter
    def drag_flag(self,value):
        if type(value)==bool:
           self._drag_flag = value
        else:
           #break
           print('needs to be boolean')

    @property
    def draw_flag(self):
        return self._draw_flag

    @draw_flag.setter
    def draw_flag(self,value):
        if type(value)==bool:
           self._draw_flag = value
        else:
           #break
           print('needs to be boolean')

    @property
    def rect(self):
        return self._rect

    @rect.setter
    def rect(self, value):
        self._rect = value

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, value):
        if issubclass(value.__class__, Geometry):
            self._model = value
        else:
            raise(ValueError('Must be a subclass of Geometry'))

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        if isinstance(value, str):
            self._label = QGraphicsTextItem(value)
        else:
            raise ValueError('label must be a string')

    @property
    def edge_width(self):
        return self._edge_width

    @edge_width.setter
    def edge_width(self, value):
        self._edge_width = value

    @property
    def half_edge_width(self):
        return self.edge_width / 2.

    @property
    def idd(self):
        return self._idd

    @idd.setter
    def idd(self, value):
        self._idd = value

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        self._color = value
        self.update()

    @property
    def handle_color(self):
        return self._handle_color

    @handle_color.setter
    def handle_color(self, value):
        self._handle_color = value
        self.update()

    @property
    def handle_size(self):
        return self._handle_size

    @handle_size.setter
    def handle_size(self, value):
        self._handle_size = value
        self.update()

    @property
    def edge_color(self):
        return self._edge_color

    @edge_color.setter
    def edge_color(self, value):
        self._edge_color = value
        self.update()

    @property
    def controls(self):
        return self._controls

    @property
    def control_points(self):
        """
        :return: control points from self._controls
        """
        return np.array([[cp.x(), cp.y()] for cp in self._controls])

    @control_points.setter
    def control_points(self, points):
        for ctr in self._controls:
            self.scene().removeItem(ctr)
            del ctr

        self._controls = []
        for cp in points:
            self.addHandle(cp)

        self._updateRect()

    @abstractmethod
    def _paintMe(self, qp, option, widget):
        """Paint the main part of this widget, subclass should impl this

        :param qp:
        :param option:
        :param widget:
        :return:
        """

    @abstractmethod
    def _updateRect(self):
        """
        update the bounding box
        :return:
        """
    @abstractmethod
    def __reInit(self):
        """
        adjust bounding rect to
        :param rect:
        :return:
        """

    def _adjustEdge(self, rect):
        """
        adjust bounding rect to
        :param rect:
        :return:
        """
        return rect.adjusted(-self.half_edge_width, -self.half_edge_width, self.half_edge_width, self.half_edge_width)


    def addHandle(self, pos):
        control = HandleItem(_QP(pos), parent=self, color=self.handle_color, size = self.handle_size)
        self._controls.append(control)
        self.update()
#        return control

    def removeHandles(self, nPts):
        L = len(self._controls)
        if L-nPts>2:
           control = self.control_points[0:nPts-1,:]
        else:
           control = self.control_points
        self.control_points = control
        #return control

    def hideHandles(self):
        for c in self._controls:
            c.setVisible(False)

    def paint(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.edge_color), self.edge_width))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        self._paintMe(qp, option, widget)
        for c in self._controls:
            c.paint(qp, option, widget)


        self.label.paint(qp, option, widget)
        if self.isSelected():
            qp.setPen(QPen(QBrush(self.color), self.edge_width, Qt.DotLine))
            qp.drawRect(self.boundingRect())

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def moveBy(self, dx, dy):
        control = self.control_points
        L = control.shape[0]
        for k in range(0,L):
            control[k,:] = control[k,:]+[dx,dy]
        self.control_points = control
        self.update()

    def moveTo(self,posx,posy):
        control = self.control_points
        L = control.shape[0]
        accum = [0,0]
        for k in range(0,L):
            control[k,:] = np.array([posx,posy]) + accum
            accum = accum + control[k,:]
        self.control_points = control
        self.update()



    def scaleBy(self, sx, sy):
        for control in self.controls:
            control.setPos(control.x() * sx, control.y() * sy)

    # def __reInit(self,posx,posy,horGap,vertGap):
    #     y = np.array([[posx,posy], [posx+horGap,posy+vertGap ]])
    #     self.control_points = y
    #
    # def mousePressEvent(self, e):
    #     if e.button() == 1 and e.modifiers() != Qt.ControlModifier and self._draw_flag == True:
    #         self.model.addControlPoints(_NP(e.scenePos())[None, ...])
    #         self.update()
    #     if e.button() == 1 and self._drag_flag == True:
    #         dx = _NP(e.scenePos())[0]-self.model.control_points[0,0]
    #         dy = _NP(e.scenePos())[1]-self.model.control_points[0,1]
    #         self.moveBy(dx, dy)
    #         #self.model._shiftControlPts(dx,dy)
    #     self.update()




class LayerStack(object):
    MAX_N_ITEMS_PER_LAYER = 1000

    def __init__(self):
        self.clear()

    def __contains__(self, item):
        try:
            re = self.itemById(item.idd)
        except: # removed ValueError
            return False

        return True

    @property
    def current_item_id(self):
        return self._current_item_id

    @current_item_id.setter
    def current_item_id(self, idd):
        if self.itemById(idd) in self:
            self._current_layer_id = self.layerByItemId(idd)
            self._current_item_id = idd
        else:
            raise ValueError('item is not managed by this stack')

    @property
    def current_item(self):
        return self.itemById(self.current_item_id)

    @current_item.setter
    def current_item(self, item):
        self.current_item_id = item.idd
        self.current_layer_id = self.layerByItemId(item.idd).idd

    @property
    def current_layer_id(self):
        return self._current_layer_id

    @current_layer_id.setter
    def current_layer_id(self, layer_id):
        if self.layerById(layer_id) in self._layers:
            self._current_layer_id = layer_id
            self._current_item_id = self.layerById(layer_id)[1].items[-1].idd

    @property
    def current_layer(self):
        return self.layerById(self.current_layer_id)[1]

    def itemById(self, item_id):
        for lx, l in enumerate(self._layers):
            for item in l.items:
                if item.idd == item_id:
                    return item

        raise ValueError('item not found!')

    def layerByItemId(self, item_id):
        item = self.itemById(item_id)
        if item.parentItem() is not None:
            return item.parentItem().idd

    def layerById(self, layer_id):
        for lx, l in enumerate(self._layers):
            if l.idd == layer_id:
                return lx, l

        raise ValueError('layer not found!')

    def layerIndexById(self, layer_id):
        lx, l = self.layerById(layer_id)
        return lx

    def hasCurrentItem(self):
        return self.current_item_id > 0

    def push(self, layer):
        next_key = len(self._layers) + 1
        self._layers[next_key] = layer

    def pop(self):
        if len(self._layers) > 0:
            return self._layers[ len(self._layers) - 1]
        else:
            raise IndexError('queue is empty')

    def addItem(self, item, layer_id):
        """
        add an item to a layer, adjust the item's order accordingly
        :param item:
        :param layer_id:
        :return:
        """
        lx, l = self.layerById(layer_id)
        l.addItem(item)

    def addItemToCurrentLayer(self, item):
        """
        add an item to the current layer
        :param item:
        :return:
        """
        self.current_layer.addItem(item)
        self.current_item_id = item.idd

    def swap(self, item_id1, item_id2):
        lx1, l1 = self.layerById(item_id1)
        lx2, l2 = self.layerById(item_id2)
        if l1 is not None and l2 is not None:
            self._layers[lx1] = l2
            self._layers[lx2] = l1

    def moveUp(self, item_id):
        lx, l = self.layerById(item_id)
        if lx + 1 < len(self._layers):
            self.swap(item_id, self._layers[lx + 1])

    def moveDown(self, item_id):
        lx, l = self.layerById(item_id)
        if lx - 1 > 0:
            self.swap(item_id, self._layers[lx - 1].idd)

    def moveToTop(self, item_id):
        self.swap(item_id, self._layers[len(self._layers) - 1].idd)

    def moveToBottom(self, item_id):
        self.swap(item_id, self._layers[0].idd)

    def updateZValue(self):
        """
        update Z values of each item according to item order in each layer
        :return:
        """
        for lx, layer in enumerate(self._layers):
            layer.setZValue(lx * self.MAX_N_ITEMS_PER_LAYER)
            for ix, item in enumerate(layer.items):
                zval = lx * self.MAX_N_ITEMS_PER_LAYER + ix + 1
                item.setZValue(zval)

    def clear(self):
        """
        empty current stack
        :return:
        """
        self._layers = [LayerItem(self, 'default', None)]
        self._current_layer_id = self._layers[0].idd
        self._current_item_id = -1


class LayerItem(QGraphicsItem):
    """"""
    def __init__(self, layer_stack, label, parent=None):
        super(LayerItem, self).__init__(parent=parent)
        self._label = label
        self._idd = DEFAULT_IDMAN.next()
        self._layer_stack = layer_stack
        # self._order = layer_stack.push(self)
        self._items = []

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, value):
        assert(isinstance(value, str))
        self._label = value

    @property
    def idd(self):
        return self._idd

    @property
    def items(self):
        return self._items

    def addItem(self, item):
        assert(len(self.items) < self._layer_stack.MAX_N_ITEMS_PER_LAYER)
        self._items.append(item)
        item.setParentItem(self)
        self.update()
        self._layer_stack.updateZValue()


class GroupItem(ControllableItem):
    """"""
    def __init__(self, items, **kwargs):
        model = Group([item.model for item in items])
        super(GroupItem, self).__init__(model, **kwargs)
        for item in items:
            item.setParentItem(self)

    def mousePressEvent(self, e):
        for ch in self.childItems():
            self.scene().sendEvent(ch, e)

    def _updateRect(self):
        x1, y1, x2, y2 = [], [], [], []
        for item in self.childItems():
            x1.append(item.boundingRect().x())
            y1.append(item.boundingRect().y())
            x2.append(item.boundingRect().right())
            y2.append(item.boundingRect().bottom())
        if len(x1) > 0:
            self.rect = QRectF(min(x1), min(y1), max(x2) - min(x1), max(y2) - min(y1))
        else:
            self.rect = QRectF(self.x(), self.y(), 100, 100)

    def _paintMe(self, painter, option, widget=None):
        for child in self.childItems():
            child._paintMe(painter, option, widget)

    def addItem(self, item):
        item.setParentItem(self)
        if self.scene() is not None:
            self.scene().activeSubItem = item
        return item

    # def setZValue(self, p_float):
    #     for child in self.childItems():
    #         child.setZValue(p_float)
    #
    #     super(GroupItem, self).setZValue(p_float)

    # @property
    # def control_points(self):
    #     points = []
    #     for child in self.childItems():
    #         points.append(child.control_points)
    #
    #     return points

    # def toPolies(self):
    #     points = []
    #     for child in self.childItems():
    #         points.append(child.toPolies())
    #
    #     return points


class PolylineItem(ControllableItem):
    """Controllable graphics item used to annotate bones and free form areas

    :param model: data model to be used
    :type model: data_models.PolyLine
    :param kwargs: additional parameters
    :type kwargs: dict
    """
    def __init__(self,model,**kwargs):

        super(PolylineItem,self).__init__(model,**kwargs)
        self._drag_flag = False
        self._draw_flag = True
    # def __init__(self, points, **kwargs):
    #     model = Polyline(points)
    #     super(PolylineItem, self).__init__(model, **kwargs)

    def _paintMe(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.edge_color), self._edge_width))
        qp.drawPolyline(*[c.pos() for c in self.controls])

    def _updateRect(self):
        pos = self.model.control_points
        r   = self.handle_size
        if len(pos) > 0:
            xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
            self.rect = self._adjustEdge(QRectF(xmin-r, ymin-r, xmax - xmin+r, ymax - ymin+r))

    def boundingRect(self):
        self._updateRect()
        return self.rect
    #"""
    def mousePressEvent(self, e):
        """Defines the behaviour of polyline.
        1. Clicking while holding control points while _drag_flag is set to true
        shifst the polylines
        2. Clicking inside the bounding rect adds a control points
        3. Holding ctr allows one to drag a control point

        :param e: mouse event
        :type e: QEvent
        :return: None
        :rtype: None
        """
        if e.button() == 1 and e.modifiers() != Qt.ControlModifier and self._draw_flag == True:
            self.model.addControlPoints(_NP(e.scenePos())[None, ...])
            self.update()
        if e.button() == 1 and self._drag_flag == True:
            ctrl = self.model.control_points
            dx = _NP(e.scenePos())[0]-ctrl[0,0]
            dy = _NP(e.scenePos())[1]-ctrl[0,1]
            #self.moveBy(dx, dy)
            #self.moveTo(_NP(e.scenePos())[0],_NP(e.scenePos())[1])
            self.model._shiftControlPts(dx,dy)
            self.update()


    def measure_area(self):
        """ measures the bounding area of the polyline. Need to re-implement

        :return: area
        :rtype: float
        """

        coordinates = self.model.control_points
        #coordinates = np.concatenate((coordinates,coordinates[0:1,:]),axis=1)
        x = np.arange(0, 1, 0.001)
        y = np.sqrt(1 - x ** 2)
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))


    def measure_circumference(self):
        """measures the perimeter of the polyline

        :return: perimeter
        :rtype: float
        """
        #todo: check if thi does \sum sqrt(dx_i^2+dy_i^2)
        coordinates = self.model.control_points
        sqdiff      = np.sqrt(np.sum(np.square(coordinates - np.roll(coordinates,shift=1,axis=0)),axis=1))
        dist        = np.sum(sqdiff)
        return dist

    def clear_coordinates(self):
        """"""
        self.polyline_annotate_item = None

class PointsItem(ControllableItem):
    """"""
    def _paintMe(self, qp, option, widget=None):
        qp.setPen(QPen(QBrush(self.edge_color), 5))
        #qp.drawPolyline(*[c.pos() for c in self.controls])
        qp.drawPoints(*[c.pos() for c in self.controls])

    def _updateRect(self):
        pos = self.model.control_points
        if len(pos) > 0:
            xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
            self.rect = self._adjustEdge(QRectF(xmin, ymin, xmax - xmin, ymax - ymin))

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() != Qt.ControlModifier and self._draw_flag == True:
            self.model.addControlPoints(_NP(e.scenePos())[None, ...])
            self.update()
        if e.button() == 1 and self._drag_flag == True:
            ctrl = self.model.control_points
            dx = _NP(e.scenePos())[0]-ctrl[0,0]
            dy = _NP(e.scenePos())[1]-ctrl[0,1]
            #self.moveBy(dx, dy)
            #self.moveTo(_NP(e.scenePos())[0],_NP(e.scenePos())[1])
            self.model._shiftControlPts(dx,dy)
            self.update()            # self.addHandle(_NP(e.scenePos()))


class Ellipse(QtWidgets.QGraphicsEllipseItem):
    """"""
    def __init__(self):
        super(Ellipse,self).__init__()
        self.size = 3
        self.color = DEFAULT_COLOR
        self.idd = DEFAULT_IDMAN.next()

    def boundingRect(self):
        size = self.size
        return self.rect.adjusted(-size,-size,0,0)

    def paint(self,painter,option,widget=None):
        qp = painter
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        # size = self.size
        qp.drawEllipse(self.boundingRect())



class BaseRectItem(ControllableItem):
    """"""
    def __init__(self, x, y, width, height, **kwargs):
        """
        :param x: top-left corner
        :param y: bottom-right corner
        :param width:
        :param height:
        :param kwargs: see @ControllableItem
        """
        model = Rect(x, y, width, height)

        super(BaseRectItem, self).__init__(model=model, **kwargs)
        self._drag_flag = False

    def _updateRect(self):
        self.rect = self._adjustEdge(QRectF(self.model.x, self.model.y, self.model.width, self.model.height))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawRect(self.model.x, self.model.y, self.model.width, self.model.height)


    def mousePressEvent(self, e):
        if e.button() == 1 and self._drag_flag == True:
            ctrl = self.model.control_points
            dx = _NP(e.scenePos())[0]-self.model.x#ctrl[0,0]
            dy = _NP(e.scenePos())[1]-self.model.y#ctrl[0,1]
            #self.moveBy(dx, dy)
            #self.moveTo(_NP(e.scenePos())[0],_NP(e.scenePos())[1])
            self.model._shiftControlPts(dx,dy)
            self.update()            # self.addHandle(_NP(e.scenePos()))



class RectItem(ControllableItem):
    """Controllable item used to place patches on images. Used for joint annotation

    :param x: top-left corner
    :type x: float
    :param y: bottom-right corner
    :type y: float
    :param width:
    :type width: float
    :param height:
    :type height: float
    :param angle: angle of rotation, defaults to zero
    :type angle: float
    :param kwargs: see @ControllableItem
    """
    def __init__(self, x, y, width, height,angle=0, **kwargs):
        """

        """

        model = RotateRect(x, y, width, height,angle=angle)


        super(RectItem, self).__init__(model=model, **kwargs)
        self._drag_flag = False

        DraggableRectItem = make_GraphicsItem_draggable(QtWidgets.QGraphicsEllipseItem)
        #DraggableRectItem = make_GraphicsItem_draggable(QtWidgets.QGraphicsEllipseItem)
        self.rotate_handle = DraggableRectItem()
        self.rotate_handle.setBrush(QBrush(QtCore.Qt.red, style = QtCore.Qt.SolidPattern))
        #self.rotate_handle._pa
        self.rotate_handle.signaller.positionChanged.connect(self.rotate_item)
        self.rotate_handle.setRect(self.model.x-10, self.model.y-10, 10, 10)
        self.setTransformOriginPoint(self.model.x+self.model.width/2,self.model.y+self.model.height/2)
        #self.rotate_handle.
        #scene.addItem(handle_item)


    def _paintMe(self, painter, option, widget=None):
        qp = painter
        polygon = self.model.bounding_polygon
        #qp.drawRect(self.model.x, self.model.y, self.model.width, self.model.height)
        qp.drawPolygon(polygon)

    def rotate_item(self,position):
        center = np.mean(self.control_points, axis=0)
        self.setTransformOriginPoint(center[0],center[1])
        item_position = self.transformOriginPoint()
        angle = math.atan2(item_position.y() - position.y(),
                           item_position.x() - position.x()) / math.pi * 180 - 45  # -45 because handle item is at upper left border, adjust to your needs
        angle *=0.8
        print('@computed angle={:.3}'.format(angle))
        #self.setRotation(180*angle/np.pi)

        self.model.angle=angle
        self.model.update()
        self.update()

        print('model angle =')
        print(self.model.angle)
        print('modelx=')
        print(self.model.x)
        print('control points =')
        print(self.control_points)


    def _updateRect(self):
        self.rect = self._adjustEdge(QRectF(self.model.x, self.model.y, self.model.width, self.model.height))

    # def _paintMe(self, painter, option, widget=None):
    #     qp = painter
    #     qp.drawRect(self.model.x, self.model.y, self.model.width, self.model.height)


    def mousePressEvent(self, e):
        if e.button() == 1 and self._drag_flag == True:
            ctrl = self.model.control_points
            dx = _NP(e.scenePos())[0]-self.model.x#ctrl[0,0]
            dy = _NP(e.scenePos())[1]-self.model.y#ctrl[0,1]
            #self.moveBy(dx, dy)
            #self.moveTo(_NP(e.scenePos())[0],_NP(e.scenePos())[1])
            self.model._shiftControlPts(dx,dy)
            self.setTransformOriginPoint(self.model.x + self.model.width / 2, self.model.y + self.model.height / 2)
            self.update()            # self.addHandle(_NP(e.scenePos()))


class CircleItem(ControllableItem):
    """"""
    # def __init__(self, x, y, r, **kwargs):
    #     model = Circle(x, y, r)
    #     super(CircleItem, self).__init__(model=model, **kwargs)
    #     self._updateRect()

    def _updateRect(self):
        center = self.model.center
        r = self.model.r
        self.rect = self._adjustEdge(QRectF(center[0] - r, center[1] - r, r * 2, r * 2))

    def _paintMe(self, painter, option, widget=None):
        qp = painter
        qp.drawEllipse(_QP(self.model.center), self.model.r, self.model.r)


class RingItem(ControllableItem):
    """"""
    # def __init__(self, x, y, inner_r, outer_r, **kwargs):
    #     model = Ring(x, y, inner_r, outer_r)
    #     super(RingItem, self).__init__(model=model, **kwargs)

    def _updateRect(self):
        center = self.model.center
        r = self.model.outer_r
        self.rect = self._adjustEdge(QRectF(center[0] - r, center[1] - r, r * 2, r * 2))

    def _paintMe(self, qp, option, widget=None):
        qp.drawEllipse(_QP(self.model.center), self.model.outer_r, self.model.outer_r)
        qp.drawEllipse(_QP(self.model.center), self.model.inner_r, self.model.inner_r)


class SplineItem(ControllableItem):
    """"""
    # def __init__(self, points, **kwargs):
    #     model = Spline(points)
    #     super(SplineItem, self).__init__(model, **kwargs)

    # def __init__(self, model, **kwargs):
    #     super(SplineItem, self).__init__(model, **kwargs)

    def _paintMe(self, qp, option, widget=None):
        path = QPainterPath(_QP(self.model.control_points[0]))
        ann_path = QPainterPath()
        cur_point = 0
        while cur_point < len(self.model.control_points) - 1:
            path.cubicTo(_QP(self.model.control_points[cur_point + 1]),
                         _QP(self.model.control_points[cur_point + 2]),
                         _QP(self.model.control_points[cur_point + 3]))

            ann_path.moveTo(_QP(self.model.control_points[cur_point + 0]))
            ann_path.lineTo(_QP(self.model.control_points[cur_point + 1]))
            ann_path.moveTo(_QP(self.model.control_points[cur_point + 3]))
            ann_path.lineTo(_QP(self.model.control_points[cur_point + 2]))

            cur_point += 3

        qp.drawPath(path)
        qp.setPen(QPen(DEFAULT_ANN_EDGE_STYLE))
        qp.drawPath(ann_path)

    def __len__(self):
        return len(self.controls)

    def _updateRect(self):
        pos = self.model.toPolies()[0]
        xmax, xmin, ymax, ymin = pos[:, 0].max(), pos[:, 0].min(), pos[:, 1].max(), pos[:, 1].min()
        self.rect = self._adjustEdge(QRectF(xmin, ymin, xmax - xmin, ymax - ymin))

    def boundingRect(self):
        self._updateRect()
        return self.rect

    def mousePressEvent(self, e):
        if e.button() == 1 and e.modifiers() == Qt.ControlModifier:
            self.model.addControlPoints(_NP(e.scenePos())[None, :])




class SRectItem(ControllableItem):
    """"""
    # def __init__(self, x, y, inner_a, outer_a, **kwargs):
    #     model = Ring(x, y, inner_a, outer_a)
    #     super(SRectItem, self).__init__(model=model, **kwargs)

    def _updateRect(self):
        center = self.model.center
        r1 = self.model.outer_r
        self.rect = self._adjustEdge(QRectF(center[0] - r1, center[1] - r1, r1 * 2, r1 * 2))

    def _paintMe(self, qp, option, widget=None):
        x, y = self.model.center[0] - self.model.inner_r, self.model.center[1] - self.model.inner_r
        qp.drawRect(x, y, self.model.inner_r * 2, self.model.inner_r * 2)

        x, y = self.model.center[0] - self.model.outer_r, self.model.center[1] - self.model.outer_r
        qp.drawRect(x, y, self.model.outer_r * 2, self.model.outer_r * 2)



class HandleItem(QGraphicsItem):
    """"""
    def __init__(self, position, size=3, parent=None, color=Qt.green):
        super(HandleItem, self).__init__(parent)
        self.setPos(position)
        self.size = size
        self.color = color
        self.idd = DEFAULT_IDMAN.next()
        # self.setZValue(10)
        self.setFlags(self.flags() |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges |
                      QGraphicsItem.ItemIsFocusable)
        self.rect = QRectF(0, 0, size, size)

    def boundingRect(self):
        size = self.size
        return self.rect.adjusted(-size,-size,0,0)

    def paint(self, painter, option, widget=None):
        qp = painter
        qp.setPen(QtGui.QColor(168, 34, 3))
        qp.setBrush(QBrush(self.color, Qt.SolidPattern))
        # size = self.size
        qp.drawEllipse(self.boundingRect())

    def points(self):
        return [[self.x(), self.y()]]

    def mousePressEvent(self, e):
        pass
        # if e.button() == 1:
        #     self.parentItem().main.bringToFront(self.parentItem().idd)
        # if e.button() == 2:
        #     self.parentItem().main.remove(self)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            self.parentItem().itemChange(ControllableItem.HandlePositionHasChanged, value)
        return super(HandleItem, self).itemChange(change, value)

    def setSize(self, size):
        self.prepareGeometryChange()
        self.size = size
        self.rect = QRectF(0,0,size,size)

    def setColor(self, color):
        self.color = color
        self.update()



"""
class graphicsScene(QtGui.QGraphicsScene):
    def __init__ (self, parent=None):
        super(graphicsScene, self).__init__ (parent)

    
"""


class DraggableGraphicsItemSignaller(QtCore.QObject):
    """"""

    positionChanged = QtCore.pyqtSignal(QtCore.QPointF)

    def __init__(self):
        super().__init__()

def make_GraphicsItem_draggable(parent):
    """"""

    class DraggableGraphicsItem(parent):

        def __init__(self, *args, **kwargs):
            """
            By default QGraphicsItems are not movable and also do not emit signals when the position is changed for
            performance reasons. We need to turn this on.
            """
            parent.__init__(self, *args, **kwargs)
            self.parent = parent
            self.setFlags(QtWidgets.QGraphicsItem.ItemIsMovable | QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges)
            self.signaller = DraggableGraphicsItemSignaller()

        def itemChange(self, change, value):
            if change == QtWidgets.QGraphicsItem.ItemPositionChange:
                self.signaller.positionChanged.emit(value)

            return parent.itemChange(self, change, value)

    return DraggableGraphicsItem

# def rotate_item(position):
#     item_position = item.transformOriginPoint()
#     angle = math.atan2(item_position.y() - position.y(), item_position.x() - position.x()) / math.pi * 180 - 45 # -45 because handle item is at upper left border, adjust to your needs
#     print(angle)
#     item.setRotation(angle)



#rectangle = RectItem(x=0,y=0,width=10,height=10)
def main():
    """"""
    DraggableRectItem = make_GraphicsItem_draggable(QtWidgets.QGraphicsRectItem)

    app = QtWidgets.QApplication([])
    window = QtWidgets.QMainWindow()
    view = QtWidgets.QGraphicsView()
    scene = QGraphicsScene()
    # item = scene.addRect(0, 0, 100, 100)
    # item.setTransformOriginPoint(50, 50)

    item = RectItem(x=20,y=30,width=10,height=10)
    scene.addItem(item)
    scene.addItem(item.rotate_handle)

    #handle_item = DraggableRectItem()






    view.setScene(scene)
    layout = QtWidgets.QVBoxLayout()
    layout.addWidget(view)
    widget = QtWidgets.QWidget()
    widget.setLayout(layout)
    window.setCentralWidget(widget)
    # layout.addWidget(QPushButton('3'))
    window.show()
    app.exec_()

if __name__=='__main__':
    main()


