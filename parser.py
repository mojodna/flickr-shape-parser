"""
Parses and converts the Flickr Shapefiles Public Dataset, Version 1.0
http://code.flickr.com/blog/2009/05/21/flickr-shapefiles-public-dataset-10/
"""

import sys
from datetime import date
import osgeo.ogr, osgeo.osr
from osgeo import ogr, osr
import xml.sax
from xml.sax import SAXException
from xml.sax.handler import ContentHandler

class FlickrShapeParser(ContentHandler):
    def getLayer(self, name):
        # return self.layer

        layer = self.shp.GetLayerByName(name)

        if layer == None:
            layer = self.shp.CreateLayer(name, geom_type=ogr.wkbPolygon, srs=self.srs)
            layer.CreateField(ogr.FieldDefn("woe_id", ogr.OFTInteger))
            layer.CreateField(ogr.FieldDefn("place_id", ogr.OFTString))
            layer.CreateField(ogr.FieldDefn("place_type", ogr.OFTString))
            layer.CreateField(ogr.FieldDefn("label", ogr.OFTString))
            layer.CreateField(ogr.FieldDefn("alpha", ogr.OFTReal))
            layer.CreateField(ogr.FieldDefn("donuthole", ogr.OFTInteger))
            layer.CreateField(ogr.FieldDefn("points", ogr.OFTInteger))
            layer.CreateField(ogr.FieldDefn("edges", ogr.OFTInteger))
            layer.CreateField(ogr.FieldDefn("created", ogr.OFTDate))

        return layer

    def startDocument(self):
        self.stack = []

        self.srs = osr.SpatialReference()
        self.srs.ImportFromProj4('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

        driver = ogr.GetDriverByName('ESRI Shapefile')
        self.shp = driver.CreateDataSource('flickr.shp')
        # create a dummy layer in the base shapefile to keep it empty
        self.layer = self.shp.CreateLayer('Flickr Alpha Shapes', geom_type=ogr.wkbPolygon, srs=self.srs)
        self.layer.CreateField(ogr.FieldDefn("woe_id", ogr.OFTInteger))
        self.layer.CreateField(ogr.FieldDefn("place_id", ogr.OFTString))
        self.layer.CreateField(ogr.FieldDefn("place_type", ogr.OFTString))
        self.layer.CreateField(ogr.FieldDefn("label", ogr.OFTString))
        self.layer.CreateField(ogr.FieldDefn("alpha", ogr.OFTReal))
        self.layer.CreateField(ogr.FieldDefn("donuthole", ogr.OFTInteger))
        self.layer.CreateField(ogr.FieldDefn("points", ogr.OFTInteger))
        self.layer.CreateField(ogr.FieldDefn("edges", ogr.OFTInteger))
        self.layer.CreateField(ogr.FieldDefn("created", ogr.OFTDate))

    def endDocument(self):
        self.shp.Destroy()

    def startElement(self, name, attrs):
        self.stack.append((name, attrs.copy()))

        if name == "places":
            pass
        elif name == "place":
            self.place_type_id = int(attrs.getValue("place_type_id"))
            self.woe_id = int(attrs.getValue("woe_id"))
            self.place_id = attrs.getValue("place_id")
            self.place_type = attrs.getValue("place_type")
            self.label = attrs.getValue("label")

            print "%s (%s)" % (self.label.encode('utf-8'), self.woe_id)
        elif name == "shape":
            self.alpha = float(attrs.getValue("alpha"))
            self.is_donuthole = int(attrs.getValue("is_donuthole"))
            self.points = int(attrs.getValue("points"))
            self.edges = int(attrs.getValue("edges"))
            self.created = date.fromtimestamp(float(attrs.getValue("created")))
        elif name == "shapefile":
            self.url = attrs.getValue("url")
        elif name == "polylines":
            self.bbox = attrs.getValue("bbox")
            self.rings = []
        elif name == "polyline":
            self.current_ring = ""

    def endElement(self, name):
        (_, attrs) = self.stack.pop()

        if name == "places":
            pass
        if name == "place":
            self.place_type_id = None
            self.woe_id = None
            self.place_id = None
            self.place_type = None
            self.label = None
        elif name == "shape":
            self.alpha = None
            self.is_donuthole = None
            self.points = None
            self.edges = None
            self.created = None
        elif name == "shapefile":
            self.url = None
        elif name == "polylines":
            self.bbox = None
            
            wkt = "POLYGON ("
            for ring in self.rings:
                wkt += "(" + ring + ")"

            wkt += ")"

            poly = ogr.CreateGeometryFromWkt(wkt)

            # layer = self.getLayer(self.created.strftime("%B %Y"))
            layer = self.getLayer(str(self.created))

            feature = ogr.Feature(feature_def=layer.GetLayerDefn())
            feature.SetGeometryDirectly(poly)
            feature.SetField(feature.GetFieldIndex("woe_id"), self.woe_id)
            feature.SetField(feature.GetFieldIndex("place_id"), self.place_id)
            feature.SetField(feature.GetFieldIndex("place_type"), self.place_type)
            feature.SetField(feature.GetFieldIndex("label"), self.label.encode('utf-8'))
            feature.SetField(feature.GetFieldIndex("alpha"), self.alpha)
            feature.SetField(feature.GetFieldIndex("donuthole"), self.is_donuthole)
            feature.SetField(feature.GetFieldIndex("points"), self.points)
            feature.SetField(feature.GetFieldIndex("edges"), self.edges)
            feature.SetField(feature.GetFieldIndex("created"), self.created)

            layer.CreateFeature(feature)

            feature.Destroy()

            self.rings = None
        elif name == "polyline":
            # transform coordinates
            r = []
            for coords in self.current_ring.split(" "):
                (y, x) = coords.split(",")
                r.append(x + " " + y)

            self.rings.append(",".join(r))
            self.current_ring = ""
            
    def characters(self, content):
        (name, attrs) = self.stack[-1]
        if name == "polyline":
            self.current_ring += content

parser = FlickrShapeParser()
xml.sax.parse(sys.stdin, parser)

