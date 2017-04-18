
from gfwumd.errors import HansenError
import ee


def get_region(geom):
    """Return ee.Geometry from supplied GeoJSON object."""
    poly = get_coords(geom)
    ptype = get_type(geom)
    if ptype.lower() == 'multipolygon':
        region = ee.Geometry.MultiPolygon(poly)
    else:
        region = ee.Geometry.Polygon(poly)
    return region


def get_coords(geojson):
    if geojson.get('features') is not None:
        return geojson.get('features')[0].get('geometry').get('coordinates')
    elif geojson.get('geometry') is not None:
        return geojson.get('geometry').get('coordinates')
    else:
        return geojson.get('coordinates')


def get_type(geojson):
    if geojson.get('features') is not None:
        return geojson.get('features')[0].get('geometry').get('type')
    elif geojson.get('geometry') is not None:
        return geojson.get('geometry').get('type')
    else:
        return geojson.get('type')


def squaremeters_to_ha(value):
    """Converts square meters to hectares, and gives val to 2 decimal places"""
    tmp = value/10000.
    return float('{0:4.2f}'.format(tmp))


class GeeService(object):

    @classmethod
    def hansen_all(threshold, geojson, begin, end):
        """For a given threshold and geometry return a dictionary of ha area.
        The threshold is used to identify which band of loss and tree to select.
        asset_id should be 'projects/wri-datalab/HansenComposite_14-15'
        Methods used to identify data:

        Gain band is a binary (0 = 0, 255=1) of locations where tree cover increased
        over data collction period. Calculate area of gain, by converting 255 values
        to 1, and then using a trick to convert this to pixel area
        (1 * pixelArea()). Finally, we sum the areas over a given polygon using a
        reducer, and convert from square meters to hectares.

        Tree_X bands show percentage canopy cover of forest, If missing, no trees
        present. Therefore, to count the tree area of a given canopy cover, select
        the band, convert it to binary (0=no tree cover, 1 = tree cover), and
        identify pixel area via a trick, multiplying all 1 vals by image.pixelArea.
        Then, sum the values over a region. Finally, divide the result (meters
        squared) by 10,000 to convert to hectares
        """
        try:
            d = {}
            asset_id = 'projects/wri-datalab/HansenComposite_14-15'
            begin = int(begin.split('-')[0][2:])
            end = int(end.split('-')[0][2:])
            region = get_region(geojson)
            reduce_args = {'reducer': ee.Reducer.sum().unweighted(),
                           'geometry': region,
                           'bestEffort': True,
                           'scale': 90}
            gfw_data = ee.Image(asset_id)
            loss_band = 'loss_{0}'.format(threshold)
            cover_band = 'tree_{0}'.format(threshold)
            # Identify 2000 forest cover at given threshold
            tree_area = gfw_data.select(cover_band).gt(0).multiply(
                            ee.Image.pixelArea()).reduceRegion(**reduce_args).getInfo()
            d['tree-extent'] = squaremeters_to_ha(tree_area[cover_band])
            # Identify tree gain over data collection period
            gain = gfw_data.select('gain').divide(255.0).multiply(
                            ee.Image.pixelArea()).reduceRegion(**reduce_args).getInfo()
            d['gain'] = squaremeters_to_ha(gain['gain'])
            # Identify area lost from begin year up untill end year
            tmp_img = gfw_data.select(loss_band)
            loss_area_img = tmp_img.gte(begin).And(tmp_img.lte(end)).multiply(ee.Image.pixelArea())
            loss_total = loss_area_img.reduceRegion(**reduce_args).getInfo()
            d['loss'] = squaremeters_to_ha(loss_total[loss_band])
            return d
        except Exception as error:
            raise HansenError(message='Generic GEE Error in Hansen analysis')
