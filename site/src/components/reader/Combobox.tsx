import { useState, type ReactNode } from "react";
import { ChevronDownIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

export interface ComboboxItem {
  value: string;
  label: string;
  /** Extra text the search also matches. */
  keywords?: string;
  hint?: string;
  group?: string;
}

interface Props {
  items: ComboboxItem[];
  selected: string[];
  onToggle: (value: string) => void;
  /** Close after a choice (single select) or stay open (multi select). */
  multiple?: boolean;
  /** What the trigger shows. */
  children: ReactNode;
  label: string;
  searchPlaceholder: string;
  className?: string;
  disabled?: boolean;
  onOpen?: () => void;
}

/** A searchable list in a popover, for lists too long for a plain select. */
export function Combobox({
  items,
  selected,
  onToggle,
  multiple = false,
  children,
  label,
  searchPlaceholder,
  className,
  disabled,
  onOpen,
}: Props) {
  const [open, setOpen] = useState(false);
  const groups = [...new Set(items.map((item) => item.group ?? ""))];

  return (
    <Popover
      open={open}
      onOpenChange={(next) => {
        setOpen(next);

        if (next) {
          onOpen?.();
        }
      }}
    >
      <PopoverTrigger
        render={
          <Button
            variant="outline"
            size="default"
            aria-label={label}
            disabled={disabled}
            className={cn("justify-between font-normal", className)}
          />
        }
      >
        <span className="min-w-0 truncate">{children}</span>
        <ChevronDownIcon className="text-muted-foreground" aria-hidden="true" />
      </PopoverTrigger>
      <PopoverContent align="start" className="w-72 gap-0 p-0 sm:w-80">
        <Command>
          <CommandInput placeholder={searchPlaceholder} aria-label={searchPlaceholder} />
          <CommandList className="max-h-64">
            <CommandEmpty>Nothing matches.</CommandEmpty>
            {groups.map((group) => (
              <CommandGroup key={group} heading={group || undefined}>
                {items
                  .filter((item) => (item.group ?? "") === group)
                  .map((item) => {
                    const isSelected = selected.includes(item.value);

                    return (
                      <CommandItem
                        key={item.value}
                        value={`${item.value} ${item.label} ${item.keywords ?? ""}`}
                        data-checked={isSelected}
                        onSelect={() => {
                          onToggle(item.value);

                          if (!multiple) {
                            setOpen(false);
                          }
                        }}
                      >
                        <span className="min-w-0 flex-1">
                          <span className="block truncate">{item.label}</span>
                          {item.hint ? (
                            <span className="text-muted-foreground block truncate text-xs">
                              {item.hint}
                            </span>
                          ) : null}
                        </span>
                      </CommandItem>
                    );
                  })}
              </CommandGroup>
            ))}
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
}
