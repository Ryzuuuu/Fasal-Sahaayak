const NUMERIC_FIELDS = [
  'field_acres', 'nitrogen', 'phosphorus', 'potassium', 'soil_ph', 'avg_temp_c', 'rainfall_mm',
];

// Empty optional fields are dropped so the API can apply its defaults.
export function toRequestBody(form) {
  const body = {};
  for (const [name, value] of Object.entries(form)) {
    if (value === '') continue;
    body[name] = NUMERIC_FIELDS.includes(name) ? Number(value) : value;
  }
  return body;
}
