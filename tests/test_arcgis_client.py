import json
import unittest
from unittest.mock import MagicMock, patch
import requests
from src.arcgis_client import ArcGISClient, SimpleArcGISClient
from src.errors import ArcGISError, ArcGISResponseError, ArcGISValidationError
import os

class TestArcGISClient(unittest.TestCase):

    def setUp(self):
        self.sample_features = [
            {"attributes": {"NAME": "County A", "SQMI": 500}},
            {"attributes": {"NAME": "County B", "SQMI": 1500}}
        ]

    # Test 1: ArcGIS query works with mocked response
    @patch("arcgis_client.requests.get")
    def test_arcgis_query_success(self, mock_get):
        service_url = "https://example.com/FeatureServer/0"
        client = SimpleArcGISClient(service_url)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"features": self.sample_features, "spatialReference": {"wkid": 4326}}
        mock_get.return_value = mock_response

        result = client.query_features(where_clause="STATE_NAME = 'Texas'", max_records=2)

        self.assertEqual(len(result["features"]), 2)
        mock_get.assert_called_once()

    # Test 2: ArcGIS query failure raises ArcGISError
    @patch("arcgis_client.requests.get")
    def test_arcgis_query_failure(self, mock_get):
        # Setup mock to raise exception
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

        client = SimpleArcGISClient("http://fake-url.com")
        
        with self.assertRaises(ArcGISError) as cm:
            client.query_features()
        
        self.assertIn("Failed to query features", str(cm.exception))

    # Test 3: Service error payload raises ArcGISResponseError
    @patch("arcgis_client.requests.get")
    def test_arcgis_service_error_payload(self, mock_get):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"error": {"message": "Bad request", "details": ["Invalid where clause"]}}
        mock_get.return_value = mock_response

        client = SimpleArcGISClient("http://fake-url.com")
        with self.assertRaises(ArcGISResponseError):
            client.query_features()

    # Test 4: Validation errors on inputs
    def test_validation_errors(self):
        client = SimpleArcGISClient("http://fake-url.com")
        with self.assertRaises(ArcGISValidationError):
            client.query_features(where_clause="", max_records=1)
        with self.assertRaises(ArcGISValidationError):
            client.query_features(where_clause="1=1", max_records=0)
        with self.assertRaises(ArcGISValidationError):
            client.query_features(where_clause="1=1", distance=-1)

    @patch("arcgis_client.requests.get")
    def test_pagination_combines_results(self, mock_get):
        service_url = "https://example.com/FeatureServer/0"
        client = SimpleArcGISClient(service_url)

        first_page = {"features": [{"attributes": {"id": 1}}], "exceededTransferLimit": True}
        second_page = {"features": [{"attributes": {"id": 2}}], "exceededTransferLimit": False}
        mock_response_1 = MagicMock()
        mock_response_1.raise_for_status.return_value = None
        mock_response_1.json.return_value = first_page
        mock_response_2 = MagicMock()
        mock_response_2.raise_for_status.return_value = None
        mock_response_2.json.return_value = second_page
        mock_get.side_effect = [mock_response_1, mock_response_2]

        result = client.query_features(max_records=1)

        self.assertEqual(len(result["features"]), 2)
        self.assertEqual(result["resultCount"], 2)
        # Ensure pagination advanced
        self.assertEqual(mock_get.call_count, 2)

    @patch("arcgis_client.requests.get")
    def test_spatial_query_parameters(self, mock_get):
        service_url = "https://example.com/FeatureServer/0"
        client = SimpleArcGISClient(service_url)

        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"features": []}
        mock_get.return_value = mock_response

        geom = {"x": -104.0, "y": 39.0, "spatialReference": {"wkid": 4326}}
        client.query_features(
            where_clause="1=1",
            geometry=geom,
            geometry_type="esriGeometryPoint",
            spatial_relationship="esriSpatialRelWithin",
            distance=5,
            units="esriSRUnit_StatuteMile",
        )

        called_params = mock_get.call_args[1]["params"]
        self.assertIn("geometry", called_params)
        self.assertEqual(json.loads(called_params["geometry"]), geom)
        self.assertEqual(called_params["geometryType"], "esriGeometryPoint")
        self.assertEqual(called_params["spatialRel"], "esriSpatialRelWithin")
        self.assertEqual(called_params["distance"], 5)
        self.assertEqual(called_params["units"], "esriSRUnit_StatuteMile")

    def test_geojson_conversion(self):
        features = [
            {"attributes": {"id": 1}, "geometry": {"x": -120.0, "y": 38.0}},
            {"attributes": {"id": 2}, "geometry": {"paths": [[[0, 0], [1, 1]]]}}
        ]
        geojson = SimpleArcGISClient.to_geojson(features, spatial_reference={"wkid": 4326})
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 2)
        self.assertEqual(geojson["features"][0]["geometry"]["type"], "Point")
        self.assertEqual(geojson["features"][1]["geometry"]["type"], "LineString")

    @patch("arcgis_client.SimpleArcGISClient.query_features")
    def test_arcgis_client_attribute_query_geojson(self, mock_query_features):
        mock_query_features.return_value = {
            "features": [{"attributes": {"id": 1}, "geometry": {"x": 0, "y": 0}}],
            "spatialReference": {"wkid": 4326},
        }
        client = ArcGISClient("http://example.com/FeatureServer/0")
        geojson = client.query(where="STATE_NAME = 'Texas'")
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 1)
        mock_query_features.assert_called_once()

    @patch("arcgis_client.SimpleArcGISClient.query_features")
    def test_arcgis_client_query_nearby_geojson(self, mock_query_features):
        mock_query_features.return_value = {
            "features": [{"attributes": {"id": 1}, "geometry": {"x": 0, "y": 0}}],
            "spatialReference": {"wkid": 4326},
        }
        client = ArcGISClient("http://example.com/FeatureServer/0")
        geojson = client.query_nearby(point=(-97.7431, 30.2672), distance_miles=50)
        called_kwargs = mock_query_features.call_args[1]
        self.assertIn("geometry", called_kwargs)
        self.assertEqual(geojson["type"], "FeatureCollection")
        self.assertEqual(len(geojson["features"]), 1)

    # Optional integration test guarded by env flag
    @unittest.skipUnless(os.getenv("RUN_ARCGIS_INTEGRATION") == "1", "Integration test disabled by default")
    def test_arcgis_query_integration(self):
        service_url = "https://services.arcgis.com/P3ePLMYs2RVChkJx/ArcGIS/rest/services/USA_Census_Counties/FeatureServer/0"
        client = SimpleArcGISClient(service_url)
        result = client.query_features(where_clause="STATE_NAME = 'Texas'", max_records=3)
        self.assertIn("features", result)

if __name__ == "__main__":
    unittest.main()
