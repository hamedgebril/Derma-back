"""
Backend API Routes Audit Script
يفحص جميع الـroutes المسجلة في التطبيق ويتأكد من مطابقتها للمواصفات
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app

# القائمة المطلوبة من الـendpoints
EXPECTED_ROUTES = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/ready"),
    ("POST", "/api/v1/auth/signup"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/diagnosis"),
    ("GET", "/api/v1/history"),
    ("GET", "/api/v1/diagnosis/{analysis_id}"),
}

# Endpoints التي يجب ألا تكون موجودة (deprecated)
FORBIDDEN_ROUTES = {
    "/api/v1/diagnosis/diagnose",
    "/api/v1/diagnosis/diagnoses",
    "/api/v1/diagnosis/diagnoses/{diagnosis_id}",
    "/api/v1/upload-image",
    "/api/v1/diagnose",
}


def audit_routes():
    """فحص جميع الـroutes المسجلة"""
    
    print("=" * 70)
    print("🔍 Backend API Routes Audit")
    print("=" * 70)
    print()
    
    # جمع جميع الـroutes من التطبيق
    actual_routes = set()
    api_routes = []
    
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for method in route.methods:
                if method != "HEAD":  # تجاهل HEAD requests
                    route_tuple = (method, route.path)
                    actual_routes.add(route_tuple)
                    
                    # فقط الـAPI routes
                    if route.path.startswith("/api/v1"):
                        api_routes.append({
                            "method": method,
                            "path": route.path,
                            "name": route.name if hasattr(route, "name") else "N/A"
                        })
    
    # 1. عرض جميع API routes الموجودة
    print("📋 All Registered API Routes:")
    print("-" * 70)
    
    # تصنيف الـroutes
    health_routes = []
    auth_routes = []
    diagnosis_routes = []
    other_routes = []
    
    for route in sorted(api_routes, key=lambda x: (x["path"], x["method"])):
        if "/health" in route["path"] or "/ready" in route["path"]:
            health_routes.append(route)
        elif "/auth" in route["path"]:
            auth_routes.append(route)
        elif "/diagnosis" in route["path"] or "/history" in route["path"]:
            diagnosis_routes.append(route)
        else:
            other_routes.append(route)
    
    # عرض Health endpoints
    if health_routes:
        print("\n🏥 Health ({}):".format(len(health_routes)))
        for route in health_routes:
            print(f"   {route['method']:6} {route['path']}")
    
    # عرض Authentication endpoints
    if auth_routes:
        print("\n🔐 Authentication ({}):".format(len(auth_routes)))
        for route in auth_routes:
            print(f"   {route['method']:6} {route['path']}")
    
    # عرض Diagnosis endpoints
    if diagnosis_routes:
        print("\n🩺 Diagnosis ({}):".format(len(diagnosis_routes)))
        for route in diagnosis_routes:
            print(f"   {route['method']:6} {route['path']}")
    
    # عرض Other endpoints
    if other_routes:
        print("\n⚠️  Other Routes ({}):".format(len(other_routes)))
        for route in other_routes:
            print(f"   {route['method']:6} {route['path']}")
    
    print()
    print("=" * 70)
    
    # 2. التحقق من المطابقة مع القائمة المطلوبة
    print("\n✅ Verification Against Expected Routes:")
    print("-" * 70)
    
    all_good = True
    
    # التحقق من وجود جميع الـroutes المطلوبة
    missing_routes = EXPECTED_ROUTES - actual_routes
    if missing_routes:
        all_good = False
        print("\n❌ Missing Required Routes:")
        for method, path in sorted(missing_routes):
            print(f"   {method:6} {path}")
    else:
        print("\n✅ All required routes are present")
    
    # التحقق من عدم وجود routes محظورة
    forbidden_found = []
    for route in api_routes:
        for forbidden_path in FORBIDDEN_ROUTES:
            if forbidden_path in route["path"]:
                forbidden_found.append(route)
                all_good = False
    
    if forbidden_found:
        print("\n❌ Forbidden/Deprecated Routes Found:")
        for route in forbidden_found:
            print(f"   {route['method']:6} {route['path']}")
    else:
        print("✅ No deprecated routes found")
    
    # التحقق من routes إضافية غير متوقعة
    api_route_tuples = {(r["method"], r["path"]) for r in api_routes}
    extra_routes = api_route_tuples - EXPECTED_ROUTES
    
    if extra_routes:
        print("\n⚠️  Extra Routes (not in expected list):")
        for method, path in sorted(extra_routes):
            print(f"   {method:6} {path}")
    
    print()
    print("=" * 70)
    
    # 3. النتيجة النهائية
    print("\n📊 Final Status:")
    print("-" * 70)
    
    total_api_routes = len(api_routes)
    expected_count = len(EXPECTED_ROUTES)
    
    print(f"Total API Routes: {total_api_routes}")
    print(f"Expected Routes: {expected_count}")
    print(f"Status: {'✅ PASS' if all_good and total_api_routes == expected_count else '❌ FAIL'}")
    
    if all_good and total_api_routes == expected_count:
        print("\n🎉 API is clean and matches specifications!")
    else:
        print("\n⚠️  API needs cleanup - see issues above")
    
    print()
    print("=" * 70)
    
    return all_good and total_api_routes == expected_count


if __name__ == "__main__":
    try:
        success = audit_routes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Error during audit: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
