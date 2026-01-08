# -*- coding: utf-8 -*-
"""
VisionCraftAI - 管理者ダッシュボード

収益・ユーザー・使用量のメトリクスを集計・提供します。
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .schemas import (
    RevenueMetrics,
    UserMetrics,
    UsageMetrics,
    PlanDistribution,
    DashboardSummary,
    UserListItem,
    RevenueChartData,
    UsageChartData,
    SystemHealth,
)

logger = logging.getLogger(__name__)


class AdminDashboard:
    """管理者ダッシュボードクラス"""

    # プラン別月額料金（USD）
    PLAN_PRICES = {
        "free": 0.0,
        "basic": 9.99,
        "pro": 29.99,
        "enterprise": 99.99,
    }

    def __init__(self, data_dir: Optional[Path] = None):
        """
        管理者ダッシュボード初期化

        Args:
            data_dir: データディレクトリ
        """
        self.data_dir = data_dir or Path("data")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # データファイルパス
        self.api_keys_file = self.data_dir / "api_keys.json"
        self.usage_file = self.data_dir / "usage_records.json"
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.credits_file = self.data_dir / "credits.json"
        self.contacts_file = self.data_dir / "contacts.json"

    def _load_json(self, file_path: Path) -> dict | list:
        """JSONファイルを読み込む"""
        if not file_path.exists():
            return {} if file_path.name in ["api_keys.json", "subscriptions.json", "credits.json"] else []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"JSONファイル読み込みエラー: {file_path}: {e}")
            return {} if file_path.name in ["api_keys.json", "subscriptions.json", "credits.json"] else []

    def get_revenue_metrics(self) -> RevenueMetrics:
        """収益メトリクスを取得"""
        subscriptions = self._load_json(self.subscriptions_file)
        credits_data = self._load_json(self.credits_file)
        api_keys = self._load_json(self.api_keys_file)

        now = datetime.now()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # サブスクリプション収益計算
        subscription_revenue = 0.0
        monthly_subscription_revenue = 0.0
        daily_subscription_revenue = 0.0
        active_mrr = 0.0

        for sub_data in subscriptions.values() if isinstance(subscriptions, dict) else subscriptions:
            if isinstance(sub_data, dict):
                plan = sub_data.get("plan", "free")
                status = sub_data.get("status", "")
                created_str = sub_data.get("created_at", "")

                price = self.PLAN_PRICES.get(plan, 0.0)

                if status == "active":
                    active_mrr += price

                # 作成日が今月以降ならカウント
                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        if created >= month_start:
                            monthly_subscription_revenue += price
                        if created.date() == today:
                            daily_subscription_revenue += price
                        subscription_revenue += price
                    except Exception:
                        pass

        # クレジット収益計算
        credit_revenue = 0.0
        monthly_credit_revenue = 0.0
        daily_credit_revenue = 0.0

        for credit_data in credits_data.values() if isinstance(credits_data, dict) else credits_data:
            if isinstance(credit_data, dict):
                transactions = credit_data.get("transactions", [])
                for tx in transactions:
                    if tx.get("type") == "purchase":
                        amount = tx.get("amount", 0)
                        # クレジット数から収益を推定（1クレジット≒$0.50）
                        tx_revenue = amount * 0.5
                        credit_revenue += tx_revenue

                        tx_date_str = tx.get("timestamp", "")
                        if tx_date_str:
                            try:
                                tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                                if tx_date >= month_start:
                                    monthly_credit_revenue += tx_revenue
                                if tx_date.date() == today:
                                    daily_credit_revenue += tx_revenue
                            except Exception:
                                pass

        total_revenue = subscription_revenue + credit_revenue
        monthly_revenue = monthly_subscription_revenue + monthly_credit_revenue
        daily_revenue = daily_subscription_revenue + daily_credit_revenue

        return RevenueMetrics(
            total_revenue=round(total_revenue, 2),
            monthly_revenue=round(monthly_revenue, 2),
            daily_revenue=round(daily_revenue, 2),
            subscription_revenue=round(subscription_revenue, 2),
            credit_revenue=round(credit_revenue, 2),
            mrr=round(active_mrr, 2),
            arr=round(active_mrr * 12, 2),
        )

    def get_user_metrics(self) -> UserMetrics:
        """ユーザーメトリクスを取得"""
        api_keys = self._load_json(self.api_keys_file)
        subscriptions = self._load_json(self.subscriptions_file)

        now = datetime.now()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        thirty_days_ago = now - timedelta(days=30)

        total_users = 0
        active_users = 0
        new_users_today = 0
        new_users_month = 0
        paying_users = 0
        free_users = 0

        for key_id, key_data in api_keys.items() if isinstance(api_keys, dict) else enumerate(api_keys):
            if isinstance(key_data, dict):
                total_users += 1

                tier = key_data.get("tier", "free")
                if tier in ["basic", "pro", "enterprise"]:
                    paying_users += 1
                else:
                    free_users += 1

                created_str = key_data.get("created_at", "")
                last_used_str = key_data.get("last_used", "")

                if created_str:
                    try:
                        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        if created >= month_start:
                            new_users_month += 1
                        if created.date() == today:
                            new_users_today += 1
                    except Exception:
                        pass

                if last_used_str:
                    try:
                        last_used = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
                        if last_used >= thirty_days_ago:
                            active_users += 1
                    except Exception:
                        pass

        # 解約率（仮の計算: 過去30日で非アクティブになったユーザーの割合）
        churn_rate = 0.0
        if total_users > 0:
            churn_rate = ((total_users - active_users) / total_users) * 100

        return UserMetrics(
            total_users=total_users,
            active_users=active_users,
            new_users_today=new_users_today,
            new_users_month=new_users_month,
            paying_users=paying_users,
            free_users=free_users,
            churn_rate=round(churn_rate, 2),
        )

    def get_usage_metrics(self) -> UsageMetrics:
        """使用量メトリクスを取得"""
        usage_records = self._load_json(self.usage_file)
        api_keys = self._load_json(self.api_keys_file)

        now = datetime.now()
        today = now.date()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        total_generations = 0
        monthly_generations = 0
        daily_generations = 0
        api_calls_today = 0
        total_errors = 0
        daily_errors = 0

        records = usage_records if isinstance(usage_records, list) else []

        for record in records:
            if isinstance(record, dict):
                total_generations += 1

                timestamp_str = record.get("timestamp", "")
                success = record.get("success", True)

                if not success:
                    total_errors += 1

                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp >= month_start:
                            monthly_generations += 1
                        if timestamp.date() == today:
                            daily_generations += 1
                            api_calls_today += 1
                            if not success:
                                daily_errors += 1
                    except Exception:
                        pass

        # ユーザーあたり平均生成回数
        total_users = len(api_keys) if isinstance(api_keys, dict) else 0
        average_per_user = 0.0
        if total_users > 0:
            average_per_user = total_generations / total_users

        # エラー率
        error_rate = 0.0
        if total_generations > 0:
            error_rate = (total_errors / total_generations) * 100

        return UsageMetrics(
            total_generations=total_generations,
            monthly_generations=monthly_generations,
            daily_generations=daily_generations,
            average_per_user=round(average_per_user, 2),
            api_calls_today=api_calls_today,
            error_rate=round(error_rate, 2),
        )

    def get_plan_distribution(self) -> PlanDistribution:
        """プラン分布を取得"""
        api_keys = self._load_json(self.api_keys_file)

        distribution = {
            "free": 0,
            "basic": 0,
            "pro": 0,
            "enterprise": 0,
        }

        for key_data in api_keys.values() if isinstance(api_keys, dict) else api_keys:
            if isinstance(key_data, dict):
                tier = key_data.get("tier", "free")
                if tier in distribution:
                    distribution[tier] += 1

        return PlanDistribution(**distribution)

    def get_dashboard_summary(self) -> DashboardSummary:
        """ダッシュボード概要を取得"""
        return DashboardSummary(
            revenue=self.get_revenue_metrics(),
            users=self.get_user_metrics(),
            usage=self.get_usage_metrics(),
            plan_distribution=self.get_plan_distribution(),
            last_updated=datetime.now(),
        )

    def get_user_list(self, page: int = 1, per_page: int = 20, plan_filter: Optional[str] = None) -> dict:
        """ユーザー一覧を取得"""
        api_keys = self._load_json(self.api_keys_file)
        subscriptions = self._load_json(self.subscriptions_file)
        usage_records = self._load_json(self.usage_file)

        # ユーザーごとの使用量を集計
        usage_by_user: dict[str, int] = {}
        for record in usage_records if isinstance(usage_records, list) else []:
            if isinstance(record, dict):
                key_id = record.get("key_id", "")
                if key_id:
                    usage_by_user[key_id] = usage_by_user.get(key_id, 0) + 1

        users = []
        for key_id, key_data in api_keys.items() if isinstance(api_keys, dict) else []:
            if isinstance(key_data, dict):
                tier = key_data.get("tier", "free")

                # フィルター適用
                if plan_filter and tier != plan_filter:
                    continue

                created_str = key_data.get("created_at", "")
                last_used_str = key_data.get("last_used", "")

                created_at = datetime.now()
                last_active = None

                if created_str:
                    try:
                        created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                if last_used_str:
                    try:
                        last_active = datetime.fromisoformat(last_used_str.replace("Z", "+00:00"))
                    except Exception:
                        pass

                # 使用量と推定支出
                total_gen = usage_by_user.get(key_id, 0)
                total_spent = self.PLAN_PRICES.get(tier, 0.0)

                users.append(UserListItem(
                    user_id=key_id,
                    email=key_data.get("email"),
                    plan=tier,
                    created_at=created_at,
                    last_active=last_active,
                    total_generations=total_gen,
                    total_spent=total_spent,
                    is_active=key_data.get("is_active", True),
                ))

        # ソート（作成日降順）
        users.sort(key=lambda u: u.created_at, reverse=True)

        # ページネーション
        total = len(users)
        total_pages = (total + per_page - 1) // per_page
        start = (page - 1) * per_page
        end = start + per_page

        return {
            "users": users[start:end],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
        }

    def get_revenue_chart_data(self, days: int = 30) -> list[RevenueChartData]:
        """収益チャートデータを取得"""
        subscriptions = self._load_json(self.subscriptions_file)
        credits_data = self._load_json(self.credits_file)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # 日付ごとのデータを初期化
        chart_data: dict[str, dict[str, float]] = {}
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            chart_data[date_str] = {"revenue": 0.0, "subscriptions": 0.0, "credits": 0.0}
            current += timedelta(days=1)

        # サブスクリプション収益を日付ごとに集計
        for sub_data in subscriptions.values() if isinstance(subscriptions, dict) else subscriptions:
            if isinstance(sub_data, dict):
                created_str = sub_data.get("created_at", "")
                plan = sub_data.get("plan", "free")
                price = self.PLAN_PRICES.get(plan, 0.0)

                if created_str and price > 0:
                    try:
                        created = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                        date_str = created.date().isoformat()
                        if date_str in chart_data:
                            chart_data[date_str]["subscriptions"] += price
                            chart_data[date_str]["revenue"] += price
                    except Exception:
                        pass

        # クレジット収益を日付ごとに集計
        for credit_data in credits_data.values() if isinstance(credits_data, dict) else credits_data:
            if isinstance(credit_data, dict):
                transactions = credit_data.get("transactions", [])
                for tx in transactions:
                    if tx.get("type") == "purchase":
                        amount = tx.get("amount", 0)
                        tx_revenue = amount * 0.5
                        tx_date_str = tx.get("timestamp", "")

                        if tx_date_str:
                            try:
                                tx_date = datetime.fromisoformat(tx_date_str.replace("Z", "+00:00"))
                                date_str = tx_date.date().isoformat()
                                if date_str in chart_data:
                                    chart_data[date_str]["credits"] += tx_revenue
                                    chart_data[date_str]["revenue"] += tx_revenue
                            except Exception:
                                pass

        # リストに変換
        result = []
        for date_str in sorted(chart_data.keys()):
            data = chart_data[date_str]
            result.append(RevenueChartData(
                date=date_str,
                revenue=round(data["revenue"], 2),
                subscriptions=round(data["subscriptions"], 2),
                credits=round(data["credits"], 2),
            ))

        return result

    def get_usage_chart_data(self, days: int = 30) -> list[UsageChartData]:
        """使用量チャートデータを取得"""
        usage_records = self._load_json(self.usage_file)

        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days - 1)

        # 日付ごとのデータを初期化
        chart_data: dict[str, dict[str, int]] = {}
        current = start_date
        while current <= end_date:
            date_str = current.isoformat()
            chart_data[date_str] = {"generations": 0, "api_calls": 0, "errors": 0}
            current += timedelta(days=1)

        # 使用量を日付ごとに集計
        records = usage_records if isinstance(usage_records, list) else []
        for record in records:
            if isinstance(record, dict):
                timestamp_str = record.get("timestamp", "")
                success = record.get("success", True)

                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        date_str = timestamp.date().isoformat()
                        if date_str in chart_data:
                            chart_data[date_str]["generations"] += 1
                            chart_data[date_str]["api_calls"] += 1
                            if not success:
                                chart_data[date_str]["errors"] += 1
                    except Exception:
                        pass

        # リストに変換
        result = []
        for date_str in sorted(chart_data.keys()):
            data = chart_data[date_str]
            result.append(UsageChartData(
                date=date_str,
                generations=data["generations"],
                api_calls=data["api_calls"],
                errors=data["errors"],
            ))

        return result

    def get_system_health(self) -> SystemHealth:
        """システムヘルス情報を取得"""
        usage_records = self._load_json(self.usage_file)

        now = datetime.now()
        twenty_four_hours_ago = now - timedelta(hours=24)

        error_count_24h = 0
        total_response_time = 0.0
        response_count = 0

        records = usage_records if isinstance(usage_records, list) else []
        for record in records:
            if isinstance(record, dict):
                timestamp_str = record.get("timestamp", "")
                success = record.get("success", True)
                response_time = record.get("response_time_ms", 0)

                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp >= twenty_four_hours_ago:
                            if not success:
                                error_count_24h += 1
                            if response_time > 0:
                                total_response_time += response_time
                                response_count += 1
                    except Exception:
                        pass

        avg_response_time = 0.0
        if response_count > 0:
            avg_response_time = total_response_time / response_count

        # ステータス判定（仮: エラー率で判定）
        api_status = "healthy"
        if error_count_24h > 100:
            api_status = "degraded"
        elif error_count_24h > 500:
            api_status = "down"

        return SystemHealth(
            api_status=api_status,
            database_status="healthy",  # JSONベースのため常にhealthy
            gemini_api_status="unknown",  # 実際のAPI呼び出しで確認が必要
            stripe_status="unknown",  # 実際のAPI呼び出しで確認が必要
            error_count_24h=error_count_24h,
            avg_response_time_ms=round(avg_response_time, 2),
        )

    def get_contact_stats(self) -> dict:
        """お問い合わせ統計を取得"""
        contacts = self._load_json(self.contacts_file)

        now = datetime.now()
        today = now.date()
        week_ago = now - timedelta(days=7)

        total = 0
        today_count = 0
        week_count = 0
        by_category: dict[str, int] = {}
        unread = 0

        records = contacts if isinstance(contacts, list) else []
        for record in records:
            if isinstance(record, dict):
                total += 1
                category = record.get("category", "other")
                by_category[category] = by_category.get(category, 0) + 1

                if not record.get("read", False):
                    unread += 1

                timestamp_str = record.get("timestamp", "")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                        if timestamp.date() == today:
                            today_count += 1
                        if timestamp >= week_ago:
                            week_count += 1
                    except Exception:
                        pass

        return {
            "total": total,
            "today": today_count,
            "this_week": week_count,
            "unread": unread,
            "by_category": by_category,
        }
