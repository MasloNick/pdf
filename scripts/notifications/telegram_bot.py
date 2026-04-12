"""Telegram Bot notification module for the NPL portfolio platform.

Sends alerts about new auction lots and portfolio scoring reports
via the Telegram Bot API using only the Python standard library.

Environment variables:
    TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
    TELEGRAM_CHAT_ID    — Target chat / channel / group ID
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

API_BASE = "https://api.telegram.org/bot{token}/{method}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_token() -> str:
    """Return bot token from env or raise."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise EnvironmentError(
            "TELEGRAM_BOT_TOKEN is not set. "
            "Export it before using the Telegram notifier."
        )
    return token


def _get_chat_id() -> str:
    """Return default chat id from env or raise."""
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not chat_id:
        raise EnvironmentError(
            "TELEGRAM_CHAT_ID is not set. "
            "Export it before using the Telegram notifier."
        )
    return chat_id


def _api_request(
    method: str,
    payload: Dict[str, Any],
    token: Optional[str] = None,
    timeout: int = 15,
) -> Dict[str, Any]:
    """Make a POST request to the Telegram Bot API and return parsed JSON.

    Parameters
    ----------
    method:
        Bot API method name, e.g. ``sendMessage`` or ``getMe``.
    payload:
        JSON-serialisable dictionary sent as the request body.
    token:
        Bot token. Defaults to ``TELEGRAM_BOT_TOKEN`` env var.
    timeout:
        HTTP timeout in seconds.

    Returns
    -------
    dict
        Parsed JSON response from Telegram.
    """
    token = token or _get_token()
    url = API_BASE.format(token=token, method=method)
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8")
        return json.loads(body)


def _fmt_number(value: Any) -> str:
    """Format a numeric value with thousands separator, or return '—' if None."""
    if value is None:
        return "—"
    try:
        num = float(value)
        if num == int(num):
            return f"{int(num):,}".replace(",", " ")
        return f"{num:,.2f}".replace(",", " ")
    except (TypeError, ValueError):
        return str(value)


def _escape_md(text: str) -> str:
    """Escape characters that break Telegram Markdown (v1) parsing."""
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_connection(token: Optional[str] = None) -> bool:
    """Verify that the bot token is valid by calling ``getMe``.

    Parameters
    ----------
    token:
        Bot token. Defaults to ``TELEGRAM_BOT_TOKEN`` env var.

    Returns
    -------
    bool
        ``True`` if the API returned a successful response, ``False`` otherwise.
    """
    try:
        token = token or _get_token()
        result = _api_request("getMe", {}, token=token)
        if result.get("ok"):
            bot_info = result.get("result", {})
            logger.info(
                "Telegram bot connected: @%s (id=%s)",
                bot_info.get("username", "?"),
                bot_info.get("id", "?"),
            )
            return True
        logger.error("Telegram getMe returned ok=false: %s", result)
        return False
    except EnvironmentError:
        logger.error("TELEGRAM_BOT_TOKEN is not configured")
        return False
    except urllib.error.HTTPError as exc:
        logger.error("Telegram getMe HTTP error %s: %s", exc.code, exc.reason)
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error("Telegram getMe failed: %s", exc)
        return False


