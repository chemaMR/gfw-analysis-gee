"""HANSEN SERVICE"""

import logging

import ee
from gfwanalysis.errors import HansenError
from gfwanalysis.config import SETTINGS
from gfwanalysis.utils.geo import get_region, squaremeters_to_ha, sum_extent, ee_squaremeters_to_ha


class HansenService(object):

    @staticmethod
    def analyze(threshold, geojson, begin, end, aggregate_values=True):
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
            # Create SERVER-SIDE dictionary for storing results
            d = ee.Dictionary()
            # Define parameters
            useMap = True
            divideGeom = False
            nDivide = 16
            useBestEffort=True
            gfw_data = ee.Image(SETTINGS.get('gee').get('assets').get('hansen'))
            extent2010_image = ee.Image(SETTINGS.get('gee').get('assets').get('hansen_2010_extent'))
            hansen_v1_5 = ee.Image(SETTINGS.get('gee').get('assets').get('hansen_2017_v1_5'))
            begin = int(begin.split('-')[0][2:])
            end = int(end.split('-')[0][2:])
            loss_band = 'loss_{0}'.format(threshold)
            cover_band = 'tree_{0}'.format(threshold)
            # Get region and optionally divide it into smaller parts
            region = get_region(geojson, divideGeom, nDivide)
            # Create threshold image
            thresh_image = ee.Image.constant(float(threshold))
            # Identify extent of 2000 forest cover in region at given threshold
            tree_area = sum_extent(hansen_v1_5.select('treecover2000').gt(thresh_image), region, useMap, useBestEffort)
            # Identify extent of 2010 forest cover in region at given threshold
            extent2010_area = sum_extent(extent2010_image.gt(thresh_image), region, useMap, useBestEffort)
            # Identify tree gain over data collection period
            gain = sum_extent(gfw_data.select('gain').divide(255.0), region, useMap, useBestEffort)
            # Mask loss with itself to avoid overcounting errors
            tmp_img = gfw_data.select(loss_band).mask(gfw_data.select(loss_band))
            if aggregate_values:
                logging.info('Aggregating values')
                # Identify one loss area from begin year up untill end year
                loss_area_img = tmp_img.gte(begin).And(tmp_img.lte(end))
                loss_total = sum_extent(loss_area_img, region, useMap, useBestEffort)
                #logging.info(f'Add loss total to dictionary: {loss_total.getInfo()}')
                # get values and add to dictionary
                logging.info('Created output dictionary')
                d = d.set('loss_start_year', begin)
                d = d.set('loss_end_year', end)
                d = d.set('tree_extent', ee_squaremeters_to_ha(tree_area))
                d = d.set('tree_extent2010', ee_squaremeters_to_ha(extent2010_area))
                d = d.set('gain', ee_squaremeters_to_ha(gain))
                d = d.set('loss', ee_squaremeters_to_ha(loss_total))
            else:
                logging.info('Yearly summaries')
                # Identify loss area per year from beginning year to end year (inclusive)
                def reduceFunction(img):
                    out = ee_squaremeters_to_ha(sum_extent(img, region, useMap, useBestEffort))
                    return ee.Feature(None, {'sum': out})
                def makeYear(x):
                    return ee.Number(x).add(2000).int().format()
                ## Calculate annual biomass loss - add subset images to a collection and then map a reducer to it
                collectionG = ee.ImageCollection([tmp_img.updateMask(tmp_img.eq(year)).divide(year).set({'year': 2000+year}) for year in range(begin, end + 1)])
                output = collectionG.map(reduceFunction)
                #logging.info(f'Output : {output.getInfo()}')
                year_list = ee.List.sequence(begin, end, 1).map(makeYear)
                loss_year = ee.Dictionary.fromLists(year_list, ee.List(output.aggregate_array('sum')))
                # get values and add to dictionary
                logging.info('Created output dictionary')
                d = d.set('loss_start_year', begin)
                d = d.set('loss_end_year', end)
                d = d.set('tree_extent', ee_squaremeters_to_ha(tree_area))
                d = d.set('tree_extent2010', ee_squaremeters_to_ha(extent2010_area))
                d = d.set('gain', ee_squaremeters_to_ha(gain))
                d = d.set('loss', loss_year)
            #logging.info(f'Output dictionary: {d.getInfo()}')
            return d.getInfo()
        except Exception as error:
            logging.error(str(error))
            raise HansenError(message='Error in Hansen Analysis')
