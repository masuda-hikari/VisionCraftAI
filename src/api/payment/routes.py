# -*- coding: utf-8 -*-
"""
VisionCraftAI - 決済エンドポイント

決済・サブスクリプション・クレジット関連のAPIエンドポイントを定義します。
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from src.api.auth.dependencies import get_api_key
from src.api.auth.models import APIKey
from src.api.payment.credit_manager import get_credit_manager
from src.api.payment.models import PlanPrice, TransactionType
from src.api.payment.schemas import (
    CreditBalanceResponse,
    CreditPackage,
    CreditPackagesResponse,
    CreditPurchaseRequest,
    CreditPurchaseResponse,
    CreditTransactionResponse,
    CreditTransactionsResponse,
    PaymentErrorResponse,
    PlanInfo,
    PlansResponse,
    SubscriptionCancelRequest,
    SubscriptionCreateRequest,
    SubscriptionResponse,
    SubscriptionStatusResponse,
    SubscriptionUpdateRequest,
    WebhookResponse,
)
from src.api.payment.stripe_client import get_stripe_client
from src.api.payment.subscription_manager import get_subscription_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payment", tags=["Payment"])


# ========== プラン情報 ==========


@router.get("/plans", response_model=PlansResponse)
async def list_plans():
    """
    利用可能なプラン一覧を取得

    認証不要
    """
    plans = PlanPrice.get_plans()
    return PlansResponse(
        plans=[
            PlanInfo(
                plan_id=p.plan_id,
                name=p.name,
                description=p.description,
                price_monthly=str(p.price_monthly),
                price_yearly=str(p.price_yearly),
                credits_included=p.credits_included,
                features=p.features,
            )
            for p in plans.values()
        ]
    )


# ========== サブスクリプション ==========


@router.post(
    "/subscriptions",
    response_model=SubscriptionResponse,
    responses={400: {"model": PaymentErrorResponse}},
)
async def create_subscription(
    request: SubscriptionCreateRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    サブスクリプションを作成

    - Freeプラン: 即時アクティベート
    - 有料プラン: Stripe Checkoutページへのリダイレクト
    """
    manager = get_subscription_manager()

    try:
        subscription, checkout_url = manager.create_subscription(
            user_id=api_key.owner_id or api_key.key_id,
            email=request.email,
            plan_id=request.plan_id,
            billing_interval=request.billing_interval,
            api_key_id=api_key.key_id,
        )

        return SubscriptionResponse(
            subscription_id=subscription.subscription_id,
            plan_id=subscription.plan_id,
            billing_interval=subscription.billing_interval,
            status=subscription.status.value,
            current_period_start=subscription.current_period_start,
            current_period_end=subscription.current_period_end,
            cancel_at_period_end=subscription.cancel_at_period_end,
            checkout_url=checkout_url,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/subscriptions/me", response_model=SubscriptionStatusResponse)
async def get_my_subscription(
    api_key: APIKey = Depends(get_api_key),
):
    """
    現在のサブスクリプション状況を取得
    """
    manager = get_subscription_manager()
    subscription = manager.get_subscription_by_api_key(api_key.key_id)

    if not subscription:
        # サブスクリプションがない場合はFreeとして扱う
        plans = PlanPrice.get_plans()
        return SubscriptionStatusResponse(
            subscription_id="",
            plan_id="free",
            plan_name="Free",
            status="none",
            is_active=True,
            current_period_end=None,
            cancel_at_period_end=False,
            credits_included=plans["free"].credits_included,
        )

    plans = PlanPrice.get_plans()
    plan = plans.get(subscription.plan_id, plans["free"])

    return SubscriptionStatusResponse(
        subscription_id=subscription.subscription_id,
        plan_id=subscription.plan_id,
        plan_name=plan.name,
        status=subscription.status.value,
        is_active=subscription.is_active(),
        current_period_end=subscription.current_period_end,
        cancel_at_period_end=subscription.cancel_at_period_end,
        credits_included=plan.credits_included,
    )


@router.patch(
    "/subscriptions/me",
    response_model=SubscriptionResponse,
    responses={400: {"model": PaymentErrorResponse}},
)
async def update_my_subscription(
    request: SubscriptionUpdateRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    サブスクリプションプランを変更
    """
    manager = get_subscription_manager()
    subscription = manager.get_subscription_by_api_key(api_key.key_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="サブスクリプションが見つかりません",
        )

    try:
        updated = manager.update_subscription_plan(
            subscription.subscription_id,
            request.plan_id,
        )

        if not updated:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="サブスクリプションの更新に失敗しました",
            )

        return SubscriptionResponse(
            subscription_id=updated.subscription_id,
            plan_id=updated.plan_id,
            billing_interval=updated.billing_interval,
            status=updated.status.value,
            current_period_start=updated.current_period_start,
            current_period_end=updated.current_period_end,
            cancel_at_period_end=updated.cancel_at_period_end,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/subscriptions/me/cancel",
    response_model=SubscriptionResponse,
)
async def cancel_my_subscription(
    request: SubscriptionCancelRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    サブスクリプションをキャンセル
    """
    manager = get_subscription_manager()
    subscription = manager.get_subscription_by_api_key(api_key.key_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="サブスクリプションが見つかりません",
        )

    updated = manager.cancel_subscription(
        subscription.subscription_id,
        immediately=request.immediately,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="キャンセルに失敗しました",
        )

    return SubscriptionResponse(
        subscription_id=updated.subscription_id,
        plan_id=updated.plan_id,
        billing_interval=updated.billing_interval,
        status=updated.status.value,
        current_period_start=updated.current_period_start,
        current_period_end=updated.current_period_end,
        cancel_at_period_end=updated.cancel_at_period_end,
    )


# ========== クレジット ==========


@router.get("/credits/packages", response_model=CreditPackagesResponse)
async def list_credit_packages():
    """
    利用可能なクレジットパッケージ一覧を取得

    認証不要
    """
    manager = get_credit_manager()
    packages = manager.get_packages()
    return CreditPackagesResponse(
        packages={
            k: CreditPackage(**v)
            for k, v in packages.items()
        }
    )


@router.get("/credits/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    api_key: APIKey = Depends(get_api_key),
):
    """
    クレジット残高を取得
    """
    manager = get_credit_manager()
    user_id = api_key.owner_id or api_key.key_id
    balance = manager.get_or_create_balance(user_id, api_key.key_id)

    return CreditBalanceResponse(
        balance=balance.balance,
        bonus_balance=balance.bonus_balance,
        total_balance=balance.get_total_balance(),
        total_purchased=balance.total_purchased,
        total_used=balance.total_used,
    )


@router.post(
    "/credits/purchase",
    response_model=CreditPurchaseResponse,
    responses={400: {"model": PaymentErrorResponse}},
)
async def purchase_credits(
    request: CreditPurchaseRequest,
    api_key: APIKey = Depends(get_api_key),
):
    """
    クレジットを購入

    PaymentIntentを作成し、client_secretを返します。
    クライアント側でStripe.jsを使用して決済を完了してください。
    """
    manager = get_credit_manager()
    user_id = api_key.owner_id or api_key.key_id

    try:
        result = manager.create_purchase_intent(
            user_id=user_id,
            package_id=request.package_id,
            api_key_id=api_key.key_id,
        )

        return CreditPurchaseResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/credits/purchase/{payment_intent_id}/complete")
async def complete_credit_purchase(
    payment_intent_id: str,
    api_key: APIKey = Depends(get_api_key),
):
    """
    クレジット購入を完了（テスト・確認用）

    本番環境ではWebhook経由で処理されます。
    """
    manager = get_credit_manager()
    transaction = manager.complete_purchase(payment_intent_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="購入の完了に失敗しました",
        )

    return {
        "transaction_id": transaction.transaction_id,
        "credits_added": transaction.amount,
        "balance_after": transaction.balance_after,
    }


@router.get("/credits/transactions", response_model=CreditTransactionsResponse)
async def get_credit_transactions(
    limit: int = 50,
    offset: int = 0,
    transaction_type: Optional[str] = None,
    api_key: APIKey = Depends(get_api_key),
):
    """
    クレジット取引履歴を取得
    """
    manager = get_credit_manager()
    user_id = api_key.owner_id or api_key.key_id

    # タイプフィルタ
    tx_type = None
    if transaction_type:
        try:
            tx_type = TransactionType(transaction_type)
        except ValueError:
            pass

    transactions = manager.get_transactions(
        user_id=user_id,
        limit=limit,
        offset=offset,
        transaction_type=tx_type,
    )

    return CreditTransactionsResponse(
        transactions=[
            CreditTransactionResponse(
                transaction_id=t.transaction_id,
                transaction_type=t.transaction_type.value,
                amount=t.amount,
                balance_after=t.balance_after,
                price_usd=str(t.price_usd) if t.price_usd else None,
                description=t.description,
                created_at=t.created_at,
            )
            for t in transactions
        ],
        total=len(transactions),
    )


# ========== Webhook ==========


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
):
    """
    Stripe Webhookエンドポイント

    Stripeからのイベントを処理します。
    """
    stripe_client = get_stripe_client()
    payload = await request.body()

    # 署名検証
    if stripe_signature:
        if not stripe_client.verify_webhook_signature(payload, stripe_signature):
            logger.warning("Webhook署名検証失敗")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature",
            )

    # イベント解析
    event = stripe_client.parse_webhook_event(payload)
    event_type = event.get("type", "")
    data = event.get("data", {}).get("object", {})

    logger.info(f"Webhookイベント受信: {event_type}")

    # イベント処理
    if event_type == "checkout.session.completed":
        # Checkout完了
        await _handle_checkout_completed(data)

    elif event_type == "customer.subscription.updated":
        # サブスクリプション更新
        await _handle_subscription_updated(data)

    elif event_type == "customer.subscription.deleted":
        # サブスクリプション削除
        await _handle_subscription_deleted(data)

    elif event_type == "payment_intent.succeeded":
        # 支払い成功（クレジット購入）
        await _handle_payment_succeeded(data)

    elif event_type == "invoice.payment_failed":
        # 請求書支払い失敗
        await _handle_payment_failed(data)

    return WebhookResponse(received=True, message=f"Processed {event_type}")


