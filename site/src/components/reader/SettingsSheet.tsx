import type { ReactNode } from "react";
import { XIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import type { Edition, ReaderBoot, Reciter, ReciterIndex, Script } from "@/lib/types";
import {
  ARABIC_SIZE_MAX,
  ARABIC_SIZE_MIN,
  MAX_TRANSLATIONS,
  editionKey,
  resolveFont,
  scriptReading,
  usableFonts,
  type ReaderPrefs,
} from "@/reader/core";
import { Combobox, type ComboboxItem } from "./Combobox";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  boot: ReaderBoot;
  prefs: ReaderPrefs;
  script: Script;
  onChange: (patch: Partial<ReaderPrefs>) => void;
  onToggleTranslation: (key: string) => void;
  reciterIndex: ReciterIndex | null;
  reciters: Reciter[];
  reciterError: string | null;
  onNeedReciters: () => void;
}

function Field({
  label,
  children,
  note,
}: {
  label: string;
  children: ReactNode;
  note?: ReactNode;
}) {
  return (
    <div className="space-y-1.5">
      <div className="text-[13px] font-medium">{label}</div>
      {children}
      {note ? <p className="text-muted-foreground text-xs">{note}</p> : null}
    </div>
  );
}

function ToggleRow({
  label,
  checked,
  disabled,
  onChange,
}: {
  label: string;
  checked: boolean;
  disabled?: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-3 text-[13px]">
      <span className={disabled ? "text-muted-foreground" : undefined}>{label}</span>
      <Switch checked={checked} disabled={disabled} onCheckedChange={onChange} aria-label={label} />
    </label>
  );
}

