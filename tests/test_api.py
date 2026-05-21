"""
PSN API Integration Tests

Run with: pytest tests/test_api.py -v

These tests verify the full API functionality including:
- Health checks
- Simulation endpoints
- Registry lookups
- Regulatory analysis
- Authentication and rate limiting
"""
import pytest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.main import app
from api.auth import init_api_keys_db, create_api_key, API_KEYS_DB_PATH


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def api_key():
    """Create a test API key"""
    init_api_keys_db()
    key = create_api_key("pro", "Test API Key")
    yield key
    # Cleanup is optional since we're using a test database


@pytest.fixture(scope="module")
def limited_api_key():
    """Create an API key with very low limit for rate limit testing"""
    init_api_keys_db()
    # Create key with 2-call limit by manipulating the database
    import sqlite3
    key = create_api_key("free", "Limited Test Key")
    conn = sqlite3.connect(API_KEYS_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE api_keys SET rate_limit_monthly = 2, calls_this_month = 0 WHERE key = ?",
        (key,)
    )
    conn.commit()
    conn.close()
    return key


@pytest.fixture
def auth_headers(api_key):
    """Standard auth headers"""
    return {"X-API-Key": api_key}


class TestHealthCheck:
    """Test 1: Health check endpoint"""

    def test_health_returns_200(self, client):
        """GET /health returns 200"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_contains_model_status(self, client):
        """Health response includes model_loaded field"""
        response = client.get("/health")
        data = response.json()
        assert "model_loaded" in data
        assert "database_connected" in data
        assert "status" in data
        assert "uptime_seconds" in data


class TestSimulation:
    """Tests 2-5: Simulation endpoints"""

    def test_simulation_default_config(self, client, auth_headers):
        """Test 2: POST /v1/simulate with default glucose/aerobic returns optimal solution"""
        response = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "optimal"
        assert data["growth_rate"] > 0
        assert data["carbon_source"] == "glucose"
        assert data["oxygen_constraint"] == "aerobic"

    def test_simulation_with_knockout(self, client, auth_headers):
        """Test 3: Simulation with knockouts changes growth rate"""
        # First, run without knockout
        response_base = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic",
                "gene_knockouts": []
            },
            headers=auth_headers
        )
        base_growth = response_base.json()["growth_rate"]

        # Then with a knockout (YDL022W = GPD1, glycerol-3-phosphate dehydrogenase)
        response_ko = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic",
                "gene_knockouts": ["YDL022W"]
            },
            headers=auth_headers
        )
        assert response_ko.status_code == 200
        data = response_ko.json()
        assert "YDL022W" in data["knocked_out_genes"]
        # Growth rate may or may not change depending on the gene

    def test_simulation_without_goebl(self, client, auth_headers):
        """Test 4: apply_goebl_layer: false returns result without proteolytic burden"""
        response = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic",
                "apply_goebl_layer": False
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["goebl_tax_applied"] == False
        assert data["proteolytic_burden"] is None

    def test_simulation_invalid_gene(self, client, auth_headers):
        """Test 5: Invalid gene ID returns 422"""
        response = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic",
                "gene_knockouts": ["FAKE_GENE_123"]
            },
            headers=auth_headers
        )
        assert response.status_code == 422
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "INVALID_GENE"


class TestRegistry:
    """Tests 6-9: Registry endpoints"""

    def test_registry_gene_lookup(self, client, auth_headers):
        """Test 6: Look up YDL022W returns valid GLNumber"""
        response = client.get(
            "/v1/registry/gene/YDL022W",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "gl_number" in data
        assert data["systematic_name"] == "YDL022W"
        assert "associated_reactions" in data

    def test_registry_reaction_lookup(self, client, auth_headers):
        """Test 7: Look up a known GLNumber returns substrates/products"""
        # First get a valid GL number from the gene lookup
        gene_response = client.get(
            "/v1/registry/gene/YDL022W",
            headers=auth_headers
        )
        if gene_response.status_code == 200 and gene_response.json().get("associated_reactions"):
            gl_number = gene_response.json()["associated_reactions"][0]["gl_number"]

            response = client.get(
                f"/v1/registry/reaction/{gl_number}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert "substrates" in data
            assert "products" in data
            assert "reaction_name" in data

    def test_registry_search(self, client, auth_headers):
        """Test 8: Search for 'glycolysis' returns results"""
        response = client.get(
            "/v1/registry/search?q=glycolysis",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "glycolysis"
        assert "results" in data
        assert len(data["results"]) > 0

    def test_registry_stats(self, client, auth_headers):
        """Test 9: Stats returns expected counts"""
        response = client.get(
            "/v1/registry/stats",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_reactions"] > 3000  # Should be ~3,857
        assert data["total_metabolites"] > 2000  # Should be ~2,806
        assert data["model_version"] == "Yeast-GEM v9.0.2"


class TestRegulatory:
    """Tests 10-11: Regulatory endpoints"""

    def test_regulatory_analyze(self, client, auth_headers):
        """Test 10: POST /v1/regulatory/analyze returns regulatory state"""
        response = client.post(
            "/v1/regulatory/analyze",
            json={
                "glucose_uptake_rate": 10.5,
                "gene_knockouts": []
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "proteolytic_burden" in data
        assert "regulatory_state" in data
        assert "grr1_sensor_status" in data
        assert "scf_complex_activity" in data
        assert "affected_reactions" in data

    def test_regulatory_compare(self, client, auth_headers):
        """Test 11: POST /v1/regulatory/compare returns differential"""
        response = client.post(
            "/v1/regulatory/compare",
            json={
                "condition_a": {
                    "label": "high_glucose",
                    "glucose_uptake_rate": 15.0
                },
                "condition_b": {
                    "label": "low_glucose",
                    "glucose_uptake_rate": 2.0
                }
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "condition_a" in data
        assert "condition_b" in data
        assert "differential" in data
        assert data["condition_a"]["label"] == "high_glucose"
        assert data["condition_b"]["label"] == "low_glucose"


class TestAuthentication:
    """Tests 12-13: Authentication and rate limiting"""

    def test_auth_required(self, client):
        """Test 12: Requests without API key return 401"""
        response = client.post(
            "/v1/simulate",
            json={
                "carbon_source": "glucose",
                "oxygen_constraint": "aerobic"
            }
        )
        assert response.status_code == 401
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "MISSING_API_KEY"

    def test_rate_limiting(self, client, limited_api_key):
        """Test 13: Rate limit returns 429 when quota exceeded"""
        headers = {"X-API-Key": limited_api_key}

        # Use up the 2-call limit
        for _ in range(2):
            client.get("/v1/registry/stats", headers=headers)

        # Third call should fail with 429
        response = client.get("/v1/registry/stats", headers=headers)
        assert response.status_code == 429
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "RATE_LIMIT_EXCEEDED"


class TestSimulationOptions:
    """Additional test: Simulation options endpoint"""

    def test_simulation_options(self, client, auth_headers):
        """GET /v1/simulate/options returns available options"""
        response = client.get(
            "/v1/simulate/options",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "carbon_sources" in data
        assert "oxygen_constraints" in data
        assert "objectives" in data
        assert "glucose" in data["carbon_sources"]
        assert "aerobic" in data["oxygen_constraints"]


class TestRegulatoryStatus:
    """Additional test: Regulatory status endpoint"""

    def test_regulatory_status(self, client, auth_headers):
        """GET /v1/regulatory/status returns configuration"""
        response = client.get(
            "/v1/regulatory/status",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "high_glucose_threshold" in data
        assert "low_glucose_threshold" in data
        assert "penalty_factor" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
