import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../App';
import { toRequestBody } from '../farmRequest';
import { translations } from '../i18n/translations';

const OPTIONS = {
  crops: ['rice', 'maize', 'wheat'],
  seasons: ['kharif', 'winter'],
  districts: ['CUTTACK', 'PURI'],
  irrigation_methods: ['rainfed', 'canal'],
  ai_chat_enabled: false,
};

const REPORT = {
  soil: {
    n: { value: 200, rating: 'low' },
    p: { value: 18, rating: 'medium' },
    k: { value: 150, rating: 'medium' },
    ph: { value: 6.5, class: 'normal' },
    sources: [{ title: 'Rating source', url: 'https://example.org/rating' }],
  },
  fertilizer: {
    status: 'available',
    dose_kg_per_ha: { n: 80, p2o5: 40, k2o: 40 },
    products_kg_per_ha: { urea: 139.9, dap: 87, mop: 66.7 },
    products_kg_for_field: { urea: 283.1, dap: 176, mop: 135 },
    source: { title: 'Dose source', url: 'https://example.org/dose' },
  },
  climate: { status: 'available', avg_temp_c: 24, rainfall_mm: 400, source: 'NASA' },
  yield_forecast: {
    status: 'available',
    t_per_ha: 2.5,
    low_t_per_ha: 1.8,
    high_t_per_ha: 3.2,
    recent_average_t_per_ha: 2.4,
    last_recorded_season: '2019-20',
    total_tonnes_for_field: 5.06,
  },
  advice: { water: ['rain_moderate'], pest: ['rotation_general'] },
};

const json = (body, status = 200) => ({ ok: status < 400, status, json: async () => body });

function mockApi(handlers = {}) {
  globalThis.fetch = vi.fn(async (url) => {
    if (url.endsWith('/api/options')) return json(OPTIONS);
    if (url.endsWith('/api/analyze')) return handlers.analyze?.() ?? json(REPORT);
    if (url.endsWith('/api/chat')) return handlers.chat?.() ?? json({ reply: 'Use 283 kg urea.', mode: 'offline' });
    throw new Error(`Unexpected request: ${url}`);
  });
}

const submit = async (user) => {
  await user.click(await screen.findByRole('button', { name: translations.en.useSample }));
  await user.click(screen.getByRole('button', { name: translations.en.submit }));
};

describe('farm report', () => {
  beforeEach(() => mockApi());

  it('sends the farm and shows the report with its source', async () => {
    const user = userEvent.setup();
    render(<App />);
    await submit(user);

    expect(await screen.findByText(translations.en.reportTitle)).toBeInTheDocument();
    expect(screen.getByText('283.1 kg')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Dose source' })).toHaveAttribute('href', 'https://example.org/dose');

    const [, request] = globalThis.fetch.mock.calls.find(([url]) => url.endsWith('/api/analyze'));
    expect(JSON.parse(request.body)).toMatchObject({ crop: 'rice', district: 'CUTTACK', field_acres: 5 });
  });

  it('does not submit invented soil values', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole('button', { name: translations.en.submit }));

    expect(screen.getByLabelText(translations.en.nitrogen)).toHaveValue(null);
    expect(globalThis.fetch.mock.calls.some(([url]) => url.endsWith('/api/analyze'))).toBe(false);
  });

  it('says so instead of inventing a dose when none is verified', async () => {
    mockApi({
      analyze: () => json({ ...REPORT, fertilizer: { status: 'no_verified_dose' } }),
    });
    const user = userEvent.setup();
    render(<App />);
    await submit(user);
    expect(await screen.findByText(translations.en.noDose)).toBeInTheDocument();
  });

  it('suggests seasons with data when there is no forecast', async () => {
    mockApi({
      analyze: () =>
        json({
          ...REPORT,
          yield_forecast: { status: 'insufficient_history', seasons_with_recent_data: ['winter'] },
        }),
    });
    const user = userEvent.setup();
    render(<App />);
    await submit(user);
    expect(await screen.findByText(/Recent data exists for: Winter/)).toBeInTheDocument();
  });

  it('highlights fields the API rejects', async () => {
    mockApi({
      analyze: () => json({ error: 'invalid_input', fields: [{ field: 'nitrogen', message: 'x' }] }, 422),
    });
    const user = userEvent.setup();
    render(<App />);
    await submit(user);
    expect(await screen.findByText(translations.en.errorInvalid)).toBeInTheDocument();
    expect(screen.getByLabelText(translations.en.nitrogen)).toHaveAttribute('aria-invalid', 'true');
  });

  it('shows an error when the server is down', async () => {
    globalThis.fetch = vi.fn().mockRejectedValue(new TypeError('Failed to fetch'));
    render(<App />);
    expect(await screen.findByText(translations.en.errorNetwork)).toBeInTheDocument();
  });

  it('switches language across the interface', async () => {
    const user = userEvent.setup();
    render(<App />);
    await screen.findByRole('button', { name: translations.en.submit });
    await user.selectOptions(screen.getByLabelText(translations.en.language), 'or');
    expect(screen.getByRole('button', { name: translations.or.submit })).toBeInTheDocument();
    await waitFor(() => expect(document.documentElement.lang).toBe('or'));
  });
});

