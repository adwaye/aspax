"""
Created on Tue Sep  8 07:32:13 2015

@author classes: phanquochuy

Module that contains underlying data models for the graphics items used as annotation landmarks. The only two that
are used are RotateRect and Polyline.
"""
from abc import abstractmethod
from PyQt5.QtCore import pyqtSignal, QObject
from PyQt5.Qt import QPolygonF, QPointF
# from skimage import draw
import json
import numpy as np


class GeometryFactory(object):
    """"""
    def __init__(self):
        pass

    def createGeometry(self, geo_type, control_points):
        if geo_type == "Polyline":
            obj = Polyline(points=control_points)
        elif geo_type == "Rect":
            obj = Rect(0, 0, 0, 0)


class Geometry(QObject):
    """Base class for data models

    """
    changed = pyqtSignal(int)
    ControlPointPositionHasChanged = 0

    def __init__(self):
        super(Geometry, self).__init__()

    def _toDict(self):
        return {
            "type": "Feature",
            "geometry": {
                "type": type(self).__name__,
                "coordinates": self.control_points.tolist()
            },
            "properties": {
                "label": ""
            }
        }

    def _fromDict(self, d):
        pass

    def toString(self):
        """convert this object to a string for serialization

        :return: json serialised object
        :rtype: str
        """
        d = self._toDict()
        return json.dumps(d)

    def fromString(self, string):
        """parse a string and return a Geometry object

        :return: None
        :rtype: None
        """
        d = json.loads(string)
        self.control_points = np.array(d['geometry']['coordinates'])

    @abstractmethod
    def toPolies(self):
        """Convert this geometry to a set of polygons

        :return: None
        :rtype: None
        """

    @property
    @abstractmethod
    def control_points(self):
        """"""

    @control_points.setter
    @abstractmethod
    def control_points(self, points):
        """set control points, remember to call self.update

        :param points:
        :return:
        """

    def update(self, change=0):
        """notify all the listeners that the geometry has changed

        :param change: 0 = default change
        :type change: int
        :return: None
        :rtype: None
        """
        self.changed.emit(change)


class Polyline(Geometry):
    """Data model for a polyline

    :param points: nodes of the polyline. Need to have shape [N,2]
    :type points: np.array or list
    """
    def __init__(self, points=[[0, 0]] * 2):

        self._points = np.atleast_2d(points)
        # if len(self._points.shape) != 2:
        #     raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Polyline, self).__init__()

    def toPolies(self):

        return self._points[None, ...]

    @property
    def control_points(self):
        """Returns the list of points making up the polyline

        :return: list of nodes in the polyline
        :rtype: array-like
        """
        return self._points

    @control_points.setter
    def control_points(self, points):
        self._points = points

    def addControlPoints(self, points):
        self.control_points = np.concatenate([self.control_points, points])
        self.update()
        
    def _shiftControlPts(self,dx,dy):
        """Translates the control points

        :param dx: x translation
        :type dx: float
        :param dy: y translation
        :type dy: float
        :return: None
        :rtype: None
        """

        control = self.control_points
        L = control.shape[0]
        for k in range(0,L):
            control[k,:] = control[k,:]+[dx,dy]
        self.control_points = control
        self.update()

#class Points(Geometry) todo: maybe add a classs to model data points



class Rect(Geometry):
    """Rectangle class

    :param x: x coordinate of top corner
    :type x: float
    :param y: y coordinate of top corner
    :type y: float
    :param width: width of rectangle
    :type width: float
    :param height: height of rectangle
    :type height: float
    """

    def __init__(self, x=0, y=0, width=0, height=0):

        self._x, self._y, self._width, self._height = x, y, width, height
        super(Rect, self).__init__()

    @property
    def x(self): return self._x

    @x.setter
    def x(self, value): self._x = value

    @property
    def y(self): return self._y

    @y.setter
    def y(self, value): self._y = value

    @property
    def width(self): return self._width

    @width.setter
    def width(self, value): self._width = value

    @property
    def height(self):
        """

        :return: height of the rectangle
        :rtype: float
        """
        return self._height

    @height.setter
    def height(self, value): self._height = value

    @property
    def control_points(self):
        return np.array([[self._x, self._y], [self._x + self._width, self._y + self._height]])

    @control_points.setter
    def control_points(self, points):
        if points.shape == (2, 2):
            self._x, self._y, self._width, self._height = \
                points[0][0], points[0][1], abs(points[1][0] - points[0][0]), abs(points[1][1] - points[0][1])

    @property
    def bounding_points(self):
        """returns the bounding box of the rectangle as a list of coordinates


        """
        x1 = self._x
        y1 = self._y
        x2 = self._x+self._width
        y2 =self._y
        x3 = self._x+self._width
        y3 =self._y+self._height
        x4 = self._x
        y4 =self._y+self._height
        theta = 0



        coords   = np.array([[x1, y1], [x2, y2],[x3,y3],[x4,y4]])
        # mean_pos = np.mean(coords,axis=0)
        mean_pos = np.array([self._x + self._width / 2, self._y + self._height / 2])
        coords = coords - mean_pos
        rotation_matrix = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        coords_rot = (rotation_matrix@coords.transpose()).transpose() + mean_pos
        return coords_rot

    def toPolies(self):
        return np.array([])

    def _shiftControlPts(self,dx,dy):
        """Translates the rectangle

        :param dx: x translation
        :type dx: float
        :param dy: y translation
        :type dy: float
        :return: None
        :rtype: None
        """
        control = self.control_points
        self.x += dx
        self.y += dy


        self.update()



