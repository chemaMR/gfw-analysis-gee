"""API ROUTER"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging

from flask import jsonify, request, Blueprint
from gfwanalysis.routes.api import error, set_params
from gfwanalysis.services.analysis.mangrove_biomass_service import MangroveBiomassService
from gfwanalysis.validators import validate_geostore
from gfwanalysis.middleware import get_geo_by_hash, get_geo_by_use, get_geo_by_wdpa, \
    get_geo_by_national, get_geo_by_subnational, get_geo_by_regional
from gfwanalysis.errors import MangroveBiomassError
from gfwanalysis.serializers import serialize_mangrove_biomass

mangrove_biomass_endpoints_v1 = Blueprint('_biomass', __name__)

def analyze(geojson, area_ha):
    """Analyze Mangrove Biomass"""
    logging.info('[ROUTER]: Mangrove Getting biomass')
    try:
        data = MangroveBiomassService.analyze(geojson=geojson)
    except MangroveBiomassError as e:
        logging.error(f'[ROUTER]: {e.message}')
        return error(status=500, detail=e.message)
    except Exception as e:
        logging.error(f'[ROUTER]: {str(e)}')
        return error(status=500, detail='Generic Error')
    data['area_ha'] = area_ha
    data['biomass_density'] = data['biomass'].get('b1') / area_ha
    return jsonify(data=serialize_mangrove_biomass(data, 'mangrove-biomass')), 200


@mangrove_biomass_endpoints_v1.route('/', strict_slashes=False, methods=['GET', 'POST'])
@validate_geostore
@get_geo_by_hash
def get_by_geostore(geojson, area_ha):
    """By Geostore Endpoint"""
    logging.info('[ROUTER]: Getting biomass by geostore')
    return analyze(geojson, area_ha)


@mangrove_biomass_endpoints_v1.route('/use/<name>/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_use
def get_by_use(name, id, geojson, area_ha):
    """Use Endpoint"""
    logging.info('[ROUTER]: Getting biomass by use')
    return analyze(geojson, area_ha)


@mangrove_biomass_endpoints_v1.route('/wdpa/<id>', strict_slashes=False, methods=['GET'])
@get_geo_by_wdpa
def get_by_wdpa(id, geojson, area_ha):
    """Wdpa Endpoint"""
    logging.info('[ROUTER]: Getting biomass by wdpa')
    return analyze(geojson, area_ha)


@mangrove_biomass_endpoints_v1.route('/admin/<iso>', strict_slashes=False, methods=['GET'])
@get_geo_by_national
def get_by_national(iso, geojson, area_ha):
    """National Endpoint"""
    logging.info('[ROUTER]: Getting biomass loss by iso')
    return analyze(geojson, area_ha)


@mangrove_biomass_endpoints_v1.route('/admin/<iso>/<id1>', strict_slashes=False, methods=['GET'])
@get_geo_by_subnational
def get_by_subnational(iso, id1, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting biomass loss by admin1')
    return analyze(geojson, area_ha)

@mangrove_biomass_endpoints_v1.route('/admin/<iso>/<id1>/<id2>', strict_slashes=False, methods=['GET'])
@get_geo_by_regional
def get_by_regional(iso, id1, id2, geojson, area_ha):
    """Subnational Endpoint"""
    logging.info('[ROUTER]: Getting biomass loss by admin2 ')
    return analyze(geojson, area_ha)