describe('chat', () => {
  beforeEach(() => mockApi());

  it('sends the question with the language and shows the reply', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(await screen.findByLabelText(translations.en.chatPlaceholder), 'How much urea?');
    await user.click(screen.getByRole('button', { name: translations.en.chatSend }));

    expect(await screen.findByText('Use 283 kg urea.')).toBeInTheDocument();
    const [, request] = globalThis.fetch.mock.calls.find(([url]) => url.endsWith('/api/chat'));
    expect(JSON.parse(request.body)).toMatchObject({
      language: 'en',
      messages: [{ role: 'user', content: 'How much urea?' }],
    });
  });

  it('shows the mode that actually answered', async () => {
    globalThis.fetch = vi.fn(async (url) =>
      url.endsWith('/api/options')
        ? json({ ...OPTIONS, ai_chat_enabled: true })
        : json({ reply: 'Fallback answer.', mode: 'offline' }),
    );
    const user = userEvent.setup();
    render(<App />);
    expect(await screen.findByText(translations.en.chatAi)).toBeInTheDocument();
    await user.type(screen.getByLabelText(translations.en.chatPlaceholder), 'Hi');
    await user.click(screen.getByRole('button', { name: translations.en.chatSend }));
    expect(await screen.findByText(translations.en.chatOffline)).toBeInTheDocument();
  });

  it('starts long histories with a user message', async () => {
    const user = userEvent.setup();
    render(<App />);
    const input = await screen.findByLabelText(translations.en.chatPlaceholder);
    for (let turn = 0; turn < 7; turn += 1) {
      await user.type(input, `Question ${turn}`);
      await user.click(screen.getByRole('button', { name: translations.en.chatSend }));
      await waitFor(() => expect(screen.getAllByText('Use 283 kg urea.')).toHaveLength(turn + 1));
    }
    const [, request] = globalThis.fetch.mock.calls.filter(([url]) => url.endsWith('/api/chat')).at(-1);
    const { messages } = JSON.parse(request.body);
    expect(messages).toHaveLength(11);
    expect(messages[0].role).toBe('user');
    expect(messages.at(-1).content).toBe('Question 6');
  });

  it('keeps the question for retry when sending fails', async () => {
    mockApi({ chat: () => json({ error: 'rate_limited' }, 429) });
    const user = userEvent.setup();
    render(<App />);
    const input = await screen.findByLabelText(translations.en.chatPlaceholder);
    await user.type(input, 'Hello');
    await user.click(screen.getByRole('button', { name: translations.en.chatSend }));

    expect(await screen.findByText(translations.en.errorRateLimited)).toBeInTheDocument();
    expect(input).toHaveValue('Hello');
  });
});

describe('translations', () => {
  const shapeOf = (value) =>
    typeof value === 'object'
      ? Object.fromEntries(Object.entries(value).map(([k, v]) => [k, Array.isArray(v) ? v.length : shapeOf(v)]))
      : 'text';

  it.each(['hi', 'or'])('%s has the same keys as English', (language) => {
    expect(shapeOf(translations[language])).toEqual(shapeOf(translations.en));
  });

  it('Odia text contains no characters from other Indian scripts', () => {
    const text = JSON.stringify(translations.or);
    // Devanagari and Gujarati, excluding the danda (U+0964, U+0965) that Odia also uses.
    expect(text).not.toMatch(/[\u0900-\u0963\u0966-\u097F\u0A80-\u0AFF]/);
  });
});

describe('toRequestBody', () => {
  it('converts numbers and drops blank optional fields', () => {
    expect(toRequestBody({ crop: 'rice', field_acres: '2.5', soil_ph: '', previous_crop: '' })).toEqual({
      crop: 'rice',
      field_acres: 2.5,
    });
  });
});