async def _handle_checkout_completed(data: dict) -> None:
    """Checkout完了を処理"""
    metadata = data.get("metadata", {})
    subscription_id = metadata.get("subscription_id")
    stripe_subscription_id = data.get("subscription")

    if subscription_id and stripe_subscription_id:
        manager = get_subscription_manager()
        manager.activate_subscription(subscription_id, stripe_subscription_id)
        logger.info(f"Checkout完了: {subscription_id}")


async def _handle_subscription_updated(data: dict) -> None:
    """サブスクリプション更新を処理"""
    stripe_subscription_id = data.get("id")
    status = data.get("status")
    current_period_end = data.get("current_period_end")

    if stripe_subscription_id:
        manager = get_subscription_manager()
        manager.handle_subscription_updated(
            stripe_subscription_id,
            status,
            current_period_end,
        )
        logger.info(f"サブスクリプション更新: {stripe_subscription_id}")


async def _handle_subscription_deleted(data: dict) -> None:
    """サブスクリプション削除を処理"""
    stripe_subscription_id = data.get("id")

    if stripe_subscription_id:
        manager = get_subscription_manager()
        manager.handle_subscription_updated(
            stripe_subscription_id,
            "canceled",
            0,
        )
        logger.info(f"サブスクリプション削除: {stripe_subscription_id}")


