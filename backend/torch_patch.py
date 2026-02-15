import torch
import warnings

# Сохраняем оригинальную функцию
_original_load = torch.load

def patched_load(*args, **kwargs):
    """Патч для torch.load с weights_only=False для совместимости"""
    # Отключаем weights_only для pyannote моделей
    kwargs['weights_only'] = False
    warnings.filterwarnings("ignore", category=UserWarning)
    return _original_load(*args, **kwargs)

# Применяем патч глобально
torch.load = patched_load

print("✅ Torch patch applied: weights_only=False")
