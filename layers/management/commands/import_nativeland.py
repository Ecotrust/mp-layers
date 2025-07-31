from django.core.management.base import BaseCommand
import requests, os, json
from django.conf import settings

class Command(BaseCommand):
    help = "Import daily-built JSON for Native-Land.ca."

    def is_valid_geojson(self, layer_file):
        
        if os.path.isfile(layer_file):
            # I can't make a valid GeoJSON with at least one feature in less than 115 bytes
            if os.stat(layer_file).st_size > 100:
                try:
                    with open(layer_file) as f:
                        geojson = json.load(f)
                        if (
                            'type' in geojson.keys() and
                            'features' in geojson.keys() and
                            geojson['type'] == 'FeatureCollection' and
                            len(geojson['features']) > 0 and
                            'type' in geojson['features'][0].keys() and
                            geojson['features'][0]['type'] == 'Feature' and
                            'geometry' in geojson['features'][0].keys() and
                            'type' in geojson['features'][0]['geometry'].keys() and
                            'coordinates' in geojson['features'][0]['geometry'].keys() and
                            len(geojson['features'][0]['geometry']['coordinates']) > 0
                        ):
                            return True
                except Exception:
                    pass
        print("NOT VALID GEOJSON: {}".format(layer_file))
        return False

    def handle(self, *args, **options):
        
        # Attempt to scrape latest JSON
        from bs4 import BeautifulSoup as bs
        from shutil import copyfile
        
        from urllib.error import URLError

        if not settings.NATIVE_LAND_API_KEY == None:

            NLD_DATA_DIR = os.path.join(settings.MEDIA_ROOT, 'data_manager', 'nativeland')
            NLD_BACKUP_DIR = os.path.join(NLD_DATA_DIR, 'backups')

            api_prefix = 'https://native-land.ca/api/polygons/geojson/'
            api_postfix = '?key={}'.format(settings.NATIVE_LAND_API_KEY)
            api_categories = {
                'territories': 'territories',
                'languages': 'languages',
                'treaties': 'treaties',
            }

            for key in api_categories.keys():
                target_file = os.path.join(NLD_DATA_DIR, 'nld_{}.json'.format(key))
                backup_file = os.path.join(NLD_BACKUP_DIR, 'nld_{}.json'.format(key))
                try:
                    # Make a backup of old data (if valid)
                    if self.is_valid_geojson(target_file):
                        copyfile(target_file, backup_file)
                    # Get the new data
                    json_data = requests.get(api_prefix + api_categories[key] + api_postfix)
                    # Write new data to target
                    with open(target_file, 'wb') as outfile:
                        outfile.write(json_data.content)
                    # If new data is no good, restor backup
                    if not(self.is_valid_geojson(target_file)):
                        copyfile(backup_file, target_file)
                    
                except Exception:
                    print('Failed to download {}.'.format(key))
                    pass

        else:
            print("NATIVE_LAND_API_KEY not set in local settings.")

                