"""
سكريبت تشخيص مشاكل تشغيل السيرفر
Diagnose server startup issues
"""
import sys
import os
from pathlib import Path

print("=" * 70)
print("🔍 تشخيص مشاكل تشغيل السيرفر")
print("🔍 Server Startup Diagnostics")
print("=" * 70)
print()

# 1. Python Version
print("1️⃣  Python Version:")
print(f"   Version: {sys.version}")
print(f"   Executable: {sys.executable}")
print()

# 2. Current Directory
print("2️⃣  Current Directory:")
print(f"   {os.getcwd()}")
print()

# 3. Check Virtual Environment
print("3️⃣  Virtual Environment:")
in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
if in_venv:
    print("   ✅ Running in virtual environment")
else:
    print("   ⚠️  NOT in virtual environment")
    print("   Run: venv\\Scripts\\activate (Windows) or source venv/bin/activate (Linux/Mac)")
print()

# 4. Check Required Files
print("4️⃣  Required Files:")
required_files = [
    ".env.example",
    "requirements.txt",
    "app/main.py",
    "app/__init__.py",
    "alembic.ini"
]

for file in required_files:
    exists = Path(file).exists()
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")
print()

# 5. Check ML Model
print("5️⃣  ML Model:")
model_path = "app/infrastructure/ml/weights/skin_efficientnet_b4_9.pth"
if Path(model_path).exists():
    size_mb = Path(model_path).stat().st_size / (1024 * 1024)
    print(f"   ✅ Model exists: {size_mb:.2f} MB")
else:
    print(f"   ❌ Model NOT found at: {model_path}")
print()

# 6. Check .env file
print("6️⃣  Environment File:")
if Path(".env").exists():
    print("   ✅ .env file exists")
else:
    print("   ⚠️  .env file NOT found")
    print("   Create it: cp .env.example .env")
print()

# 7. Check Database
print("7️⃣  Database:")
if Path("skin_analysis.db").exists():
    print("   ✅ Database file exists")
else:
    print("   ⚠️  Database NOT found")
    print("   Run: alembic upgrade head")
print()

# 8. Try importing FastAPI
print("8️⃣  Dependencies Check:")
try:
    import fastapi
    print(f"   ✅ FastAPI: {fastapi.__version__}")
except ImportError as e:
    print(f"   ❌ FastAPI not installed: {e}")
    print("   Run: pip install -r requirements.txt")

try:
    import sqlalchemy
    print(f"   ✅ SQLAlchemy: {sqlalchemy.__version__}")
except ImportError as e:
    print(f"   ❌ SQLAlchemy not installed: {e}")

try:
    import torch
    print(f"   ✅ PyTorch: {torch.__version__}")
except ImportError as e:
    print(f"   ❌ PyTorch not installed: {e}")

try:
    import uvicorn
    print(f"   ✅ Uvicorn: {uvicorn.__version__}")
except ImportError as e:
    print(f"   ❌ Uvicorn not installed: {e}")
print()

# 9. Try importing app
print("9️⃣  Application Import:")
try:
    sys.path.insert(0, os.getcwd())
    from app.main import app as fastapi_app
    print("   ✅ App imported successfully")
except Exception as e:
    print(f"   ❌ Failed to import app: {e}")
    print(f"   Error type: {type(e).__name__}")
    import traceback
    print("\n   Full error:")
    traceback.print_exc()
print()

# 10. Port Check
print("🔟 Port Check:")
try:
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('localhost', 8000))
    sock.close()
    
    if result == 0:
        print("   ⚠️  Port 8000 is already in use")
        print("   Another server might be running")
        print("   Solution: Stop other server or use different port")
    else:
        print("   ✅ Port 8000 is available")
except Exception as e:
    print(f"   ⚠️  Could not check port: {e}")
print()

print("=" * 70)
print("📋 Summary:")
print("=" * 70)

# Summary
issues = []

if not in_venv:
    issues.append("Virtual environment not activated")

if not Path(".env").exists():
    issues.append(".env file missing")

if not Path("skin_analysis.db").exists():
    issues.append("Database not initialized")

if not Path(model_path).exists():
    issues.append("ML model file missing")

if issues:
    print("\n⚠️  Issues Found:")
    for i, issue in enumerate(issues, 1):
        print(f"   {i}. {issue}")
    print("\n📝 Solutions:")
    if "Virtual environment not activated" in issues:
        print("   • Activate venv: venv\\Scripts\\activate")
    if ".env file missing" in issues:
        print("   • Create .env: copy .env.example .env")
    if "Database not initialized" in issues:
        print("   • Initialize DB: alembic upgrade head")
    if "ML model file missing" in issues:
        print("   • Add model file to: app/infrastructure/ml/weights/")
else:
    print("\n✅ No major issues found!")
    print("\n🚀 Try running:")
    print("   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")

print()
print("=" * 70)