def send_message(
    text: str,
    chat_id: Optional[str] = None,
    token: Optional[str] = None,
    parse_mode: str = "Markdown",
    disable_web_page_preview: bool = True,
) -> bool:
    """Send a text message to a Telegram chat.

    Parameters
    ----------
    text:
        Message text (may include Markdown formatting).
    chat_id:
        Target chat ID. Defaults to ``TELEGRAM_CHAT_ID`` env var.
    token:
        Bot token. Defaults to ``TELEGRAM_BOT_TOKEN`` env var.
    parse_mode:
        Telegram parse mode (``Markdown`` or ``HTML``).
    disable_web_page_preview:
        If ``True``, link previews are suppressed.

    Returns
    -------
    bool
        ``True`` if the message was sent successfully.
    """
    try:
        chat_id = chat_id or _get_chat_id()
        token = token or _get_token()

        payload: Dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": disable_web_page_preview,
        }

        result = _api_request("sendMessage", payload, token=token)
        if result.get("ok"):
            logger.debug("Message sent to chat %s", chat_id)
            return True
        logger.error("sendMessage returned ok=false: %s", result)
        return False
    except EnvironmentError as exc:
        logger.error("Configuration error: %s", exc)
        return False
    except urllib.error.HTTPError as exc:
        logger.error(
            "sendMessage HTTP error %s: %s", exc.code, exc.reason
        )
        return False
    except Exception as exc:  # noqa: BLE001
        logger.error("sendMessage failed: %s", exc)
        return False


def send_new_lot_alert(
    lot_data: dict,
    chat_id: Optional[str] = None,
    token: Optional[str] = None,
) -> bool:
    """Format an auction lot as a readable Ukrainian-language message and send it.

    Expected keys in *lot_data* (all optional except ``title``):
        title, source, url, total_debt, start_price, current_price,
        currency, seller, seller_type, portfolio_type, debt_type,
        num_debtors, auction_date, end_date, description.

    Parameters
    ----------
    lot_data:
        Dictionary describing the auction lot (see above).
    chat_id:
        Target chat ID.
    token:
        Bot token.

    Returns
    -------
    bool
        ``True`` if the alert was sent successfully.
    """
    try:
        title = lot_data.get("title", "Без назви")
        source = lot_data.get("source", "—")
        url = lot_data.get("url", "")
        total_debt = lot_data.get("total_debt")
        start_price = lot_data.get("start_price")
        current_price = lot_data.get("current_price")
        currency = lot_data.get("currency", "UAH")
        seller = lot_data.get("seller", "—")
        seller_type = lot_data.get("seller_type", "—")
        portfolio_type = lot_data.get("portfolio_type", "—")
        debt_type = lot_data.get("debt_type", "—")
        num_debtors = lot_data.get("num_debtors")
        auction_date = lot_data.get("auction_date", "—")
        end_date = lot_data.get("end_date", "—")
        description = lot_data.get("description", "")

        # Price-to-debt ratio
        ratio_str = "—"
        if total_debt and start_price:
            try:
                ratio = float(start_price) / float(total_debt) * 100
                ratio_str = f"{ratio:.1f}%"
            except (ZeroDivisionError, TypeError, ValueError):
                pass

        lines = [
            f"*Новий лот NPL*",
            f"*{_escape_md(title)}*",
            "",
            f"*Джерело:* {_escape_md(source)}",
            f"*Продавець:* {_escape_md(seller)} ({_escape_md(seller_type)})",
            f"*Тип портфеля:* {_escape_md(portfolio_type)}",
            f"*Тип боргу:* {_escape_md(debt_type)}",
            "",
            f"*Загальний борг:* {_fmt_number(total_debt)} {currency}",
            f"*Стартова ціна:* {_fmt_number(start_price)} {currency}",
            f"*Поточна ціна:* {_fmt_number(current_price)} {currency}",
            f"*Ціна / борг:* {ratio_str}",
            "",
            f"*Кількість боржників:* {_fmt_number(num_debtors)}",
            f"*Дата аукціону:* {auction_date}",
            f"*Дата завершення:* {end_date}",
        ]

        if description:
            short_desc = description[:300]
            if len(description) > 300:
                short_desc += "..."
            lines += ["", f"*Опис:* {_escape_md(short_desc)}"]

        if url:
            lines += ["", f"[Переглянути лот]({url})"]

        text = "\n".join(lines)
        return send_message(text, chat_id=chat_id, token=token)

    except Exception as exc:  # noqa: BLE001
        logger.error("send_new_lot_alert failed: %s", exc)
        return False