class RotateRect(Rect):
    """Extension of Rect, that allows it to be rotated with an angle theta

    :param x: x coordinate of top corner
    :type x: float
    :param y: y coordinate of top corner
    :type y: float
    :param width: width of rectangle
    :type width: float
    :param height: height of rectangle
    :type height: float
    :param angle: angle of rotation
    :type angle: float
    """
    def __init__(self,x=0, y=0, width=0, height=0,angle=0):

        self._angle = angle
        super(RotateRect,self).__init__(x=x,y=y,height=height,width=width)


    @property
    def angle(self):
        """Angle of rotation

        :return: angle
        :rtype:  float
        """

        return self._angle

    @angle.setter
    def angle(self,theta): self._angle = theta


    @property
    def control_points(self):
        """returns the diagonal coordinates of the rotated rectangle
        
        :return: 
        :rtype: 
        """

        x1 = self._x
        y1 = self._y
        x2 = self._x+self._width
        y2 =self._y+self._height
        theta = self.angle



        coords   = np.array([[x1, y1], [x2, y2]])
        # mean_pos = np.mean(coords,axis=0)
        mean_pos = np.array([self._x + self._width / 2, self._y + self._height / 2])
        coords = coords - mean_pos
        rotation_matrix = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        coords_rot = (rotation_matrix@coords.transpose()).transpose() + mean_pos
        return coords_rot

    @control_points.setter
    def control_points(self, points):


        if points.shape == (2, 2):
            theta = -self.angle
            coords = points.copy()
            mean_pos = np.mean(coords,axis=0)
            #mean_pos = np.array([self._x + self._width / 2, self._y + self._height / 2])
            coords = coords - mean_pos
            rotation_matrix = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
            coords_rot = (rotation_matrix @ coords.transpose()).transpose() + mean_pos
            self._x, self._y, self._width, self._height = \
                coords_rot[0][0], coords_rot[0][1], abs(coords_rot[1][0] - coords_rot[0][0]), abs(coords_rot[1][1] - coords_rot[0][1])

    @property
    def bounding_polygon(self):
        """return the bounding points of the rectangle as a polygon.
        rotation

        :return: polygon
        :rtype: PyQt5.Qt.QPolygonF
        """


        x1 = self._x
        y1 = self._y
        x2 = self._x+self._width
        y2 =self._y
        x3 = self._x+self._width
        y3 =self._y+self._height
        x4 = self._x
        y4 =self._y+self._height
        theta = self.angle



        coords   = np.array([[x1, y1], [x2, y2],[x3,y3],[x4,y4]])
        # mean_pos = np.mean(coords,axis=0)
        mean_pos = np.array([self._x + self._width / 2, self._y + self._height / 2])
        coords = coords - mean_pos
        rotation_matrix = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        coords_rot = (rotation_matrix@coords.transpose()).transpose() + mean_pos
        polygon = QPolygonF()#todo: look up the proper syntax
        for i in range(4):
            polygon.append(QPointF(coords_rot[i][0], coords_rot[i][1]))


        return polygon

    @property
    def bounding_points(self):
        """Returns the bounding points of the rectangle. The control_points are rotated using the angle of rotation

        :return: coords_rot shape (4,2)
        :rtype: np.array
        """
        x1 = self._x
        y1 = self._y
        x2 = self._x+self._width
        y2 =self._y
        x3 = self._x+self._width
        y3 =self._y+self._height
        x4 = self._x
        y4 =self._y+self._height
        theta = self.angle



        coords   = np.array([[x1, y1], [x2, y2],[x3,y3],[x4,y4]])
        # mean_pos = np.mean(coords,axis=0)
        mean_pos = np.array([self._x + self._width / 2, self._y + self._height / 2])
        coords = coords - mean_pos
        rotation_matrix = np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
        coords_rot = (rotation_matrix@coords.transpose()).transpose() + mean_pos
        return coords_rot


    def rotate(self,theta):
        pass







