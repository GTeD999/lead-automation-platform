# Novactiv Presentations

Плагин добавляет чистый REST API для получения всех данных объекта недвижимости из WordPress.

## Установка

1. Загрузите ZIP `novactiv-presentations.zip` в WordPress: `Плагины -> Добавить новый -> Загрузить плагин`.
2. Активируйте плагин `Novactiv Presentations`.
3. Откройте `Настройки -> Novactiv Presentations`.
4. API token можно оставить пустым на время теста. Если заполнить, n8n должен отправлять заголовок `X-Novactiv-Token`.

## Endpoint

```text
GET /wp-json/novactiv/v1/property/{ID}
```

Пример:

```text
https://novactiv.ru/wp-json/novactiv/v1/property/4131
```

Ответ включает:

- нормализованные поля: `title`, `city`, `address`, `area_m2`, `price`, `deal_type`, `segment`, `description`, `photos`;
- реальные поля плагина `novactiv-real-estate`: цена, адрес, район, координаты, площадь, этажи, агент, метро, видео, тур, изображения `_property_images`;
- `acf`: все поля ACF, если ACF установлен;
- `meta`: все поля `_property_*` без начального подчеркивания, например `_property_price` придет как `property_price`;
- `taxonomies`: все термины объекта;
- `source_url`, `published_at`, `updated_at`.