function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function SettingsSheet({
  open,
  onOpenChange,
  boot,
  prefs,
  script,
  onChange,
  onToggleTranslation,
  reciterIndex,
  reciters,
  reciterError,
  onNeedReciters,
}: Props) {
  const fontIds = usableFonts(boot.coverage, script.id);
  const fonts = boot.coverage.fonts.filter((font) => fontIds.includes(font.id));
  const activeFont = resolveFont(boot.coverage, script.id, prefs.font);
  const hafs = scriptReading(script) === "hafs" && script.verse_ids !== "mapped";
  const transliterations = boot.transliterations;
  const selectedTransliteration = transliterations.find(
    (edition) => editionKey(edition) === prefs.transliteration,
  );

  const translationItems: ComboboxItem[] = [...boot.translations]
    .sort((a, b) => `${a.language}${a.author}`.localeCompare(`${b.language}${b.author}`))
    .map((edition) => ({
      value: editionKey(edition),
      label: edition.author,
      group: capitalize(edition.language ?? ""),
      keywords: `${edition.language} ${edition.code} ${editionKey(edition)}`,
    }));

  const reciterItems: ComboboxItem[] = reciters.map((reciter) => ({
    value: reciter.id,
    label: reciter.name,
    hint: [
      reciter.scope === "ayah" ? "per ayah" : "per surah",
      reciter.bitrate_kbps ? `${reciter.bitrate_kbps} kbps` : null,
    ]
      .filter(Boolean)
      .join(" · "),
    group: reciterIndex?.hosts[reciter.host]?.name ?? reciter.host,
    keywords: `${reciter.recitation ?? ""} ${reciter.host}`,
  }));
  const selectedReciter = reciters.find((reciter) => reciter.id === prefs.reciter);

  const editionByKey = (key: string): Edition | undefined =>
    boot.translations.find((edition) => editionKey(edition) === key);

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full gap-0 sm:max-w-sm">
        <SheetHeader className="border-b">
          <SheetTitle>Settings</SheetTitle>
          <SheetDescription className="sr-only">
            Script, font, translations, transliteration and recitation.
          </SheetDescription>
        </SheetHeader>
        <div className="min-h-0 flex-1 space-y-5 overflow-y-auto p-4">
          <Field label="Script" note={script.description}>
            <Select
              value={script.id}
              onValueChange={(value) => value && onChange({ script: value })}
              items={boot.scripts.map((entry) => ({ value: entry.id, label: entry.name }))}
            >
              <SelectTrigger className="w-full" aria-label="Script">
                <SelectValue />
              </SelectTrigger>
              <SelectContent alignItemWithTrigger={false}>
                {boot.scripts.map((entry) => (
                  <SelectItem key={entry.id} value={entry.id}>
                    {entry.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field
            label="Arabic font"
            note={
              fonts.length < 2 ? "Only one font covers every character of this script." : undefined
            }
          >
            <Select
              value={activeFont ?? ""}
              onValueChange={(value) => value && onChange({ font: value })}
              items={fonts.map((font) => ({ value: font.id, label: font.name }))}
            >
              <SelectTrigger className="w-full" aria-label="Arabic font">
                <SelectValue />
              </SelectTrigger>
              <SelectContent alignItemWithTrigger={false}>
                {fonts.map((font) => (
                  <SelectItem key={font.id} value={font.id}>
                    {font.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field label={`Arabic size: ${prefs.size}px`}>
            <Slider
              value={[prefs.size]}
              min={ARABIC_SIZE_MIN}
              max={ARABIC_SIZE_MAX}
              step={1}
              onValueChange={(value) => {
                const next = Array.isArray(value) ? value[0] : value;

                onChange({ size: next });
              }}
              aria-label="Arabic size"
            />
          </Field>

          <Field
            label={`Translations (up to ${MAX_TRANSLATIONS})`}
            note="Translations follow Hafs verse numbering and are joined to other readings through each verse's Hafs map."
          >
            <Combobox
              items={translationItems}
              selected={prefs.translations}
              onToggle={onToggleTranslation}
              multiple
              label="Add or remove translations"
              searchPlaceholder="Search language or translator"
              className="w-full"
            >
              {prefs.translations.length === 0
                ? "None selected"
                : `${prefs.translations.length} selected`}
            </Combobox>
            {prefs.translations.length > 0 ? (
              <ul className="space-y-1">
                {prefs.translations.map((key) => (
                  <li
                    key={key}
                    className="bg-muted flex items-center justify-between gap-2 rounded-md py-0.5 pr-0.5 pl-2 text-[13px]"
                  >
                    <span className="min-w-0 truncate">{editionByKey(key)?.author ?? key}</span>
                    <Button
                      variant="ghost"
                      size="icon-xs"
                      aria-label={`Remove ${editionByKey(key)?.author ?? key}`}
                      onClick={() => onToggleTranslation(key)}
                    >
                      <XIcon aria-hidden="true" />
                    </Button>
                  </li>
                ))}
              </ul>
            ) : null}
          </Field>

          <Field
            label="Transliteration"
            note={
              transliterations.length === 0
                ? "None published yet."
                : !hafs
                  ? "Transliteration is generated from the Hafs reading, so it is off for this script."
                  : selectedTransliteration?.review
            }
          >
            {transliterations.length === 0 ? null : (
              <Select
                value={prefs.transliteration ?? "none"}
                onValueChange={(value) =>
                  onChange({ transliteration: value && value !== "none" ? value : null })
                }
                disabled={!hafs}
                items={[
                  { value: "none", label: "None" },
                  ...transliterations.map((edition) => ({
                    value: editionKey(edition),
                    label: edition.name ?? edition.author,
                  })),
                ]}
              >
                <SelectTrigger className="w-full" aria-label="Transliteration">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent alignItemWithTrigger={false}>
                  <SelectItem value="none">None</SelectItem>
                  {transliterations.map((edition) => (
                    <SelectItem key={editionKey(edition)} value={editionKey(edition)}>
                      {edition.name ?? edition.author}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </Field>

          {boot.audio ? (
            <Field
              label="Reciter"
              note={
                reciterError ??
                (reciterIndex && reciters.length === 0
                  ? `No recording matches the reading of ${script.name}.`
                  : "Only recordings of this script's reading are listed.")
              }
            >
              <Combobox
                items={reciterItems}
                selected={prefs.reciter ? [prefs.reciter] : []}
                onToggle={(value) => onChange({ reciter: value })}
                label="Reciter"
                searchPlaceholder="Search reciters"
                className="w-full"
                onOpen={onNeedReciters}
                disabled={reciterIndex !== null && reciters.length === 0}
              >
                {selectedReciter?.name ?? (reciterIndex ? "Choose a reciter" : "Choose a reciter")}
              </Combobox>
            </Field>
          ) : null}

          <Field label="Show">
            <div className="space-y-2.5">
              <ToggleRow
                label="Arabic"
                checked={prefs.showArabic}
                onChange={(value) => onChange({ showArabic: value })}
              />
              <ToggleRow
                label="Transliteration"
                checked={prefs.showTransliteration}
                disabled={transliterations.length === 0 || !hafs}
                onChange={(value) => onChange({ showTransliteration: value })}
              />
              <ToggleRow
                label="Translations"
                checked={prefs.showTranslations}
                onChange={(value) => onChange({ showTranslations: value })}
              />
            </div>
          </Field>
        </div>
      </SheetContent>
    </Sheet>
  );
}
