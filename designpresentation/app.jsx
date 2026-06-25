/* global React, ReactDOM, PROPERTIES */
const { useState, useEffect, useMemo, useRef, useCallback } = React;

/* ─── helpers ─── */
const fmtMoney = (n, currency = "RUB") => {
  if (n == null) return "—";
  const sym = currency === "RUB" ? "₽" : currency;
  return new Intl.NumberFormat("ru-RU", { maximumFractionDigits: 0 }).format(n) + " " + sym;
};
const fmtNum = (n) => n == null ? "—" : new Intl.NumberFormat("ru-RU").format(n);

const PERIOD_LABEL = { month: "/ мес", year: "/ год", day: "/ сутки" };
const CATEGORY_LABEL = { commercial: "Коммерческая", residential: "Жилая" };
const TYPE_LABEL = { rent: "Аренда", sale: "Продажа" };
const COMMERCIAL_LABEL = {
  office: "Офис",
  warehouse: "Склад",
  retail: "Торговое помещение",
  free_purpose: "Свободного назначения",
  manufacturing: "Производство"
};

const PROP_RU = {
  renovation: "Ремонт",
  quality: "Класс",
  building_type: "Тип здания",
  commercial_building_type: "Тип бизнес-центра",
  building_name: "Название здания",
  built_year: "Год постройки",
  cadastral_number: "Кадастровый номер",
  office_class: "Класс офиса",
  parking: "Парковка",
  parking_places: "Машиномест",
  security: "Охрана",
  twenty_four_seven: "Доступ 24/7",
  internet: "Интернет",
  air_conditioner: "Кондиционирование",
  ventilation: "Вентиляция",
  fire_alarm: "Пожарная сигнализация",
  electric_capacity: "Электрическая мощность",
  freight_elevator: "Грузовой лифт",
  truck_entrance: "Заезд для фур",
  ramp: "Рампа",
  railway: "Железнодорожная ветка",
  open_area: "Открытая площадка, м²",
  responsible_storage: "Ответственное хранение",
  service_three_pl: "3PL сервис",
  water_supply: "Водоснабжение",
  gas_supply: "Газоснабжение",
  sewerage_supply: "Канализация",
  heating_supply: "Отопление",
  electricity_supply: "Электроснабжение",
  living_space: "Жилая площадь, м²",
  kitchen_space: "Кухня, м²",
  rooms: "Комнат",
  ceiling_height: "Высота потолков, м",
  layout: "Планировка",
  cadastral: "Кадастр",
  sale_type: "Тип сделки",
  prepayment: "Предоплата",
  security_payment: "Обеспечительный платёж",
  commission: "Комиссия"
};

const formatBool = (v) => v === true ? "Да" : (v === false ? "Нет" : v);

