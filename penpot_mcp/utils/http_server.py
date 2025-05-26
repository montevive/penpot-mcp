"""HTTP server module for serving exported images from memory."""

import io
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import socketserver

class InMemoryImageHandler(BaseHTTPRequestHandler):
    """HTTP request handler for serving images stored in memory."""
    
    # Class variable to store images
    images = {}
    
    def do_GET(self):
        """Handle GET requests."""
        # Remove query parameters if any
        path = self.path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        
        # Extract image ID from path
        # Expected path format: /images/{image_id}.{format}
        parts = path.split('/')
        if len(parts) == 3 and parts[1] == 'images':
            # Extract image_id by removing the file extension if present
            image_id_with_ext = parts[2]
            image_id = image_id_with_ext.split('.')[0]
            
            if image_id in self.images:
                img_data = self.images[image_id]['data']
                img_format = self.images[image_id]['format']
                
                # Set content type based on format
                content_type = f"image/{img_format}"
                if img_format == 'svg':
                    content_type = 'image/svg+xml'
                
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.send_header('Content-length', len(img_data))
                self.end_headers()
                self.wfile.write(img_data)
                return
        
        # Return 404 if image not found
        self.send_response(404)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {'error': 'Image not found'}
        self.wfile.write(json.dumps(response).encode())


class ImageServer:
    """Server for in-memory images."""
    
    def __init__(self, host='localhost', port=0):
        """Initialize the HTTP server.
        
        Args:
            host: Host address to listen on
            port: Port to listen on (0 means use a random available port)
        """
        self.host = host
        self.port = port
        self.server = None
        self.server_thread = None
        self.is_running = False
        self.base_url = None
    
    def start(self):
        """Start the HTTP server in a background thread.
        
        Returns:
            Base URL of the server with actual port used
        """
        if self.is_running:
            return self.base_url
        
        # Create TCP server with address reuse enabled
        class ReuseAddressTCPServer(socketserver.TCPServer):
            allow_reuse_address = True
            
        self.server = ReuseAddressTCPServer((self.host, self.port), InMemoryImageHandler)
        
        # Get the actual port that was assigned
        self.port = self.server.socket.getsockname()[1]
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Start server in a separate thread
        self.server_thread = threading.Thread(target=self.server.serve_forever)
        self.server_thread.daemon = True  # Don't keep process running if main thread exits
        self.server_thread.start()
        self.is_running = True
        
        print(f"Image server started at {self.base_url}")
        return self.base_url
    
    def stop(self):
        """Stop the HTTP server."""
        if not self.is_running:
            return
        
        self.server.shutdown()
        self.server.server_close()
        self.is_running = False
        print("Image server stopped")
    
    def add_image(self, image_id, image_data, image_format='png'):
        """Add image to in-memory storage.
        
        Args:
            image_id: Unique identifier for the image
            image_data: Binary image data
            image_format: Image format (png, jpg, etc.)
            
        Returns:
            URL to access the image
        """
        InMemoryImageHandler.images[image_id] = {
            'data': image_data,
            'format': image_format
        }
        return f"{self.base_url}/images/{image_id}.{image_format}"
    
    def remove_image(self, image_id):
        """Remove image from in-memory storage."""
        if image_id in InMemoryImageHandler.images:
            del InMemoryImageHandler.images[image_id] 