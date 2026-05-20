/**
 * Labeled textarea for long-form text (resume or job description).
 * Presentational only — parent owns value and onChange (controlled input).
 */

interface JDInputProps {
  id: string;
  label: string;
  placeholder: string;
  value: string;
  onChange: (value: string) => void;
  minLength?: number;
}

export default function JDInput({
  id,
  label,
  placeholder,
  value,
  onChange,
  minLength,
}: JDInputProps) {
  const charCount = value.trim().length;
  const showMinHint = minLength !== undefined && charCount > 0;

  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className="text-sm font-medium text-zinc-800">
        {label}
      </label>
      <textarea
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={10}
        className="w-full resize-y rounded-lg border border-zinc-300 bg-white px-3 py-2 text-sm text-zinc-900 placeholder:text-zinc-400 focus:border-zinc-500 focus:outline-none focus:ring-1 focus:ring-zinc-500"
      />
      {showMinHint && (
        <p
          className={`text-xs ${
            charCount >= minLength! ? "text-zinc-500" : "text-amber-700"
          }`}
        >
          {charCount} / {minLength} characters minimum
        </p>
      )}
    </div>
  );
}
