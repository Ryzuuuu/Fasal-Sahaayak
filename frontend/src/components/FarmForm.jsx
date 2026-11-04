import { useState } from 'react';
import { toRequestBody } from '../farmRequest';

const INITIAL_FORM = {
  crop: 'rice',
  district: 'CUTTACK',
  season: 'winter',
  field_acres: '',
  nitrogen: '',
  phosphorus: '',
  potassium: '',
  soil_ph: '',
  irrigation: 'canal',
  previous_crop: '',
  avg_temp_c: '',
  rainfall_mm: '',
};

const SAMPLE_VALUES = {
  field_acres: '5',
  nitrogen: '200',
  phosphorus: '18',
  potassium: '150',
  soil_ph: '6.5',
};

const inputClass = (hasError) =>
  `mt-1 block w-full rounded-lg border bg-white px-3 py-2 text-stone-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-emerald-600 ${
    hasError ? 'border-red-500' : 'border-stone-300'
  }`;

function Field({ label, name, error, children }) {
  return (
    <div>
      <label htmlFor={name} className="block text-sm font-medium text-stone-700">
        {label}
      </label>
      {children}
      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm text-red-700">
          {error}
        </p>
      )}
    </div>
  );
}

function Section({ title, hint, children }) {
  return (
    <fieldset className="space-y-3">
      <legend className="text-base font-semibold text-emerald-900">{title}</legend>
      {hint && <p className="text-sm text-stone-500">{hint}</p>}
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </fieldset>
  );
}

export function FarmForm({ t, options, isLoading, fieldErrors, onSubmit }) {
  const [form, setForm] = useState(INITIAL_FORM);

  const update = (event) => {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  };

  const numberField = (name, label, props = {}) => (
    <Field label={label} name={name} error={fieldErrors[name] && t.fieldError}>
      <input
        id={name}
        name={name}
        type="number"
        step="any"
        min="0"
        value={form[name]}
        onChange={update}
        className={inputClass(Boolean(fieldErrors[name]))}
        aria-invalid={Boolean(fieldErrors[name])}
        aria-describedby={fieldErrors[name] ? `${name}-error` : undefined}
        {...props}
      />
    </Field>
  );

  const selectField = (name, label, choices, withEmptyChoice = false) => (
    <Field label={label} name={name} error={fieldErrors[name] && t.fieldError}>
      <select
        id={name}
        name={name}
        value={form[name]}
        onChange={update}
        className={inputClass(Boolean(fieldErrors[name]))}
      >
        {withEmptyChoice && <option value="">{t.notSure}</option>}
        {choices.map(([value, text]) => (
          <option key={value} value={value}>
            {text}
          </option>
        ))}
      </select>
    </Field>
  );

  const titleCase = (name) => name.charAt(0) + name.slice(1).toLowerCase();
  const crops = options.crops.map((id) => [id, t.crops[id]]);

  return (
    <form
      className="space-y-6 rounded-2xl bg-white p-5 shadow-sm ring-1 ring-stone-200 sm:p-6"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit(toRequestBody(form));
      }}
    >
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-xl font-bold text-stone-900">{t.formTitle}</h2>
        <button
          type="button"
          onClick={() => setForm((current) => ({ ...current, ...SAMPLE_VALUES }))}
          className="rounded-lg px-3 py-1 text-sm font-medium text-emerald-800 underline hover:bg-emerald-50 focus:outline-none focus:ring-2 focus:ring-emerald-600"
        >
          {t.useSample}
        </button>
      </div>

      <Section title={t.sectionFarm}>
        {selectField('crop', t.crop, crops)}
        {selectField('district', t.district, options.districts.map((d) => [d, titleCase(d)]))}
        {selectField('season', t.season, options.seasons.map((id) => [id, t.seasons[id]]))}
        {numberField('field_acres', t.fieldAcres, { required: true })}
      </Section>

      <Section title={t.sectionSoil} hint={t.sectionSoilHint}>
        {numberField('nitrogen', t.nitrogen, { required: true })}
        {numberField('phosphorus', t.phosphorus, { required: true })}
        {numberField('potassium', t.potassium, { required: true })}
        {numberField('soil_ph', t.soilPh, { max: 14 })}
      </Section>

      <Section title={t.sectionWater}>
        {selectField(
          'irrigation',
          t.irrigation,
          options.irrigation_methods.map((id) => [id, t.irrigationMethods[id]]),
        )}
        {selectField('previous_crop', t.previousCrop, crops, true)}
      </Section>

      <Section title={t.sectionWeather} hint={t.sectionWeatherHint}>
        {numberField('avg_temp_c', t.avgTemp)}
        {numberField('rainfall_mm', t.rainfall)}
      </Section>

      <button
        type="submit"
        disabled={isLoading}
        className="w-full rounded-lg bg-emerald-700 px-4 py-3 text-lg font-semibold text-white transition hover:bg-emerald-800 focus:outline-none focus:ring-2 focus:ring-emerald-600 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isLoading ? t.submitting : t.submit}
      </button>
    </form>
  );
}
