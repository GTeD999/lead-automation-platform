// Property data fixtures — three different property types to verify modularity
// Mirrors the WordPress/QuickDeal field schema from the brief.

window.PROPERTIES = {
  office: {
    title: "БЦ «Меркурий Тауэр», офис на 41 этаже",
    category: "commercial",
    property_type: "rent",
    commercial_type: "office",
    source_url: "https://example.com/object/MX-4187",
    quickdeal_id: "QD-89421",
    internal_id: "NV-MX-4187",
    published_at: "2026-04-12",
    updated_at: "2026-05-02",

    price: 8_950_000,
    currency: "RUB",
    price_period: "month",
    price_unit: "object",
    commission: "50% от месячной аренды",
    prepayment: "1 месяц",
    security_payment: "1 месяц",
    deposit_months: 1,
    prepay_months: 1,

    area_m2: 642,
    area_unit: "м²",
    ceiling_height: 3.4,
    floor: 41,
    floors_total: 75,
    layout: "Open space + 4 переговорные + кабинет руководителя",

    city: "Москва",
    region: "Москва",
    district: "Пресненский",
    sub_locality_name: "Москва-Сити",
    address: "1-й Красногвардейский проезд, 15",
    full_address: "Москва, Пресненский район, ММДЦ «Москва-Сити», 1-й Красногвардейский проезд, 15",
    latitude: 55.7494,
    longitude: 37.5378,
    metro: [
      { name: "Деловой центр", walk_min: 4, transport_min: null, line: "#0099cc" },
      { name: "Выставочная", walk_min: 7, transport_min: null, line: "#0099cc" },
      { name: "Международная", walk_min: 9, transport_min: null, line: "#0099cc" }
    ],

    photos: [
      { url: "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1600&q=80", caption: "Open space" },
      { url: "https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=1600&q=80", caption: "Переговорная" },
      { url: "https://images.unsplash.com/photo-1604328698692-f76ea9498e76?w=1600&q=80", caption: "Кабинет руководителя" },
      { url: "https://images.unsplash.com/photo-1545167622-3a6ac756afa4?w=1600&q=80", caption: "Зона ресепшн" },
      { url: "https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=1600&q=80", caption: "Лаунж-зона" },
      { url: "https://images.unsplash.com/photo-1568992687947-868a62a9f521?w=1600&q=80", caption: "Холл этажа" },
      { url: "https://images.unsplash.com/photo-1577412647305-991150c7d163?w=1600&q=80", caption: "Вид из окна", is_default: true },
      { url: "https://images.unsplash.com/photo-1582653291997-079a1c04e208?w=1600&q=80", caption: "План этажа", is_plan: true }
    ],
    video_review: "https://example.com/video",
    virtual_tour: "https://example.com/tour",

    renovation: "Дизайнерский, 2024",
    quality: "Премиум",
    building_type: "Бизнес-центр",
    commercial_building_type: "Офисный небоскрёб класса A+",
    building_name: "Меркурий Тауэр",
    built_year: 2013,
    cadastral_number: "77:01:0004042:1156",
    office_class: "A+",
    parking: "Подземная, гостевая",
    parking_places: 12,
    security: true,
    twenty_four_seven: true,
    internet: "Оптика, 1 Гбит/с",
    air_conditioner: "VRF-система",
    ventilation: "Приточно-вытяжная",
    fire_alarm: true,
    electric_capacity: "180 кВт",
    freight_elevator: true,

    manager: {
      name: "Анна Соколова",
      phone: "+7 (495) 120-34-56",
      email: "a.sokolova@example.com",
      organization: "Office Commercial",
      position: "Старший консультант, отдел офисной недвижимости",
      photo: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=400&q=80"
    },

    features: [
      "Прямой договор с собственником",
      "Панорамное остекление 270°",
      "Готов к въезду без отделки доп.",
      "Свободные часы доступа 24/7",
      "Личная зона ресепшн на этаже"
    ]
  },

  warehouse: {
    title: "Складской комплекс класса A, Новая Рига",
    category: "commercial",
    property_type: "rent",
    commercial_type: "warehouse",
    source_url: "https://example.com/object/WH-2210",
    quickdeal_id: "QD-77110",
    internal_id: "NV-WH-2210",
    published_at: "2026-03-28",

    price: 1_250_000,
    currency: "RUB",
    price_period: "month",
    price_unit: "object",
    commission: "1 месяц",

    area_m2: 4800,
    area_unit: "м²",
    ceiling_height: 12,
    open_area: 1500,

    city: "Москва",
    region: "Московская область",
    district: "Истринский",
    address: "Новорижское шоссе, 24 км",
    full_address: "Московская обл., Истринский р-н, Новорижское шоссе, 24 км",
    latitude: 55.8312,
    longitude: 36.9012,

    photos: [
      { url: "https://images.unsplash.com/photo-1566576912321-d58ddd7a6088?w=1600&q=80", caption: "Главный зал" },
      { url: "https://images.unsplash.com/photo-1553413077-190dd305871c?w=1600&q=80", caption: "Стеллажные системы" },
      { url: "https://images.unsplash.com/photo-1601598851547-4302969d0614?w=1600&q=80", caption: "Зона погрузки" },
      { url: "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=1600&q=80", caption: "Внешний вид" }
    ],

    quality: "Класс A",
    building_type: "Складской комплекс",
    commercial_building_type: "Логистический парк",
    built_year: 2021,
    parking: "Грузовая стоянка",
    parking_places: 30,
    security: true,
    twenty_four_seven: true,
    fire_alarm: true,
    electric_capacity: "350 кВт",
    truck_entrance: true,
    ramp: true,
    railway: false,
    responsible_storage: true,
    service_three_pl: true,
    heating_supply: true,
    water_supply: true,
    sewerage_supply: true,

    manager: {
      name: "Дмитрий Воронин",
      phone: "+7 (495) 120-34-78",
      email: "d.voronin@example.com",
      organization: "Office Industrial",
      position: "Руководитель направления «Складская недвижимость»",
      photo: "https://images.unsplash.com/photo-1560250097-0b93528c311a?w=400&q=80"
    },

    features: [
      "Прямой въезд фуры",
      "12 доковых ворот с гидравликой",
      "Антипылевые полы с упрочнённым топингом",
      "Собственная подстанция"
    ]
  },

  apartment: {
    title: "Резиденция «Скай-Вью», 4-комнатная квартира с террасой",
    category: "residential",
    property_type: "sale",
    source_url: "https://example.com/object/RS-9001",
    quickdeal_id: "QD-90011",
    internal_id: "NV-RS-9001",
    published_at: "2026-04-20",

    price: 187_500_000,
    currency: "RUB",
    sale_type: "Свободная продажа",
    estimated_payback_years: null,

    area_m2: 218,
    area_unit: "м²",
    living_space: 142,
    kitchen_space: 28,
    rooms: 4,
    floor: 32,
    floors_total: 38,
    ceiling_height: 3.2,
    layout: "4 спальни, 3 санузла, кухня-гостиная, гардеробная, терраса 42 м²",

    city: "Москва",
    region: "Москва",
    district: "Хамовники",
    sub_locality_name: "Хамовники",
    address: "Пречистенская набережная, 7",
    full_address: "Москва, Хамовники, Пречистенская набережная, 7, корп. 2",
    latitude: 55.7421,
    longitude: 37.5972,
    metro: [
      { name: "Кропоткинская", walk_min: 8, transport_min: null, line: "#dc2626" },
      { name: "Парк культуры", walk_min: 11, transport_min: null, line: "#dc2626" }
    ],

    photos: [
      { url: "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1600&q=80", caption: "Гостиная с видом на Москва-реку" },
      { url: "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1600&q=80", caption: "Кухня-столовая" },
      { url: "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=1600&q=80", caption: "Главная спальня" },
      { url: "https://images.unsplash.com/photo-1631679706909-1844bbd07221?w=1600&q=80", caption: "Ванная мастер-сьют" },
      { url: "https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?w=1600&q=80", caption: "Терраса" },
      { url: "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1600&q=80", caption: "Гардеробная" }
    ],

    renovation: "Дизайнерский ремонт под ключ",
    quality: "De Luxe",
    building_type: "Жилой комплекс",
    building_name: "Sky View Residence",
    built_year: 2022,
    parking: "Подземная, 2 м/м включены в стоимость",
    parking_places: 2,
    security: true,
    twenty_four_seven: true,
    air_conditioner: "Канальная",
    ventilation: "С рекуперацией",

    manager: {
      name: "Екатерина Лазарева",
      phone: "+7 (495) 120-34-90",
      email: "e.lazareva@example.com",
      organization: "Office Private",
      position: "Эксперт по элитной жилой недвижимости",
      photo: "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=400&q=80"
    },

    features: [
      "Видовой 32-й этаж",
      "Терраса с панорамой на Кремль",
      "Концьерж-сервис",
      "Резидентский лаунж и винотека",
      "Спа и бассейн в доме"
    ]
  }
};
