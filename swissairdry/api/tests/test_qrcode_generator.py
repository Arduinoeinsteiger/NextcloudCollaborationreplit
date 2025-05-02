"""
Tests für den QR-Code-Generator des SwissAirDry Minimal HTTP Servers

Diese Tests überprüfen die Funktionalität des QR-Code-Generators, der im
SwissAirDry Minimal HTTP Server implementiert ist.

Hinweis: Dieser Test setzt voraus, dass die Abhängigkeiten `qrcode` und `pillow`
installiert sind.
"""

import os
import sys
import unittest
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock

# Stellen Sie sicher, dass der Pfad zum Modul im Suchpfad ist
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from PIL import Image
    import qrcode
    HAS_DEPENDENCIES = True
except ImportError:
    HAS_DEPENDENCIES = False

# Mock für BaseHTTPRequestHandler
class MockHandler:
    def __init__(self):
        self.wfile = BytesIO()
        self.headers = {}
        self.path = ""
        self.sent_data = None
        self.sent_headers = {}
        self.response_code = None
        
    def send_response(self, code):
        self.response_code = code
        
    def send_header(self, key, value):
        self.sent_headers[key] = value
        
    def end_headers(self):
        pass
        
    def wfile_write(self, data):
        self.sent_data = data
        self.wfile.write(data)


@unittest.skipUnless(HAS_DEPENDENCIES, "Abhängigkeiten qrcode und/oder pillow nicht installiert")
class TestQRCodeGenerator(unittest.TestCase):
    """Tests für die QR-Code-Generator-Funktionalität"""
    
    def setUp(self):
        """Setup für die Tests"""
        # Import hier, damit der Test skippt wenn Abhängigkeiten fehlen
        from minimal_http_server import SwissAirDryHTTPHandler
        
        # Mock-Handler erstellen
        self.handler = SwissAirDryHTTPHandler.__new__(SwissAirDryHTTPHandler)
        self.handler.wfile = BytesIO()
        self.handler.path = ""
        self.mock_handler = MockHandler()
        
        # Methoden des Handlers patchen
        self.original_send_response = self.handler.send_response
        self.original_send_header = self.handler.send_header
        self.original_end_headers = self.handler.end_headers
        self.original_wfile_write = self.handler.wfile.write
        
        # Patchen mit den Mock-Methoden
        self.handler.send_response = self.mock_handler.send_response
        self.handler.send_header = self.mock_handler.send_header
        self.handler.end_headers = self.mock_handler.end_headers
        self.handler.wfile.write = self.mock_handler.wfile_write
    
    def tearDown(self):
        """Cleanup nach den Tests"""
        # Methoden des Handlers zurücksetzen
        self.handler.send_response = self.original_send_response
        self.handler.send_header = self.original_send_header
        self.handler.end_headers = self.original_end_headers
        self.handler.wfile.write = self.original_wfile_write
    
    def test_generate_qrcode_basic(self):
        """Test der grundlegenden QR-Code-Generierung"""
        # Testdaten
        test_data = "Test QR Code Data"
        test_size = 200
        test_title = "Test QR Code"
        
        # QR-Code generieren
        qrcode_img = self.handler._generate_qrcode(test_data, test_size, test_title)
        
        # Überprüfen, ob ein Bild zurückgegeben wurde
        self.assertIsInstance(qrcode_img, Image.Image)
        
        # Überprüfen, ob die Größe stimmt
        self.assertEqual(qrcode_img.width, test_size)
        self.assertEqual(qrcode_img.height, test_size + 40)  # +40 für Titel
        
    def test_generate_qrcode_wifi(self):
        """Test der QR-Code-Generierung für WLAN-Konfiguration"""
        # WLAN-Testdaten
        wifi_data = "WLAN:T:WPA;S:TestNetwork;P:TestPassword;;"
        
        # QR-Code generieren
        qrcode_img = self.handler._generate_qrcode(wifi_data, 300, "WLAN-Konfiguration")
        
        # Überprüfen, ob ein Bild zurückgegeben wurde
        self.assertIsInstance(qrcode_img, Image.Image)
        
    def test_generate_qrcode_device_config(self):
        """Test der QR-Code-Generierung für Gerätekonfiguration"""
        # Geräte-Testdaten
        device_data = '{"device_id":"test001","server":"test.server:5002","mode":"standard"}'
        
        # QR-Code generieren
        qrcode_img = self.handler._generate_qrcode(device_data, 300, "Gerätekonfiguration")
        
        # Überprüfen, ob ein Bild zurückgegeben wurde
        self.assertIsInstance(qrcode_img, Image.Image)
        
    def test_qrcode_html_response(self):
        """Test der HTML-Antwort für QR-Codes"""
        # Path für HTML-Antwort setzen
        self.handler.path = "/qrcode?data=TestData&format=html"
        
        # QR-Code-Antwort simulieren
        with patch('minimal_http_server.SwissAirDryHTTPHandler._generate_qrcode') as mock_generate:
            # Mock-Bild erstellen
            mock_img = Image.new('RGB', (300, 340), color = 'white')
            mock_generate.return_value = mock_img
            
            # HTML-Antwort generieren
            self.handler.do_GET()
            
            # Überprüfen, ob die Antwort HTML ist
            self.assertEqual(self.mock_handler.response_code, 200)
            self.assertEqual(self.mock_handler.sent_headers.get('Content-type'), 'text/html')
            
            # Überprüfen, ob die Antwort HTML-Tags enthält
            self.assertIn(b'<!DOCTYPE html>', self.mock_handler.sent_data)
            self.assertIn(b'<img', self.mock_handler.sent_data)
            
    def test_qrcode_png_response(self):
        """Test der PNG-Antwort für QR-Codes"""
        # Path für PNG-Antwort setzen
        self.handler.path = "/qrcode?data=TestData&format=png"
        
        # QR-Code-Antwort simulieren
        with patch('minimal_http_server.SwissAirDryHTTPHandler._generate_qrcode') as mock_generate:
            # Mock-Bild erstellen
            mock_img = Image.new('RGB', (300, 340), color = 'white')
            mock_generate.return_value = mock_img
            
            # PNG-Antwort generieren
            self.handler.do_GET()
            
            # Überprüfen, ob die Antwort PNG ist
            self.assertEqual(self.mock_handler.response_code, 200)
            self.assertEqual(self.mock_handler.sent_headers.get('Content-type'), 'image/png')
            
            # Überprüfen, ob die Antwort mit dem PNG-Header beginnt
            self.assertTrue(self.mock_handler.sent_data.startswith(b'\x89PNG'))
            
    def test_qrcode_generator_page(self):
        """Test der QR-Code-Generator-Seite"""
        # Path für Generator-Seite setzen
        self.handler.path = "/qrcode"
        
        # QR-Code-Generator-Seite abrufen
        self.handler.do_GET()
        
        # Überprüfen, ob die Antwort HTML ist
        self.assertEqual(self.mock_handler.response_code, 200)
        self.assertEqual(self.mock_handler.sent_headers.get('Content-type'), 'text/html')
        
        # Überprüfen, ob die Antwort Formular-Elemente enthält
        self.assertIn(b'<form', self.mock_handler.sent_data)
        self.assertIn(b'<input', self.mock_handler.sent_data)
        self.assertIn(b'<button', self.mock_handler.sent_data)


if __name__ == '__main__':
    unittest.main()