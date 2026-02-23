"""
Mejora 4: Tests unitarios para la logica del pipeline FCI.
Ejecutar con: python tests.py
"""
import os
import sys
import json
import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)

PASSED = 0
FAILED = 0

def assert_eq(name, actual, expected, tolerance=None):
    global PASSED, FAILED
    if tolerance:
        ok = abs(actual - expected) < tolerance
    else:
        ok = actual == expected
    
    if ok:
        PASSED += 1
        print(f"  [OK] {name}")
    else:
        FAILED += 1
        print(f"  [FAIL] {name}: expected {expected}, got {actual}")


def test_fifo_logic():
    """Test FIFO consumption with multiple subscriptions."""
    print("\n=== Test: Logica FIFO ===")
    
    # Simulate: Sub1=100 CPs, Sub2=50 CPs, then Rescue 120 CPs
    subs = [
        {'id': 1, 'remaining_cp': 100.0, 'price': 10.0},
        {'id': 2, 'remaining_cp': 50.0, 'price': 12.0},
    ]
    
    needed = 120.0
    active_idx = 0
    consumed_log = []
    
    while needed > 0.0001 and active_idx < len(subs):
        sub = subs[active_idx]
        if sub['remaining_cp'] >= needed:
            consume = needed
            sub['remaining_cp'] -= needed
            needed = 0
        else:
            consume = sub['remaining_cp']
            needed -= consume
            sub['remaining_cp'] = 0
            active_idx += 1
        consumed_log.append((sub['id'], consume))
    
    assert_eq("FIFO: Sub1 fully consumed", subs[0]['remaining_cp'], 0.0)
    assert_eq("FIFO: Sub2 partial", subs[1]['remaining_cp'], 30.0, tolerance=0.01)
    assert_eq("FIFO: Needed satisfied", needed, 0.0, tolerance=0.01)
    assert_eq("FIFO: Two consumption events", len(consumed_log), 2)
    assert_eq("FIFO: First from Sub1 (100)", consumed_log[0], (1, 100.0))
    assert_eq("FIFO: Second from Sub2 (20)", consumed_log[1], (2, 20.0))


def test_fifo_exact_depletion():
    """Test FIFO when rescue exactly depletes a subscription."""
    print("\n=== Test: FIFO Agotamiento Exacto ===")
    
    subs = [{'id': 1, 'remaining_cp': 50.0}]
    needed = 50.0
    active_idx = 0
    
    while needed > 0.0001 and active_idx < len(subs):
        sub = subs[active_idx]
        if sub['remaining_cp'] >= needed:
            sub['remaining_cp'] -= needed
            needed = 0
        else:
            needed -= sub['remaining_cp']
            sub['remaining_cp'] = 0
            active_idx += 1
    
    assert_eq("Exact: Sub fully consumed", subs[0]['remaining_cp'], 0.0)
    assert_eq("Exact: Needed satisfied", needed, 0.0, tolerance=0.01)


def test_date_filtering():
    """Test date filtering logic (>= last date)."""
    print("\n=== Test: Filtro de Fechas ===")
    
    last_date = datetime.datetime(2024, 10, 1)
    
    movements = [
        {'date': '30/09/2024', 'type': 'COMPRA'},  # Before -> excluded
        {'date': '01/10/2024', 'type': 'VENTA'},    # Same day -> included
        {'date': '02/10/2024', 'type': 'COMPRA'},   # After -> included
    ]
    
    filtered = []
    for m in movements:
        d = datetime.datetime.strptime(m['date'], "%d/%m/%Y")
        if d >= last_date:
            filtered.append(m)
    
    assert_eq("Filter: 2 movements pass", len(filtered), 2)
    assert_eq("Filter: First is 01/10 VENTA", filtered[0]['date'], '01/10/2024')
    assert_eq("Filter: Second is 02/10 COMPRA", filtered[1]['date'], '02/10/2024')


def test_color_cycling():
    """Test that colors cycle correctly through the palette."""
    print("\n=== Test: Ciclo de Colores ===")
    
    from config import VIBRANT_COLORS
    
    assert_eq("Colors: 16 colors defined", len(VIBRANT_COLORS), 16)
    
    # Test cycling
    for i in range(20):
        color = VIBRANT_COLORS[i % len(VIBRANT_COLORS)]
        assert_eq(f"Color {i}: valid hex", len(color), 6)


def test_movements_json_structure():
    """Test that movements.json has correct structure."""
    print("\n=== Test: Estructura JSON ===")
    
    json_path = os.path.join(SCRIPT_DIR, 'movements.json')
    if not os.path.exists(json_path):
        print("  [SKIP] movements.json no existe")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert_eq("JSON: es lista", isinstance(data, list), True)
    
    if data:
        m = data[0]
        assert_eq("JSON: tiene 'date'", 'date' in m, True)
        assert_eq("JSON: tiene 'type'", 'type' in m, True)
        assert_eq("JSON: tiene 'cp'", 'cp' in m, True)
        assert_eq("JSON: tiene 'amount'", 'amount' in m, True)
        assert_eq("JSON: type valido", m['type'] in ('COMPRA', 'VENTA'), True)
        
        # Check chronological order
        dates = [datetime.datetime.strptime(x['date'], "%d/%m/%Y") for x in data]
        ordered = all(dates[i] <= dates[i+1] for i in range(len(dates)-1))
        assert_eq("JSON: orden cronologico", ordered, True)


def test_prueba_formula():
    """Test prueba column formulas are mathematically correct."""
    print("\n=== Test: Formulas Prueba AF/AG ===")
    
    # Simulate: COMPRA 1000 CPs at price 10 -> amount = 10000
    cp = 1000.0
    amount = 10000.0
    price = amount / cp  # 10.0
    
    # AF = IF(AB>1, AB, -AB) / AA  => For COMPRA: 10000/10 = 1000
    af = (amount if amount > 1 else -amount) / price
    # AG = AF - IF(Y=1, Z, -Z)  => For Sub (Y=1): 1000 - 1000 = 0
    ag = af - cp  # Y=1 so: af - z
    
    assert_eq("Prueba Sub: AF = CPs", af, cp, tolerance=0.01)
    assert_eq("Prueba Sub: AG = 0", ag, 0.0, tolerance=0.01)
    
    # For VENTA: cp=-500, amount=-5000, price=10
    cp_v = -500.0
    amount_v = -5000.0
    price_v = amount_v / cp_v  # 10.0
    
    af_v = (-amount_v if amount_v < 1 else amount_v) / price_v  # 5000/10 = 500
    ag_v = af_v - (-cp_v)  # Y=2 so: af - (-z) = 500 - 500 = 0
    
    assert_eq("Prueba Resc: AF = |CPs|", af_v, abs(cp_v), tolerance=0.01)
    assert_eq("Prueba Resc: AG = 0", ag_v, 0.0, tolerance=0.01)


def run_all():
    global PASSED, FAILED
    
    print("=" * 50)
    print("   FCI PIPELINE — TESTS UNITARIOS")
    print("=" * 50)
    
    test_fifo_logic()
    test_fifo_exact_depletion()
    test_date_filtering()
    test_color_cycling()
    test_movements_json_structure()
    test_prueba_formula()
    
    print("\n" + "=" * 50)
    total = PASSED + FAILED
    print(f"   Resultado: {PASSED}/{total} OK", end="")
    if FAILED:
        print(f" | {FAILED} FALLIDOS")
    else:
        print(" - TODOS LOS TESTS PASARON")
    print("=" * 50)
    
    return FAILED == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
