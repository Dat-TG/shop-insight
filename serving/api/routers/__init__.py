# serving/api/routers package — one module per BR.
#
# Pattern for a new BR (e.g., BR3):
#   1. Create serving/api/routers/br3.py
#   2. Define router = APIRouter(prefix="/api/br3", tags=["BR3"])
#   3. Add GET endpoints that return ApiResponse
#   4. Import and include in serving/api/main.py
