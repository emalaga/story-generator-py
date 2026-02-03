"""
Image Cost Calculator for estimating GPT Image generation costs.

Calculates cost estimates based on OpenAI API usage data including
token counts and per-image fees.
"""

from typing import Dict, Any, Optional


def estimate_gpt_image_cost(
    *,
    model: str,
    size: str,
    quality: str,
    usage: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Estimate cost for GPT Image models from an OpenAI API response.

    Expects `usage` dict from Responses API (or compatible).
    Works even if image token fields are nested in *_details.

    Args:
        model: The image model used (e.g., 'gpt-image-1', 'gpt-image-1-mini')
        size: Image size (e.g., '1024x1024', '1024x1536')
        quality: Image quality (e.g., 'low', 'medium', 'high')
        usage: Usage dictionary from the API response

    Returns:
        Dictionary with cost breakdown and total estimated cost
    """

    # ---- Helpers to safely extract image token counts from various shapes ----
    def get_nested(d: Dict, *path, default=0):
        cur = d
        for p in path:
            if not isinstance(cur, dict) or p not in cur:
                return default
            cur = cur[p]
        return cur

    # Text token usage
    text_in = usage.get("input_tokens", 0)
    text_out = usage.get("output_tokens", 0)

    # Image token usage (handle multiple possible response shapes)
    image_in = usage.get("image_input_tokens")
    if image_in is None:
        image_in = get_nested(usage, "input_tokens_details", "image_tokens", default=0)

    image_out = usage.get("image_output_tokens")
    if image_out is None:
        image_out = get_nested(usage, "output_tokens_details", "image_tokens", default=0)

    # ---- Pricing tables (fill only what you use; add more entries as needed) ----
    # Rates are $ per 1,000,000 tokens.
    token_rates = {
        "gpt-image-1": {"text_in": 5.00, "text_out": 0.00, "img_in": 10.00, "img_out": 40.00},
        "gpt-image-1-mini": {"text_in": 2.00, "text_out": 0.00, "img_in": 2.50, "img_out": 8.00},
        # For gpt-image-1.5, plug in the exact token rates from the model page you're using.
        "gpt-image-1.5": {"text_in": 0.00, "text_out": 0.00, "img_in": 0.00, "img_out": 0.00},
    }

    # Per-image generation fees (examples; expand to cover your full matrix)
    per_image_fee = {
        "gpt-image-1": {
            ("low", "1024x1024"): 0.011,
            ("medium", "1024x1024"): 0.042,
            ("high", "1024x1024"): 0.167,
            ("low", "1024x1536"): 0.016,
            ("low", "1536x1024"): 0.016,
            ("medium", "1024x1536"): 0.063,
            ("medium", "1536x1024"): 0.063,
            ("high", "1024x1536"): 0.250,
            ("high", "1536x1024"): 0.250,
        },
        "gpt-image-1-mini": {
            ("low", "1024x1024"): 0.005,
            ("high", "1024x1024"): 0.036,
            ("low", "1024x1536"): 0.006,
            ("low", "1536x1024"): 0.006,
            ("high", "1024x1536"): 0.052,
            ("high", "1536x1024"): 0.052,
            ("medium", "1024x1024"): 0.015,
            ("medium", "1024x1536"): 0.022,
            ("medium", "1536x1024"): 0.022,
        },
        "gpt-image-1.5": {
            ("low", "1024x1024"): 0.009,
            ("high", "1024x1024"): 0.133,
            ("low", "1024x1536"): 0.013,
            ("low", "1536x1024"): 0.013,
            ("high", "1024x1536"): 0.20,
            ("high", "1536x1024"): 0.20,
            ("medium", "1024x1024"): 0.045,
            ("medium", "1024x1536"): 0.068,
            ("medium", "1536x1024"): 0.068,
        },
    }

    if model not in token_rates:
        # Unknown model - return zero costs but include usage info
        return {
            "per_image_fee": 0.0,
            "text_input_cost": 0.0,
            "text_output_cost": 0.0,
            "image_input_cost": 0.0,
            "image_output_cost": 0.0,
            "total_estimated_cost": 0.0,
            "usage_extracted": {
                "text_in_tokens": text_in,
                "text_out_tokens": text_out,
                "image_in_tokens": image_in,
                "image_out_tokens": image_out,
            },
            "warning": f"Unknown model: {model}",
        }

    # Resolve auto size/quality if you use them:
    # - Best practice: log the actual chosen size/quality on your side, or treat auto as unknown and skip P_image.
    p_image = per_image_fee.get(model, {}).get((quality, size), 0.0)

    rates = token_rates[model]
    to_per_token = lambda per_million: per_million / 1_000_000.0

    cost_breakdown = {
        "per_image_fee": p_image,
        "text_input_cost": text_in * to_per_token(rates["text_in"]),
        "text_output_cost": text_out * to_per_token(rates["text_out"]),
        "image_input_cost": image_in * to_per_token(rates["img_in"]),
        "image_output_cost": image_out * to_per_token(rates["img_out"]),
    }
    cost_breakdown["total_estimated_cost"] = sum(cost_breakdown.values())

    # Helpful debug info
    cost_breakdown["usage_extracted"] = {
        "text_in_tokens": text_in,
        "text_out_tokens": text_out,
        "image_in_tokens": image_in,
        "image_out_tokens": image_out,
    }
    return cost_breakdown


def format_cost(cost: float) -> str:
    """
    Format a cost value for display.

    Args:
        cost: Cost in dollars

    Returns:
        Formatted string like "$0.042" or "$0.00" if very small
    """
    if cost < 0.001:
        return "$0.00"
    return f"${cost:.3f}"


def extract_usage_from_response(response) -> Optional[Dict[str, Any]]:
    """
    Extract usage data from an OpenAI API response object.

    Args:
        response: OpenAI API response object

    Returns:
        Usage dictionary if available, None otherwise
    """
    if hasattr(response, 'usage'):
        usage = response.usage
        if hasattr(usage, '__dict__'):
            return usage.__dict__
        elif isinstance(usage, dict):
            return usage
    return None
