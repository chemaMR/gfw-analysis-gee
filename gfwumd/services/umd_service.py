"""UMD SERVICE (WRAPPER)"""

import json

from gfwumd.services import HansenService, CartoService
from gfwumd.errors import HansenError, CartoError


class UmdService(object):
    """."""

    @staticmethod
    def get_world(geojson, threshold=30, begin='2001-01-01', end='2013-01-01'):
        """Query GEE using supplied args with threshold and polygon."""
        try:
            return HansenService.hansen_all(
                threshold,
                geojson,
                begin,
                end)
        except HansenError as e:
            raise e
        except Exception as e:
            raise e

    @staticmethod
    def get_use(name, id, threshold=30, begin='2001-01-01', end='2013-01-01'):
        """Query GEE using supplied concession id."""
        try:
            data = CartoService.get_use_geojson(name, id)
        except CartoError as e:
            raise e
        except Exception as e:
            raise e
        if not data:
            raise CartoError(message='Not Found')

        geojson = json.loads(data.get('rows')[0].get('geojson'))
        area_ha = data.get('rows')[0].get('area_ha')
        try:
            hansen = HansenService.hansen_all(
                threshold=threshold,
                geojson=geojson,
                begin=begin,
                end=end)
        except HansenError as e:
            raise e
        except Exception as e:
            raise e

        hansen['area_ha'] = area_ha
        return hansen

    @staticmethod
    def get_wdpa(id, threshold=30, begin='2001-01-01', end='2013-01-01'):
        """Query GEE using supplied concession id."""
        try:
            data = CartoService.get_wdpa_geojson(id)
        except CartoError as e:
            raise e
        except Exception as e:
            raise e
        if not data:
            raise CartoError(message='Not Found')

        geojson = json.loads(data.get('rows')[0].get('geojson'))
        area_ha = data.get('rows')[0].get('area_ha')
        try:
            hansen = HansenService.hansen_all(
                threshold=threshold,
                geojson=geojson,
                begin=begin,
                end=end)
        except HansenError as e:
            raise e
        except Exception as e:
            raise e

        hansen['area_ha'] = area_ha
        return hansen
