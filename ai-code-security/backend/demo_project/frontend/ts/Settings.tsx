import { useState } from "react";

interface Props {
  locale: string;
  currencyCode: string;
  onSave: (next: { locale: string; currency: string }) => void;
}

export default function Settings({ locale, currencyCode, onSave }: Props) {
  const [nextLocale, setNextLocale] = useState(locale);
  const [nextCurrency, setNextCurrency] = useState(currencyCode);
  const [saved, setSaved] = useState(false);

  function submit(event: React.FormEvent) {
    event.preventDefault();
    onSave({ locale: nextLocale, currency: nextCurrency });
    setSaved(true);
  }

  return (
    <form onSubmit={submit} className="settings-form">
      <label htmlFor="locale">Locale</label>
      <select
        id="locale"
        value={nextLocale}
        onChange={(event) => setNextLocale(event.target.value)}
      >
        <option value="en">English</option>
        <option value="es">Español</option>
        <option value="fr">Français</option>
      </select>

      <label htmlFor="currency">Currency</label>
      <input
        id="currency"
        value={nextCurrency}
        onChange={(event) => setNextCurrency(event.target.value.toUpperCase())}
        maxLength={3}
      />

      <button type="submit">Save settings</button>
      {saved && <p className="notice">Settings saved.</p>}
    </form>
  );
}