/* ─── Icons (inline svg) ─── */
const Icon = ({ name, size = 16 }) => {
  const paths = {
    pin: <><path d="M12 21s-7-7.5-7-12a7 7 0 1 1 14 0c0 4.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/></>,
    phone: <><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92z"/></>,
    mail: <><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m2 6 10 7L22 6"/></>,
    share: <><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98M15.41 6.51l-6.82 3.98"/></>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/></>,
    check: <path d="M5 12l5 5L20 7"/>,
    chevronL: <path d="m15 18-6-6 6-6"/>,
    chevronR: <path d="m9 6 6 6-6 6"/>,
    close: <><path d="M18 6 6 18"/><path d="m6 6 12 12"/></>,
    eye: <><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></>,
    play: <path d="m6 4 14 8-14 8V4z"/>,
    grid: <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
};

/* ─── Sections ─── */
function Hero({ p, onOpenLightbox }) {
  const mainPhoto = p.photos?.find(x => x.is_default) || p.photos?.[0];
  const periodLabel = p.property_type === "rent" ? (PERIOD_LABEL[p.price_period] || "/ мес") : "";

  return (
    <section className="hero" data-screen-label="Hero">
      <div className="hero-info">
        <div className="crumbs">
          <span>{CATEGORY_LABEL[p.category]}</span>
          <span>{TYPE_LABEL[p.property_type]}</span>
          {p.commercial_type && <span>{COMMERCIAL_LABEL[p.commercial_type]}</span>}
          {p.city && <span>{p.city}</span>}
        </div>

        <h1 className="hero-title">{p.title}</h1>

        {p.full_address && (
          <div className="hero-address">
            <Icon name="pin" size={18} />
            <span>{p.full_address}</span>
          </div>
        )}

        <div className="hero-price-block">
          <div className="hero-price">
            {fmtMoney(p.price, p.currency)}
            {periodLabel && <span className="period">{periodLabel}</span>}
          </div>
          <div className="hero-price-meta">
            {p.area_m2 && p.property_type === "rent" && (
              <span>≈ <b>{fmtMoney(Math.round(p.price * 12 / p.area_m2), p.currency)}</b>/{p.area_unit}/год</span>
            )}
            {p.area_m2 && p.property_type === "sale" && (
              <span>≈ <b>{fmtMoney(Math.round(p.price / p.area_m2), p.currency)}</b>/{p.area_unit}</span>
            )}
            {p.commission && <span>Комиссия: <b>{p.commission}</b></span>}
          </div>
        </div>

        <div className="hero-stats">
          {p.area_m2 && (
            <div className="hero-stat">
              <div className="lbl">Площадь</div>
              <div className="val">{fmtNum(p.area_m2)}<small>{p.area_unit}</small></div>
            </div>
          )}
          {p.floor != null && (
            <div className="hero-stat">
              <div className="lbl">Этаж</div>
              <div className="val">{p.floor}{p.floors_total && <small>/ {p.floors_total}</small>}</div>
            </div>
          )}
          {p.rooms != null && (
            <div className="hero-stat">
              <div className="lbl">Комнат</div>
              <div className="val">{p.rooms}</div>
            </div>
          )}
          {p.ceiling_height && p.rooms == null && (
            <div className="hero-stat">
              <div className="lbl">Потолки</div>
              <div className="val">{p.ceiling_height}<small>м</small></div>
            </div>
          )}
          {p.office_class && p.floor == null && (
            <div className="hero-stat">
              <div className="lbl">Класс</div>
              <div className="val">{p.office_class}</div>
            </div>
          )}
          {!p.rooms && !p.ceiling_height && !p.office_class && p.built_year && (
            <div className="hero-stat">
              <div className="lbl">Год постройки</div>
              <div className="val">{p.built_year}</div>
            </div>
          )}
        </div>

        <div className="hero-tags">
          {p.office_class && <span className="tag accent">Класс {p.office_class}</span>}
          {p.quality && <span className="tag">{p.quality}</span>}
          {p.renovation && <span className="tag">{p.renovation}</span>}
          {p.twenty_four_seven && <span className="tag">24/7</span>}
          {p.parking && <span className="tag">Парковка</span>}
        </div>
      </div>

      <div className="hero-photo" onClick={() => onOpenLightbox(0)}>
        {mainPhoto ? (
          <img src={mainPhoto.url} alt={p.title} />
        ) : (
          <Placeholder label="фото объекта" />
        )}
        <div className="hero-photo-overlay">
          <span className="hero-photo-id">{p.internal_id || p.quickdeal_id}</span>
          {p.photos?.length > 0 && (
            <span className="hero-photo-count">
              <Icon name="grid" size={13} /> {p.photos.length} фото
            </span>
          )}
        </div>
      </div>
    </section>
  );
}

function Placeholder({ label }) {
  return (
    <div style={{
      position: "absolute", inset: 0,
      backgroundImage: "repeating-linear-gradient(45deg, rgba(255,255,255,.04) 0 12px, transparent 12px 24px)",
      display: "flex", alignItems: "center", justifyContent: "center",
      color: "var(--text-faint)", fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".1em", textTransform: "uppercase"
    }}>{label}</div>
  );
}

function Gallery({ p, onOpen }) {
  const trackRef = useRef(null);
  const [active, setActive] = useState(0);
  const photos = p.photos || [];
  if (photos.length === 0) return null;

  const scrollTo = (i) => {
    setActive(i);
    const el = trackRef.current?.children[i];
    el?.scrollIntoView({ behavior: "smooth", inline: "start", block: "nearest" });
  };

  const nav = (dir) => {
    const next = Math.max(0, Math.min(photos.length - 1, active + dir));
    scrollTo(next);
  };

  return (
    <section className="block" data-screen-label="Gallery">
      <div className="block-head">
        <div>
          <div className="eyebrow">01 — Галерея</div>
          <h2>Фото объекта</h2>
        </div>
        <button className="btn" onClick={() => onOpen(0)}>
          <Icon name="eye" /> Открыть в полном размере
        </button>
      </div>
      <div className="gallery">
        <button className="gallery-nav prev" onClick={() => nav(-1)}><Icon name="chevronL" /></button>
        <button className="gallery-nav next" onClick={() => nav(1)}><Icon name="chevronR" /></button>
        <div className="gallery-track" ref={trackRef}>
          {photos.map((ph, i) => (
            <div className="gallery-item" key={i}
                 style={{ aspectRatio: i % 3 === 0 ? "4/3" : (i % 3 === 1 ? "3/4" : "16/10") }}
                 onClick={() => onOpen(i)}>
              <img src={ph.url} alt={ph.caption || ""} loading="lazy" />
              {ph.caption && <div className="cap">{ph.caption}</div>}
            </div>
          ))}
        </div>
        <div className="gallery-thumbs">
          {photos.map((ph, i) => (
            <div key={i} className={"gallery-thumb" + (i === active ? " active" : "")} onClick={() => scrollTo(i)}>
              <img src={ph.url} alt="" loading="lazy" />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Finance({ p }) {
  const cells = [];
  if (p.price != null) {
    cells.push({ lbl: "Цена", val: fmtMoney(p.price, p.currency), sub: p.property_type === "rent" ? "в месяц" : "к оплате" });
  }
  if (p.area_m2 && p.price && p.property_type === "rent") {
    cells.push({ lbl: "Ставка", val: fmtMoney(Math.round(p.price * 12 / p.area_m2), p.currency), sub: `за ${p.area_unit}/год` });
  }
  if (p.area_m2 && p.price && p.property_type === "sale") {
    cells.push({ lbl: "Цена за метр", val: fmtMoney(Math.round(p.price / p.area_m2), p.currency), sub: `за ${p.area_unit}` });
  }
  if (p.commission) cells.push({ lbl: "Комиссия", val: p.commission, sub: "" });
  if (p.prepayment) cells.push({ lbl: "Предоплата", val: p.prepayment, sub: "" });
  if (p.security_payment) cells.push({ lbl: "Обеспечительный платёж", val: p.security_payment, sub: "" });
  if (p.deposit_months) cells.push({ lbl: "Депозит", val: `${p.deposit_months} мес`, sub: "" });
  if (p.sale_type) cells.push({ lbl: "Тип сделки", val: p.sale_type, sub: "" });
  if (p.estimated_payback_years) cells.push({ lbl: "Окупаемость", val: `${p.estimated_payback_years} лет`, sub: "" });
  if (p.profitability) cells.push({ lbl: "Доходность", val: `${p.profitability}%`, sub: "годовых" });

  if (cells.length === 0) return null;

  return (
    <section className="block" data-screen-label="Finance">
      <div className="block-head">
        <div>
          <div className="eyebrow">02 — Условия</div>
          <h2>Финансовые условия</h2>
        </div>
      </div>
      <div className="finance">
        {cells.map((c, i) => (
          <div className="finance-cell" key={i}>
            <div className="lbl">{c.lbl}</div>
            <div className="val">{c.val}</div>
            {c.sub && <div className="sub">{c.sub}</div>}
          </div>
        ))}
      </div>
    </section>
  );
}

function KeyParams({ p }) {
  const specs = [];
  const push = (k, v) => v != null && v !== "" && specs.push([k, v]);

  push("Площадь", p.area_m2 && `${fmtNum(p.area_m2)} ${p.area_unit}`);
  push("Жилая площадь", p.living_space && `${p.living_space} м²`);
  push("Кухня", p.kitchen_space && `${p.kitchen_space} м²`);
  push("Комнат", p.rooms);
  push("Этаж", p.floor != null && (p.floors_total ? `${p.floor} из ${p.floors_total}` : p.floor));
  push("Высота потолков", p.ceiling_height && `${p.ceiling_height} м`);
  push("Планировка", p.layout);
  push("Открытая площадка", p.open_area && `${p.open_area} м²`);
  push("Класс объекта", p.office_class || p.quality);
  push("Год постройки", p.built_year);

  if (specs.length === 0) return null;

  return (
    <section className="block" data-screen-label="KeyParams">
      <div className="block-head">
        <div>
          <div className="eyebrow">03 — Параметры</div>
          <h2>Ключевые параметры</h2>
        </div>
      </div>
      <dl className="specs">
        {specs.map(([k, v], i) => (
          <div className="spec" key={i}>
            <dt>{k}</dt>
            <dd>{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function Location({ p }) {
  if (!p.address && !p.metro?.length) return null;

  // Schematic map: position pin + metro stations using random-but-stable offsets
  const stations = (p.metro || []).slice(0, 4);

  return (
    <section className="block" data-screen-label="Location">
      <div className="block-head">
        <div>
          <div className="eyebrow">04 — Локация</div>
          <h2>Локация и транспорт</h2>
        </div>
        {p.full_address && (
          <div style={{ color: "var(--text-dim)", fontSize: 13, textAlign: "right", maxWidth: 420 }}>
            {p.full_address}
          </div>
        )}
      </div>
      <div className="location">
        <div className="map-frame">
          <svg className="map-svg" viewBox="0 0 600 400" preserveAspectRatio="xMidYMid slice">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="var(--line)" strokeWidth="0.5"/>
              </pattern>
              <radialGradient id="glow" cx="50%" cy="50%">
                <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.15"/>
                <stop offset="100%" stopColor="var(--accent)" stopOpacity="0"/>
              </radialGradient>
            </defs>
            <rect width="600" height="400" fill="var(--bg-elev2)"/>
            <rect width="600" height="400" fill="url(#grid)"/>
            <circle cx="300" cy="200" r="180" fill="url(#glow)"/>
            {/* Roads */}
            <path d="M0 200 Q 200 180 300 200 T 600 220" stroke="var(--line-strong)" strokeWidth="2" fill="none"/>
            <path d="M300 0 Q 280 150 300 200 T 320 400" stroke="var(--line-strong)" strokeWidth="2" fill="none"/>
            <path d="M50 50 L 250 180 L 400 100 L 580 320" stroke="var(--line)" strokeWidth="1" fill="none"/>
            <path d="M100 380 L 230 250 L 420 280 L 550 50" stroke="var(--line)" strokeWidth="1" fill="none"/>
            {/* River-ish */}
            <path d="M0 320 Q 150 300 300 330 T 600 310" stroke="rgba(80,140,200,0.15)" strokeWidth="14" fill="none"/>
            {/* Blocks */}
            {Array.from({length: 12}).map((_, i) => {
              const x = (i*73 + 30) % 540;
              const y = (i*97 + 50) % 340;
              return <rect key={i} x={x} y={y} width="36" height="28" fill="var(--bg-elev)" stroke="var(--line)" strokeWidth="0.5" rx="2"/>;
            })}
          </svg>
          <div className="map-pin" style={{ left: "50%", top: "50%" }}>
          </div>
          {stations.map((s, i) => {
            const positions = [
              { left: "32%", top: "38%" },
              { left: "66%", top: "44%" },
              { left: "44%", top: "70%" },
              { left: "70%", top: "28%" }
            ];
            return (
              <div key={i} style={{
                position: "absolute", ...positions[i],
                display: "flex", alignItems: "center", gap: 6,
                transform: "translate(-50%,-50%)"
              }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: s.line || "#888", border: "2px solid var(--bg)" }}/>
                <div style={{ fontSize: 11, color: "var(--text-dim)", fontFamily: "var(--mono)", background: "var(--bg)", padding: "2px 6px", borderRadius: 4, whiteSpace: "nowrap" }}>
                  м. {s.name}
                </div>
              </div>
            );
          })}
        </div>

        <div className="card">
          {stations.length > 0 ? (
            <>
              <div className="eyebrow" style={{ marginBottom: 12 }}>Метро рядом</div>
              <div className="metro-list">
                {stations.map((s, i) => (
                  <div className="metro-item" key={i}>
                    <div className="metro-circle" style={{ background: s.line || "#888" }}/>
                    <div className="metro-name">{s.name}</div>
                    <div className="metro-time">
                      {s.walk_min ? `🚶 ${s.walk_min} мин` : ""}
                      {s.transport_min ? ` · 🚗 ${s.transport_min} мин` : ""}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <div style={{ color: "var(--text-dim)", fontSize: 14 }}>
              {p.full_address}
            </div>
          )}
          {p.district && (
            <div style={{ marginTop: 16, paddingTop: 16, borderTop: "1px solid var(--line)", fontSize: 13, color: "var(--text-dim)" }}>
              <div style={{ color: "var(--text-faint)", fontSize: 11, fontFamily: "var(--mono)", textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 6 }}>Район</div>
              {p.district}{p.sub_locality_name && p.sub_locality_name !== p.district ? `, ${p.sub_locality_name}` : ""}
            </div>
          )}
        </div>
      </div>
    </section>
  );
}

function Specs({ p }) {
  // Show curated "characteristics" — building/utilities specifics
  const groups = [
    {
      title: "Здание",
      items: [
        ["building_name", p.building_name],
        ["commercial_building_type", p.commercial_building_type],
        ["building_type", p.building_type],
        ["built_year", p.built_year],
        ["office_class", p.office_class],
        ["renovation", p.renovation],
        ["cadastral_number", p.cadastral_number],
      ]
    },
    {
      title: "Инфраструктура",
      items: [
        ["parking", p.parking],
        ["parking_places", p.parking_places],
        ["security", formatBool(p.security)],
        ["twenty_four_seven", formatBool(p.twenty_four_seven)],
        ["fire_alarm", formatBool(p.fire_alarm)],
        ["freight_elevator", formatBool(p.freight_elevator)],
        ["truck_entrance", formatBool(p.truck_entrance)],
        ["ramp", formatBool(p.ramp)],
        ["railway", formatBool(p.railway)],
      ]
    },
    {
      title: "Инженерия",
      items: [
        ["air_conditioner", p.air_conditioner],
        ["ventilation", p.ventilation],
        ["internet", p.internet],
        ["electric_capacity", p.electric_capacity],
        ["heating_supply", formatBool(p.heating_supply)],
        ["water_supply", formatBool(p.water_supply)],
        ["sewerage_supply", formatBool(p.sewerage_supply)],
        ["gas_supply", formatBool(p.gas_supply)],
      ]
    }
  ];

  const filtered = groups
    .map(g => ({ ...g, items: g.items.filter(([_, v]) => v != null && v !== "" && v !== "Нет") }))
    .filter(g => g.items.length > 0);

  if (filtered.length === 0) return null;

  return (
    <section className="block" data-screen-label="Specs">
      <div className="block-head">
        <div>
          <div className="eyebrow">05 — Характеристики</div>
          <h2>Характеристики</h2>
        </div>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(filtered.length, 3)}, 1fr)`, gap: 16 }}>
        {filtered.map((g, gi) => (
          <div className="card" key={gi}>
            <div className="eyebrow" style={{ marginBottom: 14 }}>{g.title}</div>
            <dl style={{ margin: 0, display: "flex", flexDirection: "column" }}>
              {g.items.map(([k, v], i) => (
                <div className="spec" key={i} style={{ flexDirection: "row" }}>
                  <dt style={{ flex: 1 }}>{PROP_RU[k] || k}</dt>
                  <dd style={{ maxWidth: "55%" }}>{v}</dd>
                </div>
              ))}
            </dl>
          </div>
        ))}
      </div>
    </section>
  );
}

function Features({ p }) {
  if (!p.features?.length) return null;
  return (
    <section className="block" data-screen-label="Features">
      <div className="block-head">
        <div>
          <div className="eyebrow">06 — Преимущества</div>
          <h2>Что отличает объект</h2>
        </div>
      </div>
      <div className="features">
        {p.features.map((f, i) => (
          <div className="feature" key={i}>
            <div className="feature-dot"><Icon name="check" size={13} /></div>
            <div>{f}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Calculator({ p }) {
  const isRent = p.property_type === "rent";
  const isSale = p.property_type === "sale";

  const [downpct, setDownpct] = useState(30);
  const [years, setYears] = useState(15);
  const [rate, setRate] = useState(14);

  const [occ, setOcc] = useState(95);
  const [opex, setOpex] = useState(20);

  if (!p.price) return null;

  let result, label, sub;
  if (isSale) {
    const principal = p.price * (1 - downpct / 100);
    const monthly = (rate / 100 / 12);
    const n = years * 12;
    const pay = principal * monthly / (1 - Math.pow(1 + monthly, -n));
    result = fmtMoney(Math.round(pay), p.currency);
    label = "Ежемесячный платёж по ипотеке";
    sub = `Первый взнос ${fmtMoney(Math.round(p.price * downpct / 100), p.currency)} · кредит ${years} лет под ${rate}%`;
  } else {
    const yearlyIncome = p.price * 12 * (occ / 100) * (1 - opex / 100);
    result = fmtMoney(Math.round(yearlyIncome), p.currency);
    label = "Чистый годовой доход арендодателя";
    sub = `Заполняемость ${occ}% · операционные расходы ${opex}%`;
  }

  return (
    <section className="block" data-screen-label="Calculator">
      <div className="block-head">
        <div>
          <div className="eyebrow">07 — Калькулятор</div>
          <h2>{isSale ? "Калькулятор ипотеки" : "Калькулятор доходности"}</h2>
        </div>
      </div>
      <div className="card">
        <div className="calc">
          <div className="calc-controls">
            {isSale ? (
              <>
                <div className="calc-row">
                  <label><span>Первоначальный взнос</span><b>{downpct}%</b></label>
                  <input type="range" min="10" max="90" step="5" value={downpct} onChange={(e) => setDownpct(+e.target.value)} />
                </div>
                <div className="calc-row">
                  <label><span>Срок кредита</span><b>{years} лет</b></label>
                  <input type="range" min="5" max="30" value={years} onChange={(e) => setYears(+e.target.value)} />
                </div>
                <div className="calc-row">
                  <label><span>Ставка</span><b>{rate}%</b></label>
                  <input type="range" min="6" max="22" step="0.5" value={rate} onChange={(e) => setRate(+e.target.value)} />
                </div>
              </>
            ) : (
              <>
                <div className="calc-row">
                  <label><span>Среднегодовая заполняемость</span><b>{occ}%</b></label>
                  <input type="range" min="60" max="100" value={occ} onChange={(e) => setOcc(+e.target.value)} />
                </div>
                <div className="calc-row">
                  <label><span>Операционные расходы</span><b>{opex}%</b></label>
                  <input type="range" min="0" max="50" value={opex} onChange={(e) => setOpex(+e.target.value)} />
                </div>
              </>
            )}
          </div>
          <div className="calc-result">
            <div className="lbl">{label}</div>
            <div className="big">{result}</div>
            <div className="sub">{sub}</div>
          </div>
        </div>
      </div>
    </section>
  );
}

function AllData({ p }) {
  // Show ALL non-null/non-handled fields as a tidy meta-list
  const SHOWN = new Set([
    "title","photos","manager","features","metro","latitude","longitude",
    "price","currency","area_m2","area_unit","floor","floors_total","rooms",
    "ceiling_height","living_space","kitchen_space","layout",
    "category","property_type","commercial_type","commission","prepayment",
    "security_payment","deposit_months","sale_type","profitability","estimated_payback_years",
    "open_area","city","region","district","sub_locality_name","address","full_address",
    "office_class","quality","renovation","building_name","commercial_building_type","building_type",
    "built_year","cadastral_number","parking","parking_places","security","twenty_four_seven",
    "fire_alarm","freight_elevator","truck_entrance","ramp","railway","air_conditioner",
    "ventilation","internet","electric_capacity","heating_supply","water_supply",
    "sewerage_supply","gas_supply","electricity_supply","price_period","price_unit",
    "video_review","virtual_tour","default_image","house_main_image",
    "responsible_storage","service_three_pl","prepay_months","rent_pledge","net_profit",
  ]);
  const items = Object.entries(p).filter(([k, v]) => !SHOWN.has(k) && v != null && v !== "" && typeof v !== "object");
  if (items.length === 0) {
    // fall back to meta of source
    return (
      <section className="block" data-screen-label="Meta">
        <div className="block-head">
          <div>
            <div className="eyebrow">08 — Документы</div>
            <h2>Идентификация и источники</h2>
          </div>
        </div>
        <dl className="meta-list">
          {p.internal_id && <div className="meta-item"><dt>Внутренний ID</dt><dd>{p.internal_id}</dd></div>}
          {p.quickdeal_id && <div className="meta-item"><dt>QuickDeal ID</dt><dd>{p.quickdeal_id}</dd></div>}
          {p.source_url && <div className="meta-item"><dt>Источник</dt><dd><a href={p.source_url} style={{ color: "var(--accent)" }}>Ссылка</a></dd></div>}
          {p.published_at && <div className="meta-item"><dt>Опубликовано</dt><dd>{p.published_at}</dd></div>}
          {p.updated_at && <div className="meta-item"><dt>Обновлено</dt><dd>{p.updated_at}</dd></div>}
          {p.cadastral_number && <div className="meta-item"><dt>Кадастр</dt><dd>{p.cadastral_number}</dd></div>}
        </dl>
      </section>
    );
  }
  return (
    <section className="block" data-screen-label="AllData">
      <div className="block-head">
        <div>
          <div className="eyebrow">08 — Все данные</div>
          <h2>Полная карточка</h2>
        </div>
      </div>
      <dl className="meta-list">
        {items.map(([k, v], i) => (
          <div className="meta-item" key={i}>
            <dt>{PROP_RU[k] || k}</dt>
            <dd>{formatBool(v)}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}

function StickyPanel({ p, onShare }) {
  const [sent, setSent] = useState(false);
  const submit = (e) => {
    e.preventDefault();
    setSent(true);
    setTimeout(() => setSent(false), 4000);
  };
  const periodLabel = p.property_type === "rent" ? (PERIOD_LABEL[p.price_period] || "/ мес") : "";

  return (
    <aside className="sticky-panel">
      <div className="price-card">
        <div className="lbl">{p.property_type === "rent" ? "Аренда" : "Продажа"}</div>
        <div className="price">{fmtMoney(p.price, p.currency)}</div>
        <div className="period">{periodLabel || (p.area_m2 ? `${fmtMoney(Math.round(p.price / p.area_m2), p.currency)} / ${p.area_unit}` : "")}</div>
      </div>

      {p.manager && (
        <div className="agent-card">
          <div className="agent-head">
            <div className="agent-photo">
              {p.manager.photo ? <img src={p.manager.photo} alt={p.manager.name} /> : <Placeholder label="фото" />}
            </div>
            <div style={{ minWidth: 0 }}>
              <h3 className="agent-name">{p.manager.name}</h3>
              <div className="agent-pos">{p.manager.position}</div>
              <div className="agent-org">{p.manager.organization}</div>
            </div>
          </div>

          <div className="agent-actions">
            {p.manager.phone && (
              <div className="contact-line">
                <Icon name="phone" />
                <a href={`tel:${p.manager.phone.replace(/\s/g, "")}`}>{p.manager.phone}</a>
              </div>
            )}
            {p.manager.email && (
              <div className="contact-line">
                <Icon name="mail" />
                <a href={`mailto:${p.manager.email}`}>{p.manager.email}</a>
              </div>
            )}
          </div>

          <form className="form" onSubmit={submit}>
            <input placeholder="Ваше имя" required />
            <input placeholder="Телефон" type="tel" required />
            <textarea placeholder="Ваш вопрос (необязательно)"/>
            <button className="btn btn-primary" type="submit">Записаться на показ</button>
            {sent && <div className="form-success">Заявка отправлена. {p.manager.name} свяжется в течение 30 минут.</div>}
          </form>
        </div>
      )}

      <div className="share-card">
        <div className="eyebrow">Поделиться</div>
        <div className="share-row">
          {[
            { l: "TG", n: "telegram" },
            { l: "WA", n: "whatsapp" },
            { l: "VK", n: "vk" },
            { l: "URL", n: "copy" }
          ].map(s => (
            <button key={s.n} className="share-btn" onClick={() => onShare(s.n)} title={s.n}>
              <span style={{ fontFamily: "var(--mono)", fontSize: 12, letterSpacing: ".05em" }}>{s.l}</span>
            </button>
          ))}
        </div>
        <button className="btn" style={{ width: "100%", justifyContent: "center", marginTop: 12 }} onClick={() => window.print()}>
          <Icon name="download" /> Скачать PDF
        </button>
      </div>
    </aside>
  );
}

function Lightbox({ photos, index, onClose, onNav }) {
  useEffect(() => {
    if (index == null) return;
    const onKey = (e) => {
      if (e.key === "Escape") onClose();
      if (e.key === "ArrowLeft") onNav(-1);
      if (e.key === "ArrowRight") onNav(1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [index, onClose, onNav]);

  if (index == null) return null;
  const photo = photos[index];
  return (
    <div className="lightbox open" onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <img src={photo.url} alt={photo.caption || ""} />
      {photo.caption && <div className="lightbox-cap">{photo.caption}</div>}
      <button className="lightbox-close" onClick={onClose}><Icon name="close" /></button>
      <button className="lightbox-nav prev" onClick={() => onNav(-1)}><Icon name="chevronL" /></button>
      <button className="lightbox-nav next" onClick={() => onNav(1)}><Icon name="chevronR" /></button>
    </div>
  );
}

/* ─── Main app ─── */
const TWEAK_DEFAULTS = /*EDITMODE-BEGIN*/{
  "property": "office",
  "accent": "#c8a96a",
  "dark": true,
  "density": "regular",
  "fontPair": "serif",
  "showFinance": true,
  "showLocation": true,
  "showSpecs": true,
  "showFeatures": true,
  "showCalculator": true,
  "showAllData": true
}/*EDITMODE-END*/;

const ACCENT_PALETTE = {
  "#c8a96a": { deep: "#8a6f3e" },  // brass
  "#b8442e": { deep: "#7a2d1e" },  // terracotta
  "#1a3a2e": { deep: "#0f261d" },  // forest
  "#2a4a7f": { deep: "#1c3157" },  // navy
  "#e8e4dc": { deep: "#a8a394" }   // platinum
};

function FONT_PAIRS(name) {
  const pairs = {
    serif: { serif: '"Cormorant Garamond", "Playfair Display", Georgia, serif', sans: '"Inter", system-ui, sans-serif' },
    modern: { serif: '"Fraunces", Georgia, serif', sans: '"Manrope", system-ui, sans-serif' },
    minimal: { serif: '"Inter", system-ui, sans-serif', sans: '"Inter", system-ui, sans-serif' },
  };
  return pairs[name] || pairs.serif;
}

function App() {
  const [t, setTweak] = useTweaks(TWEAK_DEFAULTS);
  const [lightboxIdx, setLightboxIdx] = useState(null);
  const [shareMsg, setShareMsg] = useState("");

  const p = PROPERTIES[t.property] || PROPERTIES.office;

  // apply theme + accent + density + fonts to document
  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = t.dark ? "dark" : "light";
    root.dataset.density = t.density;
    const accentDeep = ACCENT_PALETTE[t.accent]?.deep || "#8a6f3e";
    root.style.setProperty("--accent", t.accent);
    root.style.setProperty("--accent-deep", accentDeep);
    const fp = FONT_PAIRS(t.fontPair);
    root.style.setProperty("--serif", fp.serif);
    root.style.setProperty("--sans", fp.sans);
  }, [t.dark, t.accent, t.density, t.fontPair]);

  // intersection animate
  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(en => {
        if (en.isIntersecting) en.target.classList.add("in");
      });
    }, { threshold: 0.08 });
    document.querySelectorAll("section.block").forEach(el => io.observe(el));
    return () => io.disconnect();
  }, [t.property, t.showFinance, t.showLocation, t.showSpecs, t.showFeatures, t.showCalculator, t.showAllData]);

  const onShare = (kind) => {
    const url = window.location.href;
    const title = encodeURIComponent(p.title);
    const links = {
      telegram: `https://t.me/share/url?url=${encodeURIComponent(url)}&text=${title}`,
      whatsapp: `https://wa.me/?text=${title}%20${encodeURIComponent(url)}`,
      vk: `https://vk.com/share.php?url=${encodeURIComponent(url)}&title=${title}`,
      copy: null
    };
    if (kind === "copy") {
      navigator.clipboard?.writeText(url);
      setShareMsg("Ссылка скопирована");
      setTimeout(() => setShareMsg(""), 2200);
    } else if (links[kind]) {
      window.open(links[kind], "_blank", "noopener");
    }
  };

  const onLightboxNav = (dir) => {
    const photos = p.photos || [];
    if (lightboxIdx == null) return;
    setLightboxIdx((lightboxIdx + dir + photos.length) % photos.length);
  };

  return (
    <>
      <header className="topbar">
        <div className="container topbar-inner">
          <a className="brand" href="#">
            <div className="brand-mark"></div>
            <div>
              <div className="brand-name">Novactiv</div>
            </div>
            <div className="brand-suffix" style={{ marginLeft: 8 }}>Real Estate</div>
          </a>
          <div className="topbar-actions">
            <button className="btn" onClick={() => onShare("copy")}>
              <Icon name="share" /> Поделиться
            </button>
            <button className="btn" onClick={() => window.print()}>
              <Icon name="download" /> PDF
            </button>
          </div>
        </div>
        {shareMsg && (
          <div style={{
            position: "absolute", top: 70, right: 32,
            background: "var(--accent)", color: "#1a1306",
            padding: "8px 14px", borderRadius: 8, fontSize: 12, fontWeight: 500
          }}>{shareMsg}</div>
        )}
      </header>

      <div className="layout">
        <main>
          <Hero p={p} onOpenLightbox={setLightboxIdx} />
          <Gallery p={p} onOpen={setLightboxIdx} />
          {t.showFinance && <Finance p={p} />}
          <KeyParams p={p} />
          {t.showFeatures && <Features p={p} />}
          {t.showLocation && <Location p={p} />}
          {t.showSpecs && <Specs p={p} />}
          {t.showCalculator && <Calculator p={p} />}
          {t.showAllData && <AllData p={p} />}
        </main>
        <StickyPanel p={p} onShare={onShare} />
      </div>

      <footer className="footer">
        <div className="container" style={{ display: "flex", justifyContent: "space-between", width: "100%", flexWrap: "wrap", gap: 16 }}>
          <div>© {new Date().getFullYear()} Novactiv. Все права защищены.</div>
          <div style={{ fontFamily: "var(--mono)" }}>
            ID объекта: {p.internal_id || p.quickdeal_id} · обновлено {p.updated_at || p.published_at || "—"}
          </div>
        </div>
      </footer>

      <Lightbox photos={p.photos || []} index={lightboxIdx}
        onClose={() => setLightboxIdx(null)} onNav={onLightboxNav} />

      <TweaksPanel>
        <TweakSection label="Объект" />
        <TweakRadio label="Тип данных" value={t.property}
          options={["office", "warehouse", "apartment"]}
          onChange={(v) => setTweak("property", v)} />

        <TweakSection label="Тема" />
        <TweakToggle label="Тёмная тема" value={t.dark} onChange={(v) => setTweak("dark", v)} />
        <TweakColor label="Акцент" value={t.accent}
          options={Object.keys(ACCENT_PALETTE)}
          onChange={(v) => setTweak("accent", v)} />
        <TweakSelect label="Шрифты" value={t.fontPair}
          options={[
            { value: "serif", label: "Cormorant + Inter" },
            { value: "modern", label: "Fraunces + Manrope" },
            { value: "minimal", label: "Inter only" }
          ]}
          onChange={(v) => setTweak("fontPair", v)} />
        <TweakRadio label="Плотность" value={t.density}
          options={["compact", "regular", "comfy"]}
          onChange={(v) => setTweak("density", v)} />

        <TweakSection label="Секции" />
        <TweakToggle label="Финансы" value={t.showFinance} onChange={(v) => setTweak("showFinance", v)} />
        <TweakToggle label="Преимущества" value={t.showFeatures} onChange={(v) => setTweak("showFeatures", v)} />
        <TweakToggle label="Локация" value={t.showLocation} onChange={(v) => setTweak("showLocation", v)} />
        <TweakToggle label="Характеристики" value={t.showSpecs} onChange={(v) => setTweak("showSpecs", v)} />
        <TweakToggle label="Калькулятор" value={t.showCalculator} onChange={(v) => setTweak("showCalculator", v)} />
        <TweakToggle label="Все данные" value={t.showAllData} onChange={(v) => setTweak("showAllData", v)} />
      </TweaksPanel>
    </>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
