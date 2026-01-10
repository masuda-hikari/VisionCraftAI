# -*- coding: utf-8 -*-
"""
VisionCraftAI - A/Bテスト・分析マネージャー

A/Bテストの管理とユーザー行動分析機能を提供します。
"""

import hashlib
import logging
import random
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional

from src.api.analytics.models import (
    ABTest,
    ABTestAssignment,
    ABTestStatus,
    ABTestVariant,
    AnalyticsEvent,
    ConversionGoal,
    ConversionGoalType,
    EventType,
)

logger = logging.getLogger(__name__)


class ABTestManager:
    """A/Bテストマネージャー"""

    def __init__(self):
        """初期化"""
        # インメモリストレージ（本番ではDBを使用）
        self._tests: dict[str, ABTest] = {}
        self._assignments: dict[str, dict[str, ABTestAssignment]] = defaultdict(dict)
        # user_id -> {test_id -> assignment}

    def create_test(
        self,
        name: str,
        description: str = "",
        goal_type: ConversionGoalType = ConversionGoalType.SUBSCRIPTION,
        goal_event: str = "",
        created_by: str = "",
    ) -> ABTest:
        """A/Bテストを作成"""
        test = ABTest.create(
            name=name,
            description=description,
            goal_type=goal_type,
            goal_event=goal_event,
            created_by=created_by,
        )
        self._tests[test.id] = test
        logger.info(f"A/Bテスト作成: {test.id} ({test.name})")
        return test

    def get_test(self, test_id: str) -> Optional[ABTest]:
        """A/Bテストを取得"""
        return self._tests.get(test_id)

    def list_tests(
        self,
        status: Optional[ABTestStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ABTest]:
        """A/Bテスト一覧を取得"""
        tests = list(self._tests.values())

        if status:
            tests = [t for t in tests if t.status == status]

        # 作成日時降順でソート
        tests.sort(key=lambda t: t.created_at, reverse=True)

        return tests[offset : offset + limit]

    def add_variant(
        self,
        test_id: str,
        name: str,
        description: str = "",
        weight: float = 50.0,
        config: Optional[dict] = None,
    ) -> Optional[ABTestVariant]:
        """バリアントを追加"""
        test = self.get_test(test_id)
        if not test:
            return None

        if test.status != ABTestStatus.DRAFT:
            raise ValueError("ドラフト状態のテストにのみバリアントを追加できます")

        variant = test.add_variant(
            name=name,
            description=description,
            weight=weight,
            config=config,
        )
        logger.info(f"バリアント追加: {variant.id} -> {test_id}")
        return variant

    def start_test(self, test_id: str) -> bool:
        """テストを開始"""
        test = self.get_test(test_id)
        if not test:
            return False

        try:
            test.start()
            logger.info(f"A/Bテスト開始: {test_id}")
            return True
        except ValueError as e:
            logger.error(f"A/Bテスト開始エラー: {e}")
            return False

    def pause_test(self, test_id: str) -> bool:
        """テストを一時停止"""
        test = self.get_test(test_id)
        if not test:
            return False

        test.pause()
        logger.info(f"A/Bテスト一時停止: {test_id}")
        return True

    def resume_test(self, test_id: str) -> bool:
        """テストを再開"""
        test = self.get_test(test_id)
        if not test:
            return False

        test.resume()
        logger.info(f"A/Bテスト再開: {test_id}")
        return True

    def complete_test(self, test_id: str) -> bool:
        """テストを完了"""
        test = self.get_test(test_id)
        if not test:
            return False

        test.complete()
        logger.info(f"A/Bテスト完了: {test_id}")
        return True

    def assign_variant(
        self,
        test_id: str,
        user_id: str,
        force_variant_id: Optional[str] = None,
    ) -> Optional[ABTestAssignment]:
        """
        ユーザーにバリアントを割り当て

        Args:
            test_id: テストID
            user_id: ユーザーID
            force_variant_id: 強制的に割り当てるバリアントID（デバッグ用）

        Returns:
            割り当て結果
        """
        test = self.get_test(test_id)
        if not test or not test.is_active:
            return None

        # 既存の割り当てをチェック
        existing = self._assignments.get(user_id, {}).get(test_id)
        if existing:
            return existing

        # バリアント選択
        variant = self._select_variant(test, user_id, force_variant_id)
        if not variant:
            return None

        # 割り当て作成
        assignment = ABTestAssignment(
            user_id=user_id,
            test_id=test_id,
            variant_id=variant.id,
        )

        # 保存
        self._assignments[user_id][test_id] = assignment

        # インプレッション記録
        variant.impressions += 1

        logger.debug(f"バリアント割り当て: {user_id} -> {variant.id} ({test_id})")
        return assignment

    def _select_variant(
        self,
        test: ABTest,
        user_id: str,
        force_variant_id: Optional[str] = None,
    ) -> Optional[ABTestVariant]:
        """
        バリアントを選択

        一貫性のある割り当てのために、ユーザーIDをハッシュして決定論的に選択します。
        """
        if not test.variants:
            return None

        # 強制指定がある場合
        if force_variant_id:
            for v in test.variants:
                if v.id == force_variant_id:
                    return v
            return None

        # ユーザーIDをハッシュして0-100の値を生成
        hash_input = f"{test.id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16) % 100

        # 重みに基づいてバリアントを選択
        cumulative_weight = 0.0
        for variant in test.variants:
            cumulative_weight += variant.weight
            if hash_value < cumulative_weight:
                return variant

        # フォールバック（最後のバリアント）
        return test.variants[-1]

    def get_assignment(
        self,
        test_id: str,
        user_id: str,
    ) -> Optional[ABTestAssignment]:
        """割り当てを取得"""
        return self._assignments.get(user_id, {}).get(test_id)

    def record_conversion(
        self,
        test_id: str,
        user_id: str,
        revenue: float = 0.0,
    ) -> bool:
        """コンバージョンを記録"""
        assignment = self.get_assignment(test_id, user_id)
        if not assignment:
            return False

        if assignment.converted:
            # 既にコンバージョン済み - 収益のみ加算
            assignment.revenue += revenue
        else:
            assignment.converted = True
            assignment.converted_at = datetime.utcnow()
            assignment.revenue = revenue

        # テストのバリアント統計を更新
        test = self.get_test(test_id)
        if test:
            for variant in test.variants:
                if variant.id == assignment.variant_id:
                    if not assignment.converted:
                        variant.conversions += 1
                    variant.revenue += revenue
                    break

        logger.info(f"コンバージョン記録: {user_id} ({test_id}) - ¥{revenue}")
        return True

    def get_test_results(self, test_id: str) -> Optional[dict]:
        """テスト結果を取得"""
        test = self.get_test(test_id)
        if not test:
            return None

        results = test.to_dict()

        # 統計的有意性の計算（簡易版）
        results["has_sufficient_sample"] = (
            test.total_impressions >= test.minimum_sample_size
        )

        # 勝者がある場合、改善率を計算
        if test.winner and len(test.variants) >= 2:
            # コントロール（最初のバリアント）との比較
            control = test.variants[0]
            winner = test.winner

            if control.conversion_rate > 0:
                improvement = (
                    (winner.conversion_rate - control.conversion_rate)
                    / control.conversion_rate
                    * 100
                )
                results["improvement_percent"] = round(improvement, 2)
            else:
                results["improvement_percent"] = 0.0

        return results

    def delete_test(self, test_id: str) -> bool:
        """テストを削除"""
        if test_id not in self._tests:
            return False

        # 関連する割り当ても削除
        for user_assignments in self._assignments.values():
            if test_id in user_assignments:
                del user_assignments[test_id]

        del self._tests[test_id]
        logger.info(f"A/Bテスト削除: {test_id}")
        return True


class AnalyticsTracker:
    """ユーザー行動分析トラッカー"""

    def __init__(self):
        """初期化"""
        # インメモリストレージ（本番ではDBを使用）
        self._events: list[AnalyticsEvent] = []
        self._goals: dict[str, ConversionGoal] = {}

        # 集計キャッシュ
        self._daily_stats: dict[str, dict] = {}
        self._user_sessions: dict[str, dict] = {}

    def track_event(
        self,
        event_type: EventType,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_name: str = "",
        event_data: Optional[dict] = None,
        **kwargs
    ) -> AnalyticsEvent:
        """イベントを記録"""
        event = AnalyticsEvent.create(
            event_type=event_type,
            user_id=user_id,
            session_id=session_id,
            event_name=event_name,
            event_data=event_data,
            **kwargs
        )

        self._events.append(event)
        self._update_daily_stats(event)
        self._update_goals(event)

        # ログ出力（デバッグ用）
        logger.debug(
            f"イベント記録: {event.event_type.value} - "
            f"user={user_id}, session={session_id}"
        )

        return event

    def _update_daily_stats(self, event: AnalyticsEvent):
        """日次統計を更新"""
        date_key = event.timestamp.strftime("%Y-%m-%d")

        if date_key not in self._daily_stats:
            self._daily_stats[date_key] = {
                "total_events": 0,
                "unique_users": set(),
                "unique_sessions": set(),
                "event_counts": defaultdict(int),
                "revenue": 0.0,
            }

        stats = self._daily_stats[date_key]
        stats["total_events"] += 1

        if event.user_id:
            stats["unique_users"].add(event.user_id)

        if event.session_id:
            stats["unique_sessions"].add(event.session_id)

        stats["event_counts"][event.event_type.value] += 1
        stats["revenue"] += event.revenue

    def _update_goals(self, event: AnalyticsEvent):
        """ゴールの進捗を更新"""
        for goal in self._goals.values():
            if event.event_type == goal.event_type:
                goal.current_count += 1
                goal.current_value += event.revenue

    def create_goal(
        self,
        name: str,
        description: str = "",
        goal_type: ConversionGoalType = ConversionGoalType.SUBSCRIPTION,
        event_type: EventType = EventType.SUBSCRIPTION_START,
        target_value: float = 0.0,
        target_count: int = 0,
        period_days: int = 30,
    ) -> ConversionGoal:
        """コンバージョンゴールを作成"""
        import secrets

        goal_id = f"goal_{secrets.token_hex(6)}"
        goal = ConversionGoal(
            id=goal_id,
            name=name,
            description=description,
            goal_type=goal_type,
            event_type=event_type,
            target_value=target_value,
            target_count=target_count,
            period_days=period_days,
        )
        self._goals[goal_id] = goal
        logger.info(f"ゴール作成: {goal_id} ({name})")
        return goal

    def get_goal(self, goal_id: str) -> Optional[ConversionGoal]:
        """ゴールを取得"""
        return self._goals.get(goal_id)

    def list_goals(self) -> list[ConversionGoal]:
        """ゴール一覧を取得"""
        return list(self._goals.values())

    def get_events(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AnalyticsEvent]:
        """イベントを検索"""
        events = self._events

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if session_id:
            events = [e for e in events if e.session_id == session_id]

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if start_date:
            events = [e for e in events if e.timestamp >= start_date]

        if end_date:
            events = [e for e in events if e.timestamp <= end_date]

        # 時刻降順でソート
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[offset : offset + limit]

    def get_daily_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> list[dict]:
        """日次統計を取得"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)

        if not end_date:
            end_date = datetime.utcnow()

        results = []
        current_date = start_date

        while current_date <= end_date:
            date_key = current_date.strftime("%Y-%m-%d")
            stats = self._daily_stats.get(date_key, {})

            result = {
                "date": date_key,
                "total_events": stats.get("total_events", 0),
                "unique_users": len(stats.get("unique_users", set())),
                "unique_sessions": len(stats.get("unique_sessions", set())),
                "event_counts": dict(stats.get("event_counts", {})),
                "revenue": stats.get("revenue", 0.0),
            }
            results.append(result)

            current_date += timedelta(days=1)

        return results

    def get_summary(self, days: int = 30) -> dict:
        """サマリー統計を取得"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)

        # 期間内のイベントを集計
        events = self.get_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )

        unique_users = set()
        unique_sessions = set()
        event_counts: dict[str, int] = defaultdict(int)
        total_revenue = 0.0

        for event in events:
            if event.user_id:
                unique_users.add(event.user_id)
            if event.session_id:
                unique_sessions.add(event.session_id)
            event_counts[event.event_type.value] += 1
            total_revenue += event.revenue

        return {
            "period_days": days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_events": len(events),
            "unique_users": len(unique_users),
            "unique_sessions": len(unique_sessions),
            "event_counts": dict(event_counts),
            "total_revenue": total_revenue,
        }

    def get_funnel(
        self,
        steps: list[EventType],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """ファネル分析を実行"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)

        if not end_date:
            end_date = datetime.utcnow()

        # ユーザーごとのイベントを取得
        user_events: dict[str, list[AnalyticsEvent]] = defaultdict(list)
        for event in self._events:
            if event.user_id and start_date <= event.timestamp <= end_date:
                user_events[event.user_id].append(event)

        # 各ステップのユーザー数をカウント
        step_users: list[set] = [set() for _ in steps]

        for user_id, events in user_events.items():
            # 時刻順にソート
            events.sort(key=lambda e: e.timestamp)

            # ステップを順番に通過したかチェック
            current_step = 0
            for event in events:
                if current_step < len(steps) and event.event_type == steps[current_step]:
                    step_users[current_step].add(user_id)
                    current_step += 1

        # 結果を構築
        funnel_steps = []
        for i, step in enumerate(steps):
            user_count = len(step_users[i])
            prev_count = len(step_users[i - 1]) if i > 0 else user_count

            conversion_rate = 0.0
            if prev_count > 0:
                conversion_rate = (user_count / prev_count) * 100

            funnel_steps.append({
                "step": i + 1,
                "event_type": step.value,
                "user_count": user_count,
                "conversion_rate": round(conversion_rate, 2),
                "drop_off": prev_count - user_count if i > 0 else 0,
            })

        overall_conversion = 0.0
        if funnel_steps and funnel_steps[0]["user_count"] > 0:
            overall_conversion = (
                funnel_steps[-1]["user_count"] / funnel_steps[0]["user_count"] * 100
            )

        return {
            "steps": funnel_steps,
            "overall_conversion": round(overall_conversion, 2),
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_retention(
        self,
        cohort_date: datetime,
        periods: int = 7,
    ) -> dict:
        """リテンション分析を実行"""
        cohort_users = set()

        # コホート日にイベントがあったユーザーを特定
        cohort_day = cohort_date.strftime("%Y-%m-%d")
        for event in self._events:
            if event.user_id and event.timestamp.strftime("%Y-%m-%d") == cohort_day:
                cohort_users.add(event.user_id)

        if not cohort_users:
            return {
                "cohort_date": cohort_day,
                "cohort_size": 0,
                "retention": [],
            }

        # 各期間でのリテンションを計算
        retention_data = []
        for period in range(periods + 1):
            target_date = (cohort_date + timedelta(days=period)).strftime("%Y-%m-%d")
            retained_users = set()

            for event in self._events:
                if (
                    event.user_id in cohort_users
                    and event.timestamp.strftime("%Y-%m-%d") == target_date
                ):
                    retained_users.add(event.user_id)

            retention_rate = 0.0
            if cohort_users:
                retention_rate = (len(retained_users) / len(cohort_users)) * 100

            retention_data.append({
                "day": period,
                "date": target_date,
                "retained_users": len(retained_users),
                "retention_rate": round(retention_rate, 2),
            })

        return {
            "cohort_date": cohort_day,
            "cohort_size": len(cohort_users),
            "retention": retention_data,
        }

    def delete_events(
        self,
        user_id: Optional[str] = None,
        before_date: Optional[datetime] = None,
    ) -> int:
        """イベントを削除"""
        initial_count = len(self._events)

        if user_id:
            self._events = [e for e in self._events if e.user_id != user_id]

        if before_date:
            self._events = [e for e in self._events if e.timestamp >= before_date]

        deleted = initial_count - len(self._events)
        logger.info(f"イベント削除: {deleted}件")
        return deleted


# シングルトンインスタンス
_ab_test_manager: Optional[ABTestManager] = None
_analytics_tracker: Optional[AnalyticsTracker] = None


def get_ab_test_manager() -> ABTestManager:
    """ABTestManagerのシングルトンを取得"""
    global _ab_test_manager
    if _ab_test_manager is None:
        _ab_test_manager = ABTestManager()
    return _ab_test_manager


def get_analytics_tracker() -> AnalyticsTracker:
    """AnalyticsTrackerのシングルトンを取得"""
    global _analytics_tracker
    if _analytics_tracker is None:
        _analytics_tracker = AnalyticsTracker()
    return _analytics_tracker