class Box(Rect):
    """"""
    def __init__(self, a=0, x=0, y=0):
        super(Box, self).__init__(x, y, width=a, height=a)


class Circle(Geometry):
    """"""
    def __init__(self, x=0, y=0, r=0):
        self.x, self.y, self.r = x, y, r
        super(Circle, self).__init__()

    @property
    def center(self):
        return np.array([self.x, self.y])

    @center.setter
    def center(self, value):
        self.x, self.y = value[0], value[1]

    @property
    def control_points(self):
        return np.array([[self.x, self.y], [self.x + self.r, self.y]])

    @control_points.setter
    def control_points(self, points):
        if len(points) >= 2:
            self.x, self.y = points[0][0], points[0][1]
            self.r = np.linalg.norm(points[0] - points[1])
            # self.update()

    def toPolies(self):
        return np.array([])


class Ring(Geometry):
    """"""
    def __init__(self, x=0, y=0, inner_r=0, outer_r=0):
        self.x, self.y, self.inner_r, self.outer_r = x, y, inner_r, outer_r
        super(Ring, self).__init__()

    @property
    def center(self):
        return np.array([self.x, self.y])

    @center.setter
    def center(self, value):
        self.x, self.y = value[0], value[1]

    @property
    def control_points(self):
        return np.array([[self.x, self.y], [self.x + self.inner_r, self.y], [self.x + self.outer_r, self.y]])

    @control_points.setter
    def control_points(self, points):
        if len(points) == 3:
            self.x, self.y = points[0][0], points[0][1]
            self.inner_r = np.linalg.norm(points[0] - points[1])
            self.outer_r = np.linalg.norm(points[0] - points[2])

    def toPolies(self):
        return np.array([])


class Point(Geometry):
    """"""
    def __init__(self, x=0, y=0):
        self._x = x
        self._y = y
        super(Point, self).__init__()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    def toPolies(self):
        return np.array([[[self._x, self._y]]])

    @property
    def control_points(self):
        return np.array([self.x, self.y])

    @control_points.setter
    def control_points(self, point):
        self.x = point[0]
        self.y = point[1]


class Line(Polyline):
    """"""
    def __init__(self, x0=0, y0=0, x1=100, y1=100):
        super(Line, self).__init__([[x0, y0], [x1, y1]])


class Spline(Geometry):
    """"""
    def __init__(self, points=[[0, 0]] * 4):
        self._points = np.array(points)
        if len(self._points.shape) != 2:
            raise ValueError('invalid points')

        if self._points.shape[1] != 2:
            raise ValueError('only 2D points are supported')

        super(Spline, self).__init__()

    def toPolies(self):
        # TODO: implement this
        return self._points[None, ...]

    @property
    def control_points(self):
        return self._points

    @control_points.setter
    def control_points(self, points):
        if len(points) >= 4:
            self._points = np.array(points)

    def addControlPoints(self, points):
        if len(points) == 1:
            cur_point = self.control_points[-1]
            end_point = points[0]
            diff = end_point - cur_point
            mid_point = diff / 2 + cur_point
            c_point1 = diff * np.array([1, -1]) + mid_point
            c_point2 = diff * np.array([-1, 1]) + mid_point
            self.control_points = np.concatenate([self.control_points, [c_point1, c_point2, end_point]])
        # elif len(points) == 3:
        self.update()


class Group(Geometry):
    """"""
    def __init__(self, geometries):
        """
        :param geometries: must be a list of Geometry
        """
        super(Group, self).__init__()
        self._geos = geometries

    @property
    def geos(self):
        return self._geos

    @geos.setter
    def geos(self, value):
        if not isinstance(value, list):
            raise ValueError('value must be a list')

        if sum([issubclass(v.__class__, Geometry) for v in value]) == len(value):
            self._geos = value
        else:
            raise ValueError('objects in the list must be Geometry')

    def toString(self):
        d = self._toDict()
        cps = []
        types = []
        for geo in self.geos:
            cps.append(geo.control_points.tolist())
            types.append(type(geo).__name__)

        d['geometry']['coordinates'] = cps
        d['geometry']['properties']['types'] = types
        return json.dumps(d)

    def fromString(self, text):
        # TODO: Under construction
        features = json.loads(text)
        geos = []
        for feature in features:
            tmp = json.dumps(feature)
            # geos.append(super())

    def toPolies(self):
        return [geo.toPolies() for geo in self.geometries]

    @property
    def control_points(self):
        return np.array([])