def send_portfolio_report(
    scoring_data: dict,
    chat_id: Optional[str] = None,
    token: Optional[str] = None,
) -> bool:
    """Format a portfolio scoring result and send as a Telegram message.

    Expected keys in *scoring_data* (all optional):
        portfolio_name, total_debt, total_price, price_to_debt_ratio,
        total_records, physical_count, legal_count, physical_debt,
        legal_debt, avg_debt, median_debt, min_debt, max_debt,
        score, risk_level, recommendation, currency,
        regions (dict), debt_types (dict), warnings (list[str]).

    Parameters
    ----------
    scoring_data:
        Dictionary with portfolio scoring / analytics results.
    chat_id:
        Target chat ID.
    token:
        Bot token.

    Returns
    -------
    bool
        ``True`` if the report was sent successfully.
    """
    try:
        name = scoring_data.get("portfolio_name", "Без назви")
        currency = scoring_data.get("currency", "UAH")
        total_debt = scoring_data.get("total_debt")
        total_price = scoring_data.get("total_price")
        ratio = scoring_data.get("price_to_debt_ratio")
        total_records = scoring_data.get("total_records")
        phys_count = scoring_data.get("physical_count")
        legal_count = scoring_data.get("legal_count")
        phys_debt = scoring_data.get("physical_debt")
        legal_debt = scoring_data.get("legal_debt")
        avg_debt = scoring_data.get("avg_debt")
        median_debt = scoring_data.get("median_debt")
        min_debt = scoring_data.get("min_debt")
        max_debt = scoring_data.get("max_debt")
        score = scoring_data.get("score")
        risk_level = scoring_data.get("risk_level", "—")
        recommendation = scoring_data.get("recommendation", "")
        regions = scoring_data.get("regions", {})
        debt_types = scoring_data.get("debt_types", {})
        warnings = scoring_data.get("warnings", [])

        # Ratio formatting
        if ratio is not None:
            try:
                ratio_str = f"{float(ratio) * 100:.1f}%"
            except (TypeError, ValueError):
                ratio_str = str(ratio)
        elif total_debt and total_price:
            try:
                ratio_str = f"{float(total_price) / float(total_debt) * 100:.1f}%"
            except (ZeroDivisionError, TypeError, ValueError):
                ratio_str = "—"
        else:
            ratio_str = "—"

        # Score formatting
        if score is not None:
            score_str = f"{score}/100"
        else:
            score_str = "—"

        lines = [
            f"*Звіт по портфелю NPL*",
            f"*{_escape_md(name)}*",
            "",
            "*--- Загальна інформація ---*",
            f"*Загальний борг:* {_fmt_number(total_debt)} {currency}",
            f"*Ціна портфеля:* {_fmt_number(total_price)} {currency}",
            f"*Ціна / борг:* {ratio_str}",
            f"*Кількість записів:* {_fmt_number(total_records)}",
            "",
            "*--- Структура боржників ---*",
            f"*Фізичні особи:* {_fmt_number(phys_count)} "
            f"(борг: {_fmt_number(phys_debt)} {currency})",
            f"*Юридичні особи:* {_fmt_number(legal_count)} "
            f"(борг: {_fmt_number(legal_debt)} {currency})",
            "",
            "*--- Статистика боргу ---*",
            f"*Середній борг:* {_fmt_number(avg_debt)} {currency}",
            f"*Медіана боргу:* {_fmt_number(median_debt)} {currency}",
            f"*Мін. борг:* {_fmt_number(min_debt)} {currency}",
            f"*Макс. борг:* {_fmt_number(max_debt)} {currency}",
        ]

        # Regions
        if regions:
            lines += ["", "*--- Регіони ---*"]
            sorted_regions = sorted(regions.items(), key=lambda kv: kv[1], reverse=True)
            for region, count in sorted_regions[:10]:
                lines.append(f"  {_escape_md(region)}: {count}")
            if len(sorted_regions) > 10:
                lines.append(f"  _...та ще {len(sorted_regions) - 10} регіонів_")

        # Debt types
        if debt_types:
            lines += ["", "*--- Типи боргу ---*"]
            for dtype, count in debt_types.items():
                lines.append(f"  {_escape_md(dtype)}: {count}")

        # Score and risk
        lines += [
            "",
            "*--- Скоринг ---*",
            f"*Оцінка:* {score_str}",
            f"*Рівень ризику:* {_escape_md(risk_level)}",
        ]

        if recommendation:
            lines.append(f"*Рекомендація:* {_escape_md(recommendation)}")

        # Warnings
        if warnings:
            lines += ["", "*Попередження:*"]
            for w in warnings:
                lines.append(f"  - {_escape_md(w)}")

        text = "\n".join(lines)

        # Telegram messages have a 4096-char limit; split if needed.
        if len(text) <= 4096:
            return send_message(text, chat_id=chat_id, token=token)

        # Split into chunks respecting the limit.
        success = True
        while text:
            chunk = text[:4096]
            # Try to split at the last newline within the limit.
            if len(text) > 4096:
                last_nl = chunk.rfind("\n")
                if last_nl > 0:
                    chunk = text[:last_nl]
                    text = text[last_nl + 1 :]
                else:
                    text = text[4096:]
            else:
                text = ""
            if not send_message(chunk, chat_id=chat_id, token=token):
                success = False
        return success

    except Exception as exc:  # noqa: BLE001
        logger.error("send_portfolio_report failed: %s", exc)
        return False


