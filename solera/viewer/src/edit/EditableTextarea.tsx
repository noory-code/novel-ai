import { useEffect, useRef } from "react";
import { useInlineEdit } from "./useInlineEdit";

export interface EditableTextareaProps {
  value: string;
  onSave: (next: string) => Promise<void>;
  placeholder?: string;
  className?: string;
  textareaClassName?: string;
  ariaLabel: string;
  rows?: number;
  disabled?: boolean;
}

/**
 * Multi-line click-to-edit text. Ctrl/Cmd+Enter commits, Esc cancels,
 * blur commits. Unlike :class:`EditableText`, plain Enter inserts a
 * newline so long-form descriptions (Role.description, Narrative.statement,
 * Concept.intent) can flow naturally.
 */
export function EditableTextarea({
  value,
  onSave,
  placeholder,
  className,
  textareaClassName,
  ariaLabel,
  rows = 3,
  disabled,
}: EditableTextareaProps) {
  const edit = useInlineEdit<string>({ value, save: onSave });
  const taRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (edit.status === "editing" && taRef.current) {
      taRef.current.focus();
      taRef.current.select();
    }
  }, [edit.status]);

  const isEditing = edit.status === "editing" || edit.status === "saving";

  if (!isEditing) {
    const hasValue = value && value.trim().length > 0;
    return (
      <div
        className={className}
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={`${ariaLabel}. Click to edit.`}
        onClick={() => {
          if (!disabled) edit.beginEdit();
        }}
        onKeyDown={(e) => {
          if (disabled) return;
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            edit.beginEdit();
          }
        }}
        data-editable={disabled ? "disabled" : "idle"}
      >
        {hasValue ? (
          value
        ) : (
          <span className="italic text-slate-400">
            {placeholder ?? "(empty — click to edit)"}
          </span>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1">
      <textarea
        ref={taRef}
        value={edit.draft}
        rows={rows}
        onChange={(e) => edit.updateDraft(e.target.value)}
        onBlur={() => {
          if (edit.status === "editing") {
            void edit.commit();
          }
        }}
        onKeyDown={(e) => {
          // Cmd/Ctrl+Enter = save; plain Enter = newline.
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
            e.preventDefault();
            void edit.commit();
          } else if (e.key === "Escape") {
            e.preventDefault();
            edit.cancel();
          }
        }}
        className={
          textareaClassName ??
          "w-full rounded border border-slate-300 px-2 py-1 text-sm focus:border-indigo-600 focus:outline-none"
        }
        aria-label={ariaLabel}
        aria-invalid={edit.error ? true : undefined}
        disabled={edit.status === "saving"}
      />
      {edit.status === "saving" && (
        <span className="text-[10px] text-slate-500" role="status">
          saving…
        </span>
      )}
      {edit.error && (
        <span className="text-[10px] text-rose-700" role="alert">
          ⚠ {edit.error}
        </span>
      )}
    </div>
  );
}
