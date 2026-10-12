"use client";

import * as React from "react";
import { CheckIcon } from "lucide-react";
import { Menu } from "@base-ui/react/menu";
import { cn } from "cn";

function DropdownMenu(props: Menu.Root.Props) {
  return <Menu.Root {...props} />;
}

function DropdownMenuTrigger({ className, ...props }: Menu.Trigger.Props) {
  return <Menu.Trigger className={cn("outline-none", className)} {...props} />;
}

function DropdownMenuContent({ className, keepMounted, ...props }: Menu.Popup.Props & { keepMounted?: boolean }) {
  return (
    <Menu.Portal keepMounted={keepMounted}>
      <Menu.Positioner align="end" sideOffset={6} className="z-50 outline-none">
        <Menu.Popup
          className={cn(
            "min-w-44 origin-[var(--transform-origin)] rounded-lg border bg-popover p-1 text-popover-foreground shadow-md outline-none transition-[scale,opacity] duration-100 data-ending-style:scale-95 data-ending-style:opacity-0 data-starting-style:scale-95 data-starting-style:opacity-0",
            className,
          )}
          {...props}
        />
      </Menu.Positioner>
    </Menu.Portal>
  );
}

function DropdownMenuItem({ className, ...props }: Menu.Item.Props) {
  return (
    <Menu.Item
      className={cn(
        "flex cursor-default items-center rounded-md px-2 py-1.5 text-sm outline-none data-highlighted:bg-muted data-highlighted:text-foreground data-disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}

function DropdownMenuGroup(props: Menu.Group.Props) {
  return <Menu.Group {...props} />;
}

function DropdownMenuLabel({ className, ...props }: Menu.GroupLabel.Props) {
  return (
    <Menu.GroupLabel
      className={cn("px-2 py-1.5 text-xs font-medium text-muted-foreground", className)}
      {...props}
    />
  );
}

function DropdownMenuSeparator({ className, ...props }: Menu.Separator.Props) {
  return <Menu.Separator className={cn("-mx-1 my-1 h-px bg-border", className)} {...props} />;
}

function DropdownMenuRadioGroup(props: Menu.RadioGroup.Props) {
  return <Menu.RadioGroup {...props} />;
}

function DropdownMenuRadioItem({ className, children, ...props }: Menu.RadioItem.Props) {
  return (
    <Menu.RadioItem
      closeOnClick
      className={cn(
        "relative flex cursor-default items-center rounded-md py-1.5 pl-8 pr-2 text-sm outline-none data-highlighted:bg-muted data-highlighted:text-foreground data-disabled:opacity-50",
        className,
      )}
      {...props}
    >
      <span className="absolute left-2 flex size-4 items-center justify-center">
        <Menu.RadioItemIndicator><CheckIcon className="size-4" aria-hidden /></Menu.RadioItemIndicator>
      </span>
      {children}
    </Menu.RadioItem>
  );
}

export {
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
};