# ---------------------------------------------------------------------------
# CLI quick-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not check_connection():
        logger.error("Bot connection check failed. Exiting.")
        raise SystemExit(1)

    # Quick smoke test: send a simple message
    ok = send_message("*Тест:* NPL Platform Telegram bot працює.")
    logger.info("Test message sent: %s", ok)

    # Example lot alert
    example_lot = {
        "title": "Портфель прав вимоги ПАТ 'Банк Тест'",
        "source": "setam",
        "url": "https://setam.net.ua/lot/12345",
        "total_debt": 15_500_000,
        "start_price": 1_200_000,
        "current_price": 1_200_000,
        "currency": "UAH",
        "seller": "ПАТ 'Банк Тест'",
        "seller_type": "bank",
        "portfolio_type": "mixed",
        "debt_type": "credit",
        "num_debtors": 47,
        "auction_date": "2026-05-01",
        "end_date": "2026-05-15",
        "description": "Портфель прав вимоги за кредитними договорами",
    }
    ok = send_new_lot_alert(example_lot)
    logger.info("Lot alert sent: %s", ok)

    # Example portfolio report
    example_report = {
        "portfolio_name": "Портфель #42 — ПАТ 'Банк Тест'",
        "total_debt": 15_500_000,
        "total_price": 1_200_000,
        "total_records": 47,
        "physical_count": 35,
        "legal_count": 12,
        "physical_debt": 8_000_000,
        "legal_debt": 7_500_000,
        "avg_debt": 329_787,
        "median_debt": 180_000,
        "min_debt": 12_000,
        "max_debt": 4_200_000,
        "score": 72,
        "risk_level": "Середній",
        "recommendation": "Рекомендовано до придбання за умови додаткової перевірки юридичних осіб",
        "currency": "UAH",
        "regions": {
            "Київська": 12,
            "Одеська": 8,
            "Харківська": 7,
            "Дніпропетровська": 6,
            "Львівська": 5,
            "Інші": 9,
        },
        "debt_types": {"credit": 30, "overdraft": 10, "receivables": 7},
        "warnings": [
            "3 юридичні особи у стані банкрутства",
            "Високий рівень пені у 12 договорах",
        ],
    }
    ok = send_portfolio_report(example_report)
    logger.info("Portfolio report sent: %s", ok)