class MultiGeometry(Geometry):
    """"""
    # """
    # Abstract class for all multi-geometry
    # """
    def __init__(self, geos):
        self._geos = geos
        super(MultiGeometry, self).__init__()

    @property
    def geos(self):
        return self._geos

    def _toDict(self):
        d = super(MultiGeometry, self)._toDict()
        cps = []
        for geo in self.geos:
            cps.append(geo.control_points.tolist())
        d['geometry']['coordinates'] = cps
        return d

    def fromString(self, string):
        # TODO: under construction
        d = json.loads(string)
        pass

    @property
    def control_points(self):
        return np.vstack([geo.control_points for geo in self._geos])

    def toPolies(self):
        return np.vstack([geo.toPolies()[0] for geo in self._geos])


class MultiSpline(MultiGeometry):
    """"""
    def __init__(self, points=[[[0, 0]] * 4]):
        splines = []
        for ps in points:
            splines.append(Spline(ps))
        super(MultiSpline, self).__init__(splines)


class MultiPolyline(Group):
    """"""
    def __init__(self, points=[[[0, 0]] * 2]):
        polygons = []
        for ps in points:
            polygons.append(Spline(ps))
        super(MultiPolyline, self).__init__(polygons)


class AnnotationModel(object):
    """"""
    # """Model for Annotating Objects
    #
    # """
    __geos__ = {'MultiSpline': MultiSpline,
                "MultiPolyline": MultiPolyline,
                "Spline": Spline,
                "Polyline": Polyline}

    def __init__(self, regions):
        """
        :param regions: list of Geometries
        :param label:
        """
        self.regions = regions
        super(AnnotationModel, self).__init__()

    def _toDict(self):
        return {
            "type": "FeatureCollection",
            "features": [re._toDict() for re in self.regions]
        }

    def toString(self):
        return json.dumps(self._toDict())

    def fromString(self):
        pass

    def save(self, filename):
        with open(filename, 'w') as fp:
            json.dump(self._toDict(), fp)

    @staticmethod
    def load(filename):
        with open(filename, 'r') as fp:
            d = json.load(fp)
            regions = []
            for sub_d in d['features']:
                data = sub_d['geometry']['coordinates']
                regions.append(AnnotationModel.__geos__[sub_d['geometry']['type']](data))

        return AnnotationModel(regions)

    def toMasks(self, mode='auto', shape=None):
        pass
        """
        convert to a binary mask
        :param mode
        :type str
        :param shape
        :return:
        """
        # if mode == 'auto':
        #     polies = self.toPolies()
        #     points = np.vstack(polies)
        #     xmax, ymax = tuple(points.max(axis=0))
        #     xmin, ymin = tuple(points.min(axis=0))
        #     w, h = xmax - xmin, ymax - ymin
        #
        #     mask = np.zeros((ymax - ymin, xmax - xmin), dtype=np.uint8)
        #     for poly in polies:
        #         poly1 = poly - np.array([xmin, ymin])
        #         rr, cc = draw.polygon(poly1[:, 1], poly[:, 0], shape=(h, w))
        #         mask[rr, cc] = 1
        # elif isinstance(shape, tuple):
        #     mask = np.zeros(shape, dtype=np.uint8)
        #     polies = self.toPolies()
        #     for poly in polies:
        #         rr, cc = draw.polygon(poly[:, 1], poly[:, 0], shape=shape)
        #         mask[rr, cc] = 1
        # else:
        #     mask = None
        #
        # return mask

if __name__ == '__main__':
    # polygon = Polyline([[0, 0], [10, 10]])
    # spline = MultiSpline(np.array([[[0, 0], [100, 100], [0, 150], [50, 200]],
    #                                [[200, 200], [300, 300], [200, 350], [250, 400]]]))

    # am = AnnotationModel([spline, polygon])
    # print(am.toString())
    # am.save("tmp.json")

    am = AnnotationModel.load("tmp.json")
    polygon, spline = tuple(am.regions)

    print(polygon.toString())
