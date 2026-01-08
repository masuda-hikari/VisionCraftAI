# -*- coding: utf-8 -*-
"""
VisionCraftAI - 管理者モジュール
"""

from .routes import router as admin_router
from .dashboard import AdminDashboard

__all__ = ["admin_router", "AdminDashboard"]
