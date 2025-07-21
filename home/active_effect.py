from datetime import datetime
from data import ActiveEffect

def apply_effect(user_id, base_value, effect_type):
    effect = ActiveEffect.query.filter_by(
        user_id=user_id,
        effect_type=effect_type
    ).filter(ActiveEffect.expires_at > datetime.utcnow()).first()

    if effect:
        #Returns base value with effect value added on
        return base_value * (1 + effect.effect_value)

    return base_value
