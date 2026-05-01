"""
Модуль для генерации продаж на основе существующих данных Northwind
"""
import random
from datetime import datetime, timedelta
import logging

from postgres_utils import execute_query, get_records

logger = logging.getLogger(__name__)

# Конфигурация
ORDERS_PER_DAY_RANGE = (15, 45)
ITEMS_PER_ORDER_RANGE = (2, 8)
PRODUCTS_LIMIT = 50


def get_last_order_date(hook):
    """Получение последней даты заказа из БД"""
    result = execute_query("SELECT MAX(order_date) FROM orders", hook=hook)
    if result and len(result) > 0:
        return result[0]
    return None


def get_existing_references(hook):
    """Получение справочных данных из Northwind"""
    
    logger.info("📚 Загрузка справочников Northwind...")
    
    # Используем get_records для получения ВСЕХ строк
    customers = get_records("""
        SELECT customer_id, company_name, country 
        FROM customers
    """, hook=hook)
    logger.info(f"✅ customers: {len(customers)} записей")
    
    employees = get_records("""
        SELECT employee_id, first_name, last_name 
        FROM employees
    """, hook=hook)
    logger.info(f"✅ employees: {len(employees)} записей")
    
    products_raw = get_records("""
        SELECT product_id, product_name, unit_price 
        FROM products 
        WHERE discontinued = 0
    """, hook=hook)
    logger.info(f"✅ products_raw: {len(products_raw)} записей")
    
    # Выводим первые 5 товаров для проверки
    for i, row in enumerate(products_raw[:5]):
        logger.info(f"   Товар {i+1}: id={row[0]}, name={row[1]}, price={row[2]}")
    
    # Преобразуем товары в список словарей
    products = []
    for row in products_raw:
        if row and len(row) >= 3:
            products.append({
                'id': row[0],
                'name': row[1],
                'price': row[2]
            })
    
    shippers = get_records("""
        SELECT shipper_id, company_name 
        FROM shippers
    """, hook=hook)
    logger.info(f"✅ shippers: {len(shippers)} записей")
    
    logger.info(f"📊 ИТОГО: {len(customers)} клиентов, {len(employees)} сотрудников, {len(products)} товаров, {len(shippers)} перевозчиков")
    
    return {
        'customers': customers,
        'employees': employees,
        'products': products,
        'shippers': shippers,
    }


def is_working_day(date):
    """Проверка, является ли день рабочим (Пн-Пт)"""
    return date.weekday() < 5


def get_daily_orders_count():
    """Расчёт количества заказов в день"""
    base_orders = 30
    variation = random.uniform(0.7, 1.3)
    daily_orders = int(base_orders * variation)
    return max(ORDERS_PER_DAY_RANGE[0], min(daily_orders, ORDERS_PER_DAY_RANGE[1]))


def generate_order(refs, order_date, order_id):
    """Генерация одного заказа"""
    
    customer = random.choice(refs['customers'])
    employee = random.choice(refs['employees'])
    shipper = random.choice(refs['shippers'])
    
    customer_id = customer[0]
    customer_company = customer[1] if len(customer) > 1 else ''
    customer_country = customer[2] if len(customer) > 2 else 'USA'
    
    employee_id = employee[0]
    shipper_id = shipper[0]
    
    required_date = order_date + timedelta(days=random.randint(5, 14))
    shipped_date = order_date + timedelta(days=random.randint(2, 10)) if random.random() > 0.05 else None
    
    items_count = random.randint(ITEMS_PER_ORDER_RANGE[0], ITEMS_PER_ORDER_RANGE[1])
    used_products = set()
    order_details = []
    order_total = 0
    
    available_products = refs['products'][:PRODUCTS_LIMIT]
    
    for _ in range(items_count):
        if len(used_products) >= len(available_products):
            break
        
        if not available_products:
            break
            
        idx = random.randint(0, len(available_products) - 1)
        product = available_products[idx]
        product_id = product['id']
        
        if product_id not in used_products:
            used_products.add(product_id)
            quantity = random.randint(1, 12)
            discount = round(random.uniform(0, 0.20), 2)
            unit_price = product['price']
            total = round(unit_price * quantity * (1 - discount), 2)
            order_total += total
            
            order_details.append({
                'product_id': product_id,
                'unit_price': unit_price,
                'quantity': quantity,
                'discount': discount
            })
    
    freight = round(random.uniform(10, 250), 2)
    ship_name = f"{customer_company[:20]}" if customer_company else f"Order {order_id}"
    
    return {
        'order_id': order_id,
        'customer_id': customer_id,
        'employee_id': employee_id,
        'shipper_id': shipper_id,
        'order_date': order_date,
        'required_date': required_date,
        'shipped_date': shipped_date,
        'freight': freight,
        'order_total': order_total,
        'ship_name': ship_name,
        'ship_address': f"{random.randint(1, 999)} Business St",
        'ship_city': random.choice(['New York', 'Los Angeles', 'Chicago', 'Moscow', 'London', 'Berlin']),
        'ship_region': random.choice(['NY', 'CA', 'IL', 'MSK', 'LON', 'BER']),
        'ship_postal_code': str(random.randint(10000, 99999)),
        'ship_country': customer_country,
        'order_details': order_details
    }


