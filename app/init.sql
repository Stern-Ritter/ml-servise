-- Инициализация тестовых данных

-- Очистка существующих данных
DELETE FROM predicts;
DELETE FROM predict_tasks;
DELETE FROM patients;
DELETE FROM transactions;
DELETE FROM balances;
DELETE FROM users;
DELETE FROM roles;

-- Сброс последовательностей
ALTER SEQUENCE roles_id_seq RESTART WITH 1;
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE balances_id_seq RESTART WITH 1;
ALTER SEQUENCE transactions_id_seq RESTART WITH 1;
ALTER SEQUENCE patients_id_seq RESTART WITH 1;
ALTER SEQUENCE predict_tasks_id_seq RESTART WITH 1;
ALTER SEQUENCE predicts_id_seq RESTART WITH 1;

-- Вставка ролей
INSERT INTO roles (name, created_at, updated_at) VALUES
('USER', NOW(), NOW()),
('ADMIN', NOW(), NOW());

-- Вставка пользователей (пароль: 'password123')
INSERT INTO users (login, email, display_name, password_hash, role_id, is_active, created_at, updated_at) VALUES
('admin_user', 'admin@example.com', 'Администратор', '$2b$12$LQv3c1yqBzwd0uG7AIQt/.WmdJZG.5XpE8V7aZb2WQn7eJNfK9XW6', 2, true, NOW(), NOW()),
('john_doe', 'john@example.com', 'Джон Доу', '$2b$12$LQv3c1yqBzwd0uG7AIQt/.WmdJZG.5XpE8V7aZb2WQn7eJNfK9XW6', 1, true, NOW(), NOW()),
('jane_smith', 'jane@example.com', 'Джейн Смит', '$2b$12$LQv3c1yqBzwd0uG7AIQt/.WmdJZG.5XpE8V7aZb2WQn7eJNfK9XW6', 1, true, NOW(), NOW()),
('test_user', 'test@example.com', 'Тестовый Пользователь', '$2b$12$LQv3c1yqBzwd0uG7AIQt/.WmdJZG.5XpE8V7aZb2WQn7eJNfK9XW6', 1, true, NOW(), NOW());

-- Вставка балансов
INSERT INTO balances (value, currency, user_id, created_at, updated_at) VALUES
(1000.00, 'RUB', 1, NOW(), NOW()),
(500.00, 'RUB', 2, NOW(), NOW()),
(750.00, 'RUB', 3, NOW(), NOW()),
(0.00, 'RUB', 4, NOW(), NOW());

-- Вставка транзакций
INSERT INTO transactions (type, amount, currency, description, user_id, created_at, updated_at) VALUES
('DEPOSIT', 1000.00, 'RUB', 'Начальный депозит', 1, NOW(), NOW()),
('DEPOSIT', 500.00, 'RUB', 'Начальный депозит', 2, NOW(), NOW()),
('WITHDRAWAL', 100.00, 'RUB', 'Оплата предсказания', 2, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
('DEPOSIT', 750.00, 'RUB', 'Начальный депозит', 3, NOW(), NOW()),
('DEPOSIT', 200.00, 'RUB', 'Пополнение баланса', 3, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days');

-- Вставка пациентов
INSERT INTO patients (
    age, gender, physical_activity_days_per_week, stress_level, bmi, 
    exercise_hours_per_week, sedentary_hours_per_day, sleep_hours_per_day,
    heart_rate, cholesterol, blood_sugar, triglycerides,
    smoking, alcohol_consumption, diabetes, obesity, family_history,
    created_at, updated_at
) VALUES
(45, 'MALE', 3, 6, 25.5, 5.0, 8.0, 7.0, 72.0, 200.0, 95.0, 150.0, false, true, false, false, true, NOW(), NOW()),
(38, 'FEMALE', 5, 3, 22.0, 7.0, 6.0, 8.0, 68.0, 180.0, 85.0, 120.0, false, false, false, false, false, NOW(), NOW()),
(52, 'MALE', 1, 8, 30.2, 1.0, 10.0, 5.0, 85.0, 240.0, 110.0, 220.0, true, true, true, true, true, NOW(), NOW()),
(29, 'FEMALE', 4, 4, 21.0, 6.0, 7.0, 8.0, 65.0, 170.0, 90.0, 100.0, false, false, false, false, false, NOW(), NOW()),
(60, 'MALE', 2, 7, 28.8, 3.0, 9.0, 6.0, 78.0, 220.0, 105.0, 180.0, true, false, false, true, false, NOW(), NOW());

-- Вставка задач на предсказание
INSERT INTO predict_tasks (patient_id, user_id, status, cost, created_at, updated_at) VALUES
(1, 2, 'COMPLETED', 100.00, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'),
(2, 3, 'COMPLETED', 100.00, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
(3, 2, 'FAILED', 100.00, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day'),
(4, 3, 'PROCESSING', 100.00, NOW(), NOW()),
(5, 1, 'PENDING', 100.00, NOW(), NOW());

-- Вставка результатов предсказаний
INSERT INTO predicts (prediction, probability, task_id, created_at, updated_at) VALUES
(true, 0.75, 1, NOW() - INTERVAL '3 days', NOW() - INTERVAL '3 days'),
(false, 0.15, 2, NOW() - INTERVAL '2 days', NOW() - INTERVAL '2 days'),
(true, 0.92, 3, NOW() - INTERVAL '1 day', NOW() - INTERVAL '1 day');

-- Вывод информации о вставленных данных
SELECT 'Roles inserted: ' || COUNT(*) FROM roles;
SELECT 'Users inserted: ' || COUNT(*) FROM users;
SELECT 'Balances inserted: ' || COUNT(*) FROM balances;
SELECT 'Transactions inserted: ' || COUNT(*) FROM transactions;
SELECT 'Patients inserted: ' || COUNT(*) FROM patients;
SELECT 'Predict tasks inserted: ' || COUNT(*) FROM predict_tasks;
SELECT 'Predicts inserted: ' || COUNT(*) FROM predicts;