async def _handle_payment_succeeded(data: dict) -> None:
    """支払い成功を処理"""
    payment_intent_id = data.get("id")
    metadata = data.get("metadata", {})

    # クレジット購入の場合
    if metadata.get("package_id"):
        manager = get_credit_manager()
        manager.complete_purchase(payment_intent_id)
        logger.info(f"クレジット購入完了: {payment_intent_id}")


async def _handle_payment_failed(data: dict) -> None:
    """支払い失敗を処理"""
    subscription_id = data.get("subscription")

    if subscription_id:
        manager = get_subscription_manager()
        # past_dueステータスに更新
        manager.handle_subscription_updated(
            subscription_id,
            "past_due",
            0,
        )
        logger.warning(f"支払い失敗: {subscription_id}")


# ========== Checkout成功/キャンセル ==========


@router.get("/success")
async def checkout_success(session_id: str = ""):
    """
    Checkout成功リダイレクト先

    実際の実装ではフロントエンドにリダイレクト
    """
    return {
        "status": "success",
        "message": "サブスクリプションが正常に作成されました",
        "session_id": session_id,
    }


@router.get("/cancel")
async def checkout_cancel():
    """
    Checkoutキャンセルリダイレクト先

    実際の実装ではフロントエンドにリダイレクト
    """
    return {
        "status": "canceled",
        "message": "サブスクリプションの作成がキャンセルされました",
    }