def generate_orders_for_date_range(hook, refs, start_date, end_date):
    """Генерация заказов за период"""
    all_orders = []
    current_date = start_date
    total_orders = 0
    
    max_id_result = execute_query("SELECT COALESCE(MAX(order_id), 0) FROM orders", hook=hook)
    max_order_id = max_id_result[0] if max_id_result and len(max_id_result) > 0 else 0
    
    logger.info(f"📅 Генерация заказов с {start_date} по {end_date}")
    logger.info(f"   Последний order_id: {max_order_id}")
    
    while current_date <= end_date:
        if is_working_day(current_date):
            daily_orders = get_daily_orders_count()
            logger.info(f"   {current_date} (рабочий): +{daily_orders} заказов")
            
            for i in range(daily_orders):
                order_id = max_order_id + total_orders + i + 1
                order = generate_order(refs, current_date, order_id)
                all_orders.append(order)
            
            total_orders += daily_orders
        else:
            logger.info(f"   {current_date} (выходной): 0 заказов")
        
        current_date += timedelta(days=1)
    
    logger.info(f"📊 Итого сгенерировано {total_orders} заказов")
    return all_orders


def insert_orders_to_db(hook, orders):
    """Вставка заказов в БД"""
    created = 0
    total_amount = 0
    
    for order in orders:
        try:
            hook.run("""
                INSERT INTO orders (
                    order_id, customer_id, employee_id, order_date, required_date, 
                    shipped_date, ship_via, freight, ship_name, ship_address, 
                    ship_city, ship_region, ship_postal_code, ship_country
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, parameters=(
                order['order_id'],
                order['customer_id'],
                order['employee_id'],
                order['order_date'],
                order['required_date'],
                order['shipped_date'],
                order['shipper_id'],
                order['freight'],
                order['ship_name'],
                order['ship_address'],
                order['ship_city'],
                order['ship_region'],
                order['ship_postal_code'],
                order['ship_country']
            ))
            
            for detail in order['order_details']:
                hook.run("""
                    INSERT INTO order_details (order_id, product_id, unit_price, quantity, discount)
                    VALUES (%s, %s, %s, %s, %s)
                """, parameters=(
                    order['order_id'],
                    detail['product_id'],
                    detail['unit_price'],
                    detail['quantity'],
                    detail['discount']
                ))
            
            created += 1
            total_amount += order['order_total']
            
        except Exception as e:
            logger.error(f"Ошибка при вставке заказа {order['order_id']}: {e}")
            raise
    
    return created, total_amount


def get_generation_stats(hook):
    """Получение статистики после генерации"""
    stats = execute_query("""
        SELECT 
            COUNT(*) as total_orders,
            COALESCE(SUM(total_amount), 0) as total_amount,
            MIN(order_date) as first_order,
            MAX(order_date) as last_order
        FROM orders
    """, hook=hook)
    
    return {
        'total_orders': stats[0] if stats and len(stats) > 0 else 0,
        'total_amount': round(stats[1], 2) if stats and len(stats) > 1 and stats[1] else 0,
        'first_order': stats[2] if stats and len(stats) > 2 else None,
        'last_order': stats[3] if stats and len(stats) > 3 else None
    }