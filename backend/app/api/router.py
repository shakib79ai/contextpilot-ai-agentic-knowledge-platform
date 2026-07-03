from fastapi import APIRouter

from app.api import routes_admin, routes_auth, routes_documents, routes_feedback, routes_query, routes_review

api_router = APIRouter()
api_router.include_router(routes_auth.router)
api_router.include_router(routes_documents.router)
api_router.include_router(routes_query.router)
api_router.include_router(routes_feedback.router)
api_router.include_router(routes_review.router)
api_router.include_router(routes_admin.router)
