# -*- coding: utf-8 -*-
"""
VisionCraftAI - オンボーディングモデル定義

新規ユーザー導入、無料トライアル、チェックリストのデータモデル。
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class OnboardingStep(str, Enum):
    """オンボーディングステップ"""
    WELCOME = "welcome"                      # ウェルカム画面
    CREATE_API_KEY = "create_api_key"        # APIキー作成
    FIRST_GENERATION = "first_generation"   # 初回画像生成
    EXPLORE_FEATURES = "explore_features"   # 機能探索
    UPGRADE_PROMPT = "upgrade_prompt"        # アップグレード促進
    COMPLETED = "completed"                  # 完了


class TrialStatus(str, Enum):
    """トライアルステータス"""
    ACTIVE = "active"              # アクティブ
    EXPIRED = "expired"            # 期限切れ
    CONVERTED = "converted"        # 有料転換
    CANCELLED = "cancelled"        # キャンセル


@dataclass
class OnboardingProgress:
    """オンボーディング進捗"""
    user_id: str
    api_key_id: str = ""

    # 現在のステップ
    current_step: OnboardingStep = OnboardingStep.WELCOME

    # 完了済みステップ
    completed_steps: list[str] = field(default_factory=list)

    # チェックリスト項目の完了状態
    checklist: dict[str, bool] = field(default_factory=lambda: {
        "api_key_created": False,
        "first_image_generated": False,
        "prompt_enhanced": False,
        "image_downloaded": False,
        "image_shared": False,
        "referral_code_created": False,
        "dashboard_visited": False,
        "pricing_viewed": False,
    })

    # 日時
    started_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    completed_at: Optional[str] = None
    last_activity_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )

    def complete_step(self, step: OnboardingStep) -> None:
        """ステップを完了としてマーク"""
        if step.value not in self.completed_steps:
            self.completed_steps.append(step.value)
        self.last_activity_at = datetime.now().isoformat()

        # 次のステップに進む
        step_order = list(OnboardingStep)
        current_idx = step_order.index(step)
        if current_idx + 1 < len(step_order):
            self.current_step = step_order[current_idx + 1]
        else:
            self.current_step = OnboardingStep.COMPLETED
            self.completed_at = datetime.now().isoformat()

    def complete_checklist_item(self, item: str) -> bool:
        """チェックリスト項目を完了"""
        if item in self.checklist:
            self.checklist[item] = True
            self.last_activity_at = datetime.now().isoformat()
            return True
        return False

    def get_completion_rate(self) -> float:
        """完了率を計算（0.0-1.0）"""
        total = len(self.checklist)
        completed = sum(1 for v in self.checklist.values() if v)
        return completed / total if total > 0 else 0.0

    def is_completed(self) -> bool:
        """オンボーディング完了チェック"""
        return self.current_step == OnboardingStep.COMPLETED

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "user_id": self.user_id,
            "api_key_id": self.api_key_id,
            "current_step": self.current_step.value,
            "completed_steps": self.completed_steps,
            "checklist": self.checklist,
            "completion_rate": self.get_completion_rate(),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "last_activity_at": self.last_activity_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "OnboardingProgress":
        """辞書からインスタンスを作成"""
        progress = cls(
            user_id=data["user_id"],
            api_key_id=data.get("api_key_id", ""),
            current_step=OnboardingStep(data.get("current_step", "welcome")),
            completed_steps=data.get("completed_steps", []),
            started_at=data.get("started_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            last_activity_at=data.get("last_activity_at", datetime.now().isoformat()),
        )
        progress.checklist = data.get("checklist", progress.checklist)
        return progress


@dataclass
class FreeTrial:
    """無料トライアル"""
    trial_id: str
    user_id: str
    api_key_id: str = ""

    # トライアル設定
    plan_id: str = "pro"             # トライアル対象プラン
    duration_days: int = 7           # トライアル期間（日）
    credits_granted: int = 20        # 付与クレジット数

    # ステータス
    status: TrialStatus = TrialStatus.ACTIVE

    # 期間
    starts_at: str = field(
        default_factory=lambda: datetime.now().isoformat()
    )
    expires_at: str = field(
        default_factory=lambda: (datetime.now() + timedelta(days=7)).isoformat()
    )

    # 使用状況
    credits_used: int = 0
    images_generated: int = 0

    # コンバージョン
    converted_at: Optional[str] = None
    converted_plan: Optional[str] = None

    def is_active(self) -> bool:
        """トライアルがアクティブかチェック"""
        if self.status != TrialStatus.ACTIVE:
            return False
        if datetime.fromisoformat(self.expires_at) < datetime.now():
            return False
        return True

    def get_remaining_days(self) -> int:
        """残り日数を取得"""
        if not self.is_active():
            return 0
        expires = datetime.fromisoformat(self.expires_at)
        remaining = expires - datetime.now()
        return max(0, remaining.days)

    def get_remaining_credits(self) -> int:
        """残りクレジットを取得"""
        return max(0, self.credits_granted - self.credits_used)

    def use_credits(self, amount: int = 1) -> bool:
        """クレジットを使用"""
        if not self.is_active():
            return False
        if self.credits_used + amount > self.credits_granted:
            return False
        self.credits_used += amount
        self.images_generated += 1
        return True

    def convert(self, plan_id: str) -> None:
        """有料プランに転換"""
        self.status = TrialStatus.CONVERTED
        self.converted_at = datetime.now().isoformat()
        self.converted_plan = plan_id

    def expire(self) -> None:
        """トライアルを期限切れにする"""
        self.status = TrialStatus.EXPIRED

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "trial_id": self.trial_id,
            "user_id": self.user_id,
            "api_key_id": self.api_key_id,
            "plan_id": self.plan_id,
            "duration_days": self.duration_days,
            "credits_granted": self.credits_granted,
            "status": self.status.value,
            "starts_at": self.starts_at,
            "expires_at": self.expires_at,
            "remaining_days": self.get_remaining_days(),
            "remaining_credits": self.get_remaining_credits(),
            "credits_used": self.credits_used,
            "images_generated": self.images_generated,
            "converted_at": self.converted_at,
            "converted_plan": self.converted_plan,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FreeTrial":
        """辞書からインスタンスを作成"""
        return cls(
            trial_id=data["trial_id"],
            user_id=data["user_id"],
            api_key_id=data.get("api_key_id", ""),
            plan_id=data.get("plan_id", "pro"),
            duration_days=data.get("duration_days", 7),
            credits_granted=data.get("credits_granted", 20),
            status=TrialStatus(data.get("status", "active")),
            starts_at=data.get("starts_at", datetime.now().isoformat()),
            expires_at=data.get("expires_at", (datetime.now() + timedelta(days=7)).isoformat()),
            credits_used=data.get("credits_used", 0),
            images_generated=data.get("images_generated", 0),
            converted_at=data.get("converted_at"),
            converted_plan=data.get("converted_plan"),
        )


# トライアル設定
TRIAL_CONFIGS = {
    "default": {
        "plan_id": "pro",
        "duration_days": 7,
        "credits_granted": 20,
    },
    "extended": {
        "plan_id": "pro",
        "duration_days": 14,
        "credits_granted": 50,
    },
    "premium": {
        "plan_id": "enterprise",
        "duration_days": 30,
        "credits_granted": 100,
    },
}

# オンボーディングステップのヘルプテキスト
ONBOARDING_HELP = {
    OnboardingStep.WELCOME: {
        "title": "VisionCraftAIへようこそ！",
        "description": "AI画像生成プラットフォームをご利用いただきありがとうございます。",
        "action": "まずはAPIキーを作成しましょう",
    },
    OnboardingStep.CREATE_API_KEY: {
        "title": "APIキーを作成",
        "description": "APIキーを使って画像生成を開始できます。",
        "action": "「APIキー作成」ボタンをクリック",
    },
    OnboardingStep.FIRST_GENERATION: {
        "title": "初めての画像生成",
        "description": "プロンプトを入力して、AI画像を生成してみましょう。",
        "action": "好きなプロンプトを入力して「生成」をクリック",
    },
    OnboardingStep.EXPLORE_FEATURES: {
        "title": "機能を探索",
        "description": "バッチ処理、画像編集、共有機能など様々な機能があります。",
        "action": "ダッシュボードで機能を確認",
    },
    OnboardingStep.UPGRADE_PROMPT: {
        "title": "もっと活用しませんか？",
        "description": "有料プランでより多くの画像を生成できます。",
        "action": "プランを確認",
    },
    OnboardingStep.COMPLETED: {
        "title": "オンボーディング完了！",
        "description": "基本的な使い方をマスターしました。",
        "action": "さらに探索を続けましょう",
    },
}
