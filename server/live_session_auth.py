###############################################################################
#  Bind RTC sessionid to the logged-in user who created it via /app offer.
###############################################################################

from server.platform_auth import json_error


def bind_live_session(app, user_id, sessionid: str):
    live = app.setdefault("user_rtc_sessions", {})
    owners = app.setdefault("live_session_owners", {})
    old = live.get(user_id)
    if old:
        owners.pop(old, None)
    live[user_id] = sessionid
    owners[sessionid] = user_id


def unbind_live_session(app, user_id):
    live = app.setdefault("user_rtc_sessions", {})
    owners = app.setdefault("live_session_owners", {})
    sid = live.pop(user_id, None)
    if sid:
        owners.pop(sid, None)
    return sid


def deny_live_drive(request, sessionid):
    """None if the session is anonymous or owned by the current user."""
    sid = "" if sessionid is None else str(sessionid)
    owners = request.app.get("live_session_owners") or {}
    owner_id = owners.get(sid)
    if owner_id is None:
        return None
    user = request.get("user")
    if not user:
        return json_error("未登录", status=401)
    if user["id"] != owner_id:
        return json_error("无权操作该会话", status=403)
    return None
