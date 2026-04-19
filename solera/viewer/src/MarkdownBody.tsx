import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface MarkdownBodyProps {
  text: string;
}

/**
 * Renders a Solera body section (Intent / Current Design / Mission / ...) as
 * rich markdown. GFM is enabled for tables, task lists, and autolinks which
 * show up frequently in banas workspace files.
 */
export function MarkdownBody({ text }: MarkdownBodyProps) {
  return (
    <div className="markdown-body text-[12.5px] leading-relaxed text-slate-700">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: (props) => <h3 className="mt-3 mb-1 text-[14px] font-semibold" {...props} />,
          h2: (props) => <h4 className="mt-2.5 mb-1 text-[13px] font-semibold" {...props} />,
          h3: (props) => (
            <h5 className="mt-2 mb-0.5 text-[12px] font-semibold uppercase tracking-wide text-slate-500" {...props} />
          ),
          p: (props) => <p className="my-1.5" {...props} />,
          ul: (props) => <ul className="my-1.5 list-disc space-y-0.5 pl-4" {...props} />,
          ol: (props) => <ol className="my-1.5 list-decimal space-y-0.5 pl-4" {...props} />,
          li: (props) => <li className="leading-snug" {...props} />,
          blockquote: (props) => (
            <blockquote
              className="my-1.5 border-l-2 border-slate-300 pl-3 italic text-slate-500"
              {...props}
            />
          ),
          code: ({ className, children, ...rest }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code
                  className="rounded bg-slate-100 px-1 py-0.5 font-mono text-[11.5px] text-rose-600"
                  {...rest}
                >
                  {children}
                </code>
              );
            }
            return (
              <code
                className={`block whitespace-pre overflow-x-auto rounded bg-slate-50 p-2 font-mono text-[11px] ${className ?? ""}`}
                {...rest}
              >
                {children}
              </code>
            );
          },
          pre: (props) => <pre className="my-2" {...props} />,
          table: (props) => (
            <div className="my-2 overflow-x-auto">
              <table className="min-w-full border-collapse text-[11.5px]" {...props} />
            </div>
          ),
          th: (props) => (
            <th
              className="border border-slate-200 bg-slate-50 px-2 py-1 text-left font-semibold"
              {...props}
            />
          ),
          td: (props) => <td className="border border-slate-200 px-2 py-1 align-top" {...props} />,
          a: (props) => (
            <a className="text-sketch underline hover:text-indigo-700" {...props} />
          ),
          hr: () => <hr className="my-3 border-slate-200" />,
        }}
      >
        {text}
      </ReactMarkdown>
    </div>
  );
}
