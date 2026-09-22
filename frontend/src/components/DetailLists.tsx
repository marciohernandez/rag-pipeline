import type { ReactNode } from "react";

export interface DetailItem { label: string; value: ReactNode; }

export default function DetailLists({ items }: { items: DetailItem[] }) {
  return <dl className="grid grid-cols-1 rounded-lg border text-sm sm:grid-cols-[minmax(10rem,16rem)_1fr]">{items.map((item) => <div key={item.label} className="grid grid-cols-subgrid gap-1 border-b p-3 last:border-b-0 sm:col-span-2 sm:gap-4"><dt className="font-medium text-muted-foreground">{item.label}</dt><dd className="min-w-0 [overflow-wrap:anywhere]">{item.value}</dd></div>)}</dl>;
}
