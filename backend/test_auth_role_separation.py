"""
Test Role-Based Authentication & Route Separation in IndicClaim API.
Verifies that:
1. Normal user endpoints (e.g. /api/verify, /api/health) are publicly accessible.
2. Developer/Admin endpoints (e.g. /api/crawl/..., /api/dataset, /api/models) require authentication.
3. Valid developer key grants access, invalid key returns 401.
"""

import sys
from pathlib import Path
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app
from app.auth import ADMIN_API_KEY


def test_auth_and_role_separation():
    client = TestClient(app)

    print("=" * 60)
    print("TESTING ROLE-BASED ACCESS CONTROL & ROUTE SEPARATION")
    print("=" * 60)

    # 1. Test Public Health Endpoint
    print("\n[1] Testing Public Health endpoint (GET /api/health)...")
    res = client.get("/api/health")
    assert res.status_code == 200
    print(f"  Public health OK (Status {res.status_code})")

    # 2. Test Auth Endpoint
    print("\n[2] Testing Auth Endpoint (POST /api/auth/verify-admin)...")
    # Invalid key
    bad_res = client.post("/api/auth/verify-admin", json={"key": "wrong-key-123"})
    assert bad_res.status_code == 401
    print("  Invalid key correctly rejected (401)")

    # Valid key
    good_res = client.post("/api/auth/verify-admin", json={"key": ADMIN_API_KEY})
    assert good_res.status_code == 200
    assert good_res.json()["role"] == "admin"
    print("  Valid key correctly accepted (200, role=admin)")

    # 3. Test Developer Crawl Endpoint without Auth
    print("\n[3] Testing Unauthenticated access to Developer Crawl endpoint (POST /api/crawl/start)...")
    unauth_crawl = client.post("/api/crawl/start", json={"topic": "COVID vaccine India"})
    assert unauth_crawl.status_code == 401
    print(f"  Unauthenticated crawl access blocked: {unauth_crawl.status_code} ({unauth_crawl.json().get('detail')})")

    # 4. Test Developer Dataset Endpoint without Auth
    print("\n[4] Testing Unauthenticated access to Developer Dataset (GET /api/dataset)...")
    unauth_ds = client.get("/api/dataset")
    assert unauth_ds.status_code == 401
    print(f"  Unauthenticated dataset access blocked: {unauth_ds.status_code}")

    # 5. Test Developer Models Endpoint without Auth
    print("\n[5] Testing Unauthenticated access to Developer Models (GET /api/models)...")
    unauth_models = client.get("/api/models")
    assert unauth_models.status_code == 401
    print(f"  Unauthenticated models access blocked: {unauth_models.status_code}")

    # 6. Test Authenticated access to Developer Endpoints
    print("\n[6] Testing Authenticated access with X-Admin-Key header...")
    headers = {"X-Admin-Key": ADMIN_API_KEY}
    auth_models = client.get("/api/models", headers=headers)
    assert auth_models.status_code == 200
    models_data = auth_models.json()
    assert "models" in models_data
    print(f"  Authenticated models access OK: {len(models_data['models'])} models listed")

    auth_ds = client.get("/api/dataset?limit=5", headers=headers)
    assert auth_ds.status_code == 200
    print(f"  Authenticated dataset access OK: {auth_ds.json().get('total')} total items")

    print("\n" + "=" * 60)
    print("ALL ROLE-BASED ACCESS CONTROL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    test_auth_and_role_separation()
