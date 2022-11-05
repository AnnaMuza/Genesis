-- Задача 1
SELECT *
FROM product.users
WHERE (gender = 'm' AND lang NOT IN ('ru', 'es'))
OR (gender = 'f' AND lower(app) = 'desktop' AND lang = 'ru');


-- Задача 2
SELECT count(DISTINCT sessions.user_id) * 100 / count(DISTINCT users.id) percentage
FROM product.users users
LEFT JOIN product.user_session_end sessions
ON users.id = sessions.user_id;


-- Задача 3
SELECT count(t.user_id) / count(id) * 100 percentage
FROM (SELECT user_id
      FROM product.user_session_end
      GROUP BY user_id
      HAVING count(*) > 2
      ) t
RIGHT JOIN product.users
ON id = t.user_id;


-- Задача 4
SELECT count(CASE WHEN session_number > 0 THEN 1 END) /
       count(CASE WHEN session_number = 0 THEN 1 END) sessions
FROM product.user_session_end;


-- Задача 5
SELECT app, gender, count(CASE WHEN session_number > 2 THEN 1 END) * 100 /
                    count(*) more_then_2_sessions
FROM (SELECT u.id, max(u.gender) gender, lower(max(u.app)) app, count(*) session_number
      FROM product.users u
      LEFT JOIN product.user_session_end sessions
      ON u.id = sessions.user_id
      GROUP BY u.id
      ) t
GROUP BY gender, app
ORDER BY more_then_2_sessions DESC;


-- Задача 6
SELECT app, gender, more_then_2_sessions
FROM (SELECT app, gender, count(CASE WHEN session_number > 2 THEN 1 END ) * 100 /
                          count(*) more_then_2_sessions
      FROM (SELECT u.id, max(u.gender) gender, lower(max(u.app)) app, count(*) session_number
            FROM product.users u
            LEFT JOIN product.user_session_end use
            ON u.id = use.user_id
            WHERE u.lang = 'en'
            GROUP BY u.id
            ) t1
      GROUP BY gender, app
      ) t2
WHERE more_then_2_sessions / 100 > 0.3
ORDER BY more_then_2_sessions DESC;


-- Задача 7
SELECT t1.user_app, messages_number, chats_number, messages_number / chats_number messages_per_chat
FROM (SELECT user_app, count(*) messages_number
      FROM product.activities
      WHERE activity_type = (SELECT id FROM dictionary.activity_types WHERE type = 'message')
      GROUP BY user_app
      ) t1
    INNER JOIN
    (SELECT user_app, count(*) chats_number
    FROM (SELECT user_app, user_id, contact_id
          FROM product.activities
          WHERE activity_type = (SELECT id FROM dictionary.activity_types WHERE type = 'message')
          UNION
          SELECT user_app, user_id, contact_id
          FROM product.activities
          WHERE activity_type = (SELECT id FROM dictionary.activity_types WHERE type = 'message')
          ) t3
    GROUP BY user_app
    ) t2
ON t1.user_app = t2.user_app;