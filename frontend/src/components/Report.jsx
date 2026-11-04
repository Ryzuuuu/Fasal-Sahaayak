function Card({ title, children }) {
  return (
    <section className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-stone-200">
      <h3 className="mb-3 text-lg font-bold text-emerald-900">{title}</h3>
      <div className="space-y-3 text-stone-700">{children}</div>
    </section>
  );
}

function Note({ children }) {
  return <p className="text-sm text-stone-500">{children}</p>;
}

function SourceLink({ t, source }) {
  return (
    <p className="text-xs text-stone-500">
      {t.source}:{' '}
      <a
        href={source.url}
        target="_blank"
        rel="noreferrer"
        className="underline hover:text-emerald-800"
      >
        {source.title}
      </a>
    </p>
  );
}

const RATING_STYLE = {
  low: 'bg-amber-100 text-amber-900',
  medium: 'bg-emerald-100 text-emerald-900',
  high: 'bg-sky-100 text-sky-900',
};

function SoilCard({ t, soil }) {
  const nutrients = [
    ['n', t.nutrientN],
    ['p', t.nutrientP],
    ['k', t.nutrientK],
  ];
  const ratings = nutrients.map(([key]) => soil[key].rating);
  const advice = ['low', 'high'].filter((rating) => ratings.includes(rating));
  if (soil.ph && soil.ph.class !== 'normal') advice.push(soil.ph.class);

  return (
    <Card title={t.soilCard}>
      <dl className="grid grid-cols-3 gap-2 text-center">
        {nutrients.map(([key, label]) => (
          <div key={key} className="rounded-lg bg-stone-50 p-2">
            <dt className="text-xs text-stone-500">{label}</dt>
            <dd className="font-semibold text-stone-900">{soil[key].value}</dd>
            <dd
              className={`mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium ${RATING_STYLE[soil[key].rating]}`}
            >
              {t.ratings[soil[key].rating]}
            </dd>
          </div>
        ))}
      </dl>
      {soil.ph && (
        <p>
          {t.ph}: <strong>{soil.ph.value}</strong> ({t.phClasses[soil.ph.class]})
        </p>
      )}
      {advice.map((code) => (
        <p key={code}>{t.soilAdvice[code]}</p>
      ))}
      {soil.sources.map((source) => (
        <SourceLink key={source.url} t={t} source={source} />
      ))}
    </Card>
  );
}

function FertilizerCard({ t, plan }) {
  if (plan.status !== 'available') {
    return (
      <Card title={t.fertilizerCard}>
        <p>{t.noDose}</p>
      </Card>
    );
  }
  const { n, p2o5, k2o } = plan.dose_kg_per_ha;
  const products = ['urea', 'dap', 'mop'];
  return (
    <Card title={t.fertilizerCard}>
      <table className="w-full text-left">
        <thead className="text-xs text-stone-500">
          <tr>
            <th scope="col" className="py-1 font-medium" />
            <th scope="col" className="py-1 font-medium">{t.productsTitle}</th>
            <th scope="col" className="py-1 font-medium">{t.perHectare}</th>
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product} className="border-t border-stone-100">
              <th scope="row" className="py-2 font-medium text-stone-900">{t[product]}</th>
              <td className="py-2 font-semibold text-stone-900">
                {plan.products_kg_for_field[product]} {t.kg}
              </td>
              <td className="py-2">{plan.products_kg_per_ha[product]} {t.kg}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="text-sm">
        {t.doseLabel}: N {n}, P₂O₅ {p2o5}, K₂O {k2o} ({t.kg})
      </p>
      <Note>{t.fertilizerNote}</Note>
      <SourceLink t={t} source={plan.source} />
    </Card>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex justify-between gap-4">
      <dt>{label}</dt>
      <dd className="font-medium">{children}</dd>
    </div>
  );
}

function YieldCard({ t, forecast }) {
  if (forecast.status !== 'available') {
    const seasons = forecast.seasons_with_recent_data ?? [];
    return (
      <Card title={t.yieldCard}>
        <p>{t.noForecast}</p>
        <p>
          {seasons.length > 0
            ? `${t.trySeasons}: ${seasons.map((id) => t.seasons[id]).join(', ')}`
            : t.noSeasons}
        </p>
      </Card>
    );
  }
  return (
    <Card title={t.yieldCard}>
      <p className="text-sm text-stone-500">{t.forecastLabel}</p>
      <p className="text-3xl font-bold text-stone-900">
        {forecast.t_per_ha} <span className="text-base font-medium">{t.tPerHa}</span>
      </p>
      <dl className="space-y-1 text-sm">
        <Row label={t.likelyRange}>
          {forecast.low_t_per_ha}–{forecast.high_t_per_ha} {t.tPerHa}
        </Row>
        <Row label={t.recentAverage}>
          {forecast.recent_average_t_per_ha} {t.tPerHa}
        </Row>
        <Row label={t.lastRecord}>{forecast.last_recorded_season}</Row>
        <Row label={t.fieldTotal}>
          {forecast.total_tonnes_for_field} {t.tonnes}
        </Row>
      </dl>
      <Note>{t.yieldNote}</Note>
    </Card>
  );
}

function WaterCard({ t, climate, codes }) {
  return (
    <Card title={t.waterCard}>
      {climate.status === 'available' && (
        <>
          <p>
            {t.climateLine
              .replace('{rain}', Math.round(climate.rainfall_mm))
              .replace('{temp}', climate.avg_temp_c)}
          </p>
          <Note>{climate.source === 'user_input' ? t.climateFromUser : t.climateFromNasa}</Note>
        </>
      )}
      {codes.map((code) => (
        <p key={code}>{t.waterAdvice[code]}</p>
      ))}
    </Card>
  );
}

export function Report({ t, report }) {
  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold text-stone-900">{t.reportTitle}</h2>
      <div className="grid gap-4 md:grid-cols-2">
        <FertilizerCard t={t} plan={report.fertilizer} />
        <YieldCard t={t} forecast={report.yield_forecast} />
        <SoilCard t={t} soil={report.soil} />
        <div className="space-y-4">
          <WaterCard t={t} climate={report.climate} codes={report.advice.water} />
          <Card title={t.pestCard}>
            {report.advice.pest.map((code) => (
              <p key={code}>{t.pestAdvice[code]}</p>
            ))}
          </Card>
        </div>
      </div>
    </div>
  );
}
