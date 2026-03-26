"""Конвертация между различными цветовыми пространствами"""
import numpy as np


def rgb_to_hsv(r, g, b):
    """
    Конвертирует RGB в HSV.
    
    Args:
        r, g, b: Значения RGB (0-255)
    
    Returns:
        tuple: (h, s, v) где h в градусах (0-360), s и v в процентах (0-100)
    """
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    delta = max_val - min_val
    
    # Value (яркость)
    v = max_val * 100
    
    # Saturation (насыщенность)
    if max_val == 0:
        s = 0
    else:
        s = (delta / max_val) * 100
    
    # Hue (тон)
    if delta == 0:
        h = 0
    elif max_val == r:
        h = 60 * (((g - b) / delta) % 6)
    elif max_val == g:
        h = 60 * (((b - r) / delta) + 2)
    else:  # max_val == b
        h = 60 * (((r - g) / delta) + 4)
    
    return (h, s, v)


def hsv_to_rgb(h, s, v):
    """
    Конвертирует HSV в RGB.
    
    Args:
        h: Тон в градусах (0-360)
        s: Насыщенность в процентах (0-100)
        v: Яркость в процентах (0-100)
    
    Returns:
        tuple: (r, g, b) в диапазоне 0-255
    """
    h, s, v = h / 360.0, s / 100.0, v / 100.0
    
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    
    if 0 <= h < 1/6:
        r, g, b = c, x, 0
    elif 1/6 <= h < 2/6:
        r, g, b = x, c, 0
    elif 2/6 <= h < 3/6:
        r, g, b = 0, c, x
    elif 3/6 <= h < 4/6:
        r, g, b = 0, x, c
    elif 4/6 <= h < 5/6:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    
    r = int((r + m) * 255)
    g = int((g + m) * 255)
    b = int((b + m) * 255)
    
    return (r, g, b)


def rgb_to_lab(r, g, b):
    """
    Конвертирует RGB в LAB цветовое пространство.
    
    Args:
        r, g, b: Значения RGB (0-255)
    
    Returns:
        tuple: (l, a, b) где l в диапазоне 0-100, a и b в диапазоне -128 до 127
    """
    # Сначала конвертируем RGB в XYZ
    # Нормализуем RGB
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    
    # Применяем гамма-коррекцию
    def gamma_correct(val):
        if val > 0.04045:
            return ((val + 0.055) / 1.055) ** 2.4
        else:
            return val / 12.92
    
    r = gamma_correct(r)
    g = gamma_correct(g)
    b = gamma_correct(b)
    
    # Конвертируем в XYZ (используя стандарт D65)
    x = (r * 0.4124564 + g * 0.3575761 + b * 0.1804375) / 0.95047
    y = (r * 0.2126729 + g * 0.7151522 + b * 0.0721750) / 1.00000
    z = (r * 0.0193339 + g * 0.1191920 + b * 0.9503041) / 1.08883
    
    # Конвертируем XYZ в LAB
    def f(t):
        if t > (6/29)**3:
            return t**(1/3)
        else:
            return (1/3) * ((29/6)**2) * t + 4/29
    
    fx = f(x)
    fy = f(y)
    fz = f(z)
    
    l = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)
    
    return (l, a, b_val)


def lab_to_rgb(l, a, b_val):
    """
    Конвертирует LAB в RGB.
    
    Args:
        l: Яркость (0-100)
        a: Зелено-красная ось (-128 до 127)
        b_val: Сине-желтая ось (-128 до 127)
    
    Returns:
        tuple: (r, g, b) в диапазоне 0-255
    """
    # Конвертируем LAB в XYZ
    fy = (l + 16) / 116
    fx = a / 500 + fy
    fz = fy - b_val / 200
    
    def f_inv(t):
        if t > 6/29:
            return t**3
        else:
            return 3 * ((6/29)**2) * (t - 4/29)
    
    x = f_inv(fx) * 0.95047
    y = f_inv(fy) * 1.00000
    z = f_inv(fz) * 1.08883
    
    # Конвертируем XYZ в RGB
    r = x * 3.2404542 + y * -1.5371385 + z * -0.4985314
    g = x * -0.9692660 + y * 1.8760108 + z * 0.0415560
    b = x * 0.0556434 + y * -0.2040259 + z * 1.0572252
    
    # Применяем обратную гамма-коррекцию
    def gamma_correct_inv(val):
        if val > 0.0031308:
            return 1.055 * (val**(1/2.4)) - 0.055
        else:
            return 12.92 * val
    
    r = gamma_correct_inv(r)
    g = gamma_correct_inv(g)
    b = gamma_correct_inv(b)
    
    # Ограничиваем значения и конвертируем в 0-255
    r = max(0, min(255, int(r * 255)))
    g = max(0, min(255, int(g * 255)))
    b = max(0, min(255, int(b * 255)))
    
    return (r, g, b)


def rgb_array_to_hsv_array(rgb_array):
    """
    Конвертирует массив RGB в массив HSV.
    
    Args:
        rgb_array: Массив в формате (height, width, 3) RGB
    
    Returns:
        numpy.ndarray: Массив в формате (height, width, 3) HSV
    """
    hsv_array = np.zeros_like(rgb_array, dtype=np.float32)
    h, w = rgb_array.shape[:2]
    
    for y in range(h):
        for x in range(w):
            r, g, b = rgb_array[y, x]
            h_val, s_val, v_val = rgb_to_hsv(r, g, b)
            hsv_array[y, x] = [h_val, s_val, v_val]
    
    return hsv_array


def rgb_array_to_lab_array(rgb_array):
    """
    Конвертирует массив RGB в массив LAB.
    
    Args:
        rgb_array: Массив в формате (height, width, 3) RGB
    
    Returns:
        numpy.ndarray: Массив в формате (height, width, 3) LAB
    """
    lab_array = np.zeros_like(rgb_array, dtype=np.float32)
    h, w = rgb_array.shape[:2]
    
    for y in range(h):
        for x in range(w):
            r, g, b = rgb_array[y, x]
            l_val, a_val, b_val = rgb_to_lab(r, g, b)
            lab_array[y, x] = [l_val, a_val, b_val]
    
    return lab_array

