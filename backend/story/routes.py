from flask import Blueprint, jsonify, request

from .service import ServiceError, StoryService

_service = None


def get_service():
    global _service
    if _service is None:
        _service = StoryService()
    return _service


def create_blueprint(service=None):
    bp = Blueprint("story", __name__)

    def svc():
        return service or get_service()

    def fail(e):
        return jsonify({"error": e.message, "code": e.code}), e.status

    @bp.route("/api/story/generate", methods=["POST"])
    def generate():
        d = request.get_json(silent=True) or {}
        try:
            return jsonify(svc().generate_story(d.get("article"), d.get("audience"), d.get("style", "everyday"), bool(d.get("fresh")), d.get("language", "en")))
        except ServiceError as e:
            return fail(e)

    @bp.route("/api/story/ask", methods=["POST"])
    def ask():
        d = request.get_json(silent=True) or {}
        try:
            return jsonify(svc().ask(d.get("article"), d.get("audience"), d.get("question"), d.get("character"), d.get("scene_summary", ""), d.get("history"), d.get("language", "en")))
        except ServiceError as e:
            return fail(e)

    return bp
