from django.core.management.base import BaseCommand
from django.utils.timezone import now
from layers.models import Layer
import requests

class Command(BaseCommand):
    help = "Check HTTP status for the layer with the least recent last_http_status."

    def handle(self, *args, **kwargs):
        # Get the layer with the least recent last_http_status
        layer = Layer.objects.order_by('last_http_status').first()

        if not layer:
            self.stdout.write("No layers found to check http status.")
            return
        
        if layer.url:
            try:
                response = requests.get(layer.url, timeout=5, allow_redirects=True)
                status = response.status_code
            except Exception as e:
                self.stderr.write(f"Error while checking URL {layer.url}: {e}")
                status = 404  # Default to 404 if the request fails

            layer.last_http_status = status
            update_fields = ['last_http_status']
            
            if status == 200:
                layer.last_success_status = now()
                update_fields.append('last_success_status')
            
            layer.save(update_fields=update_fields)
            self.stdout.write(f"Layer {layer.name} status updated to {status}.")
        
        else:
            self.stdout.write(f"Layer {layer.name} has no URL to check.")