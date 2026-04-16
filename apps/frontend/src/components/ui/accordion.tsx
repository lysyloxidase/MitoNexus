"use client";

import { type HTMLAttributes, type ReactNode, createContext, useContext, useState } from "react";

import { cn } from "@/lib/utils";

type AccordionMode = "single" | "multiple";

type AccordionContextValue = {
  openValues: string[];
  toggle: (value: string) => void;
};

const AccordionContext = createContext<AccordionContextValue | null>(null);
const AccordionItemContext = createContext<string | null>(null);

type AccordionProps = {
  children: ReactNode;
  className?: string;
  defaultValue?: string[];
  type?: AccordionMode;
};

type AccordionItemProps = HTMLAttributes<HTMLDivElement> & {
  value: string;
};

export function Accordion({
  children,
  className,
  defaultValue = [],
  type = "multiple",
}: AccordionProps) {
  const [openValues, setOpenValues] = useState<string[]>(defaultValue);

  const contextValue: AccordionContextValue = {
    openValues,
    toggle: (value) => {
      setOpenValues((current) => {
        if (type === "single") {
          return current.includes(value) ? [] : [value];
        }

        return current.includes(value)
          ? current.filter((entry) => entry !== value)
          : [...current, value];
      });
    },
  };

  return (
    <AccordionContext.Provider value={contextValue}>
      <div className={cn("space-y-4", className)}>{children}</div>
    </AccordionContext.Provider>
  );
}

export function AccordionItem({ children, className, value, ...props }: AccordionItemProps) {
  return (
    <AccordionItemContext.Provider value={value}>
      <div
        className={cn(
          "overflow-hidden rounded-[1.5rem] border border-white/10 bg-white/5",
          className,
        )}
        {...props}
      >
        {children}
      </div>
    </AccordionItemContext.Provider>
  );
}

type AccordionTriggerProps = HTMLAttributes<HTMLButtonElement>;

export function AccordionTrigger({ children, className, ...props }: AccordionTriggerProps) {
  const accordion = useContext(AccordionContext);
  const itemValue = useContext(AccordionItemContext);

  if (accordion === null || itemValue === null) {
    throw new Error("AccordionTrigger must be used inside AccordionItem.");
  }

  const isOpen = accordion.openValues.includes(itemValue);

  return (
    <button
      className={cn(
        "flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-base font-semibold text-white transition hover:bg-white/5",
        className,
      )}
      onClick={() => accordion.toggle(itemValue)}
      type="button"
      {...props}
    >
      <span>{children}</span>
      <span className="text-lg text-emerald-300">{isOpen ? "-" : "+"}</span>
    </button>
  );
}

type AccordionContentProps = {
  children: ReactNode;
  className?: string;
};

export function AccordionContent({ children, className }: AccordionContentProps) {
  const accordion = useContext(AccordionContext);
  const itemValue = useContext(AccordionItemContext);

  if (accordion === null || itemValue === null) {
    throw new Error("AccordionContent must be used inside AccordionItem.");
  }

  if (!accordion.openValues.includes(itemValue)) {
    return null;
  }

  return <div className={cn("px-5 pb-5", className)}>{children}</div>;
}
